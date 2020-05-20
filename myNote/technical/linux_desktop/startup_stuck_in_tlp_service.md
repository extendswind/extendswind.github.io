---
title: "系统启动时卡在 'TLP System startup/shutdown' "
date: 2020-05-20T22:30:00+08:00
toc: false

categories:
- "linux desktop"

tags:
- "linux"

---


# 问题

manjaro 在笔记本上启动时卡住（manjaro-awesome + refind引导），停在

`TLP System startup/shutdown`

TLP 提供优秀的 Linux 高级电源管理功能（详见arch wiki），不知道为什么在启动后卡主。

# 解决

没有太研究，一般启动卡住的问题和内核参数、驱动等关系比较大，具体的不太好找，可以试试下面的三种方案。

方案一：换内核（可能是硬件的驱动问题导致，对新一点的设备换新内核可能会有效）。

方案二：关闭TLP服务的开机启动， `systemctl disable tlp.service` 。

方案三：将refind引导改为grub引导（难道启动的时候两者的内核参数不一致？）
