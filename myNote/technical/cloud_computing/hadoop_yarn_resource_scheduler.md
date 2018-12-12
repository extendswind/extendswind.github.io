---
title: "Hadoop YARN 调度器（scheduler） —— 资源调度策略"
date: 2018-09-04T10:30:00+08:00
toc: true

# draft: true

categories:
- "cloud computing"

tags:
- "hadoop"
---


搜了一些博客，发现写得最清楚的还是《Hadoop权威指南》，以下内容主要来自《Hadoop The Definitive Guide》 4th Edition 2015.3。

# Hadoop YARN Scheduler

## 三个调度器

YARN提供了CapacityScheduler, FairScheduler, FifoScheduler三个调度器，继承于AbstractYarnScheduler，Resource Manager通过调度器决定对提交application分配的资源大小。

CapacityScheduler首先将所有资源分配到hierarchical queue中，每个任务执行时指定对应的queue，使大任务不会占用整个集群的资源，通过对queue的资源管理提高整个集群的资源共享能力。通常会使小任务执行更快，大任务更慢。

Fair Scheduler 会在第一个任务运行时分配当前同级队列的所有资源，当有其它任务运行时，回收前面任务运行时的部分资源（一般为运行完成的Container）用于其它任务。

至于FIFO，源码里都没有描述，可能就是一般的先进先出了。

YARN默认使用CapacityScheduler，通过下面的属性配置：

```xml
<property>
  <name>yarn.resourcemanager.scheduler.class</name>
  <value>org.apache.hadoop.yarn.server.resourcemanager.scheduler.fair.FairScheduler</value>
</property>
```

## YARN 动态资源分配

YARN 能够动态申请资源，如MapReduce中reduce的container会在map过程结束后申请。但Spark On YARN的机制为申请固定的executor，而不动态改变已申请的资源。

YARN上新运行的任务能够使用已运行任务回收的资源(如运行完Map task的container)，甚至还能够通过强行结束先前任务的container抢占资源。


# Capacity Scheduler

CapacityScheduler重点解决多个组织共享集群资源，并保证每个组织自己的资源使用量。当自己的资源不足时能够使用其它组织的空闲资源。

资源通过层级队列（hierarchical queues）的形式进行组织，配置在etc/hadoop/capacity-scheduler.xml.

```xml
<!-- 队列结构设置 -->
<property>
  <name>yarn.scheduler.capacity.root.queues</name>
  <value>a,b</value>
  <description>The queues at the this level (root is the root queue).
  </description>
</property>

<property>
  <name>yarn.scheduler.capacity.root.a.queues</name>
  <value>a1,a2</value>
  <description>The queues at the this level (root is the root queue).
  </description>
</property>

<!-- 队列能力设置 -->
<property>
  <name>yarn.scheduler.capacity.root.a.capacity</name>
  <value>40</value>
</property>

<property>
  <name>yarn.scheduler.capacity.root.b.capacity</name>
  <value>60</value>
</property>

<property>
  <name>yarn.scheduler.capacity.root.a.a1.capacity</name>
  <value>50</value>
</property>

<property>
  <name>yarn.scheduler.capacity.root.a.a2.capacity</name>
  <value>50</value>
</property>

<!-- 最大能力占用 -->
<property>
  <name>yarn.scheduler.capacity.root.a.maximum-capacity</name>
  <value>75</value>
</property>
```

```
root  
├── a 40%  
|   ├── a1 50%  
|   └── a2 50%  
└── b 60%  
```

上面的设置形成了如图的hierarchical queues，并指定a队列使用40%的资源，b队列60%，a1 a2各占a队列的50%，a队列在b队列资源空闲时，最高可占用集群75%的资源。

## 一些设置和特点

- 通过设置queue的maximum capacity能够避免使用相邻子队列的所有资源。
- 改变文件后需要运行 `$HADOOP_YARN_HOME/bin/yarn rmadmin -refreshQueues`
- 子队列能使用的最大资源为父队列的资源
- 队列上除了对资源的管理，还提供了运行的用户、应用数量等的限制功能。
- 默认只支持内存，通过配置可以支持CPU

# Fair Scheduler （公平调度器）

对比CapacityScheduler的主要区别： 任务提交时占用同一层队列所有的资源 (Capacity Scheduler中只使用maximum-capacity限制下的其它队列闲置的资源），另一个任务提交时，会回收先前任务的部分资源。


```xml
<allocations>
  <defaultQueueSchedulingPolicy>fair</defaultQueueSchedulingPolicy>
  <queue name="a">
    <weight>4</weight>
    <schedulingPolicy>fifo</schedulingPolicy>
    <queue name="a1" />
    <queue name="a2" />
  </queue>
  <queue name="b">
    <weight>6</weight>
  </queue>
  <queuePlacementPolicy>
    <rule name="specified" create="false" />
    <rule name="primaryGroup" create="false" />
    <rule name="default" queue="a.a1" />
  </queuePlacementPolicy>
</allocations>
```

上面的配置文件给出了一个如下图的层级队列。

```
root 
├── a (权重4 因此占用总体40%的资源）
|   ├── a1  没有指定权重，因此与a2队列平分a队列40%的资源；队列内部的多个应用使用fifo策略。 
|   └── a2 
└── b （权重6 因此占用总体60%的资源）
```

向a1队列中提交任务1时，首先会占用整个集群；向b队列提交任务2时，会从任务1中回收60%的资源用于任务2；向a1队列中继续提交任务3时，会按fifo的策略使用a队列的40%资源；向a2队列提交任务4时，会从a1队列的任务1、任务3中回收资源，使a1队列资源和a2队列相同。

在Hadoop Fair Scheduler的具体实现中，并没有对每个application实现绝对公平的资源分配，而是针对同一级队列内部的资源，队列内部可以选择其它的调度策略。并且使用weight参数，使相同层级的队列资源根据weight分配而非直接平均，设置不同weight后并不“fair”。（实质上和CapacityScheduler类似，都是对层级队列的管理，每一层的队列之间资源存在共享，有博客提到FairScheduler在不断的发展中已经能够实现大部分CapacityScheduler的功能，两者的功能越来越接近）

注意，Fair Scheduler会默认对每个用户创建一个queue用于没指定queue的任务，weight为1，因此要想忽略默认创建的用户queue，需要将权重设置偏大。

## 队列内部调度策略

每个队列内使用一定的调度策略，常见的FIFO、FAIR和DRF。

FIFO(first in first out), 先提交的任务先分配资源。

FAIR (max-min fairness)， 先把资源平均分配，某些任务如果有多出资源则将多出的资源分配给其它任务，对资源要求低的任务优先。

DRF（dominant resource fairness），解决有多种资源（CPU、内存等）同时考虑的分配问题，如一个CPU要求高内存要求低与一个CPU要求低内存要求高的应用。

