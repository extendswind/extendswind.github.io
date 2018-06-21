---
title: "设计模式 之 工厂模式"
date: 2018-06-15T17:25:25+08:00

toc: true

categories:
- "programming"

tags:
- "design patterns"
---


# 几种工厂模式(Factory Pattern)简介

工厂模式主要分为： 

- 简单工厂模式（Simple Factory Pattern）
- 工厂方法模式（Factory Method Pattern 经常简称为工厂模式）
- 抽象工厂模式（Abstract Factory Pattern）

主要思想：将类的初始化过程转移到工厂类中，使用类的位置通过工厂类直接得到产品类，使产品类的初始化逻辑清晰，并容易添加新的产品。

# 需求示例

## 简单工厂模式 和 工厂方法模式

- 实现多个日志记录器logger(文件logger，数据库logger等)
- 通过配置文件确定使用的具体logger类
- 添加新的logger类不修改源码（添加新的java包并修改配置文件）

## 抽象工厂模式

抽象工厂模式应用场景略有不同。

存在多种不同的主题，每个主题都有不同的Button和Text的实现逻辑，因此每个主题都有Button和Text控件的派生类，导致类的初始化较多。

容易添加新的主题

# 不应用工厂模式的一般实现  （FactoryProblem.java）

- logger 基类实现通用的日志记录功能，子类实现各自的特有功能
- 使用时根据配置文件中的类型，new相应的子类

类的实现：

```java
abstract class Logger {
   public void writeLog(){
       System.out.println("writeLog by Logger");
   }
   // 可添加公共实现
}

class FileLogger extends Logger {
    @Override
    public void writeLog(){
        System.out.println("writeLog by the FileLogger");
    }
}

class DataBaseLogger extends Logger {
    @Override
    public void writeLog(){
        System.out.println("writeLog by the DataBaseLogger");
    }
}
```

使用时:

```java
if (loggerType.equals("database")){
    // 此处一般会添加相应的初始化
    logger = new FileLogger();
}
else if(loggerType.equals("file")){
    // 此处一般会添加相应的初始化
    logger = new DataBaseLogger();
}
else
    logger = null;
```


# 从一般实现到工厂方法模式

一般实现存在下面的两个问题。

## 问题一：根据字符串生成对象会产生大量的判断

简单工厂模式将对象的初始化放入工厂类中，以简化调用类的逻辑。（还可以使用后面的反射机制）

```java
// simple factoryPatten
class SimpleFact {
    public static Logger produceLogger(String loggerType){
        Logger logger;
        if (loggerType == "database"){
            // 此处一般会添加相应的初始化（连接数据库等）
            logger = new FileLogger();
        }
        else if(loggerType == "file"){
            // 此处一般会添加相应的初始化 （创建日志文件等）
            logger = new DataBaseLogger();
        }
        else
            logger = null;
        return logger;
    }
}
```

使用时直接通过工厂类得到对象

```java
Logger logger = SimpleFact.produceLogger("database");
```

实质上主要提高了代码的可读性，将logger的具体类型和初始化过程用单独的简单工厂类处理，主要为逻辑清晰上的优点。

添加新的对象需要修改简单工厂类。

## 问题二：添加新的对象需要修改源码的问题

利用java的反射机制，直接通过字符串直接创建对象（一般loggerName来自配置文件）

```java
// simple factoryPatten
class SimpleFact {
    public static Logger produceLogger2(String loggerName) {
         Logger logger = null;
         Class c = Class.forName(loggerName);
         logger = (Logger)c.newInstance();
         // 省略 try catch  ......
         return logger;
    }
}
```

添加新类时，直接添加新类的jar包，将类名添加到配置文件即可。

## 问题三：不同logger的初始化需要各自不同的设置

前面的反射使客户端无法对各个具体的logger派生类实现不同的初始化。**当初始化过程复杂时，放在另一个类（工厂类）中会让逻辑更为清晰。（工厂模式）** 

对每个logger构建一个工厂类，使用工厂类初始化logger后得到最后的对象。

