
---
title: "Java数据结构笔记"
date: 2020-07-25T10:30:00+08:00
toc: true
 
categories:
- "programming basic"
  
tags:
- "java"
---
   


系统的看一下Java支持的数据结构，记一下从数据结构到java实现的一些基础笔记。以下内容主要参考《java核心技术》与jdk11源码。

用于保存对象的数据结构一般称作容器类，也称作泛型集合（generic collection，由于容易和Collection接口混淆，因此有些书直接叫做容器类container library）。主要分为Collection和Map两种，Collection用于存储独立的元素，而Map用于存储“键值对”对象。

# 一些细节

在查找元素、查找位置、移除等操作中，判断对象是否相同的方式是调用equal函数。

retainAll(Collection<?> c)求两个集合的交集。

实现时接口与实现分离。使用时用满足需要的接口（如队列使用Queue），针对具体的场景new合适的实现。当需要自行实现对应的功能，为了降低实现接口中过多函数的复杂程度，可以直接扩展对应的Abastract类（如AbstractQueue），这种抽象接口加抽象类的方式在集合设计中经常遇到。

集合类只能容纳对象句柄。集合在存储基本类型时，会通过封装器（Integer等）将基本类型转换成普通类，因此在处理效率上不如数组（直接存储基本类型）。

# 迭代器 Iterator

```java
public interface Iterator<E>{
  E next();
  boolean hasNext();
  void remove();
}
// 并没有一个函数直接返回迭代器指向位置的值

public interface Iterable<E>{
  Iterator<E> iterator();
}
```

for each循环可以针对任何实现了Iterable的对象（由编译器直接翻译成Iterator对应的代码）。for (String e: c){...}

Collection接口实现了Iterable接口，可以返回遍历元素的迭代器。

通过迭代器，能够用一套代码访问不同的容器类。

和C++的迭代器指向具体位置的设计不同，java的迭代器指向的位置可以看作是两个元素的中间。当调用next时，迭代器会跳过下一个元素，并返回被跳过元素的引用。不能像C++那样直接取当前位置的元素。对于remove函数，删除的是上一次next函数返回的位置（由于经常需要通过此位置的值判断是否删除）。也因此，每次调用remove函数前必须调用一次next方法，因此连续调用两次remove会出错。

## List

ArrayList相当于dynamic array，随机访问快，随机插入慢。类似的实现还有Vector，相当于一个线程安全的ArrayList。

LinkedList，双向链表，随机访问慢，随机插入快。LinkedList比较特殊，除了List接口还是了双端队列的Deque接口。

LinkedList无法获取到node的指针，但可以通过获取ListIterator控制前后的位置（相对于Iterator，添加了previous等向前访问的函数）。

LikedList并没有缓存指针的位置，因此get(n)等随机访问和修改的操作效率不高。

```java
public class LinkedList<E>
    extends AbstractSequentialList<E>
    implements List<E>, Deque<E>, Cloneable, java.io.Serializable
```

## Map

《java核心技术》中将Map的介绍放在了Set之后，但是Hashset的实现直接使用了HashMap，此处先写写Map的实现。

### HashMap

（下面的默认参数取自openjdk11源码）

实现常量时间的数据get和put。

HashMap用hashcode结合链表的实现。使用了桶（bucket）机制，将hashcode取余后放入一个链表，当一个桶中的数据达到8个时，会通过treeifyBin函数将链表的形式转成红黑树存储以加快检索效率。

在构造函数中设置了两个参数。threshold（默认为16）和loadFactor（默认为0.75），初始化时桶的数量会用threshold，往后threshold会等于 `桶的数量×loadFactor`。添加元素时，HashMap中的元素个数达到threshold时会调用resize让桶的数量翻倍，此时会遍历先前的所有元素添加到扩容之后的数组中（rehash过程）。

通过一个名为table的数组存储桶的节点，默认情况下的初始化桶的个数为16，每次会增加为之前的2倍，最大为Int型的最大值。

```java
transient Node<K,V>[] table;

static class Node<K,V> implements Entry<K,V> {
 final int hash;
 final K key;
 V value;
 Node<K,V> next;
 // ...
}
```

