---
title: "python脚本避免被多次执行"
date: 2021-09-01T08:30:00+08:00
toc: true

categories:
- "programming basic"

tags:
- "python"

---

写了一个脚本，想挂后台运行，又想避免重复运行，需要检测后台是否有已经运行的脚本。实现目标：python脚本只运行一次，第二次运行时直接退出。

在linux上比较合适的做法是创建一个systemd控制的service，有时候就临时用一用，还有考虑跨设备运行的时候也有点麻烦。

找了两个比较简单的方案。

# 1. 使用tendo

```python
import tendo.singleton

single = tendo.singleton.SingleInstance()

# 测试代码
import time
while(True):
    print("test")
    time.sleep(2)
```

# 2. 使用pidfile

```python
from pid import PidFile

# 会对with中的代码块加锁
with PidFile():
    import time
    while(True):
        print("test")
        time.sleep(2)
```

或者

```python
from pid.decorator import pidfile

@pidfile
def main():
    # 被pidfile标签装饰的函数只能运行一次
    # running code
```

# 基本原理

最常见的基本操作都差不多，在运行到需要只能执行一次的代码时，在某个路径下创建一个pidfile的文件，第二次执行时如果检测到路径下有pidfile就报错跳过执行。代码执行完成后删除pidfile。

为了避免pidfile在某些特殊情况下退出未执行，通过atexit等库处理退出时的情况。


类似的做法还有创建一个linux的socket，退出时删除。以及基于ps等linux脚本命令查看运行的进程名。

# 参考链接

https://stackoverflow.com/questions/788411/check-to-see-if-python-script-is-running/7758075#7758075

https://pythonhosted.org/tendo/

https://pypi.org/project/pid/

