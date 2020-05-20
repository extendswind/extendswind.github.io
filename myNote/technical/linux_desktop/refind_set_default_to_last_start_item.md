---
title: "REFInd默认启动上次的启动项"
date: 2020-05-20T22:30:00+08:00
toc: false

categories:
- "linux desktop"

tags:
- "linux"

---

windows和linux的双系统偶尔需要切换，设置一个默认启动项没看到直接的资料。

修改配置文件 `/boot/efi/EFI/refind/refind.conf`（linux下），相关的项都有说明，但是这个和常规差距略大。

默认启动项的设置在`default_selection` 项，可以设置为如下：

`default_selection "+,Microsoft,vmlinuz"`

Microsoft表示windows系统，vmlinuz表示linux系统，+号表示选择上一次打开的选项。
