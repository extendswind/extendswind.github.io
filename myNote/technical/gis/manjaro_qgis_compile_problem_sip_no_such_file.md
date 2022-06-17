---
title: "Manjaro上编译QGIS时出现的/usr/bin/sip: No such file or directory错误"
date: 2022-06-17T15:30:00+08:00
toc: true

mathjax: true

categories:
- "GIS"

tags:
- "GIS"
- "QGIS"

---

解决方案:

`sudo pacman -S sip4`

sip库的默认版本比较新，/usr/bin/sip文件在sip4库中。（估计是旧版和新版的sip使用方式不一样吧，sip4的包里是sip可执行文件和一个头文件，默认安装的sip包是python的包。）

```bash
# sip包中的文件：
sip /usr/bin/sip-build
sip /usr/bin/sip-distinfo
sip /usr/bin/sip-install
sip /usr/bin/sip-module
sip /usr/bin/sip-sdist
sip /usr/bin/sip-wheel
sip /usr/lib/python3.10/site-packages/... # 还有一些python包文件


# sip4包中的文件：
sip4 /usr/bin/sip
sip4 /usr/include/sip.h
sip4 /usr/share/licenses/sip4/LICENSE

```