```java
abstract class Logger {
   public void writeLog(){
       System.out.println("writeLog by Logger");
   }
   // 可添加公共实现
}
abstract class SuperFactory{
    public abstract Logger produceLogger();
}

class FileLogger extends Logger {
    @Override
    public void writeLog(){
        System.out.println("writeLog by the FileLogger");
    }
}
class FileLoggerFactory extends SuperFactory{
    @Override
    public Logger produceLogger(){
        // 初始化忽略
        return new FileLogger();
    }
}

class DataBaseLogger extends Logger {
    @Override
    public void writeLog(){
        System.out.println("writeLog by the DataBaseLogger");
    }
}
class DataBaseLoggerFactory extends SuperFactory{
    @Override
    public Logger produceLogger(){
        // 初始化忽略
        return new DataBaseLogger();
    }
}
```

添加新的产品时添加logger和对应的工厂类，然后通过配置文件创建对应的工厂即可。

ps: 感觉此处如果初始化较为简单，构建工厂类的行为有点多余。

# 再到抽象工厂模式

工厂方法模式的思想主要是每个产品类使用一个工厂类初始化。

类似提供多套主题的情况，每套主题有多个控件，此时可以使用一个工厂初始化同一主题下的多个产品对象。

```java
// ---- button
class ButtonUI{
    public void print() { System.out.println("ButtonUI");}
}
class ButtonUI_theme1 extends ButtonUI{
    @Override
    public void print() { System.out.println("ButtonUI_theme1");}
}
class ButtonUI_theme2 extends ButtonUI{
    @Override
    public void print() { System.out.println("ButtonUI_theme2");}
}

// ---- text
class TextUI{
    public void print() { System.out.println("TextUI");}
}
class TextUI_theme1 extends TextUI{
    @Override
    public void print() { System.out.println("TextUI_theme1");}
}
class TextUI_theme2 extends TextUI{
    @Override
    public void print() { System.out.println("TextUI_theme2");}
}

// ---- factory
abstract class AbstractThemeFactory{
    public void printCommon(){
        System.out.println("common factory method");
    }
    abstract public ButtonUI createButton();
    abstract public TextUI createText();
}
class Theme1Factory extends AbstractThemeFactory{
    @Override
    public ButtonUI createButton(){ return new ButtonUI_theme1(); }

    @Override
    public TextUI createText() {
        return new TextUI_theme1();
    }
}
class Theme2Factory extends AbstractThemeFactory{

    @Override
    public ButtonUI createButton() {
        return new ButtonUI_theme2();
    }
    @Override
    public TextUI createText() {
        return new TextUI_theme2();
    }
}

// ------------ Test
public class AbstractFactory {

    public static void main(String args[]){
        AbstractThemeFactory factory = new Theme1Factory();
        ButtonUI buttonUI = factory.createButton();
        TextUI textUI = factory.createText();
    }
}
```

# 个人看法

new具体对象的主要问题不只是使用不同的类，而是不同类有不同的初始化流程需要处理。

个人认为工厂模式的主要作用为：

- 处理多个产品的选择逻辑（通过if或者反射机制）
- 处理产品的初始化逻辑
- 对产品分类创建（抽象工厂）

工厂模式不应该被过分整体套用，而应对于具体解决的问题选择其中的处理方式。如对于随便几个参数就能初始化的情况，工厂类起到的作用并不大。

主要的启示：

- 在有多个产品或以后可能有多个产品扩展的情况下（而且数量不会过多、初始化逻辑不复杂），使用简单工厂模式将产品的选择逻辑放在工厂类以简化使用代码。
- 在产品类有较为复杂的初始化和其他逻辑时，使用工厂方法模式构建工厂类包装简化使用。
- 在产品类较多且有明显的分类时，使用抽象工厂模式对每个分类的产品构建一个工厂类。

## 吐槽

某些书上讲的各种问题感觉就是根据已有的模式写法强套的问题，如很多提到简单工厂模式的缺点在于不适合管理多个产品，添加新产品需要修改源码。前者只在于产品类需要复杂的初始化逻辑，后者和工厂方法模式一样使用反射就能解决了。

## 网上其他的看法

使用new对类实例化可能破坏类的可扩展性，由于new跟随的是具体的对象，很可能会被修改，因此给其他人使用的类要尽可能少用new。感觉工厂方法模式虽然对加入新的产品能够降低修改，但反射同样可以解决此问题。

