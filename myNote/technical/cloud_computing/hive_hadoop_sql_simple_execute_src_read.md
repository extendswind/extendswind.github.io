---
title: "Apache Hive代码阅读 -- SQL语句执行流程"
date: 2021-12-17T19:30:00+08:00
toc: true

categories:
- "cloud computing"

tags:
- "hadoop"
- "hive"
---


写一下Hive源码中执行SQL的SELECT语句的简单执行流程，手头没有具体的环境进调试模式，只根据源码写写大概的处理流程。

总体上从beeline脚本执行，调用了类Beeline.java，将终端的命令读入后通过rpc发送给driver处理。driver调用SemanticAnalyzer将SQL语句编译为可以执行的tasks，然后给每个task创建一个线程执行，在task中调用Tez等并行框架处理。


# 脚本执行

以beeline脚本执行为例，跳了两个脚本后执行了etx/beeline.sh中的beeline()执行对应的java类。

bin/beeline 脚本的执行会跳到 bin/hive 脚本，并传递service参数。

```bash
# beeline 脚本

bin=`dirname "$0"`
bin=`cd "$bin"; pwd`

. "$bin"/hive --service beeline "$@"
```

在 bin/hive 脚本中，首先从`$bin/ext/*.sh`以及`$bin/ext/util/*.sh`目录下执行所有脚本，脚本中定了一个和service名相同的函数，并且把service名加入到`SERVICE_LIST`变量。然后根据SREVICE名称运行对应脚本中的函数。

```bash
# bin/hive  省略了大部分代码

SERVICE_LIST=""

for i in "$bin"/ext/*.sh ; do
  . $i
done

for i in "$bin"/ext/util/*.sh ; do
  . $i
done

TORUN=""
for j in $SERVICE_LIST ; do
  if [ "$j" = "$SERVICE" ] ; then
    TORUN=${j}$HELP
  fi
done

if [ "$TORUN" = "" ] ; then
  echo "Service $SERVICE not found"
  echo "Available Services: $SERVICE_LIST"
  exit 7
else
  set -- "${SERVICE_ARGS[@]}"
  $TORUN "$@"
fi
```

对应执行bin/ext/beeline.sh中的beeline()函数。通过`hadoop jar`命令运行了java类org.apache.hive.beeline.BeeLine 。

```bash
# bin/ext/beeline.sh

THISSERVICE=beeline
export SERVICE_LIST="${SERVICE_LIST}${THISSERVICE} "

beeline () {
  CLASS=org.apache.hive.beeline.BeeLine;

  # include only the beeline client jar and its dependencies
  beelineJarPath=`ls ${HIVE_LIB}/hive-beeline-*.jar`
  superCsvJarPath=`ls ${HIVE_LIB}/super-csv-*.jar`
  jlineJarPath=`ls ${HIVE_LIB}/jline-*.jar`
  hadoopClasspath=""
  if [[ -n "${HADOOP_CLASSPATH}" ]]
  then
    hadoopClasspath="${HADOOP_CLASSPATH}:"
  fi
  export HADOOP_CLASSPATH="${hadoopClasspath}${HIVE_CONF_DIR}:${beelineJarPath}:${superCsvJarPath}:${jlineJarPath}"
  export HADOOP_CLIENT_OPTS="$HADOOP_CLIENT_OPTS -Dlog4j.configurationFile=beeline-log4j2.properties "

  exec $HADOOP jar ${beelineJarPath} $CLASS $HIVE_OPTS "$@"
}

beeline_help () {
  beeline "--help"
} 
```

# cli端java代码执行逻辑

总体上，java代码中不断读取输入的行，区分命令的类型后，将SQL语句通过Thrift的rpc发送给Thrift Server。

Beeline.java类中按行读命令行后处理，根据每行开头的字符决定是作为beeline命令还是sql语句执行。

