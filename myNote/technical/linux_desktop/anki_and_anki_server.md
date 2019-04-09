---
title: "anki的使用以及anki server的配置"
date: 2019-03-04T21:59:49+08:00

categories:
- "linux desktop"

tags:
- "software"
---

首先吐槽，anki作为老牌软件，国内资料并不多。

虽然html的卡片显示和python的插件式开发上看比较适合程序员，但从各种配置上感觉程序员用户量并不大。

因此，想深度使用准备折腾。


# 简单使用

- 淘制作好的卡片，导入
- 卡片可以套模板更美观（添加时的Cards选项，支持html）
- 插件里的`awesome TTS`很多人推荐但速度略慢
- 添加单词可以用`Word Query`

官方文档[https://apps.ankiweb.net/docs/manual.html](https://apps.ankiweb.net/docs/manual.html)

插件编写文档[https://apps.ankiweb.net/docs/addons.html](https://apps.ankiweb.net/docs/addons.html)


# 一些坑

删除卡片不会删除对应的媒体文件，需要点击 check media 后手动删除。


# anki server 的安装

官网的速度爆表，而且有数据安全问题，因此官网给出了自建anki server的解决方案。

百度上的大多使用 https://github.com/dsnopek/anki-sync-server ，可以基于pip2和python2直接安装，个人在基于Arch的linux下感觉坑多，在linux上的anki 2.1.9连不上上面python2的服务器（bug解决一个又出一个），更建议使用基于python3的fork项目：https://github.com/tsudoko/anki-sync-server 。


## 基于python3的仓库

github上的readme已经写得比较清楚，下面的搬运点大概。

1、clone 仓库

` git clone https://github.com/tsudoko/anki-sync-server.git`

2、安装anki或anki-bundled相关的库

直接使用包管理器安装 `sudo pacman -S anki` 

如果包管理器里没有anki（如debian），也可以用pip安装anki-bundled相关的库

```bash
 $ git submodule update --init  # anki-bundled已经加入为submodule，可以先更新
 $ cd anki-bundled
 $ pip install -r requirements.txt  # 安装相关的库
```

3、安装webob

`pip install webob`

4、修改 ankisyncd.conf 文件

文件中保存了主要的配置，主要改端口，默认端口一般也就能用。

5、创建用户

`./ankisyncctl.py adduser <username>`

6、启动服务器

` python -m ankisyncd`


## 客户端配置

**android anki** 在高级设置里填上ip和端口就行。


**anki桌面版2.1.x** 修改了添加插件方式。在插件文件夹下新建一个新的文件夹（官方插件命名都是数字方便更新，用字母也行），然后在其下新建一个文件`__init__.py`，加入以下内容。

```python
import anki.sync, anki.hooks, aqt

addr = "http://127.0.0.1:27701/" # put your server address here
anki.sync.SYNC_BASE = "%s" + addr
def resetHostNum():
    aqt.mw.pm.profile['hostNum'] = None
anki.hooks.addHook("profileLoaded", resetHostNum)
```


**anki桌面版2.0** 直接在插件文件夹下新建一个.py文件（如ankisyncd.py），加入以下内容。

```python
import anki.sync

addr = "http://127.0.0.1:27701/" # put your server address here
anki.sync.SYNC_BASE = addr
anki.sync.SYNC_MEDIA_BASE = addr + "msync/"
```

## 基于python2的server

百度上搜到的差不多都是这种，可能出各种bug，不怎么建议折腾，列一下大概的折腾步骤和踩坑。

简直就是个没人测试的系统！各种莫名奇妙的bug需要调。

好不容易装好了，局域网下卡片数量较多时（4000）速度也不怎么样....

debian 系统安装稍正常

```bash
easy_install ankiserver  # 为什么不用pip？  因为会有莫名奇妙的错误！！
mkdir ankiserver_data  # anki server的数据目录
cd ankiserver_data
cp /usr/lib/python2.7/site-packages/AnkiServer-2.0.6-py2.7.egg/examples/example.ini ./production.ini # 复制配置文件，如有必要可以改改端口一类的

ankiserverctl adduser test # 添加用户
ankiserverctl debug  # debug模式启动 （为什么是debug，你猜一次成功的概率？）
```

如果此时显示了正常启动然后手机能连上就算幸运了。

踩过的坑：

- 虽然python3的ankiserver在pip仓库里有，但还是不试为好。
- 要用 `easy_install` 代替pip（小心找不到文件一个个改路径）
- 装server的系统上最好不要装anki客户端（anki使用的python3莫名奇妙会被python2的server调用....估计是anki在/usr/share文件夹下，/usr/share又是PATH的目录，如果非要装就把/usr/share/anki改个名字吧，虚拟环境都上了还是跳到anki客户端的python3代码上报错）
- andriod手机登录时显示服务器和手机时间差了5s，可能折腾一下ntp就行吧
- 系统编码需要设置成utf-8（默认用英语没碰到这问题）

安卓手机使用正常，但是anki 2.1.9 linux桌面版连不上。