resize过程使用的头插入（新的table数组中插入的元素插入到链表头部，避免遍历到尾部的开销）。

当一个桶中的数据达到TREEIFY_THRESHOLD（8）个，并且桶的数量超过MIN_TREEIFY_CAPACITY（64）时，会在treeifyBin函数中将每个桶中的数据从链表转换成红黑树。

通过hashCode()函数得到hash值，通过equal()函数判断对象是否相等。

并发访问中，HashMap的实现中并没有考虑多线程的问题，在多线程结构化（structurally）修改HashMap时可能会出问题（结构化主要指添加和删除，修改某个key对应的值不算结构化修改）。


### TreeMap

基于红黑树实现的Map，对于获取键值、插入、删除的操作时间复杂度为log(n)。put时将数据插入红黑树，get时从树中取数据。

由于数据存储在红黑树有序排列，获得排序后的数据较快。

将key-value键值对做为节点插入到红黑树中，由于需要排序，通过Comparator<? super K>接口让插入的键值可比较。

```java
static final class Entry<K,V> implements Map.Entry<K,V> {
    K key;
    V value;
    Entry<K,V> left;
    Entry<K,V> right;
    Entry<K,V> parent;
    boolean color = BLACK;
	// ...
}
```

当类默认的比较函数不能满足需要时，可以另外定义新的comparator传入TreeMap。

```java
public TreeMap(Comparator<? super K> comparator) {
    this.comparator = comparator;
}
```

### EnumMap 用于枚举类型

所有的key必须是同一个enum类型中。内部通过数组的方式表达。每个类型对应数组中的一个元素。

put时直接获取key对应的enum位置，直接对数组中的此位置赋值。

```java
private transient K[] keyUniverse;
private transient Object[] vals;

public V put(K key, V value) {
    typeCheck(key);
    int index = key.ordinal();
    Object oldValue = vals[index];
    vals[index] = maskNull(value);
    if (oldValue == null)
        size++;
    return unmaskNull(oldValue);
}
```

在put函数中，直接获取key对应的enum索引位置

### LinkedHashMap实现原理

LinkedHashMap通过一个额外的双向链表链接所有的元素，通过构造函数中的参数accessOrder决定记录元素添加顺序还是元素访问顺序。

可以用来copy一个map，使新的map中的元素顺序与被赋值的map顺序相同（如下）。也适用于LRU cache类似的场景。

```java
void foo(Map m) {
  Map copy = new LinkedHashMap(m);
  // ...
}
```

#### 源码实现

总体逻辑为，每次添加新的元素，都回加入到链表的尾部。每次访问节点时，如果accessOrder为true（链表按照访问顺序），则将当前访问的节点放到链表尾部；当accessOrder为false（链表按照插入顺序），则不对链表操作。

通过两个指针可以获得所有元素的链表。

```java
// The head (eldest) of the doubly linked list.
transient LinkedHashMap.Entry<K,V> head;

// The tail (youngest) of the doubly linked list.
transient LinkedHashMap.Entry<K,V> tail;
```

jdk11的实现上略微有点跳，不同于jdk8直接重写了关键函数，jdk11通过多态的形式插入了一些和HashMap不同的操作。

想象中的让链表记录元素插入顺序的方式，直接在put新的元素后，直接将新的元素加入到链表（记录元素访问顺序在get函数中类似）。jdk11在实现时，在HashMap类中定义了三个空函数用于在LinkedHashMap中实现：

```java
// Callbacks to allow LinkedHashMap post-actions
void afterNodeAccess(Node<K,V> p) { }
void afterNodeInsertion(boolean evict) { }
void afterNodeRemoval(Node<K,V> p) { }
```

三个函数分别在Node的访问、插入、删除三种情况后被调用，在HashMap中为空函数，LinkedHashMap中具体实现。 但是，链表的插入顺序并没有直接放在afterNodeInsertion函数中，而是重写了创建新节点的newNode函数：

