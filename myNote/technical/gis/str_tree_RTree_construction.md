---
title: "STR树 —— R-tree的构建方案之一"
date: 2020-11-18T10:30:00+08:00
toc: true

mathjax: true

categories:
- "GIS"

tags:
- "hadoop"
- "GIS"

---

{{<mathjax>}}


最近需要使用R树做一下空间索引，在GeoSpark中使用了JTS库中实现的STR树，一开始以为是R-tree的一个变种，细看发现只是R树的构建（packing）方式之一。

STR是Sort-Tile-Recursive的缩写，本质上是一种R树的构建算法，不能单独算是R树。但在一些GIS开源库的实现中，经常直接命名为STRTree，负责STR算法的R树构建以及构建后的数据查询工作。具体的介绍可以看作者的论文 [https://www.cs.odu.edu/%7Emln/ltrs-pdfs/icase-1997-14.pdf](https://www.cs.odu.edu/%7Emln/ltrs-pdfs/icase-1997-14.pdf) ，CSDN上有个主要内容的翻译 [https://blog.csdn.net/qq_41775852/article/details/105405918](https://blog.csdn.net/qq_41775852/article/details/105405918)。

# R树常见构建过程

通常R树是针对动态有增删的数据，因此构建过程可以将所有的数据逐个插入到R树中。这种情况可能会存在一些缺点：

- (a) high load time 
- (b) sub-optimal spac eutilization 
- (c) poor R-tree structure requiring the retrieval of anunduly large number of nodes in order to satisfy a query.

因此，常用packing的方式自底向上的构建R树，主要流程如下：

1. 假设一共有r个矩形需要被索引，每个叶子结点中存储的矩形数量为n。首先将所有的矩形分成r/n（此处取上界）个组；（分组方式通过下面的packing算法）
2. 将各个分组写入硬盘的pages，并计算每个分组内所有矩形的MBR以及分组对应的page-id；
3. 对分组的MBR递归的执行上面的步骤，直到根节点。

在第1步中，将需要被索引的矩形分成r/n个组，论文中介绍了常见的Nearest-X(NX)、HilbertSort(HS)以及论文提出的Sort-Tile-Recursive(STR)。

# STR算法

STR的算法本身并不复杂，以2维空间为例。对矩形的分组只考虑每个矩形的中心点，STR的基本思想是将所有的矩形以“tile”的方式分配到r/n（取上界）个分组中，此处的tile和网格类似。

首先，对矩形按x坐标排序，然后划分成 $\sqrt{r/n}$ 个slices。然后对每个slice内的矩形按y坐标排序，进一步划分成 $\sqrt{r/n}$ 份。

对于更高维的空间，可以按这种方式接着划分。

# 总结

这个算法主要做一个简单的划分，正如论文的标题 《STR: A Simple and Efficient Algorithm for R-Tree Packing》，有种方法对于一篇论文来讲略简单的感觉。文章内还做了些对比实验，表明针对不同的空间数据分布情况最好选择对应合适的方法，STR的packing算法并不是适合所有的场景。

简单点来看，也就是R树的每层将空间中的矩形划分到了一个x、y方向数量相等分组中，当数据为长宽差距较大的矩形范围分布时，x、y方向的分组数量相同应该不是最好的方案。
