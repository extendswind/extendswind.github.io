---
title: "Hadoop集群对datanode宕机后的处理机制源码阅读"
date: 2021-12-06T16:00:00+08:00
toc: true

categories:
- "cloud computing"

tags:
- "hadoop"
---

总体上涉及了心跳检测、副本移除线程、副本恢复线程。当datanode发生宕机或者datanode中的某个storage（如一块硬盘）发生的错误时，namenode会根据datanode发送的心跳进行检测。但namenode并没有在心跳检测的汇报中进行即时反应，而是先记录对应的心跳信息，由另一个定期检测线程移除DatanodeManager和BlockManager中对应的block信息，并记录需要恢复的数据。对于数据的恢复，又新建了一个线程进行定期扫描，分配恢复副本需要的源数据节点和目标数据节点，在datanode的下一轮心跳检测中转换为对应的命令返回给datanode。

# 宕机的心跳检测

datanode会定时向namenode发送心跳数据包汇报当前的运行状态。namenode在一定时间内没收到数据节点的心跳时会标记为stale状态，然后转移该数据节点中的block到其它的数据节点。

hdfs配置中的几个参数：

- `dfs.heartbeat.interval`，Hadoop心跳检测间隔，默认为3s。
- `dfs.namenode.stale.datanode.minimum.interval`，datanode标记为stale状态的需要丢失的最小心跳次数，默认为3。
- `dfs.namenode.stale.datanode.interval`，Hadoop datanode超时范围，超过此时间没收到心跳检测会被标记为stale状态，默认为30s，大小必须超过前面两个参数的乘积。

# 接收心跳消息

Hadoop的datanode心跳检测通过rpc的形式发送，rpc函数通过参数传递数据节点统计信息，返回namenode需要对数据节点的命令。

datanode在通过rpc发送消息时，namenode首先在rpc server处理，交给NameSystem。NameNodeRpcServer中的处理：

```java
@Override // DatanodeProtocol
public HeartbeatResponse sendHeartbeat(DatanodeRegistration nodeReg,
    StorageReport[] report, long dnCacheCapacity, long dnCacheUsed,
    int xmitsInProgress, int xceiverCount,
    int failedVolumes, VolumeFailureSummary volumeFailureSummary,
    boolean requestFullBlockReportLease,
    @Nonnull SlowPeerReports slowPeers,
    @Nonnull SlowDiskReports slowDisks) throws IOException {
  checkNNStartup();
  verifyRequest(nodeReg);
  return namesystem.handleHeartbeat(nodeReg, report,
      dnCacheCapacity, dnCacheUsed, xceiverCount, xmitsInProgress,
      failedVolumes, volumeFailureSummary, requestFullBlockReportLease,
      slowPeers, slowDisks);
}
```

namesystem的类型为FSNamesystem，负责name-space state的相关管理（is a container of both transient and persisted name-space state, and does all the book-keeping work on a NameNode），是BlockManager, DatanodeManager, DelegationTokens, LeaseManager等服务的容器。在handleHeartbeat函数中，通过blockManager获取的DatanodeManager进行了处理：

```java
DatanodeCommand[] cmds = blockManager.getDatanodeManager().handleHeartbeat(
  nodeReg, reports, getBlockPoolId(), cacheCapacity, cacheUsed,
  xceiverCount, maxTransfer, failedVolumes, volumeFailureSummary,
  slowPeers, slowDisks);
```

然后DatanodeManager中调用HeartbeatManager进行了处理：

```java
heartbeatManager.updateHeartbeat(nodeinfo, reports, cacheCapacity,
        cacheUsed, xceiverCount, failedVolumes, volumeFailureSummary);
```

# HeartbeatManager中心跳的处理

HeartbeatManager类负责心跳的处理，心跳的处理并没有在接收到心跳消息后，而是用了一个额外的线程进行处理，默认每5min进行一次状态扫描。可能是某些处理中需要多个datanode的信息，所以没有直接对单个datanode发送消息时回复。对于datanodeManager中记录的有问题的datanode和storage，直接进行移除。此处只负责移除namenode（BlockManager和DatanodeManager等）中的datanode信息，对于丢失副本的恢复过程并不处理。

