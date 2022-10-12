---
title: "配置好公钥后git push还需要输入密码"
date: 2022-10-12T17:00:48+08:00

categories:
- "programming basic"

tags:
- "git"
---

之前配好的公钥一直能用，最近不能用了，通过`ssh git@github.com`测试公钥是否生效，先报REMOTE HOST IDENTIFICATION警告，将`~/.ssh/known_hosts`中对应的条目删除后，然后需要输入密码，如下：

```bash
git@github.com's password:
```

github被墙一般也只是长时间不出结果得到连接超时，出现需要输入密码有点奇怪。

检查了github网页设置、秘钥权限、网络ip，之后发现是DNS的解析问题，ping github.com时得到了一个武汉的IP，教育网的DNS服务器有点过分了……以前都是解析到正常的ip无法访问，现在直接来一波不知道什么的IP，如果被利用为钓鱼服务器坑就大了，不过我的代码也没太大价值还无所谓。

问题解决方法：在站长工具上ping github.com，找能用的服务器IP，然后Host文件中添加对应的ip和github.com解析选项。

可能会涉及DNS污染需要相关工具的情况。
