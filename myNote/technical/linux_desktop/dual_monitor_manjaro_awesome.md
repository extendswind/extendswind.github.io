---
title: "manjaro AwesomeWM 上使用双显示器"
date: 2019-01-24T21:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---


安装manjaro时使用独显的单显示器，在主板上接第二个显示器一直没反应。

# 几个问题和解决

## BIOS里检查是否关闭了集显开关

大多数显卡的默认设置都会在识别独显后关闭集显，要使用集显上的接口需要单独设置。

如果接口允许，最好将两个显示器都接在独显上。

## 基于KDE等桌面

如果主板和显卡驱动正常，一般各大桌面环境都支持GUI配置，可以在显示设置里直接修改。

## 使用 xrandr 识别和控制显示器

xrandr  直接执行会得到显示器的连接状态，获取显示器的名称后可以用下面的命令显示。

（其中DVI-I-1-1与VGA1为两个显示器的名称）

`xrandr --output DVI-I-1-1 --mode 1440x900 --primary --output VGA1 --mode 1366x768 --pos 1440x132`  设置输出的显示器以及显示参数，每个`--output`后接显示器名以及参数，`--mode`指定分辨率，`--primary`指定主显示器，`--pos`指定位置，或者用`--right-of`指定相对位置。

更进一步的设置可以在arch wiki

## xrandr 找不到显示器

xrandr --listproviders  得到当前的显示器输入设备（一般name为Intel的是集显，name为nouveau的是开源独显驱动，Nvidia为闭源显卡驱动）

xrandr --setprovideroutputsource 0 1  将上面的设备设置为输入源

如果xrandr --listproviders 没有得到所有的输入源，则需要折腾驱动。

## 驱动问题

一般建议将两个显示器都接在独显上，出问题的概率更低（独显一般口不够或者需要转换略尴尬）。

我将显示器分别接在独显和主板接口上，在manjaro和deepin两个系统下都发现NVIDIA驱动有问题，primary显示器会显示两个显示器的内容。而将显卡驱动切换到开源驱动（nouveau）时正常(据说开源驱动性能略低）。

```
mhwd -li --pci 查看已经安装的驱动
mhwd -l --pci 查看能用的驱动
sudo mhwd -r pci video-nvidia 移除驱动video-nvidia
sudo mhwd -a pci videa-linux 安装开源显卡驱动（nouveau）
```

manjaro上通过mhwd简化了各种配置，详见：

`https://wiki.manjaro.org/index.php/Configure_Graphics_Cards`

## AwesomeWM

默认快捷键：

ctrl+super+j/k  屏幕之间焦点移动
super+o  当前窗口移动到另一个屏幕

默认的设置不多，想要的功能可以自己撸，如

添加一个快捷键，将窗口移动到另一个屏幕并且保持焦点在当前屏幕

```lua
awful.key({ modkey, "Shift" }, "o", function (c) c:
      move_to_screen()
      awful.screen.focus_relative(-1)
    end, 
    {description = "move to other screen without move focus", group = "MySettings"})
```