```java
while (!exit) {
  try {
    // Execute one instruction; terminate on executing a script if there is an error
    // in silent mode, prevent the query and prompt being echoed back to terminal
    String line = (getOpts().isSilent() && getOpts().getScriptFile() != null) ? reader
        .readLine(null, ConsoleReader.NULL_MASK) : reader.readLine(getPrompt());

    // trim line
    if (line != null) {
      line = line.trim();
    }

    if (!dispatch(line)) {
      lastExecutionResult = ERRNO_OTHER;
      if (exitOnError) break;
    } else if (line != null) {
      lastExecutionResult = ERRNO_OK;
    }

  } catch (Throwable t) {
    handleException(t);
    return ERRNO_OTHER;
  }
}

// ....
// dispatch(line)函数中

// isBeeLine标记运行为beeline模式还是兼容模式
  if (isBeeLine) {
    if (line.startsWith(COMMAND_PREFIX)) {
      // handle SQLLine command in beeline which starts with ! and does not end with ;
      return execCommandWithPrefix(line);
    } else {
      return commands.sql(line, getOpts().getEntireLineAsCommand());
    }
  } else {
    return commands.sql(line, getOpts().getEntireLineAsCommand());
  }
```

在SQL语句的执行中，实现了java.sql包中的几个类，使用HiveConnection创建了HiveStatement，调用execute函数执行具体的操作。

execute函数中，向服务器发送了sql语句后等待服务器回应，返回结果。runAsyncOnServer函数中实现了向服务器的发送，通过thrift库的rpc调用实现。

```java
// Beeline 正常调用
InPlaceUpdateStream.EventNotifier eventNotifier =
    new InPlaceUpdateStream.EventNotifier();
logThread = new Thread(createLogRunnable(stmnt, eventNotifier));
logThread.setDaemon(true);
logThread.start();
if (stmnt instanceof HiveStatement) {
  HiveStatement hiveStatement = (HiveStatement) stmnt;
  hiveStatement.setInPlaceUpdateStream(
      new BeelineInPlaceUpdateStream(
          beeLine.getErrorStream(),
          eventNotifier
      ));
}
hasResults = stmnt.execute(sql);
logThread.interrupt();
logThread.join(DEFAULT_QUERY_PROGRESS_THREAD_TIMEOUT);


// execute函数
@Override
public boolean execute(String sql) throws SQLException {
  runAsyncOnServer(sql);
  TGetOperationStatusResp status = waitForOperationToComplete();

  // The query should be completed by now
  if (!status.isHasResultSet() && !stmtHandle.isHasResultSet()) {
    return false;
  }
  resultSet =  new HiveQueryResultSet.Builder(this).setClient(client).setSessionHandle(sessHandle)
      .setStmtHandle(stmtHandle).setMaxRows(maxRows).setFetchSize(fetchSize)
      .setScrollable(isScrollableResultset)
      .build();
  return true;
}


private void runAsyncOnServer(String sql) throws SQLException {
  // ...

  TExecuteStatementReq execReq = new TExecuteStatementReq(sessHandle, sql);
  execReq.setRunAsync(true);
  execReq.setConfOverlay(sessConf);
  execReq.setQueryTimeout(queryTimeout);
  try {
    // client 是Thrift的模板编译出来的RPC client
    TExecuteStatementResp execResp = client.ExecuteStatement(execReq);
    Utils.verifySuccessWithInfo(execResp.getStatus());
    stmtHandle = execResp.getOperationHandle();
    isExecuteStatementFailed = false;
  } 
  // ... 
}
```

# 服务端的处理

服务端的rpc调用通过CLIService类处理，调用了HiveSession，获取到SQLOperation对象后，传递给driver进行处理。

## RPC服务端的处理

CLIService将SQL语句传递给driver。

