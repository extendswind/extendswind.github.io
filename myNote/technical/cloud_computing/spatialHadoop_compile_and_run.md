---
title: "SpatialHadoop的编译与运行"
date: 2018-09-05T10:30:00+08:00
toc: true

# draft: true

categories:
- "cloud computing"

tags:
- "hadoop"
- "GIS"

---

SpatialHadoop相对HadoopGIS等库，在MapReduce时代的空间数据处理开源库算处理较好。SpatialHadoop在效率上相对一些新的基于Spark空间数据处理开源库明显偏低，加上本身的功能实现得差不多，最近提交的更新越来越少，感觉发展趋势不太好，主要用于学习相关的索引技术。

# 编译与运行

主页上有已经编译好的包，可以直接解压到Hadoop目录下运行，但官方的版本解压有错误，因此下载github上源码编译。

需要的环境：

- jdk8
- Hadoop 2.7.7
- maven

## 源码编译

源码地址 https://github.com/aseldawy/spatialhadoop2，直接下载或者git clone到本地。

需要安装maven用于代码编译。

编译前将pom.xml文件中hadoop相关的版本改为需要的版本。

`mvn compile` 编译源码
`mvn assembly:assembly` 代码打包，会在target目录下生成jar和一个包含jar与相关依赖的tar.gz包

在2f1aefd32860d0279f2fc479a8bafb68d07e3761版本（Mar 13,2018）编译时会由于缺少一个测试文件测试失败，可以选择跳过测试，或者注释掉测试的代码（src/test/java/edu/umn/cs/spatialHadoop/indexing/RStarTreeTest.java中的某个函数）。

## 运行

首先需要有一个Hadoop集群，能够提交yarn任务。

将target目录下生成的tar.gz包（spatialhadoop-2.4.3-SNAPSHOT-bin.tar.gz）拷贝到Hadoop目录下并解压即可。

```bash
cp target/spatialhadoop-2.4.3-SNAPSHOT-bin.tar.gz $HADOOP_HOME/
cd $HADOOP_HOME
tar -zxvf spatialhadoop-2.4.3-SNAPSHOT-bin.tar.gz
```

Hadoop目录下运行下面的测试代码，会向HDFS中写入一个随机生成的矩形文件。

`sbin/shadoop generate test.rects size:1.gb shape:rect mbr:0,0,1000000,1000000 -overwrite`


# SpatialHadoop运行机制

## shadoop 脚本

SpatialHadoop 通过脚本shadoop运行命令，脚本就只有几行代码

```bash
bin=`dirname "$0"`
bin=`cd "$bin" > /dev/null; pwd`

# Call Hadoop with the operations.Main as the main class
. "$bin"/hadoop edu.umn.cs.spatialHadoop.operations.Main $@
```
其实只是将spatialhadoop的jar包与相关依赖jar包放入Hadoop的包目录中，然后通过shadoop脚本调用Hadoop脚本调用包中的一个类，向YARN提交MapReduce任务。

## spatialhadoop的相关文件

spatialhadoop-2.4.3-SNAPSHOT-bin.tar.gz 中有以下的文件。

```bash
.
├── bin
│   └── shadoop
├── etc
│   └── hadoop
│       ├── spatial-site.xml
│       └── spatial-site.xml.template
├── LICENSE.txt
├── README.md
└── share
    └── hadoop
        └── common
            └── lib
                ├── esri-geometry-api-1.2.1.jar
                ├── javax.mail-1.5.5.jar
                ├── javax.mail-api-1.5.5.jar
                ├── jts-1.13.jar
                └── spatialhadoop-2.4.3-SNAPSHOT.jar
```

配置文件貌似基本功能上用得不多，shadoop脚本也比较简单，除去使用的相关环境依赖jar包，spatialhadoop实质上只是执行spatialhadoop-2.4.3-SNAPSHOT.jar包中的函数而已。


# SpatialHadoop 基本使用

构建索引文件与空间范围查询

```bash
shadoop index test.rects sindex:grid test.grid shape:rect 
shadoop rangequery test.grid rect:10,10,2000,3000 rangequery.out shape:rect
```

主要的索引结构，文件存储形式等在官网有相关文档。

具体运行的参数和运行的命令很多没有介绍，输入bin/shadoop以及bin/shadoop 接命令能够看到命令的基本使用情况，更具体的估计要去找源码了。



# 主要参考链接

- http://spatialhadoop.cs.umn.edu/all_operations.html 所有操作和说明
- http://spatialhadoop.cs.umn.edu/ 官网
- https://github.com/aseldawy/spatialhadoop2  github仓库

