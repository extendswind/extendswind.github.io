---
title: "华为笔记本magicbook14 AMD安装Manjaro Linux的一些踩坑配置"
date: 2020-05-20T16:30:00+08:00
toc: true

categories:
- "linux desktop"

tags:
- "linux"

---

虽然是linux版出厂自带deepin专业版，但是随后发的一键win10装机U盘一声不坑的把deepin格式化了，售后还只在线下才提供安装包...

# 笔记本参数

Magicbook 14 (2019)

- AMD R5 3500U 
- 8G + 512G

# 内核

不同的内核在这个笔记本的表现差距略大。当前（2020年-4月）测试过的内核里，只有linux56运行比较平稳。LTS的414/419直接开机黑屏，好像有一个是由于TLP服务的问题，`systemctl disable tlp`可以解决，TLP提供了电源管理功能，禁止了不知道影响有多大。LTS的linux54在睡眠时仍能听到风扇转动，无法正常睡眠。

当前的linux56的主要问题（其它内核也存在）：

- 指纹识别不能用
- 麦克风禁音键不能用
- 风扇无法控制 (好像没有现成的驱动）

# Huawei-WMI

相当于华为为自己的笔记本添加的驱动程序，具体介绍可以参考下面的链接。

https://github.com/aymanbagabas/Huawei-WMI

主要的Features：

> - Function hotkeys, implemented in v1.0
> - Micmute LED, implemented in v2.0. Updated in v3.0 to work with newer laptops.
> - Battery protection, implemented in v3.0. Updated in v3.3 to use battery charge API.
> - Fn-lock, implemented v3.0.

`NOTE: Version v2.0 is the one in mainline kernel >= 5.0, this repository is used for testing and development purposes. v3.3 has been merged in kernel 5.5`

## 电池保护与Fn锁

参考某些理论，锂电池在不用的时候保存为一半的电量对电池的损耗最少。因此，如果笔记本一直插电使用，最好让电池在50%左右时只使用电源的电，而不继续充电，ThinkPad、Surface等笔记本都提供了类似的电源保护功能，huawei-wmi在新的版本里也加入了电池的充电保护（默认是关闭状态）。

Fn锁似乎是个解决强迫症的设置，默认是在Fn键灯亮的时候是F1-F12，而在不亮的时候才是对应的功能键。Fn锁可以将这个改成Fn灯不亮的时候是F1-F12。

这两项设置一般通过下面的matebook-applet设置，在AUR里可以直接安装，里面有使用说明。如果不需要这两个功能可以不折腾。

https://github.com/nekr0z/matebook-applet

使用起来略麻烦，这个applet使用之前需要修改目录`/sys/devices/platform/huawei-wmi/`的权限，`sudo chmod -R 777 /sys/devices/platform/huawei-wmi`，然后命令行运行`matebook-applet`，通知栏里会出现能够改变这两项的图标。如果此目录没有执行命令的用户的权限，则可以查看当前状态而不能修改。

但是，这个目录是动态创建的，重新开机之后权限会还原为root权限。`https://github.com/nekr0z/matebook-applet#huawei-wmi-driver`里有个现成的脚本，使用如下。大概是新建了两个service，动态修改`huawei-wmi`文件夹的用户组，并将当前用户添加到修改的用户组中以获得权限。这个applet设置一次后重启会保留之前的设置，用得不多感觉折腾的必要不大，要调整的时候改一下权限就行。

```bash
$ git clone https://github.com/qu1x/huawei-wmi.git
$ cd huawei-wmi/generic
$ sudo make install
```

貌似主要是改变了`huawei-wmi`里的`fn_lock_state`和`charge_control_thresholds` 两个文件的访问权限，但是这两个文件无法直接修改，不知道matebook-applet是调用的api还是其它的修改方式。

不知道这些是不是华为官方写的，实现的几种语言里都没有中文，这种权限的问题也略不优雅。

# 开机时 Failed to start Load/Save Screen Backlight Brightness of backlight:acpi_video0

启动显示错误信息Failed to start Load/Save Screen Backlight Brightness of backlight:acpi_video0，虽然不影响（其实系统使用了systemd-backlight@backlight:amdgpu_b10来补充了)。

`sudo systemctl mask systemd-backlight@backlight:acpi_video0`

这个服务反正也启动不了，可以直接屏蔽了

此处参照 https://blog.csdn.net/grsharp/article/details/105735792

# 一些其它的参考链接

https://github.com/nekr0z/linux-on-huawei-matebook-13-2019

https://github.com/zer0nka/linux-on-huawei-matebook-d-14-amd
