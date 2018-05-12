---


---


# arch(manjaro-xfce 17.1.4 64-bit) 安装搜狗输入法


本来还很简单的事，被默认的选项弄出一堆坑

### 1. 安装fcitx以及配置

` sudo pacman -S fcitx fcitx-im fcitx-configtool`

fcitx 为基础安装包，fcitx-im用于GTK/QT等界面上使用的包，fcitx-configtool为配置界面。


### 2. 安装搜狗输入法

` yaourt fcitx-sogoupinyin `

此处有坑，默认的安装方式会编译安装qtwebkit，速度非常的慢（一个小时午觉后还没好...)

在库的官方说明中（来自 https://aur.archlinux.org/packages/fcitx-sogoupinyin/ ）依赖项为qtwebkit (qtwebkit-bin)

**其实只依赖qtwebkit-bin，因此先安装qtwebkit-bin可以解决依赖问题（不到一分钟...)**

` yaourt -S qtwebkit-bin`

### 3. fcitx 中设置

fcitx configuration中点加号添加sogou pinyin（默认语言为英语时需要勾选一个选项）

### 4. 添加默认配置

KDM, GDM, LightDM 等显示管理器，请使用 ~/.xprofile
警告: 上述用户不要在~/.xinitrc中加入下述脚本，否则会造成无法登陆。

如果您用 startx 或者 Slim 启动，请使用~/.xinitrc 中加入
如果你使用的是较新版本的GNOME，使用 Wayland 显示管理器，则请在/etc/environment中加入


根据上面的三种情况加入下面的三句

> 
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS=@im=fcitx

参考链接中有更详细的

### 5. 注销后重新登录

### 汇总
` yaourt -S qtwebkit-bin`
` sudo pacman -S fcitx fcitx-im fcitx-configtool`
` yaourt fcitx-sogoupinyin `

fcitx configuration 配置

在配置文件中添加fcitx相关设置

注销重新登录

### 主要参考

https://wiki.archlinux.org/index.php/Fcitx_(简体中文)

https://www.yangshengliang.com/kaiyuan-shijie/linux-shijie/651.html



