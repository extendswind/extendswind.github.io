---
title: "Manjaro内核编译"
date: 2020-05-19T22:30:00+08:00
toc: true

categories:
- "linux"

tags:
- "linux"

---

重新编译内核可以修改编译时的参数，使内核在运行时更高效的支持本地硬件。Manjaro团队在gitlab上放了Manjaro内核的编译文件，稍加修改即可使用自己的选项编译。

主要参考论坛中Manjaro团队的philm的回答 https://forum.manjaro.org/t/how-to-compile-the-mainline-kernel-the-manjaro-way/51700/35

# Gitlab 仓库

philm提到了manjaro在gitlab上编译内核的仓库。https://gitlab.manjaro.org/packages/core/linux56.git  后面使用不同的linux版本号。


# 仓库文件介绍

仓库中不同后缀文件的作用

> - files ending with .patch should be clear. These are adjustments we think will fit for our distro best.  
> - files starting with config are our modified settings on how we configure the kernel on our end.  
> - files starting with linux are specific files to post configure the system. They are used either by pacman or mkinitcpio, which configures the initramfs image.  
> - files ending with .hook are used by pacman to pre- or post-configure the kernel.  

主要的脚本文件为PKGBUILD，指定了包中包含的文件，需要执行的操作等。

内核编译参数的设置在config.x86_64文件中，需要改变的参数可以在这里修改。（PKGBUILD中新建了.config文件并将config.x86_64文件的内如cat进入）


# 主要编译过程

> So here is a quick tutorial to compile your own kernel on Manjaro:  
> 
> first you have to clone our package repo for linux417 via git clone https://gitlab.manjaro.org/packages/core/linux417.git  
> 
> then change into that directory and execute makepkg -s. This will compile the kernel as I had configured it. You may want to stop the time.  
> 
> If you however want to use our tools, you may install manjaro-tools-pkg and only change into the directory where you cloned the git-repo. No need to change into the linux417 folder. You simply may use then buildpkg -p linux417. This will create a new chroot on which the package gets compiled in a separate system to avoid any issues with other systems. Only used if you want to redistribute your package to somebody else.
	
大概流程为：

1. git clone对应的仓库
2. 修改编译参数config.x86_64
3. makepkg编译内核

国内可能存在git下载代码非常慢的问题，可以通过网页端或其它镜像站下载代码文件到指定目录，然后修改PKGBUILD文件，将`source=(`后的链接替换成下载后的文件名。如果内核代码或其它文件（config.x86_64）修改过，还需要将`sha256sums=(`后的对应位置改为`'SKIP'`或者计算后的值。

为了避免编译器版本等造成的环境问题，manjaro还提供了manjaro-tool-pkg，在仓库所在的目录运行`buildpkg -p linux56`会新安装一个新的环境然后chroot使用独立的环境构建。

最好给新编译的内核一个重新的命名，否则在安装时会覆盖同名称的官方内核。需要改命令的地方不止在PKGBUILD，具体在哪也懒得找了...
 
> [optional] give your kernel a different name so it can be easily installed alongside existing ones.
> For that, you have to replace every instance of -MANJARO with a name of your choice, this in every file, not only in PKGBUILD!
> You could use a simple ‘find and replace’ in your text editor, or use the sed command, e.g. sed -i -e "s|-MANJARO|-CUSTOM|" PKGBUILD.
> You also have to edit various other names, like

# 修改内核参数

`zcat /proc/config.gz > .config ` 导出当前内核的配置。

在linux内核代码目录通过make可以得到内核的设置参数或设置界面：

- `make localmodconfig`  获取当前的内核参数，这种方法能够得到一个非常精简的内核，但没有加载过的内核模块都不会被编译。（在我的笔记本上内核大小成了之前的25%，但是睡眠出问题）
- `make nconfig`: 新的命令行 ncurses 界面
- `make xconfig`: 用户友好的图形界面，需要安装 packagekit-qt4[断开的链接：package not found]。建议没有经验的用户使用此方法。
- `make gconfig`: 和 xconfig 类似的图形界面，使用 gtk.

运行后会生成一个新的.config文件，将文件覆盖config.x86_64后，直接makepkg即可。

一些内核参数可以参考gentoo的wiki：

https://wiki.gentoo.org/wiki/Handbook:X86/Installation/Kernel
