---
title: "Geotools的点类型简单要素创建以及大数据量下的效率问题"
date: 2022-09-28T17:30:00+08:00
toc: true

# mathjax: true

categories:
- "GIS"

tags:
- "GIS"
- "QGIS"

---

GeoTools使用JTS处理空间索引、查询、几何分析等操作，在此基础上增加了空间对象属性相关的处理。通过SimpleFeatureImpl类包装处理，由于每个空间要素实体对象中增加了很多其它的对象，外加java类包装的额外开销，以至于原本的空间数据在内存中的存储空间增加了很多倍，当属性字段较少时，甚至可以多出一个量级。

# 创建简单要素

```java
// -- 首先创建SimpleFeatureType  一个点和一个类型为Integer的number字段
SimpleFeatureTypeBuilder b = new SimpleFeatureTypeBuilder();
b.setName( "TestFields" );  // type name
b.add( "location", Point.class ); // 增加一个点字段
b.add( "number", Integer.class);  // 增加一个属性字段 
b.setCRS( DefaultGeographicCRS.WGS84);
SimpleFeatureType type = b.buildFeatureType();

// -- 使用SimpleFeatureBuilder创建SimpleFeature
SimpleFeatureBuilder builder = new SimpleFeatureBuilder(type);
// 用于创建JTS Point的工厂类
GeometryFactory geometryFactory = JTSFactoryFinder.getGeometryFactory();
Point point = geometryFactory.createPoint(new Coordinate(longitude, latitude));
builder.add(point);
builder.add(i);
SimpleFeature feature = builder.buildFeature(null);  // 参数为Feature id，为null时会赋默认值
```

# SimpleFeatureImpl实现

GeoTools的SimpleFeature是一个Java接口，没有直接使用基类具体实现，定义了对简单要素的函数操作，主要包括获取ID、Type、FeatureType，以及获取和设置Attribute、DefaultGeometry等。

SimpleFeatureImpl实现了SimpleFeature接口，主要包括以下数据：

```java
public class SimpleFeatureImpl implements SimpleFeature {

    protected FeatureId id;
    protected SimpleFeatureType featureType;
    /** The actual values held by this feature */
    protected Object[] values;
    /** The attribute name -> position index */
    protected Map<String, Integer> index;
    /** The set of user data attached to the feature (lazily created) */
    protected Map<Object, Object> userData;
    /** The set of user data attached to each attribute (lazily created) */
    protected Map<Object, Object>[] attributeUserData;
    /** Whether this feature is self validating or not */
    protected boolean validating;
	
	// ....
}
```

基于上一节的代码创建后，userData、attributeUserData都为null，validating为false，Point对象和number属性字段都被存储在values中，存储的索引号通过index标记（key为字段名，value为索引号）。除了上面Point类型的location字段和Integer类型的number字段，values中还存储了一个null的key，value为空间属性所在的索引号，getDefaultGeometry()函数会通过这一索引号获取空间属性对应的对象。

SimpleFeatureImpl的空间操作如getBounds()，需要遍历values中的所有对象，考虑其中所有类型为JTS Geometry的对象范围，得到Feature的结果。

# 大数据量下的存储效率问题

GeoTools基于OGC的Simple Feature实现标准，在小数据量下各种操作比较完备，但大数据量下以Feature为单位的数据组织形式浪费了大量的操作空间。

以大规模的点数据文件为例，在理想的存储方式下，每个点只需要存储坐标以及相应的属性字段的值，由于点集中的属性字段名称相同，只需要存储一次即可。而在GeoTools的SimpleFeatureImpl中，id和values是必需存储的选项，其它的成员变量都可以通过其它的方式避免内存消耗。userData和attributeUserData虽然使用了lazily created的形式降低了内存开销，null指针仍占用了8字节的空间。

除了分析过程中不一定使用的成员变量，Java类对象本身的开销也不可以忽略。每个Java对象都存在16字节（不同JVM实现可能不同，但不可忽略）的对象头存储开销，基本数据类型（如int）通过对应的类（如Integer）包装存储时，占用的内存都会提高几倍。

# 内存使用测试

存储对象为10000000 (10^6) 个点，每个点通过两个double类型的（x，y）存储，然后包含一个int类型的number属性。理想情况下所有点的属性字段、坐标系等元数据只存储一次，每个点存储2个double（8字节）和1个int（4字节），共20字节，总的内存开销低于20M（20 * 10^6 / 2^100）。

