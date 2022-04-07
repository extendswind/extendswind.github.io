---
title: "设计模式 之 单例模式"
date: 2018-07-02T11:25:25+08:00
toc: true

categories:
- "programming"

tags:
- "design patterns"
---


singleton pattern

主要目标：对象只创建一次，每次都获得先前第一次创建的对象而不创建新的对象。（最好在使用时创建对象）

实现思想：使用静态方法getInstance得到对象，为了保证对象只能通过getInstance创建，使构造函数私有。

主要麻烦在于：

- 多线程环境下getInstance方法的调用可能产生多个对象
- 使用synchronized关键字可能降低高并发效率

单例模式有很多种，大多用于解决多线程环境下的效率问题，高并发场景通常使用某些固定方案（java常用内部类机制），一般情况下思想比较简单，从应用的角度感觉不必深究。

（后面懒得用实际例子命名了，Log4j中获取的logger对象就使用了单例模式）



```java

/**
 * 简单实现
 *
 * 存在的问题：
 *
 * 当创建过程需要时间时，连续调用getInstance方法会导致创建多个对象，特别是涉及多线程时容易出问题。
*/
class Singleton_problem {
    private static Singleton_problem m_singletonProblem = null;
    private Singleton_problem(){
        // ...
    }
    public static Singleton_problem getInstance(){
        if (m_singletonProblem == null)
            m_singletonProblem = new Singleton_problem();
        return m_singletonProblem;
    }
}


/**
 * 解决方案一： eager initialization
 *
 * 缺点在于没有lazy loading机制
 */
class Singleton_eager{
    private static final Singleton_eager m_singleton = new Singleton_eager();
    private Singleton_eager(){
        // ...
    }
    public static Singleton_eager getInstance(){
        return m_singleton;
    }
}


/**
 * 解决方案二： lazy initialization
 *
 * 在进行高并发操作时可能造成系统性能降低，由于调用getInstance函数每次只能一个线程使用
 * 在后面的测试代码里时间不明显，通过线程池等方式可能会不一样
 */
class Singleton_lazy{
    private static Singleton_lazy m_singleton = null;
    // 线程锁，加锁的位置每次只能运行一个线程
    public static synchronized Singleton_lazy getInstance(){
        if (m_singleton == null)
            m_singleton = new Singleton_lazy();
        return m_singleton;
    }
}


/**
 * 解决方案三： lazy initialization + 双重加锁
 *
 * 降低方案二中的等待用时，当对象创建后就不用通过锁判断，创建后没有效率问题。
 */
class Singleton_lazy_double_lock{
    private static volatile Singleton_lazy_double_lock m_singleton = null;
    // 线程锁，加锁的位置每次只能运行一个线程
    public static Singleton_lazy_double_lock getInstance(){
        //第一重判断
        if (m_singleton == null) { //锁定代码块
            synchronized (Singleton_lazy_double_lock.class) { //第二重判断
                if (m_singleton == null) {
                    m_singleton = new Singleton_lazy_double_lock(); //创建单例实例
                }
            }
        }
        return m_singleton;
    }
}

/** Initialization on Demand Holder，通过java内部类机制
 * 貌似是java的最优实现方式，依赖具体语言
 * 由于内部类对象依赖外部类对象，因此内部类中的静态成员会在外部类对象创建后得到，
 * 此时相当于在使用时才进行初始化。
 */
class Singleton_holder{
    private Singleton_holder() {
    }
    private static class HolderClass {
        private final static Singleton_holder instance = new Singleton_holder();
    }
    public static Singleton_holder getInstance() {
        return HolderClass.instance;
    }
    public static void main(String args[]) {
        Singleton_holder s1, s2;
        s1 = Singleton_holder.getInstance();
        s2 = Singleton_holder.getInstance();
        System.out.println(s1==s2);
    }
}


/**
 * 对上面的测试
 */
public class Singleton{

    // 下面两个函数测试的结果使用两种方式的速度基本一致？？？？
    // 线程创建和启动的时间过长，基本忽略了线程锁带来的时间差

    public static void time4singleton_lazy(){
        System.out.println("start");
        for(int i=0; i<10000; i++){
            Thread thread = new Thread() {
                @Override
                public void run() {
                    Singleton_lazy.getInstance();
                }
            };
            thread.start();
        }
        System.out.println("end");
    }

    public static void time4singleton_eager(){
        int threadNum = 10000;
        Thread []threads = new Thread[threadNum];
        for(int i=0; i<threadNum; i++){
            threads[i] = new Thread() {
                @Override
                public void run() {
                    Singleton_eager.getInstance();
                }
            };
        }
        System.out.println("start");
        for(int i=0; i<threadNum; i++)
            threads[i].start();
        System.out.println("end");
    }

    public static void main(String []argvs){
        //time4singleton_lazy();
        time4singleton_eager();

    }

}
```
