---
title: "java从toArray返回Object[]到泛型的类型擦除"
date: 2020-05-19T11:30:00+08:00
toc: true

categories:
- "programming basic"

tags:
- "java"

---


在将ArrayList等Collection转为数组时，函数的返回值并不是泛型类型的数组，而是Object[]。刚好最近翻了一遍《java核心技术》，以及参考《Think in Java》，写写为什么没有直接返回对应类型的数组，以及Java泛型中类型擦除的处理方式。

主要涉及：

1. ArrayList的toArray函数使用
2. 为什么不直接定义函数 T[] toArray() 
3. 泛型数组的创建的两种常用方法
4. 在泛型中创建具体的类实例

(部分代码没有运行过）

# ArrayList的toArray函数使用

将ArrayList转为数组，提供了两个函数

```java
Object[] toArray();
<T> T[] toArray(T[] a);

// 后面考虑一个Integer类型的ArrayList
ArrayList<Integer> aa = new ArrayList<>();
aa.add(1);
aa.add(3);
```

## Object[] toArray();

第一个函数是直接将ArrayList转换成Object的数组，可以用`Object[] bb = aa.toArray()`，在具体使用时对每个对象进行强制类型转换，如`System.out.println((Integer)bb[1])`。（java不支持数组之间的强制类型转换）

## <T> T[] toArray(T[] a);

第二个函数能够直接得到T类型的数组，当传入的`T[] a`能放下ArrayList时，会将ArrayList中的内容复制到a中（a的size较大时会a[size]=null）。否则，将构建一个新的数组并返回。具体实现如下:

```java
public <T> T[] toArray(T[] a) {
    if (a.length < size)
        // Make a new array of a's runtime type, but my contents:
        return (T[]) Arrays.copyOf(elementData, size, a.getClass());
    System.arraycopy(elementData, 0, a, 0, size);
    if (a.length > size)
        a[size] = null;
    return a;
}
```

对于第二个函数，可以考虑将一个大小一致的T[]数组传入toArray()函数（为了数组复用），或者直接`Integer[] ArrayAA = aa.toArray(new Integer[0]);`。


# 为什么不直接定义函数 T[] toArray();

通常，直观上更直接的返回数组的方式应该是`T[] toArray()`，为什么JDK定义了一个不怎么好用的返回Object数组的函数。

数组之间虽然占用空间大小相同，但是不能强制改变类型（由于数组也是类，而数组类之间没有继承关系）。以`object[] a; ...; (Integer[])a`强制转换一个数组类型时，会在编译器产生警告，运行时抛出异常。因此对于泛型数组，无法以`(T[]) array`的形式，将擦除Object类型的数组强转为T[]类型。

主要和jdk向前兼容以及泛型的类型擦除有关，个人认为主要应该还是由于类型擦除机制导致了返回T[] toArray()的实现困难。


## 泛型的类型擦除

泛型是从SE 5才开始引入，为了不破坏现有的类型机制，用了一种类型擦除的机制，相比C++使类型擦除时的考虑更为复杂。

虚拟机并不支持泛型，而是将泛型类编译成了一个类型擦除（erased）的类，将类型变量转换成一个原始类型（raw type）。原始类型在默认类型变量时会被转换成Object，在类型变量有限定时（如 <T extends Comparable>）会被转换成限定的类。在运行时获取到的T类型都是擦除后的类型。

```java
public class Pair<T> {
  private T first;
  private T second;
  public Pair(T first, T second){ this.first = first; this.second = second; }
}

// 会被替换成
public class Pair {
  private Object first;
  private Object second;
  public Pair(Object first, Object second){ 
    this.first = first;
	this.second = second; 
	System.out.println(this.first.getClass()); // 不管T类型如何，得到的都是Object
  }
}

//当类型为Pair<T extends Comparable>时，T会被替换为Comparable
```

这和C++的处理方式很不一样，C++中每个模板的实例化都会产生不同的具体类型，相当于对与每一种类型都会编译出一套独立的代码，会有“模板代码膨胀”。而在java中，使用了模板的类作为一个通用类进行了编译，传入不同的泛型参数也只会运行在同一个类上，模板的类型使用擦除后的类型进行编译。

在使用到具体的对象时，编译器会添加一个强制类型的转换指定，将Object或限定的类型强转为具体的类型。如对于类成员函数 `public T getFirst()`，由于类型擦除后函数会变为`public Object getFirst()`，当泛型T为整型时，编译器调用 `Int a = pair1.getFirst()`会添加一个强制类型转换指令给虚拟机。而在没有具体类型时，一直使用擦除后的类型进行处理。

## 泛型方法不涉及类型擦除

```java
public <T> void f(T x){
  System.out.println(x.getClass().getName());
}

f.(""); // java.lang.String
f.(1);  // java.lang.Integer
```

对于泛型方法，使用的是类型推断机制，当调用方法时，通过参数判断T的类型，而非擦除为Object。

`<T> T[] toArray(T[] a);` 函数就是通过这一方式，在调用toArray函数时通过参数类型得到泛型的类型，然后通过反射创建数组。

## 类型擦除导致的结果

**由于类型的擦除，在使用时需要一直注意类型变量的类型并非T，编译期无法得到关于T类型的具体信息，在运行时的类型并不会替换为具体的类型，而是在需要的地方执行强制类型转换。** 在运行时会出现下面的情况：

- 类型List<String>和List<Integer>的类型在擦除后相同。
- 同上 instanceOf 也无法使用。
- `T a = new T(); `编译器会报错，因为类型在编译期不存在，而且编译阶段无法确定在T中是否存在默认的无参构造函数。
- 同上，无法使用 `T[] a = new T[10]`。 

外加数组类之间无继承关系导致无法将Object[]的数组强转为T[]。

因此，java中直接设计`T[] toArray()`类型的函数需要额外的传入类型。


# 泛型数组的创建的两种常用方法

虽然无法直接创建T类型的对象，但可以利用反射机制间接的创建T类型的对象。对于创建泛型数组，一般的方案是使用ArrayList。如果某些情况下需要自己实现，可以使用和ArrayList类似的方式。

1、JDK通过创建Object[]的数组放对象，在取对象时进行类型转换，此时toArray函数通过泛型函数的参数获取类型。

```java
// 数组仍使用Object类型
private Object[] array = new Object[size];

// 在get函数中强制类型转换
public T get(int index){
  return (T)array[index];
}

// 转换成数组
public T[] toArray(T[] a){
  // 此处a只用于获取类型
  // 更严谨的实现参考上面的JDK代码
  return (T[]) Arrays.copyOf(elementData, size, a.getClass());
}
```

2、或者传入具体的类型，由于传入的具体类型可以创建具体类型数组，因此可以直接实现`T[] toArray()`。可能是传入类型的方式不太优雅，JDK并没有使用这种形式。

```java
class GenericArray{
  private T[] array;

  // 构造函数直接传入类型，数组的强制类型转换会产生编译警告，此处直接用标签忽略 
  @SuppressWarnings("unchecked")
  public GenericArray(Class<T> type, int size){
    array = (T[]) Array.newInstance(type, size);
  }
  
  public T[] toArray(){
    return array;
  }
}
```

# 在泛型中创建具体的类实例

和上面的情况类似，要想在泛型类中创建具体的类型，也就是需要在类中能够得到`T.class`，通常需要使用两种方式：

1. 将`T.class`通过函数或其它方式传入类中，通过反射机制创建。
2. 泛型函数能够从参数的类型中获取`T.class`。

后面简单介绍构造函数包装后传入的方式。

## 通过构造函数传入类型后创建类实例

对于`T a = new T();`，由于类型擦除无法创建，但可以通过在运行时传入类变量来实现创建，将类型通过构造函数传入。在有类型后，通过反射机制（newInstance）构建新的类。

```java
public class ClassAsFactory<T>{
  Class<T> kind;
  public ClassAsFactory(Class<T> kind){ this.kind = kind; }
  
  // 构建时传入 String.class
  public static void main(String[] argvs){
    ClassAsFactory<String> gClass = new ClassAsFactory<String>(String.class);
  }
}
```

但是对于这段代码，编译器无法检查构造函数是否存在等问题，一般更建议使用显示类型工厂，在构造函数中传入new过具体类型的工厂类：

```java
Interface FactoryI<T>{
  T create();
}

// 在工厂类中传入具体的对象
Class IntegerFactory implements FactoryI<Integer>{
  public Integer Create() { return new Interger(0);}
}

Class Foo2<T> {
  private T x;
  // 类型F用来限制参数为工厂类
  public <F extends FactoryI<T>> Foo2(F factory){ 
    x = factory.create();
  }
  
  public static void main(String[] argvs){
    new Foo2<Integer>(new IntegerFactory());
}
```

此时，具体工厂类由于针对具体的类型，编译期间可以对创建过程进行检查。

《Think in Java》里还提到一种模板方法设计模式，没有太大的本质上的区别。

