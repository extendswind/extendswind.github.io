---
title: "SpatialHadoop的编译与运行"
date: 2018-08-29T10:30:00+08:00
toc: true

categories:
- "cloud computing"

tags:
- "hadoop"

---


SpatialHadoop相对HadoopGIS等库，在MapReduce时代的空间数据处理开源库算处理得比较好的。貌似是Spark的流行与RDD处理效率优势，SpatialHadoop在效率上相对一些新的基于Spark空间数据处理开源库明显偏低，最近提交的更新越来越少。

貌似当前基于Spark的空间数据处理开源库中，很少涉及基于HDFS上存储数据的空间索引，因此准备从SpatialHadoop上入手分析大规模空间数据的存储问题。


# 安装与运行

首先需要有一个Hadoop集群，能够提交yarn任务。

# SpatialHadoop运行机制

SpatialHadoop 通过脚本shadoop运行命令，脚本就只有几行代码

```bash
bin=`dirname "$0"`                                                 
bin=`cd "$bin" > /dev/null; pwd`

# Call Hadoop with the operations.Main as the main class
. "$bin"/hadoop edu.umn.cs.spatialHadoop.operations.Main $@
```

上面通过Hadoop的任务提交脚本 bin/hadoop 运行已经编译好的 jar包中的类。


java.lang.NoClassDefFoundError: org/mortbay/jetty/handler/AbstractHandler
java.lang.NoClassDefFoundError: org/mortbay/jetty/handler/AbstractHandler
