---
title: "vsftp 匿名访问设置设置"
date: 2019-10-18T21:59:49+08:00

categories:
- "linux"

tags:
- "software"
---


vsftpd (very secure ftpd)，这软件在权限管理什么的也太安全了点，一点小细节出问题也会出现访问不了的问题。只是想架个ftp局域网传文件，一些博客里小细节和背后设计没有提到，踩了一点坑，记录一下简单的匿名ftp访问方案。

# 主要步骤

**1. 使用包管理器安装 `vsftpd` 。（apt, yum, pacman等)**

**2. 修改配置文件 /etc/vsftpd.conf**

```bash
anonymous_enable=YES  # 允许匿名访问
write_enable=YES  # 允许写文件
anon_upload_enable=YES  # 允许匿名用户上传文件
anon_mkdir_write_enable=YES  # 允许匿名用户创建目录和写权限
anon_other_write_enable=YES  # 允许匿名用户删除、重命名等其它权限  这个在配置文件里默认找不到
```

**3. 新建匿名访问的用户和文件夹**

通过 `local_enable` 选项能够允许ftp通过本地用户访问，登录之后会访问用户的主目录。当使用匿名用户访问时，vsftpd会将用户名为ftp的用户作为登录用户，进入ftp用户的主目录。

**注意，考虑到安全问题，ftp匿名用户的主目录必须为只读**，如果需要上传文件，需要在主目录下新建有写权限的文件夹。

通常会选择`/var/ftp`文件夹存放文件而不是用户默认的`/home`，因此可以修改用户的主目录位置（一般放在/var/ftp），不修改也能用。再次强调，**注意主目录对ftp用户的权限必须为只读**。

```bash
sudo mkdir /var/ftp  # 新建用户文件夹
sudo useradd -d /var/ftp ftp  # 新建用户，并指定用户home目录 
# 如果ftp用户已经存在，在/etc/passwd文件里改用户目录为/var/ftp

sudo mkdir /var/ftp/pub  # 新建一个用于写数据的文件夹
sudo chmod 777 /var/ftp/pub   # 修改文件夹权限
```

**4. 启动服务**

`systemctl start vsftpd`

# 其它

防火墙和SELinux如果使用了需要添加响应的通过规则。

测试访问可以直接用浏览器 `ftp://ip_address`，linux下可以使用FileZilla。







