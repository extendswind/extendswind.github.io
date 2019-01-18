---
title: "在非gnome系桌面环境下运行deepin-wine tim"
date: 2018-10-20T20:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---

i3wm, kde, awesome等桌面管理器或桌面环境里运行基于deepin-wine的qq和tim时，会出现下面的错误

> 
X Error of failed request: BadWindow (invalid Window parameter) Major opcode of failed request: 20 (X_GetProperty)

在gnome、mate、cinnamon三个桌面上运行较好，xfce4上运行有少许焦点上的bug，其它桌面环境和管理器下直接出上面的错误。

最近终于在aur上看到是因为deepin-wine依赖了gnome-setttings-daemon。

# 解决方案

貌似是因为对gnome-setttings-daemon的依赖。

arch系：

```bash
sudo pacman -S gnome-settings-daemon
/usr/lib/gsd-setttings
```

运行tim和qq即可


ubuntu 下的包和运行的程序名略不一样，参考：

https://github.com/wszqkzqk/deepin-wine-ubuntu/issues/12#issuecomment-443656358


# 完

又从mate+awesomewm回到纯awesomewm。
