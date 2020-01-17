---
title: "一次修复linux的efi引导的集中方法总结记录"
date: 2019-11-26T20:59:49+08:00
toc: true

categories:
- "linux desktop"

tags:
- "linux"
---

起因：EFI分区被删除导致引导问题。

症状：

1. 通过安装其它系统的方式。正好想试试其它的linux发行版，就在另一个分区装了deepin，完成后硬盘没有发现UEFI引导；然后又尝试装了openSUSE，仍没在硬盘发现UEFI引导。（失败）

2. 通过live cd重新在efi分区安装grub。（wiki推荐的一般方式，仍失败）

3. 通过live cd安装refind。（仍不行）

4. 安装的系统可以通过manjaro live cd直接boot。

5. 安装win10可以发现UEFI的引导方式（只启动win10，安装grub也只启动win10）



引导的问题网上的解决方案很多，对于一些新的电脑UEFI的方式应该很好修复，但一些比较老的电脑可能出现各种坑问题，用legacy的引导还是稳定一点。


UEFI的引导通过grub的各种安装尝试都无法被主板识别，一直检测不到硬盘UEFI的启动项。怀疑主板并不支持linux grub2写入的UEFI引导信息，只支持windows的。最后通过安装win10，用refind覆盖win10的efi启动条目解决问题。


# 最常规的修复方式 通过live cd

将系统烧入U盘，启动U盘进入系统后修复。涉及两种方式：

1. 通过boot-repair
2. grub-install 命令安装


还有通过grub命令行的方式，不常用没折腾。

建议烧入的系统为ubuntu和manjaro。deepin的live cd在我的电脑上有显示的bug，而且添加ppa有一点坑。openSUSE上的grub命令和debian系arch系不怎么一样。ubuntu的主要优点在于可以通过安装boot-repair进行一键修复，manjaro和arch的live cd提供了直接的manjaro-chroot以及arch-chroot，进入后直接安装grub就行，而且manjaro的live cd支持直接引导启动efi分区中的系统。

在下面的两种操作之前，最好通过gparted等软件新建一个efi分区（fat32,一般几十兆，openSUSE建议不小于500M，带efi标签）。

## 基于ubuntu的boot-repair

网上的资料多操作也不复杂，主要注意U盘从UEFI模式启动。

```bash
sudo add-apt-repository ppa:yannubuntu/boot-repair -y
sudo apt-get update
sudo apt-get install boot-repair -y
sudo boot-repair
```

## grub-install 命令安装

使用manjaro live cd，其它的系统可能需要安装grub2、efibootmgr、grub-efi-amd64、os-prober等包。

以下需要root权限，`sudo -i`或命令前加`sudo`

1、 查看要引导系统的分区和efi分区的编号（`fdisk -l`）
2、 挂载引导系统的分区（一般 `mount /dev/sda4 /mnt`）
3、 挂载efi分区到系统分区的`/boot/efi`目录（`mount /dev/sda2 /mnt/boot/efi）
4、 chroot到硬盘系统分区 

对于ubuntu

``` 
mount --bind /dev/ /mnt/dev
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
chroot /mnt
```

对于manjaro直接

```
manjaro-chroot /mnt
```

5、 安装grub

```
grub-install --target=x86_64-efi /dev/sda2  # target默认是x86_64-efi
grub-grub-mkconfig -o /boot/grub/grub.cfg
update-grub
```


# 各种操作和问题

上面的操作在一般较新的电脑上就能启动了。


## refind 引导程序

可以在启动时动态检查和引导所有硬盘里efi分区里的配置，还可以设置各种主题。grub每次只能识别efi分区EFI目录下的某一个写好的配置。

安装后直接运行`refind-install`脚本即可，也可以指定efi分区。


## 安装完仍默认启动win10

UEFI支持一种安全模式，win10会独占UEFI，双系统时需要在win10中关闭安全启动。（没碰到，具体资料可搜）。

其次，修改efi的引导顺序，进入win10后，使用bcdedit命令

```
bcdedit /enum  # 查看引导
bcdedit /default {12277df3-07da-11e8-a54c-9f200771404e}  # 设置默认项

# 如果上面的设置默认没有用，可以暴力修改windows的引导文件到其它的引导文件
# refind可以改为其它的系统
bcdedit /set {bootmgr} path \EFI\refind\refind_x64.efi   
```


## win10启动几次就让grub引导消失的问题

win10会默认修改UEFI的引导顺序。

好像是win10 系统配置->常规 里的最后一个勾，用了上面的方式后，没怎么遇到这个问题。


## 启动时仍没有UEFI引导选项的问题

一般上面的操作能解决绝大多数电脑的，我的2代i3电脑开机f12的启动菜单中，怎么安装linux都出现不了UEFI菜单，但安装windows能，于是一般先装windows再改默认引导...

一次windows的UEFI在装完系统第一次启动后也不显示无法选择，在BIOS里设置只允许UEFI启动，竟然启动了....

更坑爹的是，双硬盘时启动不了，通过换sata线的接口就启动了...




