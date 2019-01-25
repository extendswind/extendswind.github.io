---
title: "manjaro (arch) 安装搜狗输入法"
date: 2019-01-21T20:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---


本来还很简单的事，被默认的选项弄出一堆坑

# 步骤 

先安装fcitx用来管理输入法，然后安装搜狗输入法并配置，然后添加环境变量使相关的应用默认加载fcitx。

## 1. 安装fcitx以及配置

`sudo pacman -S fcitx fcitx-im fcitx-configtool`

fcitx 为基础安装包，fcitx-im用于GTK/QT等界面上使用的包，fcitx-configtool为配置界面（kde下还能安装一个kde版的configtool）。


## 2. 安装搜狗输入法

` yaourt fcitx-sogoupinyin `

此处有坑，默认的安装方式会编译安装qtwebkit，速度非常的慢（一个小时午觉后还没好...)

在库的官方说明中（来自 https://aur.archlinux.org/packages/fcitx-sogoupinyin/ ）依赖项为qtwebkit (qtwebkit-bin)

**其实只依赖qtwebkit-bin，因此先安装qtwebkit-bin可以解决依赖问题（不到一分钟...)**

` yaourt -S qtwebkit-bin`

## 3. fcitx 设置中添加搜狗拼音

fcitx configuration中点加号添加sogou pinyin（默认语言为英语时需要勾选一个选项）

## 4. fcitx环境变量的添加

gui应用的环境变量一般不通过profile和bashrc。

arch wiki下的内容：

> 
KDM, GDM, LightDM 等显示管理器，请使用 ~/.xprofile
arch wiki 警告: 上述用户不要在~/.xinitrc中加入下述脚本，否则会造成无法登陆。(但在里头加了也没挂)
如果您用 startx 或者 Slim 启动，请使用~/.xinitrc 中加入

> 
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx

> 
如果你使用的是较新版本的GNOME，使用 Wayland 显示管理器，则请在/etc/environment中加入

> 
GTK_IM_MODULE=fcitx
QT_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx

参考链接中有更详细的说明，我用的manjaro+xfce4以及后面改装的cinnamon和awesome都是在lightDM下该的.xinitrc，没有.xprofile文件，也能正常用。
（注意添加在最后exec $(...)的前面）

使用manjaro+kde和awesomewm混用时，加在.xinitrc下莫名奇妙的失效，不知道和为了deepin-wine运行的cinnamon-xsettings有没有关系，加在/etc/environment文件中正常运行。

## 5. 注销后重新登录

# 汇总

` yaourt -S qtwebkit-bin`
` sudo pacman -S fcitx fcitx-im fcitx-configtool`
` yaourt fcitx-sogoupinyin `

fcitx configuration 配置搜狗输入法

添加fcitx相关的环境变量

注销重新登录

# 少量问题

1. fcitx的安装一般会自动启动（右下角会有输入法图标，top里可以看），如果在i3 awesomewm等窗口管理器中没有自动启动，则将`fcitx -r`加入到自动启动的脚本中。
2. ibus输入法管理与fcitx冲突，如果已有安装需要禁用。


# 主要参考

https://wiki.archlinux.org/index.php/Fcitx_(简体中文)

https://www.yangshengliang.com/kaiyuan-shijie/linux-shijie/651.html



