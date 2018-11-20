---
title: "arch linux下网易云音乐运行没反应，只能使用root用户运行"
date: 2018-11-20T19:59:49+08:00
toc: true

categories:
- "linux desktop"

tags:
- "linux"
---

最近打开网易云音乐没有反应，只在htop命令下能看到运行的进程（manjaro+mate+awesome）。

命令行sudo可以正常运行

# 无用尝试

- 安装官网给的最新1.1.3的deepin与ubuntu16两个版本
- 网上提到的--no-sandbox参数运行
- kill已经运行的netease-cloud-music相关进程

# 解决方案

回退到更早的1.0.0版，估计新版没有在各个linux系统下测试。

`http://s1.music.126.net/download/pc/netease-cloud-music_1.0.0-2_amd64_ubuntu16.04.deb`

debian系就直接dpkg -i吧

arch系通过AUR安装稍麻烦:

1. 卸载原版本
2. `yaourt -S netease-cloud-music`
3. 按y `Edit PKGBUILD`
4. 将1.1.3的安装包地址替换为1.1.0的安装包地址，并且将对应hash值改为skip，具体如下

改之前：

```
source=(
	"http://packages.deepin.com/deepin/pool/main/n/netease-cloud-music/netease-cloud-music_${pkgver}-${_pkgrel}_amd64.deb"
	"http://music.163.com/html/web2/service.html"
)
md5sums=('53c47c1bf6797b2a0e455bc59833ab2d'
         'SKIP')
```

改之后

```
source=(
  "http://s1.music.126.net/download/pc/netease-cloud-music_1.0.0-2_amd64_ubuntu16.04.deb"
	"http://music.163.com/html/web2/service.html"
)
md5sums=('SKIP'
         'SKIP')
```

然后正常安装即可



