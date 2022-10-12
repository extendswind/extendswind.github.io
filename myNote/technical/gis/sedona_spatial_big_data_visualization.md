---
title: "Sedona空间数据可视化源码分析"
date: 2022-10-11T20:30:00+08:00
toc: true

mathjax: true

categories:
- "GIS"

tags:
- "Hadoop"
- "Sedona"
- "GIS"

---

Sedona (GeoSpark) 空间数据可视化过程不太复杂，主要是每个空间对象向对应栅格空间的映射，和矢量转栅格类似。直接上代码：

```java

// 已经通过Sedona创建了类型为LineStringRDD的slineRDD对象

import org.apache.sedona.viz.core.ImageGenerator
import org.apache.sedona.viz.extension.visualizationEffect.ScatterPlot
import org.apache.sedona.viz.utils.ImageType
import java.awt.Color

// 创建新的对象
var visualizationOperator = new ScatterPlot(10000, 10000, slineRDD.boundaryEnvelope, false)
visualizationOperator.CustomizeColor(255, 255, 255, 255, Color.blue, true)

// 具体的可视化过程实现
visualizationOperator.Visualize(sc, slineRDD)

// 将结果保存为PNG图像
var imageGenerator = new ImageGenerator
imageGenerator.SaveRasterImageAsLocalFile(visualizationOperator.rasterImage, "/home/sparkl/visual", ImageType.PNG)
```

其中具体的可视化操作在visualizationOperator.Visualize(sc, slineRDD)函数中，分为visualize、colorize和renderImage三步，具体操作如下：

```java
public boolean Visualize(JavaSparkContext sparkContext, SpatialRDD spatialRDD)
            throws Exception
{
  // 返回值为JavaPairRDD<Pixel, Double>
  // 栅格图中的每个像素对应一个Pixel，包含x、y信息，Double和属性值相关
  this.Rasterize(sparkContext, spatialRDD, true);

  // 修改value的值，通过value值赋颜色
  this.Colorize();
  this.RenderImage(sparkContext);
  return true;
}

```

# Rasterize

Rasterize函数是最主要的矢量向栅格的转换函数，先通过flatMapToPair算子计算每个空间对象对应的像素位置和像素值，然后filter掉超出范围的像素值。Sedona的实现中value没有考虑空间实体的属性，每个像素点的value直接赋值的1.0。

```java
protected JavaPairRDD<Pixel, Double> Rasterize(JavaSparkContext sparkContext,
        SpatialRDD spatialRDD, boolean useSparkDefaultPartition)
{
    JavaRDD<Object> rawSpatialRDD = spatialRDD.rawSpatialRDD;
	// rawSpatialRDD中包含对应的空间对象，通过flatMapToPair算子计算每个空间对象对应的Pixel，得到<Pixel, Double> 类型的键值对
    JavaPairRDD<Pixel, Double> spatialRDDwithPixelId = rawSpatialRDD.flatMapToPair(new PairFlatMapFunction<Object, Pixel, Double>(){
        @Override
        public Iterator<Tuple2<Pixel, Double>> call(Object spatialObject) throws Exception {
			// 分不同的数据类型进行处理
            if (spatialObject instanceof Point) {
                return RasterizationUtils.FindPixelCoordinates(resolutionX, resolutionY, datasetBoundary, (Point) spatialObject, colorizeOption, reverseSpatialCoordinate).iterator();
            }
            else if (spatialObject instanceof Polygon) {
                return RasterizationUtils.FindPixelCoordinates(resolutionX, resolutionY, datasetBoundary, (Polygon) spatialObject, reverseSpatialCoordinate).iterator();
            }
            else if (spatialObject instanceof LineString) {
				// 计算每个空间对象对应栅格图中的<像素位置,像素值>，会得到一个像素值列表
                return RasterizationUtils.FindPixelCoordinates(resolutionX, resolutionY, datasetBoundary, (LineString) spatialObject, reverseSpatialCoordinate).iterator();
            }
            else {
				// 只支持上面的三种数据类型
                throw new Exception("[Sedona-VizViz][Rasterize] Unsupported spatial object types. Sedona-VizViz only supports Point, Polygon, LineString");
            }
        }
    });
	
	// 去除不在范围内的点（这个在上一步直接处理比较合适？）
	spatialRDDwithPixelId = spatialRDDwithPixelId.filter(new Function<Tuple2<Pixel, Double>, Boolean>()
    {
        @Override
        public Boolean call(Tuple2<Pixel, Double> pixelCount)
                throws Exception
        {
            return !(pixelCount._1().getX() < 0) && !(pixelCount._1().getX() > resolutionX) && !(pixelCount._1().getY() < 0) && !(pixelCount._1().getY() > resolutionY);
        }
    });

    this.distributedRasterCountMatrix = spatialRDDwithPixelId;
    return this.distributedRasterCountMatrix;
}
```