```java
// CLIService.java

/**
   * Execute statement on the server. This is a blocking call.
   */
  @Override
  public OperationHandle executeStatement(SessionHandle sessionHandle, String statement,
      Map<String, String> confOverlay) throws HiveSQLException {
    HiveSession session = sessionManager.getSession(sessionHandle);
    // need to reset the monitor, as operation handle is not available down stream, Ideally the
    // monitor should be associated with the operation handle.
    session.getSessionState().updateProgressMonitor(null);
    OperationHandle opHandle = session.executeStatement(statement, confOverlay);
    LOG.debug(sessionHandle + ": executeStatement()");
    return opHandle;
  }

// HiveSessionImpl.java
  operation = getOperationManager().newExecuteStatementOperation(getSession(), statement,
      confOverlay, runAsync, queryTimeout);  // SQLOperation
  opHandle = operation.getHandle();
  operation.run();
  addOpHandle(opHandle);
  return opHandle;


// SQLOperation.java
@Override
public void runInternal() throws HiveSQLException {
  setState(OperationState.PENDING);

  boolean runAsync = shouldRunAsync();
  final boolean asyncPrepare = runAsync
    && HiveConf.getBoolVar(queryState.getConf(),
      HiveConf.ConfVars.HIVE_SERVER2_ASYNC_EXEC_ASYNC_COMPILE);
  if (!asyncPrepare) {
    prepare(queryState);
  }
  if (!runAsync) {
    runQuery();
  } else {
    // 后面还是调用了runQuery()
    Runnable work = new BackgroundWork(getCurrentUGI(), parentSession.getSessionHive(),
        SessionState.getPerfLogger(), SessionState.get(), asyncPrepare);
    try {
      // This submit blocks if no background threads are available to run this operation
      Future<?> backgroundHandle = getParentSession().submitBackgroundOperation(work);
      setBackgroundHandle(backgroundHandle);
    } catch (RejectedExecutionException rejected) {
      setState(OperationState.ERROR);
      throw new HiveSQLException("The background threadpool cannot accept" +
          " new task for execution, please retry the operation", rejected);
    }
  }
}

// SQLOperation.java
private void runQuery() throws HiveSQLException {
  try {
    OperationState opState = getStatus().getState();
    // Operation may have been cancelled by another thread
    if (opState.isTerminal()) {
      LOG.info("Not running the query. Operation is already in terminal state: " + opState
          + ", perhaps cancelled due to query timeout or by another thread.");
      return;
    }
    // In Hive server mode, we are not able to retry in the FetchTask
    // case, when calling fetch queries since execute() has returned.
    // For now, we disable the test attempts.
    driver.setTryCount(Integer.MAX_VALUE);
    response = driver.run();
  }
}

```

## driver的SQL语句处理

driver中在runInternal函数执行主要逻辑。主要执行了编译SQL语句、执行编译后的SQL计划、事务提交等操作。

```java
private CommandProcessorResponse runInternal(String command, boolean alreadyCompiled)
    throws CommandNeedRetryException {

  // ... 省略日志、容错、Hive事务、绑定的hook事件执行等细节
  int ret;

  // 编译SQL语句 ****** 
  ret = compileInternal(command, true);

  // 执行计划 ******
  ret = execute(true);
  if (ret != 0) {
    //if needRequireLock is false, the release here will do nothing because there is no lock
    return rollback(createProcessorResponse(ret));
  }

  // 事务提交 ******
  // if needRequireLock is false, the release here will do nothing because there is no lock
  try {
    if(txnManager.getAutoCommit() || plan.getOperation() == HiveOperation.COMMIT) {
      releaseLocksAndCommitOrRollback(true, null);
    }
    else if(plan.getOperation() == HiveOperation.ROLLBACK) {
      releaseLocksAndCommitOrRollback(false, null);
    }
    else {
      //txn (if there is one started) is not finished
    }
  } catch (LockException e) {
    return handleHiveException(e, 12);
  }
}
```

### SQL语句编译和编译后执行过程

