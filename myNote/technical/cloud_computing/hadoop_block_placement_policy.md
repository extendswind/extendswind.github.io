---
title: "Hadoop 副本放置策略的源码阅读和设置"
date: 2018-12-11T21:30:00+08:00
toc: true


categories:
- "cloud computing"

tags:
- "hadoop"

---

大多数的叫法都是副本放置策略，实质上是HDFS对所有数据的位置放置策略，并非只是针对数据的副本。因此Hadoop的源码里有block replicator(configuration)、 BlockPlacementPolicy(具体逻辑源码)两种叫法。

主要用途：上传文件时决定文件在HDFS上存储的位置（**具体到datanode上的具体存储介质，如具体到存储在哪块硬盘**）；rebalance、datanode退出集群、副本数量更改等导致数据移动的操作中，数据移动的具体位置。 

# BlockPlacementPolicy

BlockPlacementPolicy 作为虚基类提供了基本的接口，具体的子类重点实现下面 *选择副本* 、 *验证副本放置是否满足要求* 、 *选择能够删除的副本* 三个函数：

```java
 /**
   * 核心的副本放置策略实现，返回副本放置数量的存储位置
   * **如果有效节点数量不够（少于副本数），返回尽可能多的节点，而非失败**
   *
   * @param srcPath 上传文件的路径
   * @param numOfReplicas 除下面chosen参数里已经选择的datanode，还需要的副本数量
   * @param writer 写数据的机器, null if not in the cluster. 一般用于放置第一个副本以降低网络通信
   * @param chosen 已经选择的节点
   * @param returnChosenNodes 返回结果里是否包含chosen的datanode
   * @param excludedNodes 不选的节点
   * @param blocksize 块大小
   * @return 排序好的选择结果
   */
  public abstract DatanodeStorageInfo[] chooseTarget(String srcPath,
                                             int numOfReplicas,
                                             Node writer,
                                             List<DatanodeStorageInfo> chosen,
                                             boolean returnChosenNodes,
                                             Set<Node> excludedNodes,
                                             long blocksize,
                                             BlockStoragePolicy storagePolicy);


  /**
   * 判断传入的放置方式是否符合要求
   */
  abstract public BlockPlacementStatus verifyBlockPlacement(
      DatanodeInfo[] locs, int numOfReplicas);
  

    /**
   * 当副本数量较多时，选择需要删除的节点
   */
  abstract public List<DatanodeStorageInfo> chooseReplicasToDelete(
      Collection<DatanodeStorageInfo> candidates, int expectedNumOfReplicas,
      List<StorageType> excessTypes, DatanodeDescriptor addedNode,
      DatanodeDescriptor delNodeHint);
```

# Hadoop 提供的 BlockPlacementPolicy 实现

Hadoop提供了BlockPlacementPolicyDefault、BlockPlacementPolicyWithNodeGroup、AvailableSpaceBlockPlacementPolicy三种实现（hadoop 2.7.7）。

其中BlockPlacementPolicyDefault是默认三副本策略的实现：第一个副本尽可能放在写入数据的节点，第二个副本放在与第一个副本不在同一机架（rack）下的节点，第三个副本与第二副本放在同一个机架。

BlockPlacementPolicyWithNodeGroup中第一、二个副本和Default副本放置相同，第三个副本在第二个机架下选择不同node group的结点。AvailableSpaceBlockPlacementPolicy实现存储平衡。Hadoop3.1中还加入了BlockPlacementPolicyRackFaultTolerant将数据存储到更多的机架下，BlockPlacementPolicyWithUpgradeDomain使用默认的副本放置策略，但是3个副本选择的datanode都要有不同的upgrade domains（为了方便大集群中datanode的更新和重启、将结点分配给不同的upgrade domain）。 

通过改变`dfs.block.replicator.classname` 能够选择具体的实现类，默认值为`org.apache.hadoop.hdfs.server.blockmanagement.BlockPlacementPolicyDefault`。（Hadoop 2.7.7下，貌似不同版本的Hadoop的命名还不一样，而且2.7.7默认的配置文件里还没有，需要在源码中查）


# BlockPlacementPolicyDefault 源码阅读

```java
  public abstract DatanodeStorageInfo[] chooseTarget(String srcPath,
                                             int numOfReplicas,
                                             Node writer,
                                             List<DatanodeStorageInfo> chosen,
                                             boolean returnChosenNodes,
                                             Set<Node> excludedNodes,
                                             long blocksize,
                                             BlockStoragePolicy storagePolicy);


```

chooseTarget函数实现了具体的三副本策略。各种特殊情况（如只有1个副本、datanode数量不够、集群拓扑不满足要求等）的考虑让代码看起来比较复杂，常规情况直接跟着调试代码走会跳过很多异常处理部分，便于裂解正常流程。

在副本的选择上用了各种带chooseTarget函数，注意有几个函数结果是通过参数传出而不是返回值。

主要实现思路：

1. 各种变量初始化
2. 考虑favoredNodes的放置
3. 除满足条件的favoredNodes后的副本放置策略（三副本）
4. 结果排序

## 首先

srcPath没有被考虑，被直接舍弃：

``` java
return chooseTarget(numOfReplicas, writer, chosenNodes, returnChosenNodes,
        excludedNodes, blocksize, storagePolicy, flags); // ignore srcPath
```

