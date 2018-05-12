### 问题

```
   // 每个点为hardData中的一个Array
    val hardData = spark.read.textFile(args(0)).rdd
      .map(_.split(" ").map(_.toDouble).toArray)
      .cache()

    hardData.map(a => println(a(0).toString + " " + a(1).toString +
      " " + a(3).toString))
```

结果中没有输出，而将map函数改为foreach则有输出


### 解决

参考  https://stackoverflow.com/questions/33225994/spark-losing-println-on-stdout

由于spark面向大数据量和分布式，在使用map函数输出时存在各种问题：可能输出到各个主机、数据量过大等问题。

因此，**spark在设计时使map函数中不能使用println输出信息流****

将map函数改为foreach则有输出...