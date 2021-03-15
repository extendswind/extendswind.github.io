---
title: "MQTT服务搭建和简单使用"
date: 2021-03-15T10:30:00+08:00
toc: true

categories:
- "IoT"

tags:
- "IoT"

---

MQTT为了物联网的消息传递而设计，业余时间弄了个报警器，之前用长轮询的实现感觉略麻烦，测试了一下MQTT的实现。

个人感觉使用比较简单，对网络问题的处理也比较完善，但是某些方面的灵活性略微不足，而且中文资料相对较少。


# 简单使用

服务端用mosquitto，客户端用python-paho-mqtt。

## 服务端

安装mosquitto，然后systemctl start mosquitto启动对应的服务。

公网环境下建议将配置文件中的默认端口1388改为其它端口，避免被直接扫描。

一些安全方面的设置也建议加上。

## 客户端

**subscriber**

```python
#!/bin/python
import paho.mqtt.subscribe as subscribe

# 当调用这个函数时，程序会堵塞在这里，直到有一条消息发送到 topics/topic1 主题
msg = subscribe.simple("topics/topic1", hostname="your ip", port=yourport,
                       retained=False, client_id="youid", clean_session=False, qos=1)
print(f"{msg.topic} {msg.payload}")
```

hostname和port需要改为正确的参数。

其中，网络环境好并且不需要离线接收消息时，可以不设置`clean_session`、`client_id`、`qos`三个参数。

**publisher**

发送一条消息

```python
#!/bin/python

import paho.mqtt.publish as publish

publish.single("topics/topic1", "a message", hostname="your ip", port=yourport, qos=1)
```

# 其它

## MQTT 几个基本概念

通常由3部分构成：subscriber订阅客户端、publisher发布消息客户端、Server服务器。

主题topic，类似一连串消息的标识符。

Message，具体的消息，对应于每个topic。

publisher向服务器指定主题发送消息。

subscriber连接服务器并且指定主题，当publisher向订阅的主题推送消息后，服务器会推送到对应的subscriber。

## retained消息

MQTT使用了一个retained消息机制，用于保存主题的状态。publisher可以向主题发送retained消息，在subscriber获取retained消息时（获取参数中retained=True）服务端会返回**最后一条**retained消息，每一次都会返回而非普通消息的那种只读取一次。ratained消息更像是一种保存消息的状态，用在主题状态的设置，如开门的感应器，ratained消息用于标记门是否打开。

在python的paho库中，publisher的retained参数默认是False，而subscriber的retained参数默认为True，这个有点小坑。

## QoS（Quality of Service）与离线消息

在subscriber和publisher中都可以指定，定义消息的可靠性级别，服务器会取两个客户端中较低的级别作为主题消息对应的处理级别。

QoS0，At most once，至多一次；
QoS1，At least once，至少一次；
QoS2，Exactly once，确保只有一次。

使用默认参数时，如果subscriber掉线，publisher发送的消息会丢失。

要想subscriber在离线后重新连接，还能收到publisher的消息，需要下面的设置：

1. publisher与subscriber的QoS级别都设置为0以上；
2. subscriber的`clean_session`设置为False；
3. subscriber设置固定的`client_id`.

## 存储消息历史记录

这个翻了一下网上的资料，感觉略不靠谱。MQTT的设计中没有考虑消息在服务端的存储，通常采用下面的几个方案：

1. 使用另一个subscriber获取消息并存储；
2. 使用EMQ等支持插件的服务端，通过插件处理消息。
3. 换kafka...

