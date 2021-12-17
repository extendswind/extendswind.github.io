---
title: "arch linux (manjaro) 下运行tim和qq"
date: 2019-01-20T21:59:49+08:00

categories:
- "linux desktop"

tags:
- "linux"
---


基于AUR的安装是没什么难度了，主要安装后会出各种问题，还有选不同的包的影响。

官方的wiki上推荐安装deepin-wine-tim，基于wine和最新版的tim。安装后存在qq密码每次都要输入的问题（201804测试没有此问题，但还是不太稳定，2018年因为wine的更新导致挂了两次只能回退）。

更推荐使用的deepin.com.qq.office，基于deepin-wine，配置好了比较稳定。

ps: 2021年12月更新，AUR里com.qq.tim.spark从Spark应用商店的移植实现的效果也差不多，deepin-wine-time 已经从wine转到了deepin-wine，各方面的问题也有比较好的解决方案，外加作者一直在积极更新。项目地址上有一些问题的解决方案：

`https://github.com/vufa/deepin-wine-tim-arch`

新版本的更新在不同的环境下出现了一些新问题，建议在各个仓库对应的github链接以及一直更新的arch wiki上找找最新的方案。

# 安装步骤

## 安装

` yaourt -S deepin.com.qq.office`

ps：吐槽，安装deepin-wine的各个确认略多。
d
## qq提取消息、截图等快捷键设置

在/opt/deepinwine/tools/sendkeys.sh脚本能够传递快捷键，如直接运行./sendkeys.sh a 则会向qq或tim进程发送 ctrl+alt+a。

不同桌面环境添加快捷键的方法差不多，主要步骤：

1. setting -> keyboard -> shortcut
2. 添加快捷键，选择上面的脚本，在脚本后面加上a 
3. 指定运行脚本的快捷键

此时按快捷键后相当于qq中按 ctrl+alt+a (截图)

同理可以设置qq其它快捷键

# 一般问题

大多出现在基于wine的tim上，基于deepin的tim问题很少。

## deepin-wine在非gnome系的桌面上的运行问题

3wm, kde, awesome等桌面管理器或桌面环境里运行基于deepin-wine的qq和tim时，会出现下面的错误

> 
X Error of failed request: BadWindow (invalid Window parameter) Major opcode of failed request: 20 (X_GetProperty)


由于deepin-wine依赖了gnome系（mate,cinnamon,gnome）的setting-daemon，需要安装后运行（一般加入开机启动）

```bash
sudo pacman -S cinnamon-settings-daemon
/usr/lib/cinnamon-settings-daemon/csd-xsettings
```

## 无法输入中文

如果其它地方可以使用输入法，一般为环境变量的问题，fcitx没有配置好。

粗暴解决方式: 下面的文件夹中加入环境变量

/opt/deepinwine/apps/Deepin-TIM/run.sh

> 
export XMODIFIERS="@im=fcitx"
export GTK_IM_MODULE="fcitx"
export QT_IM_MODULE="fcitx"

正常的解决方式: 根据系统环境在.xinitrc、.xprofile、/etc/environment等文件中选择正确的文件加入环境变量。（具体参考fcitx的配置）

# 基于wine的问题

## 文字过小问题

出现在基于wine的TIM上，deepin-wine下没问题。

后面列出的官方wiki上有设置字体的方法，我只是在winecfg命令后加大了dpi，还可以具体改字体。（已经能忍，不想折腾）

## 表情无法使用

出现在xfce4上

all settings -> window Manager -> Focus -> 取消勾选 "automatically give focus to newly created windows"

## 点右键的菜单都不能用的问题

一个很烦的一点，特别是不能收藏表情，保存图片，还不能屏蔽群消息！

从xfce4转到i3wm后就好了，不知道是不是xfce4的专属bug，现在不想折腾，以后再换KDE一类的试试。

貌似xfce4对wine特别是wine qq不怎么友好。

## 每次登录显示身份过期,必须重新输入密码

安装deepin后卸载xfce4,然后就出现了这一奇葩问题.

安装xfce4后解决问题.（不知道怎么出的问题，也不知道怎么好的）

## other

一些没有出现的问题，在wiki上有说明，可在后面的链接上找。此处只列问题：

- 文件被占用
- 字体设置


# 参考

从deepin系统转向arch的，deepin在国产软件的处理上确实相当不错，deepin-wine应该算是对开源社区做出的最大贡献之一，解决qq这一大刚需问题。

https://wiki.archlinux.org/index.php/Tencent_QQ_(简体中文)

https://aur.archlinux.org/packages/deepin.com.qq.office/