```java
Node<K,V> newNode(int hash, K key, V value, Node<K,V> e) {
     Entry<K,V> p =
         new Entry<>(hash, key, value, e);
     linkNodeLast(p); // 将p节点通过tail指针添加到链表尾部
     return p;
}
```

### 其它Map

WeakHashMap  值不用后会被回收，利用了GC机制中的标记。

IdentityHashMap  用==而非equals比较键值。

## Set

接口和Colection基本相同，除了java9加了几个针对不可变集合的函数。

```java
public interface Set<E> extends Collection<E> {...}
```

Set的内部很多都直接使用上面的Map实现，如HashSet内部直接使用了HashMap做为存储，在添加元素时，将加入的元素作为key，用一个常量作为value。

```java
private transient HashMap<E,Object> map; 
private static final Object PRESENT = new Object();

public boolean add(E e) {
    return map.put(e, PRESENT)==null;
}
```

LinkedHashSet 记录了插入的顺序。

TreeSet使用了TreeMap，通过红黑树适用于需要排序的数据。

EnumSet包含枚举类型

## Queue

### ArrayDeque and LinkedList

Deque(double-ended queue）双端队列，发音为|deck|。

常见的队列主要有ArrayDeque（数组实现的双端循环队列）和 LinkedList（链表实现的双端队列），其中LinkedList虽然名字是List，但实现了Queue的函数，定义如下）。

通常情况下ArrayDeque的数组型实现效率会高于LinkedList的指针型实现。

```java
public class LinkedList<E>
    extends AbstractSequentialList<E>
    implements List<E>, Deque<E>, Cloneable, java.io.Serializable{
	//...
}
```

双端循环队列的addFirst函数实现如下

```java
// 其中Deque表示“double end queue”，发音为deck
public interface Deque<E> extends Queue<E> {...}

// ArrayDeque使用的是循环队列
// addFirst函数会向队列头部加入一个新的元素
// 当头部为0时，会通过dec函数将head指针移到数组尾部对应的位置
public void addFirst(E e) {
    if (e == null)
        throw new NullPointerException();
    final Object[] es = elements;
    es[head = dec(head, es.length)] = e;
    if (head == tail)
        grow(1);
}

static final int dec(int i, int modulus) {
    if (--i < 0) i = modulus - 1;
    return i;
}
```

### PriorityQueue

通过一个数组形式的堆实现最小优先队列，`transient Object[] queue;`，默认将最小值放在堆顶，peek()函数返回堆中最小值。没有直接的更改顺序的方式，如果需要将最大值放在堆顶需要传入Comparator接口的实现。

满足堆的性质，poll()函数返回队列中的最小值或者最大值O(log(n))。

## Stack

```java
public class Stack<E> extends Vector<E> {...}

public class Vector<E> extends AbstractList<E>
    implements List<E>, RandomAccess, Cloneable, java.io.Serializable {}
 ```

LIFO (后进先出）

# 源码中的一些操作

## 位操作

### 用按位与操作提高取余效率

仅针对取余数为2^n次方的数。

对2取余实质上就是取2进制的最后一位，对4取余实质上是取2进制数的最后两位。

如 5 % 2 = （2进制）101 & 001。 

2^n - 1 = （2进制的n个1）11....1

hash % n 等于 (n - 1) & hash

### 移位表示2^n

1 << 4 // 相当于2^4

当数组为2的倍数时，向左移m位相当于乘2的m次方

4 << m // 相当于 4*(2^m)

### 移位表示乘2和除2

22 >> 1 // 除以二
22 << 1 // 乘2
22 >>> 1 // 忽略符号位除以2

### 通过-1向右移位>>>

对于8位的byte，-1 的源码为 10000001，因此可以通过>>>得到一个00010000的2^n的数。

在HashMap中，hash桶的数量只能为2^n。下面的函数能够获取最小的n使2^n > cap。

```java
/**
 * Returns a power of two size for the given target capacity.
 */
static final int tableSizeFor(int cap) {
    int n = -1 >>> Integer.numberOfLeadingZeros(cap - 1);
    return (n < 0) ? 1 : (n >= MAXIMUM_CAPACITY) ? MAXIMUM_CAPACITY : n + 1;
}
```
