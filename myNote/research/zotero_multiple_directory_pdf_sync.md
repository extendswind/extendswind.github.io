---
title: "zotero zotfile插件 pdf附件文件夹在多系统下的同步设置"
date: 2019-01-09T09:59:49+08:00
toc: true

categories:
- "research"

tags:
- "linux"
---

之前的附件使用zotfile单独的文件夹管理，换了一块硬盘，挂载目录发生变化后zotero里所有的附件都打不开，在zotero的目录设置和zotfile的目录设置里改了都没用。

使用sqllite的浏览器看了一眼zotero的存储数据库(zotero.sqlite)，在表itemAttachments中存储了所有附件的类型地址等信息，发现里头的地址全都使用的绝对路径！！

重点在于设置zotero和zotfile的附件路径和转移文件。

**使用网盘同步的不用折腾这些。**

# 设置

1. zotero preferences -> Files and Folders -> Linked Attachment Base Directory 设置存储路径 （注意不是 data directory）
2. 把zotfile里的路径也改到这（不知道具体什么机制，zotfile有个相对路径的pull request不知道读的是不是这个，懒得多折腾）

# 已有的文件移动

1. 如果由于换硬盘换系统一类的问题，先使用软连接指向原来的目录，让zotero能够找到原来的文件。（源目录可以使用sqllite的浏览器看到）

2. 在library下全选所有的items，然后右键 Manage Attachments -> Rename Attachments。（看起来是重命名，实质上会移动所有的文件）

此时此前附件中的绝对路径`/mnt/data/...`会变成`attachments：catagory1/test1.pdf` 类似的相对路径。

更高端一点的可以直接操作sqllite数据库来改...


# 最后

跨操作系统或者跨目录直接设置到相同的目录即可。