一个Monitor内部类实现了Runnable接口，负责监测线程的运行。`private final Daemon heartbeatThread = new Daemon(new Monitor());`。在当前的时间与上次检测的时间超过heartbeatRecheckInterval时，会调用heartbeatCheck()函数进行处理。

heartbeatCheck()函数中。每次循环首先遍历DatanodeManager中的所有的datanode状态以及每个datanode中的storage状态，统计发生错误的datanode和storage（每个datanode上可能有多个storage，标记datanode运行正常但是storage出现问题的情况）；然后通过DatanodeManager和BlockManager处理其中第一个datanode和storage，直至所有存在问题的datanode和storage都被处理完。

```java
  public void run() {
    while(namesystem.isRunning()) {
      restartHeartbeatStopWatch();
      try {
        final long now = Time.monotonicNow();
        if (lastHeartbeatCheck + heartbeatRecheckInterval < now) {
          heartbeatCheck();
          lastHeartbeatCheck = now;
        }
	  // ....
     }
  }
	
	
  void heartbeatCheck() {
    final DatanodeManager dm = blockManager.getDatanodeManager();
    // It's OK to check safe mode w/o taking the lock here, we re-check
    // for safe mode after taking the lock before removing a datanode.
    if (namesystem.isInStartupSafeMode()) {
      return;
    }
    boolean allAlive = false;
    while (!allAlive) {
      // locate the first dead node.
      DatanodeDescriptor dead = null;

      // locate the first failed storage that isn't on a dead node.
      DatanodeStorageInfo failedStorage = null;

      // check the number of stale nodes
      int numOfStaleNodes = 0;
      int numOfStaleStorages = 0;
      synchronized(this) {
        for (DatanodeDescriptor d : datanodes) {
          // check if an excessive GC pause has occurred
          if (shouldAbortHeartbeatCheck(0)) {
            return;
          }
          if (dead == null && dm.isDatanodeDead(d)) {
            stats.incrExpiredHeartbeats();
            dead = d;
          }
          if (d.isStale(dm.getStaleInterval())) {
            numOfStaleNodes++;
          }
          DatanodeStorageInfo[] storageInfos = d.getStorageInfos();
          for(DatanodeStorageInfo storageInfo : storageInfos) {
            if (storageInfo.areBlockContentsStale()) {
              numOfStaleStorages++;
            }
            if (failedStorage == null &&
                storageInfo.areBlocksOnFailedStorage() &&
                d != dead) {
              failedStorage = storageInfo;
            }
          }
        }
        
        // Set the number of stale nodes in the DatanodeManager
        dm.setNumStaleNodes(numOfStaleNodes);
        dm.setNumStaleStorages(numOfStaleStorages);
      }

      allAlive = (dead == null && failedStorage == null);
      if (!allAlive && namesystem.isInStartupSafeMode()) {
        return;
      }
      if (dead != null) {
        // acquire the fsnamesystem lock, and then remove the dead node.
        namesystem.writeLock();
        try {
          dm.removeDeadDatanode(dead, !dead.isMaintenance());
        } finally {
          namesystem.writeUnlock();
        }
      }
      if (failedStorage != null) {
        // acquire the fsnamesystem lock, and remove blocks on the storage.
        namesystem.writeLock();
        try {
          blockManager.removeBlocksAssociatedTo(failedStorage);
        } finally {
          namesystem.writeUnlock();
        }
      }
    }
  }
```

dm.removeDeadDatanode(dead, !dead.isMaintenance())。在removeDeadDatanode函数中又调用了removeDatanode处理datanode的删除逻辑。删除heartbeatManager中记录的datanode、blockManager中相关的block、DatanodeManager内部（networktopology）的datanode记录、版本信息处理、blockManager中的租约信息。

