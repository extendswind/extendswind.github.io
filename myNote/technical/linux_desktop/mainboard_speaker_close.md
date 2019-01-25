---
title: "linux 关闭主板上的蜂鸣器声音"
date: 2019-01-25T10:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---


在从deepin的kdd桌面换到xfce桌面后，命令行和界面操作上动不动会让主机响一声。

manjaro的xfce版也是如此，不知道是不是linux下xfce的通病。

主要是搜索的时候百度的结果很奇葩...


用关键字 beep of xfce4 搜到了arch wiki下的内容，原来这玩意叫pc speaker，针对不同的情况有不同的解决方案。

### 最简单粗暴的方式

内核中加载了pcspkr模块导致的主板声音，rmmod移除此模块，然后/etc/modprobe.d文件夹下加入黑名单，使开机过程不加载。

> 
# rmmod pcspkr
# echo "blacklist pcspkr" > /etc/modprobe.d/nobeep.conf


### 具体参考

https://wiki.archlinux.org/index.php/PC_speaker
