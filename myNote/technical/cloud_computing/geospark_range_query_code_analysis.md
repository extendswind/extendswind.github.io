---
title: "GeoSpark范围查询源码分析"
date: 2020-11-05T10:30:00+08:00
toc: true

categories:
- "cloud computing"

tags:
- "hadoop"
- "GIS"
- "GeoSpark"
- "Spark"

---

# GeoSpark

GeoSpark是基于Spark的空间数据处理开源库，在RDD模型的基础上添加了空间数据操作，以底层的SpatialRDD为基础设计了空间分析、空间SQL、空间数据可视化等组件。详细信息可以参考作者博客 [https://jiayuasu.github.io/](https://jiayuasu.github.io/) 以及项目主页 [http://sedona.apache.org](http://sedona.apache.org)。GeoSpark一开始是Spark的一个第三方组件，之后改名为sedona提交到apache基金会，当前（2020.11）正处于孵化阶段。

在空间数据的索引与并行访问上，没有像SpatialHadoop那样直接基于HDFS构建针对文件的索引，而是将数据读到RDD中在内存中后进行分区和索引构建操作，索引后的数据可以持久化到硬盘避免下一次的读取，内存的大小一定程度上限制了单次能够处理的数据总量。

最近通过Spark提高SpatialHadoop在设计上的效率，看了一眼GeoSpark在常见的空间处理上的逻辑，针对空间数据读取、索引、划分几个方面的逻辑记个笔记。

# 主要代码逻辑

GeoSpark的代码大多直接用的java编写，调用了Spark的java API，整体的逻辑比我想象的要简单。代码注释、缩进、命名等貌似都略有非主流的地方。

示例代码主要参考官网教程 http://sedona.apache.org/tutorial/rdd/ 与github仓库源码。


## 读取csv文件并创建PointRDD

> 官方示例
> Suppose we have a checkin.csv CSV file at Path /Download/checkin.csv as follows:
> 
> -88.331492,32.324142,hotel
> -88.175933,32.360763,gas
> -88.388954,32.357073,bar
> -88.221102,32.35078,restaurant
> 
> This file has three columns and corresponding offsets(Column IDs) are 0, 1, 2. Use the following code to create a PointRDD
 
> ```scala
> val pointRDDInputLocation = "/Download/checkin.csv"
> val pointRDDOffset = 0 // The point long/lat starts from Column 0
> val pointRDDSplitter = FileDataSplitter.CSV
> val carryOtherAttributes = true // Carry Column 2 (hotel, gas, bar...)
> var objectRDD = new PointRDD(sc, pointRDDInputLocation, pointRDDOffset, pointRDDSplitter, carryOtherAttributes)
> ```

通过继承SpatialRDD的PointRDD处理点数据，对于csv格式的文件： 

1. 通过sparkContext.textFile读取text文件；
2. mapPartition分行处理，由PointFormatMapper将文本的每一行解析成点的对象。

## RangeQuery范围查询

查询PointRDD中一个范围内的点，GeoSpark对索引过的数据与不带索引的数据做了两种实现。

```scala
// 不带索引查询
val rangeQueryWindow = new Envelope(-90.01, -80.01, 30.01, 40.01)
val considerBoundaryIntersection = false // Only return gemeotries fully covered by the window
val usingIndex = false
var queryResult = RangeQuery.SpatialRangeQuery(spatialRDD, rangeQueryWindow, considerBoundaryIntersection, usingIndex)
```

对于没有空间索引的点数据，直接基于filter算子，在RangeFilter类中判断点是否在范围内。

```scala
// 构建空间索引并利用索引查询
val rangeQueryWindow = new Envelope(-90.01, -80.01, 30.01, 40.01)
val considerBoundaryIntersection = false // Only return gemeotries fully covered by the window
val buildOnSpatialPartitionedRDD = false // Set to TRUE only if run join query
spatialRDD.buildIndex(IndexType.QUADTREE, buildOnSpatialPartitionedRDD)
val usingIndex = true
var queryResult = RangeQuery.SpatialRangeQuery(spatialRDD, rangeQueryWindow, considerBoundaryIntersection, usingIndex)
```

对于有空间索引的点数据（如四叉树索引），首先对每个partition构建索引，在mapPartition算子中将所有的点插入到STR-tree或Quad-tree，结果存入indexedRawRDD。范围查询中以partition为单位多indexedRawRDD做mapPartition操作。

## SpatialPartitioning空间划分

前面的空间索引构建和分析都是基于Spark在读取数据时根据数据文件的位置直接做的RDD划分，当有需要邻近数据在同一个partition增加邻域查询效率时，可以考虑使用空间划分对数据重新分区。

```scala
objectRDD.spatialPartitioning(GridType.KDBTREE)
queryWindowRDD.spatialPartitioning(objectRDD.getPartitioner)
```

GeoSpark提供了KDB-tree、R-tree、维诺图等多种划分方式，总体上的逻辑差不多。为了降低总体的计算量，GeoSpark并没有直接在元数据上进行空间划分，而是通过采样的方式首先提取一定比例的数据构建空间划分。然后用了三个Spark算子，flatMapToPair将rawSpatialRDD中的每条数据转成（分区id，空间对象）的形式，partitionBy将数据按照分区id重新划分，最后mapPartitions将（分区id，空间对象）提取为空间对象。

# 具体源码分析

## 读取csv文件并创建PointRDD

PointRDD是一个java写的类，其构造函数如下。主要逻辑通过sparkContext.textFile读取text文件，然后mapPartition分行处理，由PointFormatMapper将文本的每一行解析成点的对象，从每一行的数据中根据分隔符splitter和标记坐标位置的Offset得到坐标和额外注释。

```java
/**
   * Instantiates a new point RDD.
   *
   * @param sparkContext      the spark context
   * @param InputLocation     the input location
   * @param Offset            the offset
   * @param splitter          the splitter，行分隔符，如csv中的','
   * @param carryInputData    the carry input data，是否存储坐标以外的数据（boolean类型，这个注释略迷）
   * @param partitions        the partitions，分区数据（命名为numOfPartitions更好？）
   * @param newLevel          the new level （newStorageLevel）
   * @param sourceEpsgCRSCode the source epsg CRS code
   * @param targetEpsgCode    the target epsg code
   */
  public PointRDD(JavaSparkContext sparkContext, String InputLocation, Integer Offset, FileDataSplitter splitter,
                  boolean carryInputData, Integer partitions, StorageLevel newLevel, String sourceEpsgCRSCode,
                  String targetEpsgCode) {
    JavaRDD rawTextRDD = partitions != null ? sparkContext.textFile(InputLocation, partitions) : sparkContext
        .textFile(InputLocation);
    if (Offset != null) {
      this.setRawSpatialRDD(
          // 上面的textFile函数已经得到了一个以line为单位的RDD
          // mapPartitions函数对每个partition内部的line进行处理
          // 将每行解析成具体的几何对象
          // 实现的逻辑在FormatMapper类中，PointFormatMapper只是传了几个参数，感觉像个FormatMapperFactory
		  // mapPartitions在scala里是传入一个函数，在java里传入一个包含call函数的对象。
          rawTextRDD.mapPartitions(new PointFormatMapper(Offset, splitter,
          carryInputData)));
    } else {
      this.setRawSpatialRDD(rawTextRDD.mapPartitions(new PointFormatMapper(splitter, carryInputData)));
    }
    if (sourceEpsgCRSCode != null && targetEpsgCode != null) {
      this.CRSTransform(sourceEpsgCRSCode,
          targetEpsgCode);
    }
    if (newLevel != null) {
      this.analyze(newLevel);
    }
    if (splitter.equals(FileDataSplitter.GEOJSON)) {
      this.fieldNames = FormatMapper.readGeoJsonPropertyNames(rawTextRDD.take(1).get(0).toString());
    }
  }
```

PointFormatMapper的点文本解析过程。PointFormatMapper的实现略奇怪，继承了FormatMapper，只是改了几个构造函数，感觉只是个初始化的工厂。具体的实现跳到FormatMapper中的call函数。

```java
public class PointFormatMapper
        extends FormatMapper
{
   public PointFormatMapper(FileDataSplitter Splitter, boolean carryInputData)
    {
        super(0, 1, Splitter, carryInputData, GeometryType.POINT);
    }
	//...
}
```

```java
// FormatMapper类
 @Override
public Iterator<T> call(Iterator<String> stringIterator)
        throws Exception
{
    List<T> result = new ArrayList<>();
    while (stringIterator.hasNext()) {
        String line = stringIterator.next();
		// 解析每一行，得到一个Geometry对象
        addGeometry(readGeometry(line), result);
    }
    return result.iterator();
}
```

```java
public Geometry readGeometry(String line)
        throws ParseException
{
//...
   geometry = createGeometry(readCoordinates(line), geometryType);
// ...
}
```

其中readCoordinates(line)从行中获取一个或多个点的坐标（返回Coordinate[]），createGeometry根据坐标和类型创建具体的Geometry对象。

```java
private Geometry createGeometry(Coordinate[] coordinates, GeometryType geometryType)
{
  GeometryFactory geometryFactory = new GeometryFactory();
  Geometry geometry = null;
  switch (geometryType) {
      case POINT:
          geometry = geometryFactory.createPoint(coordinates[0]);
          break;
      case POLYGON:
          geometry = geometryFactory.createPolygon(coordinates);
          break;
  // ...
```

geometryFactory.createPoint先把Coordinate[]转成CoordinateSequence，然后得到一个Point对象，每个对象需要占用的额外空间略大。Point类继承了Geometry类，除去static对象就已经有包围盒、创建工厂对象、空间参考系id、辅助数据。Point类在此基础上添加了CoordinateSequence类成员存储具体的坐标。按照之前的测试，如果点坐标只包含(x,y)信息，会占用很多的额外存储空间（JVM对象的额外占用以及上面多余的对象变量），仅存一个坐标数组的效率会更高。

```java
public abstract class Geometry
    implements Cloneable, Comparable, Serializable
{
  /**
   *  The bounding box of this <code>Geometry</code>.
   */
  protected Envelope envelope;

  /**
   * The {@link GeometryFactory} used to create this Geometry
   */
  protected final GeometryFactory factory;

  /**
   *  The ID of the Spatial Reference System used by this <code>Geometry</code>
   */
  protected int SRID;

  /**
   * An object reference which can be used to carry ancillary data defined
   * by the client.
   */
  private Object userData = "";

  /**
   * Creates a new <code>Geometry</code> via the specified GeometryFactory.
   *
   * @param factory
   */
  public Geometry(GeometryFactory factory) {
    this.factory = factory;
    this.SRID = factory.getSRID();
  }
```


## RangeQuery范围查询

GeoSpark实现代码

```scala
val rangeQueryWindow = new Envelope(-90.01, -80.01, 30.01, 40.01)
val considerBoundaryIntersection = false // Only return gemeotries fully covered by the window
val usingIndex = false
var queryResult = RangeQuery.SpatialRangeQuery(spatialRDD, rangeQueryWindow, considerBoundaryIntersection, usingIndex)
```

RangeQuery分带索引的查询和不带索引查询两种形式，在SparkRangeQuery中传参。

```java
    public static <U extends Geometry, T extends Geometry> JavaRDD<T> SpatialRangeQuery(SpatialRDD<T> spatialRDD, U originalQueryGeometry, boolean considerBoundaryIntersection, boolean useIndex)
            throws Exception
    {
        U queryGeometry = originalQueryGeometry;
        if (spatialRDD.getCRStransformation()) { // 坐标系转换
            queryGeometry = CRSTransformation.Transform(spatialRDD.getSourceEpsgCode(), spatialRDD.getTargetEpgsgCode(), originalQueryGeometry);
        }

        if (useIndex == true) {
            if (spatialRDD.indexedRawRDD == null) {
                throw new Exception("[RangeQuery][SpatialRangeQuery] Index doesn't exist. Please build index on rawSpatialRDD.");
            }
            return spatialRDD.indexedRawRDD.mapPartitions(new RangeFilterUsingIndex(queryGeometry, considerBoundaryIntersection, true));
        }
        else {
            return spatialRDD.getRawSpatialRDD().filter(new RangeFilter(queryGeometry, considerBoundaryIntersection, true));
        }
    }
```



```java

public Boolean call(T geometry)
{
    if (leftCoveredByRight) {
        return match(geometry, queryGeometry);
    }
    else {
        return match(queryGeometry, queryGeometry);
    }
}

public boolean match(Geometry spatialObject, Geometry queryWindow)
{
    if (considerBoundaryIntersection) {
        if (queryWindow.intersects(spatialObject)) { return true; }
    }
    else {
        if (queryWindow.covers(spatialObject)) { return true; }
    }
    return false;
}
```

要使用带空间索引的查询，首先需要构建索引，然后查询时标记使用索引，下面的代码以四叉树索引为例。

```scala
val rangeQueryWindow = new Envelope(-90.01, -80.01, 30.01, 40.01)
val considerBoundaryIntersection = false // Only return gemeotries fully covered by the window
val buildOnSpatialPartitionedRDD = false // Set to TRUE only if run join query
spatialRDD.buildIndex(IndexType.QUADTREE, buildOnSpatialPartitionedRDD)

val usingIndex = true
var queryResult = RangeQuery.SpatialRangeQuery(spatialRDD, rangeQueryWindow, considerBoundaryIntersection, usingIndex)
```

针对有索引的数据，用mapPartition算子处理spatialRDD.indexedRawRDD中的每一条数据，每一条数据具体对应了一个treeIndex。通过treeIndex.query(Envelope searchEnv)函数得到一个List存储的结果，然后依次遍历List中的数据是否符合要求。

```java
// ...
if (useIndex == true) {
    if (spatialRDD.indexedRawRDD == null) {
        throw new Exception("[RangeQuery][SpatialRangeQuery] Index doesn't exist. Please build index on rawSpatialRDD.");
    }
    return spatialRDD.indexedRawRDD.mapPartitions(new RangeFilterUsingIndex(queryGeometry, considerBoundaryIntersection, true));
}
else {
    return spatialRDD.getRawSpatialRDD().filter(new RangeFilter(queryGeometry, considerBoundaryIntersection, true));
}
// ...

@Override
public Iterator<T> call(Iterator<SpatialIndex> treeIndexes)
        throws Exception
{
    assert treeIndexes.hasNext() == true;
    SpatialIndex treeIndex = treeIndexes.next();
    List<T> results = new ArrayList<T>();
    List<T> tempResults = treeIndex.query(this.queryGeometry.getEnvelopeInternal());
    for (T tempResult : tempResults) {
        if (leftCoveredByRight) {
            if (match(tempResult, queryGeometry)) {
                results.add(tempResult);
            }
        }
        else {
            if (match(queryGeometry, tempResult)) {
                results.add(tempResult);
            }
        }
    }
    return results.iterator();
}
```

索引的构建通过buildIndex函数，貌似比想象的简单，还是以partition为单位构建索引，通过mapPartition算子对每个partition中的空间数据构建索引，

```java
/**
 * Builds the index.
 *
 * @param indexType the index type
 * @param buildIndexOnSpatialPartitionedRDD the build index on spatial partitioned RDD
 * @throws Exception the exception
 */
public void buildIndex(final IndexType indexType, boolean buildIndexOnSpatialPartitionedRDD)
        throws Exception
{
    if (buildIndexOnSpatialPartitionedRDD == false) {
        //This index is built on top of unpartitioned SRDD
        this.indexedRawRDD = this.rawSpatialRDD.mapPartitions(new IndexBuilder(indexType));
    }
    else {
        if (this.spatialPartitionedRDD == null) {
            throw new Exception("[AbstractSpatialRDD][buildIndex] spatialPartitionedRDD is null. Please do spatial partitioning before build index.");
        }
        this.indexedRDD = this.spatialPartitionedRDD.mapPartitions(new IndexBuilder(indexType));
    }
}
```

在IndexBuilder中，只支持R-tree和四叉树两种索引方式。

```java
@Override
public Iterator<SpatialIndex> call(Iterator<T> objectIterator)
       throws Exception
{
    SpatialIndex spatialIndex;
    if (indexType == IndexType.RTREE) {
        spatialIndex = new STRtree();
    }
    else {
        spatialIndex = new Quadtree();
    }
    while (objectIterator.hasNext()) {
        T spatialObject = objectIterator.next();
        spatialIndex.insert(spatialObject.getEnvelopeInternal(), spatialObject);
    }
    Set<SpatialIndex> result = new HashSet();
	
	// 这啥操作
    spatialIndex.query(new Envelope(0.0, 0.0, 0.0, 0.0));

    result.add(spatialIndex);
    return result.iterator();
}
```

## SpatialPartitioning空间划分

```scala
objectRDD.spatialPartitioning(GridType.KDBTREE)
queryWindowRDD.spatialPartitioning(objectRDD.getPartitioner)
```

```java
public boolean spatialPartitioning(GridType gridType)
         throws Exception
{
     int numPartitions = this.rawSpatialRDD.rdd().partitions().length;
	 // 基于RDD的分区数量构建空间划分
     spatialPartitioning(gridType, numPartitions);
     return true;
}

public void spatialPartitioning(GridType gridType, int numPartitions)
        throws Exception
{
   // 并非直接针对元数据做划分，而是针对采样后的数据
   int sampleNumberOfRecords = RDDSampleUtils.getSampleNumbers(numPartitions, this.approximateTotalCount, this.sampleNumber);
   // 采样的比例
   final double fraction = SamplingUtils.computeFractionForSampleSize(sampleNumberOfRecords, approximateTotalCount, false);
   // 这个samples变量存储的是一堆外包围盒，取名叫sampleEnvelopes更好，外包围盒用于后面的Partitioning类的构建
   List<Envelope> samples = this.rawSpatialRDD.sample(false, fraction)
       // sample函数是RDD自带的算子
           .map(new Function<T, Envelope>()
           {
               @Override
               public Envelope call(T geometry)
                       throws Exception
               {
                   return geometry.getEnvelopeInternal();
               }
           })
           .collect();

	// 外包围盒扩宽一点
   final Envelope paddedBoundary = new Envelope(
           boundaryEnvelope.getMinX(), boundaryEnvelope.getMaxX() + 0.01,
           boundaryEnvelope.getMinY(), boundaryEnvelope.getMaxY() + 0.01);

   switch (gridType) {
   //...
      case QUADTREE: {
           QuadtreePartitioning quadtreePartitioning = new QuadtreePartitioning(samples, paddedBoundary, numPartitions);
           partitionTree = quadtreePartitioning.getPartitionTree();
           partitioner = new QuadTreePartitioner(partitionTree);
           break;
       }
       case KDBTREE: {
           final KDBTree tree = new KDBTree(samples.size() / numPartitions, numPartitions, paddedBoundary);
           for (final Envelope sample : samples) {
               tree.insert(sample);
           }
           tree.assignLeafIds();
           partitioner = new KDBTreePartitioner(tree);
           break;
       }
       default:
           throw new Exception("[AbstractSpatialRDD][spatialPartitioning] Unsupported spatial partitioning method.");
   }

   this.spatialPartitionedRDD = partition(partitioner);
}

// 首先flatMapToPair使用partitioner计算每个spatialObject的partition_id，转成(partition_id, spatialObject)的形式
// 然后partitionBy根据partition_id重划分
// 最后mapPartitons将（partition_id, spatialObject）的二元组转成spatialObject
// 感觉几个算子用得略奇怪
private JavaRDD<T> partition(final SpatialPartitioner partitioner)
{
    return this.rawSpatialRDD.flatMapToPair(
            new PairFlatMapFunction<T, Integer, T>()
            {
                @Override
                public Iterator<Tuple2<Integer, T>> call(T spatialObject)
                        throws Exception
                {
                    return partitioner.placeObject(spatialObject);
                    // 返回二元组（spatialObject所在的partition的id, spatialObject）
                }
            }
    ).partitionBy(partitioner)  // rdd默认的函数，根据key值（上面的partition_id）分配具体的partition
            .mapPartitions(new FlatMapFunction<Iterator<Tuple2<Integer, T>>, T>()
            {
                @Override
                public Iterator<T> call(final Iterator<Tuple2<Integer, T>> tuple2Iterator)
                        throws Exception
                {
                    return new Iterator<T>()
                    {
                        @Override
                        public boolean hasNext()
                        {
                            return tuple2Iterator.hasNext();
                        }

                        @Override
                        public T next()
                        {
                            return tuple2Iterator.next()._2();
                        }

                        @Override
                        public void remove()
                        {
                            throw new UnsupportedOperationException();
                        }
                    };
                }
            }, true);
}
```

