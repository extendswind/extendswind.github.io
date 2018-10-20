---
title: "使用AwesomeWM作为Mate(Gnome相同) Desktop的窗口管理器"
date: 2018-10-20T20:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---

AwesomeWM这种平铺的窗口管理器用得很爽，只是基于wine的qq最近又莫名其妙抽风，感觉还是切到deepin-wine上比较靠谱。而deepin-wine在awesome下运行qq会报错`X Error of failed request: BadWindow (invalid Window parameter) Major opcode of failed request: 20 (X_GetProperty)`，而在Gnome系下运行正常。看到Gnome和Mate能够运行i3wm，就折腾了一下试试。

1. 安装AwesomeWM、Mate桌面环境与dconf-editor（arch下使用`pacman -S`）。

2. 进入Mate桌面环境后，修改`org.mate.session.required-components windowmanager `的值为'awesome'，如果不需要桌面上的图标，可以将`org.mate.session.required-components`的值只留下`windowmanager`。

3. 上面的设置无法通过命令行打开awesome，需要添加awesome的图标。在/usr/share/applications目录下新建awesome.desktop，内容如下（网上直接粘的，估计有些可以不要，懒得试了）：

```
[Desktop Entry]
Type=Application
Name=awesome
Exec=awesome
NoDisplay=true
# name of loadable control center module
X-MATE-WMSettingsModule=awesome
# name we put on the WM spec check window
X-MATE-WMName=awesome
# back compat only
X-MateWMSettingsLibrary=awesome
X-MATE-Bugzilla-Bugzilla=MATE
X-MATE-Bugzilla-Product=awesome
X-MATE-Bugzilla-Component=general
X-MATE-Autostart-Phase=WindowManager
X-MATE-Provides=windowmanager
X-MATE-Autostart-Notify=true
```


