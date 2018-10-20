---
title: "Hadoop HDFS 远程调试（Docker环境下的Hadoop集群）"
date: 2018-07-26T21:30:00+08:00

toc: true

categories:
- "cloud computing"

tags:
- "hadoop"

---

Hadoop 典型的调试方式是通过log4j输出日志，基于日志的形式查看运行信息。在源码阅读中，经常有不容易猜的变量，通过大量日志输出调试没有远程调试方便。


# Java 远程调试

*不想了解的可以直接跳到下面Hadoop*

通过JPDA（Java Platform Debugger Architecture），调试时启动服务，通过socket端口与调试服务端通信。

下面只用最常用的服务端启动调试服务监听端口，本地IDE（idea）连接服务端。

## 具体操作

### 1、启动被调试程序时添加参数：

> 
jdk9: `-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:8000`  
jdk5-8: `-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=8000`  
jdk4: `-Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=n,address=8000`  
jdk3 及以前: `-Xnoagent -Djava.compiler=NONE -Xdebug -Xrunjdwp:transport=dt_socket,server=y,suspend=n,address=8000`  

**此处有坑，网上大部分没有提到jdk版本不同导致的区别，很多博客使用jdk4的写法，可能导致问题（idea配置远程调试时有上面的选项）。**

**另外一个小坑**, 下面第一个命令正常执行，第二个命令会忽略调试选项：

- `java -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=8000 test`
- `java test -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=8000`

主要参数。suspend=y时，程序启动会先挂起，IDE连接后才会运行；suspend=n时，程序启动会直接运行。address后面为端口号，不与其它端口重合即可。

### 2、启动Idea连接调试

使用idea打开调试项目的源码工程

Run -> Edit Configurations , 点“加号” -> remote，然后填上被调试程序所在主机的ip以及上面的address对应端口号，并选择源码所在的module。

添加后debug运行，剩下的和本地调试相同。

# Hadoop 远程调试

思路和上面的操作一致。下面以调试HDFS中的namenode为例。

## 具体操作

### 1、修改Hadoop启动参数为debug模式

如果需要调试namenode服务，在`etc/hadoop/hadoop-env.sh`文件后添加：

`export HDFS_NAMENODE_OPTS="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=8000" ` 

HDFS启动的jvm主要为namenode和datanode，jvm启动的参数设置在`etc/hadoop/hadoop-env.sh`中。其中namenode启动参数环境变量为 `HDFS_NAMENODE_OPTS`，datanode为 `HDFS_DATANODE_OPTS`（针对Hadoop3，hadoop2的设置为`HADOOP_NAMENODE_OPTS` `HADOOP_NAMENODE_OPTS`）。YARN等服务对应的环境变量需要另查。

### 2、启动服务

`sbin/start-dfs.sh`  或者 `bin/hdfs --daemon start namenode`仅启动namenode

### 3、启动idea连接服务

下载源码并导入到工程（可以只导入需要调试的部分）

Run -> Edit Configurations , 点“加号” -> remote，然后填上被调试程序所在主机的ip以及上面的address对应端口号，并选择需要调试的module。

## 踩坑

- 不建议像某些博客中写的直接修改`HADOOP_OPTS`变量，容易发生端口冲突等问题（在Hadoop 3.1.0上运行出错）

- 注意指定的端口避免冲突，如一台主机上同时运行namenode和datanode服务时端口要分开。

- 注意jdk版本的不同需要设置不同的调试参数。

## 未解之坑

使用一台服务器通过Docker运行4个容器组建Hadoop集群，主机能够直接通过端口访问Docker内容器的服务，当无法通过debug端口连接上容器内的调试程序，**只能通过内部端口映射到外部主机后访问**。

google上有类似问题未解决。

# 总结

实质上比较简单，主要是踩坑，特别是docker内部一直连不上的坑，以及某些博客比较早已经不适用于Hadoop 3.1.0。

在hadoope-env.sh文件中设置需要调试服务的jvm启动参数，然后启动idea导入源码后连接即可。