```java
  private void removeDatanode(DatanodeDescriptor nodeInfo,
      boolean removeBlocksFromBlocksMap) {
    assert namesystem.hasWriteLock();
    heartbeatManager.removeDatanode(nodeInfo);
    if (removeBlocksFromBlocksMap) {
      blockManager.removeBlocksAssociatedTo(nodeInfo);
    }
    networktopology.remove(nodeInfo);
    decrementVersionCount(nodeInfo.getSoftwareVersion());
    blockManager.getBlockReportLeaseManager().unregister(nodeInfo);

    if (LOG.isDebugEnabled()) {
      LOG.debug("remove datanode " + nodeInfo);
    }
    blockManager.checkSafeMode();
  }
```

# 恢复数据

当数据节点被判断为丢失时，blockManager在删除数据节点内的block信息的同时，会将block加入到pendingReconstruction类的列表中。BlockManager中的另一个线程会定期（默认3s）处理pendingReconstruction对象中的数据。

主要分成3步：1. 将block分为EC码block和副本block；2. 选择目标节点执行task；3. 将task放入到DatanodeDescriptor类的replicateBlocks队列中。

```java
  /**
   * Periodically calls computeBlockRecoveryWork().
   * 默认每3s调用一次block recovery的操作。
   */
  private class RedundancyMonitor implements Runnable {

    @Override
    public void run() {
      while (namesystem.isRunning()) {
        try {
          // Process recovery work only when active NN is out of safe mode.
          if (isPopulatingReplQueues()) {
		    // 扫描neededReconstruction中的block，并且对每个block选择需要被恢复到的数据节点和拷贝数据的节点
            computeDatanodeWork();
            processPendingReconstructions();
            rescanPostponedMisreplicatedBlocks();
          }
          TimeUnit.MILLISECONDS.sleep(redundancyRecheckIntervalMs); // 默认 3s
        } catch (Throwable t) {
			// 省略异常处理
        }
      }
    }
  }
  
    /**
   * Reconstruct a set of blocks to full strength through replication or
   * erasure coding
   *
   * @param blocksToReconstruct blocks to be reconstructed, for each priority
   * @return the number of blocks scheduled for replication
   */
  @VisibleForTesting
  int computeReconstructionWorkForBlocks(
      List<List<BlockInfo>> blocksToReconstruct) {
    int scheduledWork = 0;
    List<BlockReconstructionWork> reconWork = new LinkedList<>();

    // Step 1: categorize at-risk blocks into replication and EC tasks
    namesystem.writeLock();
    try {
      synchronized (neededReconstruction) {
        for (int priority = 0; priority < blocksToReconstruct.size(); priority++) {
          for (BlockInfo block : blocksToReconstruct.get(priority)) {
            BlockReconstructionWork rw = scheduleReconstruction(block,
                priority);
            if (rw != null) {
              reconWork.add(rw);
            }
          }
        }
      }
    } finally {
      namesystem.writeUnlock();
    }

    // Step 2: choose target nodes for each reconstruction task
    final Set<Node> excludedNodes = new HashSet<>();
    for(BlockReconstructionWork rw : reconWork){
      // Exclude all of the containing nodes from being targets.
      // This list includes decommissioning or corrupt nodes.
      excludedNodes.clear();
      for (DatanodeDescriptor dn : rw.getContainingNodes()) {
        excludedNodes.add(dn);
      }

      // choose replication targets: NOT HOLDING THE GLOBAL LOCK
      final BlockPlacementPolicy placementPolicy =
          placementPolicies.getPolicy(rw.getBlock().getBlockType());
      rw.chooseTargets(placementPolicy, storagePolicySuite, excludedNodes);
    }

    // Step 3: add tasks to the DN
    namesystem.writeLock();
    try {
      for(BlockReconstructionWork rw : reconWork){
        final DatanodeStorageInfo[] targets = rw.getTargets();
        if(targets == null || targets.length == 0){
          rw.resetTargets();
          continue;
        }

        synchronized (neededReconstruction) {
          if (validateReconstructionWork(rw)) {
            scheduledWork++;
          }
        }
      }
    } finally {
      namesystem.writeUnlock();
    }
	// 省略debug
    return scheduledWork;
  }

```

