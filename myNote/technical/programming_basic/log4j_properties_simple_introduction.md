---
title: "log4j 1.2 配置和使用简述"
date: 2019-05-29T20:30:00+08:00
toc: true

categories:
- "programming basic"

tags:
- "java"
- "log4j"

---

# 简述

使用log4j可以根据配置文件控制输出日志的级别，记录到文件、命令行等的位置，不需要代码上的更改。

日志在一定程度上会影响性能，特别是高并发环境。**一般更建议使用log4j 2.x，在性能上有较大的提高，由于hadoop 2.7使用的log4j 1.2，下面主要写这一版本。**


- 根据日志级别记录日志 (logger上设置）
- 运行时决定具体的记录位置（appender上设置）和日志格式（layout上设置）




# 一些概念

## 日志级别（priority，代码里为level）

日志级别从低到高为trace, debug, info, warn, error, fatal。默认级别为info，低于设置级别的日志不会被打印。

## 常用组件

一般情况下常设置的组件有logger，appender， layout。

用类的方式表达三个组件的关系为

```
Logger{
  name;
  level; // 控制日志级别
  appenderList;  // 可对应多个appender
}

Appender{
  name;   // 控制文件位置  如fileAppender
  layout; // 控制格式
  filter; // 过滤部分日志
}
```



## logger

logger以一种树状关系管理日志的类型，log4j.rootCategory为根节点，如果没有标记 `log4j.additivity.MyLogger = false` ，则子logger会默认继承上一级的设置。

通过树的组织形式，对不同的包中的不同的类，可以分别设置不同的日志方式。

通过点表示层级，如com.foo为com.foo.Bar的上级

关于category，**早期的log4j使用category较多，但在log4j 1.2之后，建议使用logger代替category**。


## appender

主要用于

1. 控制日志的输出位置，当前支持the console, files, GUI components, remote socket servers, NT Event Loggers, and remote UNIX Syslog daemons.
2. 控制日志的格式（通过下面的layout）

一个logger能够指定多个appender，使日志记录在多个位置。


## layout

用于控制日志的格式，一个典型的格式为

> 
%r [%t]%-5p %c - %m%n   会得到：
176 [main] INFO  org.foo.Bar - Located nearest gas station.

上面的日志分别对应：程序运行时间  线程  优先级  category的名称  日志信息



# log4j.properties 配置

提供了两种动态的配置方式，一种使用配置文件log4j.properties（更建议），另一种使用java代码直接配置。

一般涉及：

- 配置rootLogger  (配置全局的appender和priority)
- 配置子logger (配置指定类的appender和priority)
- 配置appender （配置日志记录的位置等属性）
- 配置layout  （配置日志输出的格式）

## 示例

```bash
# root logger 的level和对应的appender (fileAppender在后面定义）
log4j.rootLogger=info, fileAppender

# 定义fileAppender 为 File appender
log4j.appender.fileAppender=org.apache.log4j.FileAppender
log4j.appender.fileAppender.File=/home/abc/test

# 定义 fileAppender 的 layout
log4j.appender.fileAppender.layout=org.apache.log4j.PatternLayout
log4j.appender.fileAppender.layout.conversionPattern=%m%n


# 子logger配置  针对com.a.Test4log这个类 设置为System.err的输出
log4j.logger.com.a.Test4log = INFO, myConsole

# 输出到标准err的appender
log4j.appender.myConsole=org.apache.log4j.ConsoleAppender
log4j.appender.myConsole.target=System.err

# 定义layout输出格式
log4j.appender.myConsole.layout=org.apache.log4j.PatternLayout
log4j.appender.myConsole.layout.ConversionPattern=%d{yy/MM/dd HH:mm:ss} %p %c{2}: %m%n  myConsole

```

分层的语法略奇葩，而且前面可以用到后面定义的变量。


# java代码调用

```java
Log log = LogFactory.getLog(Test4log.class);
log.info("test");
```

程序会在classpath下查找log4j.properties，因此一般放在src/main/resources文件夹下