像素值的计算将LineString拆分为两个点构成的线段进行计算，先计算每个点在栅格图中的位置，然后计算两个栅格图坐标练成线段时中间穿过的点。

```java

public static List<Tuple2<Pixel, Double>> FindPixelCoordinates(int resolutionX, int resolutionY, Envelope datasetBoundary, LineString spatialObject, boolean reverseSpatialCoordinate) {
    List<Tuple2<Pixel, Double>> result = new ArrayList<Tuple2<Pixel, Double>>();
    for (int i = 0; i < spatialObject.getCoordinates().length - 1; i++) {
        Tuple2<Integer, Integer> pixelCoordinate1 = null;
        Tuple2<Integer, Integer> pixelCoordinate2 = null;
        try {
			// 两个点在栅格图中的位置
            pixelCoordinate1 = FindOnePixelCoordinate(resolutionX, resolutionY, datasetBoundary, spatialObject.getCoordinates()[i], reverseSpatialCoordinate);
            pixelCoordinate2 = FindOnePixelCoordinate(resolutionX, resolutionY, datasetBoundary, spatialObject.getCoordinates()[i + 1], reverseSpatialCoordinate);
        }
        catch (Exception e) {
            // This line segment is out of boundary, Should be ignored.
            continue;
        }
		// 通过两个栅格图的坐标位置计算连成线段后经过的其它栅格点，并将结果加入到result
        result.addAll(FindPixelCoordinates(resolutionX, resolutionY, pixelCoordinate1, pixelCoordinate2, reverseSpatialCoordinate));
    }
    return result;
}

// 计算点在栅格图像中的位置
public static Tuple2<Integer, Integer> FindOnePixelCoordinate(int resolutionX, int resolutionY, Envelope datasetBoundaryOriginal, Coordinate spatialCoordinateOriginal, boolean reverseSpatialCoordinate) {
    Coordinate spatialCoordinate;
    Envelope datasetBoundary;
    if (reverseSpatialCoordinate) {
        spatialCoordinate = new Coordinate(spatialCoordinateOriginal.y, spatialCoordinateOriginal.x);
        datasetBoundary = new Envelope(datasetBoundaryOriginal.getMinY(), datasetBoundaryOriginal.getMaxY(), datasetBoundaryOriginal.getMinX(), datasetBoundaryOriginal.getMaxX());
    }
    else {
        spatialCoordinate = spatialCoordinateOriginal;
        datasetBoundary = datasetBoundaryOriginal;
    }
    Double pixelXDouble = ((spatialCoordinate.x - datasetBoundary.getMinX()) / (datasetBoundary.getMaxX() - datasetBoundary.getMinX())) * resolutionX;
    Double xRemainder = (spatialCoordinate.x - datasetBoundary.getMinX()) % (datasetBoundary.getMaxX() - datasetBoundary.getMinX());
    Double pixelYDouble = ((spatialCoordinate.y - datasetBoundary.getMinY()) / (datasetBoundary.getMaxY() - datasetBoundary.getMinY())) * resolutionY;
    Double yRemainder = (spatialCoordinate.y - datasetBoundary.getMinY()) % (datasetBoundary.getMaxY() - datasetBoundary.getMinY());
    int pixelX = pixelXDouble.intValue();
    int pixelY = pixelYDouble.intValue();
    if (xRemainder == 0.0 && pixelXDouble != 0.0) {
        pixelX--;
    }
    if (pixelX >= resolutionX) {
        pixelX--;
    }
    if (yRemainder == 0.0 && pixelYDouble != 0) {
        pixelY--;
    }
    if (pixelY >= resolutionY) {
        pixelY--;
    }
    return new Tuple2<Integer, Integer>(pixelX, pixelY);
}

// 通过两个栅格图上的点，计算连线线段经过的点
public static List<Tuple2<Pixel, Double>> FindPixelCoordinates(int resolutionX, int resolutionY, Tuple2<Integer, Integer> pixelCoordinate1, Tuple2<Integer, Integer> pixelCoordinate2, boolean reverseSpatialCoordinate) {
    // This function uses Bresenham's line algorithm to plot pixels touched by a given line segment.
    int x1 = pixelCoordinate1._1;
    int y1 = pixelCoordinate1._2;
    int x2 = pixelCoordinate2._1;
    int y2 = pixelCoordinate2._2;
    int dx = x2 - x1;
    int dy = y2 - y1;
    int ux = dx > 0 ? 1 : -1; // x direction
    int uy = dy > 0 ? 1 : -1; // y direction
    int x = x1, y = y1;
    int eps = 0; //cumulative errors
    dx = Math.abs(dx);
    dy = Math.abs(dy);
    List<Tuple2<Pixel, Double>> result = new ArrayList<Tuple2<Pixel, Double>>();
    if (dx > dy) {
        for (x = x1; x != x2; x += ux) {
            try {
                Pixel newPixel = new Pixel(x, y, resolutionX, resolutionY);
                result.add(new Tuple2<Pixel, Double>(newPixel, 1.0));
            }
            catch (Exception e) {
                 // This spatial object is out of the given dataset boudanry. It is ignored here.
            }
            eps += dy;
            if ((eps << 1) >= dx) {  // x值每次+1，y值在eps/2 > dx时+1
                y += uy;
                eps -= dx;
            }
        }
    }
    else {
        for (y = y1; y != y2; y += uy) {
            try {
                Pixel newPixel = new Pixel(x, y, resolutionX, resolutionY);
                result.add(new Tuple2<Pixel, Double>(newPixel, 1.0));
            }
            catch (Exception e) {
                 // This spatial object is out of the given dataset boudanry. It is ignored here.
            }
            eps += dx;
            if ((eps << 1) >= dy) {
                x += ux;
                eps -= dy;
            }
        }
    }
    return result;
}
```

