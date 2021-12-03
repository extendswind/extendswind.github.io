---
title: "git push时提示错误 sign_and_send_pubkey: no mutual signature supported"
date: 2021-12-03T16:00:48+08:00

categories:
- "programming basic"

tags:
- "git"
---

git push命令之后，出现下面的错误提示：

> sign_and_send_pubkey: no mutual signature supported
> git@gitee.com: Permission denied (publickey).
> fatal: Could not read from remote repository.
>
> Please make sure you have the correct access rights
> and the repository exists.

openssh的新版本（当前8.8p1-1）默认不支持ras的默认秘钥。

一开始以为是gitee码云干了什么升级，之后发现是我的manjaro openssh版本太新的问题，已经不支持我几年前生成的秘钥（但是为什么ssh-keygen还是默认用的rsa）。

# 推荐做法

ssh-keygen -t ed25519 -C "your_email@example.com"

生成一个新的秘钥，然后公钥添加到gitee账户。


# 最简单处理

修改ssh的客户端的配置文件，`~/.ssh/config` 或全局的配置文件 `/etc/ssh/ssh_config`，在其中加下面的代码。

> PubkeyAcceptedKeyTypes +ssh-rsa



