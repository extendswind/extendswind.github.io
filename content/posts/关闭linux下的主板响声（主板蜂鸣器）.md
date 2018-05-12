
在从deepin的kdd桌面换到xfce桌面后，命令行和界面操作上动不动会让主机响一声。

manjaro的xfce版也是如此，不知道是不是linux下xfce的通病。

主要是搜索的时候百度的结果很奇葩...



用关键字 beep of xfce4 搜到了arch wiki下的内容，原来这玩意叫pc speaker，针对不同的情况有不同的解决方案。

### 最简单粗暴的方式

> 
# rmmod pcspkr
# echo "blacklist pcspkr" > /etc/modprobe.d/nobeep.conf

在基于ubuntu的deepin下和arch下有效，其他的未测试。

### 具体参考

https://wiki.archlinux.org/index.php/PC_speaker
