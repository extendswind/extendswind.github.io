---
title: "使用Python3发布博客到支持mateweblog的平台（博客园等）"
date: 2018-09-04T10:30:00+08:00
toc: true

categories:
- "Operation"

tags:
- "blog"

---


用个人域名搭建的博客在百度搜索上的SEO太差，百度一直只收录主页，懒得再为这些问题折腾，直接同步到博客园算了，考虑用Python。

貌似CSDN已经关闭了metawebblog接口，只在博客园上测试。


# Python发博客的主要方案

1. 通过xmlprc的metaweblog接口（首选）
2. CSDN和博客园的api（定位不是用来发博客的，申请key和调接口略麻烦）
3. 使用抓包的技术模拟浏览器登录发博客（没悬念更折腾）

# 代码

对于支持metaweblog的博客平台，只要提供用户名、密码和博客相关信息。

python2 需要将后面的xmlrpc.client改为xmlrpclib，并且import xmlrpclib

```python
#!/bin/python3

import xmlrpc.client

username = ''  # TODO  your username
passwd = '' # TODO your passwd
# url = 'http://www.cnblogs.com/' + username + '/services/metaweblog.aspx' # 此链接已挂
url = 'https://rpc.cnblogs.com/metaweblog/' + username

title = "helloWorld"
content = "<p> test <p>"
tags = "tag1, tag2"

blogProxy = xmlrpc.client.ServerProxy(url)

# 获取最近博客列表
print(blogProxy.metaWeblog.getRecentPosts('', username, passwd, 1))

# 发布博客
blogProxy.metaWeblog.newPost('', username, passwd, dict(title=title, description=content, mt_keywords=tags), True)
```

# 参考

https://rpc.cnblogs.com/metaweblog/fly2wind#Post API文档

https://magicsword.wordpress.com/2012/01/17/tet34/

https://blog.csdn.net/shajunxing/article/details/79553472

https://github.com/RussellLuo/pymwa

https://github.com/huafengxi/pblog

