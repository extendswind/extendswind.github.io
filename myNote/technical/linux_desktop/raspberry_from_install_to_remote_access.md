---
title: "树莓派从烧录系统到通过wifi远程访问（新树莓派配置，无显示器、网线、键盘）"
date: 2019-10-25T10:59:49+08:00

categories:
- "linux desktop"

tags:
- "raspberry"
---


网上教程很多，但是google和百度排在前面的博客操作起来各种问题，因此简单写写。


# 1. 烧录系统

官网有可以系统可以下载，通常建议![raspberry](https://www.raspberrypi.org/downloads/raspbian/)，有特殊需求可以考虑其它的几个系统。

官网推荐使用balenaEtcher烧录系统。（很多博客推荐先一个工具格式化sd卡，然后win32imagewriter不知道是不是以前的做法）


## 2. 配置系统

上面的烧录后，sd卡会被分为多个分区，其中windows系统下能识别的只有一个名为boot的分区，存储启动相关的配置文件。

### 2.1 开启ssh

raspbian 系统默认不开启ssh远程访问，在boot分区下新建文件名为`SSH`的文件（内容为空无后缀），系统启动时检测到此文件会开启ssh进程。


### 2.2 配置wifi

在boot分区下新建文件名为`wpa_supplicant.conf`的文件，添加以下内容：

```
country=CN
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="yourWifiName"
    psk="passwd"
    key_mgmt=WPA-PSK
    priority=1
}

```

修改其中的wifi名和密码（ssid与psk）

*如果想省事可以直接用网线连上路由器*


# 3. 远程访问

## 3.1 查找树莓派ip

此处需要将电脑和树莓派连接在同一路由器下。

方法一：浏览器上输入192.168.1.1 （根据不同路由器网关不同），进入管理页面查看树莓派ip。

方法二：使用软件`Advanced IP Scanner`扫描局域网中的树莓派。

## 3.2 ssh 远程登录

ssh是linux上最常用的命令行远程访问工具。

使用软件`putty`用于远程ssh登录，输入树莓ip，密码为raspberry。

## 3.3 开启vnc

vnc类似windows上的rdp远程登录，是linux上最常用的带界面远程访问协议。

ssh远程登录后，`sudo raspi-config` 然后在`Interfacing Options` -> `VNC`里enable VNC服务。（貌似是启动vnc的服务后设置了开机启动）

然后使用`realVNC viewer`输入ip访问即可。

vnc默认使用5900端口，当端口占用时会往后推使用5901等端口。多个vncserver运行时需要使用ip:590x的形式指定端口号。

### 此处小坑

树莓派自带的vnc server使用的加密方式和tigerVNC viewer不兼容，会显示以下错误：

`Unknown authentication scheme from VNC server: 13, 5, 6, 130, 192`

使用realVNC客户端正常访问。

还可以考虑在树莓派上安装tightvncserver。


# 4. 附软件源安装

默认的软件源仓库的网速较慢，使用apt安装某些软件时过于龟速，可以考虑换国内的镜像源。如![清华源](https://mirror.tuna.tsinghua.edu.cn/help/raspbian/)等。
