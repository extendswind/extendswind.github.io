---
title: "设计模式 之 原型模式"
date: 2018-07-03T21:25:25+08:00

toc: true

categories:
- "programming"

tags:
- "design patterns"
---

# 吐槽

感觉这是至今最值得吐槽的设计模式之一，由于原型模式在本质上与工厂模式极为类似，并且简单，但相关的书和博客很少提到要点。某些书上和博客还直接在类里加个clone方法就告诉我这是原型模式，**不说清楚为什么要划分原型类和具体类**....

还有某些书上把原型模式划分为通用实现和java、c#一类的特定语言实现，不就是稍微改改clone函数的具体实现么，一点简单的语法而已....

有些地方提到原型模式与工厂模式类似，而极少有位置提到后面的客户端的实现问题....

感觉原型模式没什么意思，实质上就是把工厂模式中new的过程改为clone，具体的类对应于完成初始化的多个对象。


# 原型模式（Prototype Pattern）

首先画重点，原型模式是一种 **创建对象** 的模式。通过复制已经初始化好的对象以避免对对象进行某些复杂和耗时的初始化过程。可能存在多个被复制的对象，创建自不同的类或同一个类的不同初始化过程，用户需要动态决定复制哪一个对象。

主要实现思想：

- 对象的复制只需要在每个类中实现一个clone函数即可
- 使用工厂模式相关思想获取具体的clone对象


# java实现的clone操作

下面的实现基于java，如c++一类的语言对于每个对象的复制需要自行处理。

java的所有类都继承于Object，Object类中定义了native实现的clone函数，但需要实现Cloneable接口才能调用。通过clone函数能够直接复制内存中的对象而不用调用构造函数。

注意，java Object的clone函数为 **浅拷贝**，只会复制对象地址而不创建新的对象。需要根据实际情况判读是否做相应的深拷贝修改。

吐槽：很多博客和书上的示例实质上就下面这一段，然后加个实例里n个成员变量和函数凑出十几到几十行，实现个Cloneable接口加个clone函数就算完了....

```java
class Prototype implements Cloneable{
    int attr;
    public Prototype clone(){
        Prototype prototype = null;
        try {
            prototype = (Prototype)super.clone();
        } catch (CloneNotSupportedException e) {
            e.printStackTrace();
        }
        return prototype;
    }
}
```

## 一个不使用java特性的简单实现

```java
class Prototype{
    int attr;
    public Prototype clone(){
        Prototype clone = new Prototype();
        clone.attr = this.attr;
        return clone;
    }
}
```
同上，注意深拷贝和浅拷贝问题。


# 原型模式具体实现

一般都会提到，原型模式有原型类（Prototype，一般为抽象类或者实际类），具体原型类（Concrete Prototype）以及调用客户端（client）。

其中具体原型类继承原型类，客户端通过具体原型的clone函数实现对象复制。

## 具体原型类定义

```java
class ConcretePrototype1 extends Prototype {
    int attr;
    public Prototype clone(){
        Prototype prototype = (ConcretePrototype1)super.clone();
        return prototype;
    }
}
class ConcretePrototype2 extends Prototype {
    int attr;
    public Prototype clone(){
        Prototype prototype = (ConcretePrototype2)super.clone();
        return prototype;
    }
}
```

有的书上提到原型类还能使用只包含clone函数的接口，这样在客户端段调用时还要根据具体类做类型转换，还是不建议折腾了。

## 客户端实现

客户端需要初始化具体的类对象，并根据参数决定具体克隆的对象，一般考虑几个工厂模式的思想。

简单工厂模式实现：

```java
class PrototypeFactory{
    public static Prototype[]prototypes;
    public PrototypeFactory(){
        prototypes = new Prototype[3];
        prototypes[0] = new ConcretePrototype1();
        prototypes[1] = new ConcretePrototype2();
        prototypes[1] = new ConcretePrototype2();// 可以对同一个类进行两种不同的初始化
        // 此处省略初始化操作....
    }
    public static Prototype getProduct(int id){
        return prototypes[id].clone();
    }
}

public class PrototypePattern {
    public static void main(String []argvs){
        Prototype prototype1 = PrototypeFactory.getProduct(0);
        Prototype prototype2 = PrototypeFactory.getProduct(2);
    }
}
```

当每个具体类需要多套初始化参数，或者具体类数量较多时，还可以参考抽象工厂模式类似的实现。


# 总结

通过克隆已经初始化对象的方式创建新的对象是一种比较好的思想。在掌握几种工厂模式的基础上，其实实现没什么难度，不用在意各种书和博客上的细节。

原型模式的典型缺点：当类成员较为复杂时，clone函数中的复制会较为复杂。（如有一堆同样需要clone的对象作为成员）