在对每个block创建新的转移任务时，需要选择一个当前已有副本的datanode和需要被复制到的datanode。对于已有副本的数据节点的选择，默认会先从没有写开销的DECOMMISSION_INPROGRESS状态的datanode中选，否则随机选一个没有达到副本限制的节点（每个节点会记录将要被复制的副本数，参数dfs.namenode.replication.max-streams用于限制每个节点上的副本数，默认为2），如果还不存在则随机选择其它符合要求的节点。对于被复制的数据节点，如同文件的第一次上传过程，调用了对应的副本放置策略进行选择。

```java
/**
   * Parse the data-nodes the block belongs to and choose a certain number
   * from them to be the recovery sources.
   *
   * We prefer nodes that are in DECOMMISSION_INPROGRESS state to other nodes
   * since the former do not have write traffic and hence are less busy.
   * We do not use already decommissioned nodes as a source, unless there is
   * no other choice.
   * Otherwise we randomly choose nodes among those that did not reach their
   * replication limits. However, if the recovery work is of the highest
   * priority and all nodes have reached their replication limits, we will
   * randomly choose the desired number of nodes despite the replication limit.
   *
   * In addition form a list of all nodes containing the block
   * and calculate its replication numbers.
   *
   * @return the array of DatanodeDescriptor of the chosen nodes from which to
   *         recover the given block
   */
  @VisibleForTesting
  DatanodeDescriptor[] chooseSourceDatanodes(BlockInfo block,
      List<DatanodeDescriptor> containingNodes,
      List<DatanodeStorageInfo> nodesContainingLiveReplicas,
      NumberReplicas numReplicas,
      List<Byte> liveBlockIndices, int priority) // ...
```

# 数据节点的执行恢复的逻辑

前面向blockManager中获取的DatanodeDescriptor类加入了block需要创建副本的任务。DatanodeManager在通过RPC发送心跳消息给namenode时，namenode会在处理心跳时将副本复制任务转变为对应的命令返回给datanode。

```java

// datanode发送心跳的rpc函数
@Override // DatanodeProtocol
public HeartbeatResponse sendHeartbeat(DatanodeRegistration nodeReg,
    StorageReport[] report, long dnCacheCapacity, long dnCacheUsed,
    int xmitsInProgress, int xceiverCount,
    int failedVolumes, VolumeFailureSummary volumeFailureSummary,
    boolean requestFullBlockReportLease,
    @Nonnull SlowPeerReports slowPeers,
    @Nonnull SlowDiskReports slowDisks) throws IOException {
  checkNNStartup();
  verifyRequest(nodeReg);
  return namesystem.handleHeartbeat(nodeReg, report,
      dnCacheCapacity, dnCacheUsed, xceiverCount, xmitsInProgress,
      failedVolumes, volumeFailureSummary, requestFullBlockReportLease,
      slowPeers, slowDisks);
}

// FSNameSystem的handleHearbeat函数，通过blockManager调用DatanodeManager处理心跳
{
  // ...
  DatanodeCommand[] cmds = blockManager.getDatanodeManager().handleHeartbeat(
          nodeReg, reports, getBlockPoolId(), cacheCapacity, cacheUsed,
          xceiverCount, maxTransfer, failedVolumes, volumeFailureSummary,
          slowPeers, slowDisks);
  // ...
}

// DatanodeManager中handleHeartbeat取出先前存储的任务，并转为BlockCommander。
{
  // ...
  List<BlockTargetPair> pendingList = nodeinfo.getReplicationCommand(
      numReplicationTasks);
  if (pendingList != null && !pendingList.isEmpty()) {
    cmds.add(new BlockCommand(DatanodeProtocol.DNA_TRANSFER, blockPoolId,
        pendingList));
  }

```