因此**默认的副本放置策略，在同一文件包含多个block时，每个block的存储位置独立考虑，并非存储在同一datanode**。

## 处理favoredNodes

上传文件时可以指定favoredNodes（默认为空），首先对favoredNodes所在的节点判断是否合适。如果满足条件的节点数还低于副本数，则添加新的副本。

```java
 // --------------Choose favored nodes ---------------
 // 从favored nodes中选择，在上传文件时可以指定
 List<DatanodeStorageInfo> results = new ArrayList<>();
 boolean avoidStaleNodes = stats != null
     && stats.isAvoidingStaleDataNodesForWrite();

 int maxNodesAndReplicas[] = getMaxNodesPerRack(0, numOfReplicas);
 numOfReplicas = maxNodesAndReplicas[0];
 int maxNodesPerRack = maxNodesAndReplicas[1];

 chooseFavouredNodes(src, numOfReplicas, favoredNodes,
     favoriteAndExcludedNodes, blocksize, maxNodesPerRack, results,
     avoidStaleNodes, storageTypes);

 // ---------------如果满足要求的favored nodes数量不足-----------
 if (results.size() < numOfReplicas) {
   // Not enough favored nodes, choose other nodes, based on block
   // placement policy (HDFS-9393).
   numOfReplicas -= results.size();
   for (DatanodeStorageInfo storage : results) {
     // add localMachine and related nodes to favoriteAndExcludedNodes
     addToExcludedNodes(storage.getDatanodeDescriptor(),
         favoriteAndExcludedNodes);
   }
   DatanodeStorageInfo[] remainingTargets =
       chooseTarget(src, numOfReplicas, writer,
           new ArrayList<DatanodeStorageInfo>(numOfReplicas), false,
           favoriteAndExcludedNodes, blocksize, storagePolicy, flags);
   for (int i = 0; i < remainingTargets.length; i++) {
     results.add(remainingTargets[i]);
   }
 }
```

## 三副本选择

实现逻辑在 chooseTargetInOrder(...) 函数中

```java
// 第一个副本的选择
if (numOfResults == 0) {
  writer = chooseLocalStorage(writer, excludedNodes, blocksize,
      maxNodesPerRack, results, avoidStaleNodes, storageTypes, true)
      .getDatanodeDescriptor();
  if (--numOfReplicas == 0) {
    return writer;
  }
}

// 选择与第一个副本不在同一Rack下的第二个副本
final DatanodeDescriptor dn0 = results.get(0).getDatanodeDescriptor();
if (numOfResults <= 1) {
  chooseRemoteRack(1, dn0, excludedNodes, blocksize, maxNodesPerRack,
      results, avoidStaleNodes, storageTypes);
  if (--numOfReplicas == 0) {
    return writer;
  }
}

// 第三个副本
if (numOfResults <= 2) {
  final DatanodeDescriptor dn1 = results.get(1).getDatanodeDescriptor();
  // 第一、二副本在同一Rack下时选第三个副本 
  // （前面的favoredNodes以及集群条件可能造成这种情况）
  if (clusterMap.isOnSameRack(dn0, dn1)) {
    chooseRemoteRack(1, dn0, excludedNodes, blocksize, maxNodesPerRack,
        results, avoidStaleNodes, storageTypes);
  } else if (newBlock){ // 正常情况，第二副本的localRack下选第三副本
    chooseLocalRack(dn1, excludedNodes, blocksize, maxNodesPerRack,
        results, avoidStaleNodes, storageTypes);
  } else {  // 其它的以外
    chooseLocalRack(writer, excludedNodes, blocksize, maxNodesPerRack,
        results, avoidStaleNodes, storageTypes);
  }
  if (--numOfReplicas == 0) {
    return writer;
  }
}

// 如果副本数量还没到0，剩下的副本随机选择
chooseRandom(numOfReplicas, NodeBase.ROOT, excludedNodes, blocksize,
    maxNodesPerRack, results, avoidStaleNodes, storageTypes);
return writer;

```

## 再到具体的选择

选择具体的存储位置被上面包装到了 chooseRemoteRack 和 chooseLocalRack 两个函数。

实际调用时只是 chooseRandom 函数，在限定的rack下选择一个随机的节点。


# 源码阅读的几个注意 

代码在直接阅读时各种跳，但主线思路比较明确。主要带来阅读困难的位置：

1. 很多函数调用不是通过返回值传出结果，而是通过参数。
2. 注意某些if后的return会直接返回结果，后面的代码不会被调用。
3. 递归的形式多次调用同一个函数以选择多个副本。
4. 很多代码为了避免一些特殊情况，可以暂时略过（如catch里的异常处理）。

# 修改HDFS默认的副本放置机制

可以选择直接复制或继承BlockPlacementPolicyDefault的实现，或者直接继承BlockPlacementPolicy类编写对应的接口具体实现。

将编译好的jar包放入`$HADOOP_PREFIX/share/hadoop/common`下（或者其它的Hadoop jar包路径）。

改变`dfs.block.replicator.classname` 为上面的实现类，要带包的名称。

# RackAwareness 机架感知

Hadoop 并不能自动检测集群的机架状态，而是要预先设置机架的状态，通过脚本或java类将datanode的ip转换成具体的机架上的位置。

官方文档介绍了基本思路，虽然实现上介绍得不是太清楚，只要将输入的ip转换成"/rackNum"的形式即可。

`https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/RackAwareness.html`







