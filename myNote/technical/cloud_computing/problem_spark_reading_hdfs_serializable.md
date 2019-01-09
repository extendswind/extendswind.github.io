---
title: "Spark设置自定义的InputFormat读取HDFS文件"
date: 2018-12-15T11:30:00+08:00
toc: true

categories:
- "cloud computing"

tags:
- "hadoop"
- "spark"

---

Spark提供了HDFS上一般的文件文件读取接口 sc.textFile()，但在某些情况下HDFS中需要存储自定义格式的文件，需要更加灵活的读取方式。


# 使用KeyValueTextInputFormat

Hadoop的MapReduce框架下提供了一些InputFormat的实现，其中MapReduce2的接口(org.apache.hadoop.mapreduce下)与先前MapReduce1(org.apache.hadoop.mapred下)有区别，对应于newAPIHadoopFile函数。

使用KeyValueTextInputFormat的文件读取如下

```scala

import org.apache.hadoop.mapreduce.lib.input.KeyValueTextInputFormat
import org.apache.hadoop.io.Text

val hFile = sc.newAPIHadoopFile("hdfs://hadoopmaster:9000/user/sparkl/README.md",
    classOf[KeyValueTextInputFormat], classOf[Text], classOf[Text])
    
hFile.collect

```

# 使用自定义InputFormat

InputFormat是MapReduce框架下将输入的文件解析成字符串的组件，Spark对HDFS中的文件实现自定义读写需要通过InputFormat的子类实现。下面只写简单的思路，具体的可以参考InputFormat和MapReduce相关资料。

InputFormat的修改可以参考TextInputFormat，继承FileInputFormat后，重载createRecordReader返回一个新的继承RecordReader的类，通过新的RecordReader读取数据返回键值对。

打包后注意上传时将jar包一起上传：

`./spark-shell --jars newInputFormat.jar

运行的代码和上面差不多，import相关的包后 

```scala
val hFile = sc.newAPIHadoopFile("hdfs://hadoopmaster:9000/user/sparkl/README.md", 
    classOf[NewTextInputFormat], classOf[Text], classOf[Text])
```


# 一些坑

## 序列化问题

在读取文件后使用first或者collect时，出现下面的错误

> 
ERROR scheduler.TaskSetManager: Task 0.0 in stage 2.0 (TID 18) had a not serializable result: org.apache.hadoop.io.IntWritable
Serialization stack:
	- object not serializable (class: org.apache.hadoop.io.IntWritable, value: 35)
	- element of array (index: 0)
	- array (class [Lorg.apache.hadoop.io.IntWritable;, size 1); not retrying
18/12/15 10:40:10 ERROR scheduler.TaskSetManager: Task 2.0 in stage 2.0 (TID 21) had a not serializable result: org.apache.hadoop.io.IntWritable
Serialization stack:
	- object not serializable (class: org.apache.hadoop.io.IntWritable, value: 35)
	- element of array (index: 0)
	- array (class [Lorg.apache.hadoop.io.IntWritable;, size 1); not retrying
    
当键值对是其它的类型时，还可能出现类似的：

> 
ERROR scheduler.TaskSetManager: Task 0.0 in stage 2.0 (TID 18) had a not serializable result: org.apache.hadoop.io.LongWritable
ERROR scheduler.TaskSetManager: Task 0.0 in stage 2.0 (TID 18) had a not serializable result: org.apache.hadoop.io.Text
    
此问题略奇怪，都实现了Hadoop的Writable接口，却不能被序列化。某些地方提到Hadoop与Spark没有使用同一套序列化机制，需要在Spark的序列化框架下注册才能使用。

一般更建议在drive程序上收集信息时，首先转换成基本的数据类型：

hFile.filter(k => k._1.toString.contains("a")).collect

## java.lang.IllegalStateException: unread block data

> 
ERROR executor.Executor: Exception in task 0.3 in stage 0.0 (TID 3)
java.lang.IllegalStateException: unread block data
	at java.io.ObjectInputStream$BlockDataInputStream.setBlockDataMode(ObjectInputStream.java:2781)
    
一个很坑的错误，spark-shell下只出现这个，并未表明真正的错误在哪。在spark的webUI上能够看到相关的运行日志，上面的异常前还有一个异常写的是我重写的InputSplit没有实现Writable接口。**此处的坑，InputFormat中用的InputSplit如果需要重写需要实现Writable接口，在MapReduce下使用貌似没有这一要求。**

补上之后上传到集群的nodemanager即可。**注意，当nodemanager和spark-shell上传的jar包中有相同的类时，nodemanager优先使用了自身的类。**