```java
// compileInternal()调用了compile()函数执行主要逻辑
public int compile(String command, boolean resetTaskIds, boolean deferClose) {
  // ... 省略日志、容错、Hive事务、绑定的hook事件执行等细节
  try {
    // command should be redacted to avoid to logging sensitive data
    // 替换中间一些敏感的字符串，默认不配置
    queryStr = HookUtils.redactLogString(conf, command);
  } catch (Exception e) {
    LOG.warn("WARNING! Query command could not be redacted." + e);
  }

  // 解析为AST树 ******
  perfLogger.PerfLogBegin(CLASS_NAME, PerfLogger.PARSE);
  ASTNode tree = ParseUtils.parse(command, ctx);
  perfLogger.PerfLogEnd(CLASS_NAME, PerfLogger.PARSE);

  // 获取语义分析对象 ******
  perfLogger.PerfLogBegin(CLASS_NAME, PerfLogger.ANALYZE);
  BaseSemanticAnalyzer sem = SemanticAnalyzerFactory.get(queryState, tree);
  List<HiveSemanticAnalyzerHook> saHooks =
      getHooks(HiveConf.ConfVars.SEMANTIC_ANALYZER_HOOK,
          HiveSemanticAnalyzerHook.class);

  // 语义分析执行 ******
  // Do semantic analysis and plan generation
  if (saHooks != null && !saHooks.isEmpty()) {
    HiveSemanticAnalyzerHookContext hookCtx = new HiveSemanticAnalyzerHookContextImpl();
    hookCtx.setConf(conf);
    hookCtx.setUserName(userName);
    hookCtx.setIpAddress(SessionState.get().getUserIpAddress());
    hookCtx.setCommand(command);
    hookCtx.setHiveOperation(queryState.getHiveOperation());
    for (HiveSemanticAnalyzerHook hook : saHooks) {
      tree = hook.preAnalyze(hookCtx, tree);
    }
    // 分析 ******
    // SemanticAnalyzer中有默认的处理细节，一个文件里有上万行的代码，
    // 根据HiveParser中的关键字进行解析
    sem.analyze(tree, ctx);
    hookCtx.update(sem);
    for (HiveSemanticAnalyzerHook hook : saHooks) {
      hook.postAnalyze(hookCtx, sem.getAllRootTasks());
    }
  } else {
    sem.analyze(tree, ctx);
  }
  
  // validate the plan
  sem.validate();

  // get the output schema
  // 构建查询计划 ******
  schema = getSchema(sem, conf);
  plan = new QueryPlan(queryStr, sem, perfLogger.getStartTime(PerfLogger.DRIVER_RUN), queryId,
    queryState.getHiveOperation(), schema);
}


public int execute(boolean deferClose) throws CommandNeedRetryException {
  // ... 省略日志、容错、绑定的hook事件执行和一些细节

  // 获取MR tasks ******
  int mrJobs = Utilities.getMRTasks(plan.getRootTasks()).size();
  int jobs = mrJobs + Utilities.getTezTasks(plan.getRootTasks()).size()
      + Utilities.getSparkTasks(plan.getRootTasks()).size();

  // plan中有一个runnable的队列存所有tasks，把plan中rootTasks中的队列加入到runnable队列中
  // 每个task对应一个线程，在单独的run函数中执行具体逻辑 ******
  for (Task<? extends Serializable> tsk : plan.getRootTasks()) {
    // This should never happen, if it does, it's a bug with the potential to produce
    // incorrect results.
    assert tsk.getParentTasks() == null || tsk.getParentTasks().isEmpty();
    driverCxt.addToRunnable(tsk);

    if (metrics != null) {
      tsk.updateTaskMetrics(metrics);
    }
  }

  // Loop while you either have tasks running, or tasks queued up
  while (driverCxt.isRunning()) {
    // Launch upto maxthreads tasks
    Task<? extends Serializable> task;
    // 遍历runnable队列，每次从队列中取出一个task启动 ******
    while ((task = driverCxt.getRunnable(maxthreads)) != null) {
      TaskRunner runner = launchTask(task, queryId, noName, jobname, jobs, driverCxt);
      if (!runner.isRunning()) {
        break;
      }
    }

    // ...
  }
}
```

SemanticAnalyzer类中有具体的SQL语句解析的处理细节，一个文件里有上万行的代码，根据HiveParser中的关键字进行解析。对具体的细节思路没概念，忽略了细节。
 
对任务提交到集群的具体的操作，在每个task内部执行。如Tez的并行分析任务，在TezTask类中调用了Tez库中的TezClient提交任务。