# colorize

上面的Visualize函数得到了一个distributedRasterCountMatrix的RDD，key为Pixel像素位置，value为表示点数量的Double类型（感觉这个Double类型可以直接用Integer）。colorize使用了一次mapValues操作，将value值归一化后赋值为Integer类型的颜色值。

```java

  this.distributedRasterColorMatrix = this.distributedRasterCountMatrix.mapValues(new Function<Double, Integer>()
  {

      @Override
      public Integer call(Double pixelCount)
              throws Exception
      {
          Double currentPixelCount = pixelCount;
          if (currentPixelCount > maxWeight) {
              currentPixelCount = maxWeight;
          }
          Double normalizedPixelCount = (currentPixelCount - minWeight) * 255 / (maxWeight - minWeight);
          Integer pixelColor = EncodeToRGB(normalizedPixelCount.intValue());
          return pixelColor;
      }
  });
  //logger.debug("[Sedona-VizViz][Colorize]output count "+this.distributedRasterColorMatrix.count());
  logger.info("[Sedona-VizViz][Colorize][Stop]");
  return true;
```

# RenderImage

RenderImage函数将上一步中得到的<Pixel, Integer>键值对转换成图像，以ImageSerializableWrapper的形式得到结果。函数中parallelRenderImage参数默认为false，直接对每个partition并行处理得到完整的图像，得到<Integer, ImageSerializablewrapper>结果，其中Integer都为0，然后ReduceByKey将所有的图像叠加得到结果。

ParalleRenderImage选项为true时，首先对上一步的distributedRasterColorMatrix进行空间分区，使每个partition对应结果图像中的一部分，并行处理各自对应的区域。得到的结果存储在distributedRasterImage。

parallelRenderImage参数为false的方法的shuffle过程将每个分区产生的完整结果图像传送到同一个节点后叠加计算，当结果图像较大时会造成大量shuffle IO。参数为true时，shuffle过程主要来自对原始数据的空间划分，对空间划分的效果有较高的要求。

