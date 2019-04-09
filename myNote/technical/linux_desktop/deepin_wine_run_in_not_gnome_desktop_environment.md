---
title: "在非gnome系桌面环境下运行deepin-wine tim的错误解决"
date: 2019-01-20T20:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---

i3wm, kde, awesome等桌面管理器或桌面环境里运行基于deepin-wine的qq和tim时，会出现下面的错误

> 
X Error of failed request: BadWindow (invalid Window parameter) Major opcode of failed request: 20 (X_GetProperty)

在gnome、mate、cinnamon三个桌面上运行较好，xfce4上运行有少许焦点上的bug，其它桌面环境和管理器下直接出上面的错误。

最近终于在aur上看到是因为deepin-wine依赖了gnome-setttings-daemon。（xsettings的一个后台进程，cinnamon和mate的xsettings进程也能用）


# 解决方案


## 1. 安装gnome-settings-daemon  (arch 系）

```bash
sudo pacman -S gnome-settings-daemon
```

ubuntu 下的包和运行的程序名略不一样，参考：

`https://github.com/wszqkzqk/deepin-wine-ubuntu/issues/12#issuecomment-443656358`


## 2. 在tim启动脚本中加入启动

`/opt/deepinwine/apps/Deepin-TIM/run.sh` 的文件前添加下面的行：

`/usr/lib/gsd-setttings &`


# 注意

## 影响主题

在使用xsettings之后，主题等需要与对应的xsettings设置相对应。如使用gnome-settings-daemon时，需要在gnome的设置里更改主题。使用lxappearance修改主题只会更改~/.gtkrc-2.0等文件，不会生效。

## csd-xsettings 的影响

csd-xsettings 主要影响两个地方：1. 启动过程； 2. 在tim内调用外部程序打开链接的过程（如打开网页、打开本地目录）。

可以考虑启动后关闭对tim，可以避免影响系统主题一类的问题，但无法调用外部程序。加上运行后5s关闭的参数即可:

`/usr/lib/cinnamon-settings-daemon/csd-xsettings --exit-time 5 &`  


# 附：使用cinnamon的xsettings的设置

主题的问题略坑，懒得去试gnome上的主题设置需要哪些包，安装整个gnome的包需要800多M，直接安装了cinnamon的基础包（90M左右）。

cinnamon的xsettings默认也没用那个不太能忍的主题。

```bash
sudo pacman -S cinnamon

# awesome的autorun里加入下面程序使开机运行
/usr/lib/cinnamon-settings-daemon/csd-xsettings

```

在系统设置里可以下载和更改主题

# 小坑

tim和qq都会在点击好友图像时卡死，原因是因为pulseaudio进程，kill掉就行，会影响声音的调整。（千里之外的两个程序不知道为什么会卡一起）

貌似pulseaudio与deepin-wine八字不合，使用csd-xsettings时无法调声音，关了之后就行了....

# 最后

又从mate+awesomewm回到纯awesomewm，但运行了一个xsetting进程也不知道和直接mate+awesome比能节约多少内存。

