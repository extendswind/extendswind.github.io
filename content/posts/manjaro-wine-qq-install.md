---
title: "Testslkfdjsd"
date: 2018-05-11T21:07:53+08:00

description: "Example article description"

categories:
  - "Manjaro"
tags:
  - "wine qq"
 
---


基于AUR的安装是没什么难度了，主要安装后会出各种问题，还有选不同的包的影响。

官方的wiki上推荐安装deepin-wine-tim，基于wine和最新版的tim。安装后存在qq密码每次都要输入的问题（201804测试没有此问题，但使用的最新版tim还是不太稳定）。

有的博客上使用的deepin.com.qq.office，虽然基于tim2.0和deepin-wine，比较稳定，存在不能从tim中复制文字的问题。

想折腾的可以结合两个，基于wine运行tim2.0，放最后头。

### 安装步骤

` yaourt -Sy deepin.com.qq.office`

qq提取消息、截图等快捷键设置

在/opt/deepinwine/tools/sendkeys.sh脚本能够传递快捷键，如直接运行./sendkeys.sh a 则会向qq或tim进程发送 ctrl+alt+a。

做法：

1. setting -> keyboard -> shortcut
2. 添加快捷键，选择上面的脚本，在脚本后面加上a 
3. 指定运行脚本的快捷键

此时按快捷键后相当于qq中按 ctrl+alt+a (截图)

同理可以设置

### 问题及解决

#### deepin-tim 安装完后无法输入中文

/opt/deepinwine/apps/Deepin-TIM/run.sh

不知道是不是其它哪环境变量设置位置不对，在此文件中重新定义环境变量后有效。（如有有更好的位置，求告知）

> 
export XMODIFIERS="@im=fcitx"
export GTK_IM_MODULE="fcitx"
export QT_IM_MODULE="fcitx"

#### 文字过小问题

后面列出的官方wiki上有设置字体的方法，我只是在winecfg命令后加大了dpi，还可以具体改字体。（已经能忍，不想折腾）

#### 表情无法使用

出现在xfce4上

all settings -> window Manager -> Focus -> 取消勾选 "automatically give focus to newly created windows"

#### other

一些没有出现的问题，在wiki上有说明，可在后面的链接上找。此处只列问题：

- 文件被占用
- 字体设置

#### 无法复制文字

感觉是deepin-wine的问题，不知道和电脑有没有关系。安装了deepine-wine-tim(基于wine而不是deepin-wine)，然后从aur中找到deepine.com.qq.office下的deb下载链接，找到里头的tim文件夹替换调`~/.deepinwine/Deepin-TIM/drive_c/Program\ Files/Tencent/TIM/`文件夹。

#### 点右键的菜单都不能用的问题

一个很烦的一点，特别是不能收藏表情，保存图片，还不能屏蔽群消息！

从xfce4转到i3wm后就好了，不知道是不是xfce4的专属bug，现在不想折腾，以后再换KDE一类的试试。

貌似xfce4对wine特别是wine qq不怎么友好啊。

i3wm通知栏图标(system tray)莫名其妙消失；换awesome wm复制的问题解决了，但发表情只能慢慢拖动鼠标，否则窗口会消失....用个qq只能忍了。

### 致谢

从deepin系统崩溃几次之后转向arch的，deepin在国产软件的处理上确实相当不错。感谢！

https://wiki.archlinux.org/index.php/Tencent_QQ_(简体中文)

https://aur.archlinux.org/packages/deepin.com.qq.office/