针对GeoTools Feature、JTS Point、ArrayList、使用Java类包装类型的数据组、基本类型的数组以及没有数据的JVM虚拟机开销，获取JVM的内存开销和创建过程中的运行时间（代码附在最后），运行结果如下：

|                 | GeoTools | JTS   | ArrayList | Java类 数组 | 数组  | JVM不存储数据 |
|:---------------:|:--------:|:-----:|:---------:|:-----------:|:-----:|:-------------:|
| 使用内存(GC后） | 319      | 140   | 82        | 82          | 24    | 4             |
| 总内存          | 971      | 303   | 303       | 303         | 240   | 240           |
| 创建过程时间    | 1.7      | 0.348 | 0.092     | 0.095       | 0.024 | \             |

其中GeoTools代码运行有未知的随机性，每次运行时间从1.5至1.9s之间，占用的内存也有细微的变化，可能和JVM的GC过程有关。

在Point属性中加入一个String类型的字段后（具体为"remark"+id），GeoTools的内存占用为388（GC前451），数组存储的内存占用为94M。当每个Point的属性字段占用空间较大时，使用GeoTools的差距会缩小，但额外的290M左右的存储开销不可忽略。

10000000 (10^7) 个点的情况，GeoTools在4G的最大堆空间情况下长时间没出结果，ArrayList的存储占用了726M内存，数组形式只占用了197M内存。

# 总结

GeoTools使用了OGC的Simple Feature标准要求的数据组织和操作形式，但使用SimpleFeatureImpl类封装时加入了很多额外的存储指针，导致大量数据存储的过程中额外指针占用的数据量较大。

如点数据的存储，每个点占用的额外存储空间约为近290字节，而每个点的实际存储只有20字节左右，当属性字段占用的存储空间较小时，额外的存储消耗相对可以高出一个量级。因此，大数据量下尤其是Feature数量较多时，需要注意GeoTools的额外内存开销。属性字段占用的内存开销较大时，额外存储开销的占比会略小，使用内存开销方便使用才更有价值。

在大数据场景下，使用GeoTools需要考虑额外的存储优化，此外Sedona空间大数据平台使用了JTS，当属性字段不大时额外开销也达到了几倍，也有很大的优化空间。但空间分析算法本身比较复杂，实现对应的算法带来的工作量和内存开销之间需要一定的平衡。按照现在的GIS发展情况，等开源社区优化后出现一个高性能的空间数据管理分析开源库貌似短时间。

# 附——几种对比的代码示意

```Java
// GeoTools
for(int i=0; i<pointNum; i++){
  double latitude = i * 10;
  double longitude = i * 11;
  Point point = geometryFactory.createPoint(new Coordinate(longitude, latitude));
  builder.add(point);
  builder.add(i);
  // builder.add("remark" + i);
  SimpleFeature feature = builder.buildFeature(null);
  features.add(feature);
  feature.getDefaultGeometry();
}


// JTS
for(int i=0; i<pointNum; i++){
  double latitude = i * 10;
  double longitude = i * 11;
  Point point = geometryFactory.createPoint(new Coordinate(longitude, latitude));
  point.setUserData(i);
  features.add(point);
}


List<Integer> ids = new ArrayList<>(pointNum);
List<Double> latitudes = new ArrayList<>(pointNum);
List<Double> longitudes = new ArrayList<>(pointNum);
for(int i=0; i<pointNum; i++){
  double latitude = i * 10;
  double longitude = i * 11;
  latitudes.add(latitude);
  longitudes.add(longitude);
  ids.add(i);
}

// Java 类数组
Double[] latitudes = new Double[pointNum];
Double[] longitudes = new Double[pointNum];
Integer[] ids = new Integer[pointNum];
for(int i=0; i<pointNum; i++){
  double latitude = i * 10;
  double longitude = i * 11;
  latitudes[i] = latitude;
  longitudes[i] = longitude;
  ids[i] = i;
}


// 普通数组
double[] latitudes = new double[pointNum];
double[] longitudes = new double[pointNum];
int[] ids = new int[pointNum];
//    String[] remarks = new String[pointNum];
for(int i=0; i<pointNum; i++){
  double latitude = i * 10;
  double longitude = i * 11;
  latitudes[i] = latitude;
  longitudes[i] = longitude;
  ids[i] = i;
  // remarks[i] = "remark" + i;
}

// 堆内存显示
System.gc();
Thread.sleep(2000);
System.out.println(Runtime.getRuntime().totalMemory() / 1024 / 1024);
System.out.println(Runtime.getRuntime().freeMemory() / 1024 / 1024);
System.out.println((Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1024 / 1024);
```
