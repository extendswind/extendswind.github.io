---
title: "设计模式 之 静态代理模式和装饰者模式"
date: 2018-06-20T17:25:25+08:00
toc: true

categories:
- "programming"

tags:
- "design patterns"
---

这两种模式的相似度极高，作用也类似，都是对已有的类进行包装，以添加新的控制（代理模式）和功能（装饰者模式），其实这两点也没有严格区分。

两种设计模式的重点在于，已有的类（被代理、被装饰）与新类（代理类、装饰类）都实现同一接口，通过接口调用新类会和调用已有的类相同。

设计模式中常说使用“组合”优先于“继承”。对于想要改变一个写好的类中的某些功能，一般情况下使用继承的灵活性不如组合。继承的某些缺点：单继承（多继承也面临一些问题）、破坏封装（子类可能改变某些细节），父类的改变对子类可能有影响。“组合”的方式将需要被修改或加强的类作为新类的类成员，可以通过添加多个类成员以得到组合多种功能的效果。


# 静态代理模式 （static proxy）

静态代理的思想：将被代理类作为代理类的成员，通过代理类调用被代理类的函数，并添加新的控制。包装类与被包装类实现同一接口，使得使用时的代码一致。

应用：已经有一个日志记录器LoggerSubject，需要对writeLog()函数的前后进行某些操作（如初始化、异常处理等），使用Proxy类间接调用LoggerSubject.writeLog()实现新控制操作的添加。

实现如下

```java 
interface Logger {
    void writeLog();
}

// 被代理类
class LoggerSubject implements Logger{
    @Override
    public void writeLog(){
        System.out.println("writeLog by LoggerSubject");
    }
}

// 代理类
class Proxy implements Logger{
    Logger logger;
    // 与装饰者模式的主要区别位置
    // 代理模式一般要求和原来的类行为一致，因此构造函数不传入对象
    Proxy(){
        this.logger = new LoggerSubject();
    }
    @Override
    public void writeLog(){
        System.out.println("logger write before");
        logger.writeLog();
        System.out.println("logger write after");
    }
}

public class StaticProxy {
    private static void write(Logger logger){
        logger.writeLog();
    }
    public static void main(String []argvs){
        Logger logger = new Proxy();
        // 还可能出现下面的嵌套
        //Logger logger = new Logger3(new Proxy(new LoggerSubject()));
        write(logger);
    }
}
```

# 装饰者模式

主要用于给一个类添加新功能

主要思想：被装饰类作为类成员被调用，为了使装饰类能和被装饰类一样的使用，两者实现相同的接口。

通过构造函数传入被包装类，能够自由组合装饰，如下面的最后的使用。


```java
interface Logger {
    public void writeLog();
}

class BaseLogger implements Logger {
    public void writeLog(){
        System.out.println("writeLog");
    }
}

class DecorationLogger implements Logger{
    private Logger logger;
    DecorationLogger(Logger logger){
        this.logger = logger;
    }
    @Override
    public void writeLog(){
        logger.writeLog();
        System.out.println("Decoration");
    }
}

class DecorationLogger2 implements Logger{
    private Logger logger;
    DecorationLogger2(Logger logger){
        this.logger = logger;
    }
    @Override
    public void writeLog(){
        logger.writeLog();
        System.out.println("Decoration2");
    }
}


public class Decoration {
    public static void main(String []argvs){
        Logger logger = new DecorationLogger2(new DecorationLogger(new BaseLogger()));
        logger.writeLog();

        Logger logger1 = new DecorationLogger(new DecorationLogger2(new BaseLogger()));
        logger1.writeLog();

        Logger logger2 = new DecorationLogger(new BaseLogger());
        logger2.writeLog();
    }
}
```

缺点和注意：包装的自由组合的灵活性可能导致测试的困难，注意组合可能带来的bug。


# 静态代理与装饰者模式的主要区别

1. 原则上的区别，代理为了控制对某个函数前后的操作，而装饰着模式是为了添加某一操作（其实目标没差太远）
2. 实现上的区别，代理模式的类一般和被代理类的操作一致，因此构造函数一般不传入类对象，使用时的不同如下：
Logger logger = new Proxy(); // 代理模式 （为了让Proxy的行为像Logger）
Logger logger = new DecorateLogger(new Logger()); // 装饰者模式，还可以有更多层


## 个人吐槽

很多博客里再提高一点深度的说法：静态代理在编译时已经确定代理的具体对象，装饰模式是在运行动态的构造。（听起来有道理，其实就是要不要在构造函数中传入对象的问题）

如果需要对一个类的众多派生类做代理，按照标准的说法岂不是对每一个派生类都需要写一个静态代理类？？ 感觉上如果不要求代理类和被代理类在构建对象时一致（或者也给被代理类一个构造函数传入），从构造函数传入被代理类能让代理类更加灵活的处理实现接口的各种类。因此，此处还是建议根据具体情况活用；当然，更建议直接用动态代理。





