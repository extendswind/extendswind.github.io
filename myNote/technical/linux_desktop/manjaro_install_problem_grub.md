---
title: "使用u盘安装linux(manjaro)时Grub报错"
date: 2018-07-17T20:59:49+08:00
toc: true

categories:
- "linux desktop"

tags:
- "linux"
---

# 错误

> 
error: invalid arch-independent ELF magic.
Entering rescue mode...
grub rescue>

使用Rufu ISO模式烧录的U盘，lagency 模式能够启动，但点安装后出上面错误；UEFI模式直接出上面错误。

# 解决方案

不多说，百度背锅，google答案的前几个就是正解。

U盘烧录问题，使用rufu烧录U盘时，最好使用DD模式而非ISO模式。（去年安装manjaro-xfce4时用ISO模式没出过）

https://forum.manjaro.org/t/grub-error-computer-with-no-os-installed-invalid-arch-independent-elf-magic/21805

解决方案：使用Rufu烧录U盘，点开始后会有选择DD模式或者ISO模式，此时选DD模式，然后UEFI启动即可。

论坛上还推荐使用etcher