```java

protected boolean RenderImage(JavaSparkContext sparkContext) throws Exception {
    if (this.parallelRenderImage == true) {
        if (this.hasBeenSpatialPartitioned == false) {
            this.spatialPartitioningWithoutDuplicates();
            this.hasBeenSpatialPartitioned = true;
        }
        this.distributedRasterImage = this.distributedRasterColorMatrix.mapPartitionsToPair(
                new PairFlatMapFunction<Iterator<Tuple2<Pixel, Integer>>, Integer, ImageSerializableWrapper>()
                {
                    @Override
                    public Iterator<Tuple2<Integer, ImageSerializableWrapper>> call(Iterator<Tuple2<Pixel, Integer>> currentPartition)
                            throws Exception
                    {
                        BufferedImage imagePartition = new BufferedImage(partitionIntervalX, partitionIntervalY, BufferedImage.TYPE_INT_ARGB);
                        Tuple2<Pixel, Integer> pixelColor = null;
                        while (currentPartition.hasNext()) {
                            //Render color in this image partition pixel-wise.
                            pixelColor = currentPartition.next();
                            if (pixelColor._1().getX() < 0 || pixelColor._1().getX() >= resolutionX || pixelColor._1().getY() < 0 || pixelColor._1().getY() >= resolutionY) {
                                pixelColor = null;
                                continue;
                            }
                            imagePartition.setRGB((int) pixelColor._1().getX() % partitionIntervalX, (partitionIntervalY - 1) - (int) pixelColor._1().getY() % partitionIntervalY, pixelColor._2);
                        }
                        List<Tuple2<Integer, ImageSerializableWrapper>> result = new ArrayList<Tuple2<Integer, ImageSerializableWrapper>>();
                        if (pixelColor == null) {
                            // No pixels in this partition. Skip this subimage
                            return result.iterator();
                        }
                        logger.info("[Sedona-VizViz][Render]add a image partition into result set " + pixelColor._1().getCurrentPartitionId());
                        result.add(new Tuple2<Integer, ImageSerializableWrapper>(pixelColor._1().getCurrentPartitionId(), new ImageSerializableWrapper(imagePartition)));
                        return result.iterator();
                    }
                });
    }
    else if (this.parallelRenderImage == false) {
        // Draw full size image in parallel
        this.distributedRasterImage = this.distributedRasterColorMatrix.mapPartitionsToPair(
                new PairFlatMapFunction<Iterator<Tuple2<Pixel, Integer>>, Integer, ImageSerializableWrapper>()
                {
                    @Override
                    public Iterator<Tuple2<Integer, ImageSerializableWrapper>> call(Iterator<Tuple2<Pixel, Integer>> currentPartition)
                            throws Exception
                    {
                        BufferedImage imagePartition = new BufferedImage(resolutionX, resolutionY, BufferedImage.TYPE_INT_ARGB);
                        Tuple2<Pixel, Integer> pixelColor = null;
                        while (currentPartition.hasNext()) {
                            //Render color in this image partition pixel-wise.
                            pixelColor = currentPartition.next();
                            if (pixelColor._1().getX() < 0 || pixelColor._1().getX() >= resolutionX || pixelColor._1().getY() < 0 || pixelColor._1().getY() >= resolutionY) {
                                pixelColor = null;
                                continue;
                            }
                            imagePartition.setRGB((int) pixelColor._1().getX(), (resolutionY - 1) - (int) pixelColor._1().getY(), pixelColor._2);
                        }
                        List<Tuple2<Integer, ImageSerializableWrapper>> result = new ArrayList<Tuple2<Integer, ImageSerializableWrapper>>();
                        if (pixelColor == null) {
                            // No pixels in this partition. Skip this subimage
                            return result.iterator();
                        }
                        result.add(new Tuple2<Integer, ImageSerializableWrapper>(1, new ImageSerializableWrapper(imagePartition)));
                        return result.iterator();
                    }
                });
        // Merge images together using reduce

        this.distributedRasterImage = this.distributedRasterImage.reduceByKey(new Function2<ImageSerializableWrapper, ImageSerializableWrapper, ImageSerializableWrapper>()
        {
            @Override
            public ImageSerializableWrapper call(ImageSerializableWrapper image1, ImageSerializableWrapper image2)
                    throws Exception
            {
                // The combined image should be a full size image
                BufferedImage combinedImage = new BufferedImage(resolutionX, resolutionY, BufferedImage.TYPE_INT_ARGB);
                Graphics graphics = combinedImage.getGraphics();
                graphics.drawImage(image1.image, 0, 0, null);
                graphics.drawImage(image2.image, 0, 0, null);
                return new ImageSerializableWrapper(combinedImage);
            }
        });
        List<Tuple2<Integer, ImageSerializableWrapper>> imageList = this.distributedRasterImage.collect();
        this.rasterImage = imageList.get(0)._2().image;
    }
    logger.info("[Sedona-VizViz][RenderImage][Stop]");
    return true;
}
```
