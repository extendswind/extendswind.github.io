---
title: "Hadoop 机架（集群拓扑）设置"
date: 2018-12-12T11:20:00+08:00
toc: true


categories:
- "cloud computing"

tags:
- "hadoop"
---


Hadoop会通过集群的拓扑（节点在交换机的连接形式）优化文件的存储，降低跨交换机的数据通信，使副本跨交换机以保证数据安全。

但Hadoop没有默认的集群拓扑识别机制，需要使用额外的java类或脚本两种形式设置。

官网上给了集群拓扑的基本说明（!(Rack Awareness)[https://hadoop.apache.org/docs/current/hadoop-project-dist/hadoop-common/RackAwareness.html]），给出来的那两段脚本看得有点懵，就自己试了一下，写了个更简单的。

其实只是Hadoop会调用脚本，将多个Datanode的ip作为输入，每次最多输入的ip数设置在`net.topology.script.number.args`，将输入的ip转换成`/rack-num`的形式(以/开头的字符串)，用标准输出流（如Python的print）输出结果。

# 具体操作

## 编写脚本

下面的脚本在输入 

```
192.168.3.1
192.168.3.4
```

时，会输出 

```
/rack1
/rack4
```



```python

#!/bin/python3
import sys

# 第一个参数是脚本路径，直接pop掉
sys.argv.pop(0)

# 0-3  rack0
# 4-7  rack1
# 8-11  rack2
# ...

# 其它的参数里每个参数都是一个ip，此处直接取ip的最后一位除以4作为Racknum
# 实践上可以读文件确定ip的对应关系
for ip in sys.argv:      
    hostNum = int(ip.split(".")[3])
    print("/rack" + str(int(hostNum/4)))

```

## 设置配置参数

```xml
<property>
  <name>net.topology.script.file.name</name>
  <value>/home/sparkl/hadoop/etc/hadoop/topology.py</value>
</property>
```

重启集群即可


# 验证结果

以下命令能够直接获取某一个文件的分布状态，以及总的rack数量：

`hdfs fsck /readme.md -files -blocks -racks`

貌似没有直接以树状的形式输出集群拓扑的命令，namenode的日志中能看到datanode在连接时的拓扑位置。

