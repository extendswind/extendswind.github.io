---
title: "SpatialHadoop二级空间索引机制源码分析"
date: 2020-11-07T10:30:00+08:00
toc: true

# draft: true

categories:
- "cloud computing"

tags:
- "hadoop"
- "GIS"

---

SpatialHadoop已经长期没有更新，MapReduce框架的效率也略低，虽然不太适合直接用，但代码的实现机制可以参考。最近准备重新了解一下HDFS上的空间索引问题，在两年前（没想到距离上次运行SpatialHadoop都两年了..）的基本使用的基础上（[一个简单使用的记录](https://extendswind.top/posts/technical/spatialhadoop_compile_and_run/)），记录一下空间索引机制的处理方式。后面重点关注在Hadoop上的任务提交、并行索引构建、索引的存储与读取这几个方面。

相比GeoSpark的代码，没有Spark现成的算子可以复用并且要处理文件方面的问题，逻辑上的处理稍复杂一点。

# 空间分析任务的提交

SpatialHadoop提供了一个脚本，用于基本的空间处理，如下面的代码生成测试数据。

```bash
sbin/shadoop generate test.rects size:1.gb shape:rect mbr:0,0,1000000,1000000 -overwrite
```

shadoop脚本做的操作不多，直接通过Hadoop的运行命令运行了edu.umn.cs.spatialHadoop.operations.Main类，在类中的Main函数中处理输入参数。

```bash
bin=`dirname "$0"`
bin=`cd "$bin" > /dev/null; pwd`

# Call Hadoop with the operations.Main as the main class
. "$bin"/hadoop edu.umn.cs.spatialHadoop.operations.Main $@
```

在Main函数中使用了Hadoop的ProgramDriver运行具体的类对象。首先从配置文件 `spatial-operations.yaml` 中读取支持的类，然后利用反射机制，读取对应类注释的shortName标签，通过shortName决定参数传递的具体的类。

```java
public static void main(String[] args) {
  int exitCode = -1;
  ProgramDriver pgd = new ProgramDriver();
  try {
  // 这个位置加载配置文件，配置文件spatial-operations.yaml中包含了支持的完整类名
    Yaml yaml = new Yaml();
    List<String> ops = yaml.load(SpatialSite.class.getResourceAsStream("/spatial-operations.yaml"));
	// 通过反射的机制，提取类对应的源码中的annotation里的shortName，运行时会通过shortname执行对应的类
	// 用在上面的生成随机数据中就是通过generate执行edu.umn.cs.spatialHadoop.operations.RandomSpatialGenerator。
    for (String op : ops) {
      Class<?> opClass = Class.forName(op);
      OperationMetadata opMetadata = opClass.getAnnotation(OperationMetadata.class);
      pgd.addClass(opMetadata.shortName(), opClass, opMetadata.description());
    }
    pgd.driver(args);  // 这个函数中调用具体的类执行任务
    exitCode = 0;
  }
  catch(Throwable e){
    e.printStackTrace();
  }
  System.exit(exitCode);
}
```

# 二级空间索引机制

```bash
bin/shadoop index <input> <output> shape:<input format> sindex:<index> blocksize:<size> -overwrite

# 示例
shadoop index test.rects test.grid sindex:grid shape:rect 
```

按照上面提到的机制，会调用Indexer类的Main函数，然后在 `index(inputPaths, outputPath, params);` 函数的调用提交任务。

```java
public static Job index(Path[] inPaths, Path outPath, OperationsParams params)
    throws IOException, InterruptedException, ClassNotFoundException {
  // initiallize主要指定local index对象以及构建全局索引
  // 索引的方式从params中读取具体的类
  // 全局索引的构建可以直接基于原数据或采样后的数据
  // 在这里Partitioner和global index是指向的同一个对象
  // 对于网格索引，初始化过程只是调用GridPartitioner的构造函数计算了网格大小等基本数据
  Partitioner p = initializeIndexers(inPaths, outPath, params);  引
  if (OperationsParams.isLocal(new JobConf(params), inPaths)) {
    indexLocal(inPaths, outPath, p, params);
    return null;
  } else {
    // 提交MapReduce任务
    Job job = indexMapReduce(inPaths, outPath, p, params);
    return job;
  }
}

// MR任务的主要配置如下
static Job indexMapReduce(Path[] inPaths, Path outPath, Partitioner partitioner,
  OperationsParams paramss) throws IOException, InterruptedException,
  ClassNotFoundException {
  // ...
  // Set mapper and reducer
  Shape shape = OperationsParams.getShape(conf, "shape");
  job.setMapperClass(PartitionerMap.class);
  job.setMapOutputKeyClass(IntWritable.class);
  job.setMapOutputValueClass(shape.getClass());
  job.setReducerClass(PartitionerReduce.class);
  // Set input and output
  job.setInputFormatClass(SpatialInputFormat3.class);
  SpatialInputFormat3.setInputPaths(job, inPaths);
  job.setOutputFormatClass(IndexOutputFormat.class);
  IndexOutputFormat.setOutputPath(job, outPath);
  //...
}
```

Hadoop对文件的输入主要通过InputFormat，常见的方式继承FileInputFormat后用类似TextFileInputFormat的方式处理中间的一些细节，如getSplits函数将输入文件切分成多个InputSplit，createRecord函数为每个InputSplit创建一个RecordReader对象读取具体的数据，然后在Map任务中通过RecordReader将InputSplit解析成key-value的形式。

对于文件输入的处理，通过SpatialInputFormat3划分数据（为啥后面有个3，没有看到1和2..），继承了FileInputFormat。InputSplit的划分比较常规，基于splitSize将文件划分成多个InputSplit，然后会根据数据本地性做一次合并以降低task的数量。在createRecordReader中，根据InputSplit中文件的后缀判断是否为已经有localIndex的文件，如果有则返回LocalIndexRecordReader，否则返回配置文件中设置的对应后缀的RecordReader（默认为SpatialRecordReader3）。

RecordReader用于解析整个InputSplit，使用的key-value形式直接为<Partition, Iterable<V>>的形式，key对应整个InputSplit，value为解析后的数据迭代器，其中V表示空间数据的类型，继承shape。

对于没有索引过的文件，直接按行读取文件后，将每行的text转为具体的Shape。

```java
protected boolean nextShape(V s) throws IOException {
  do {
    if (!nextLine(tempLine))
      return false;
    s.fromText(tempLine);
  } while (!isMatched(s));
  return true;
}
```

map过程的逻辑比较常规，遍历所有的shape，分别判断每个shape与哪些partition相交，以<partitionID, shape>的key-value形式送到reduce过程处理。

```java
// 去除了些异常处理的语句
@Override
protected void map(Rectangle key, Iterable<? extends Shape> shapes,
    final Context context) throws IOException, InterruptedException {
  final IntWritable partitionID = new IntWritable();
  for (final Shape shape : shapes) {
    Rectangle shapeMBR = shape.getMBR();
    if (disjoint) {
	  // 这个位置用了个套娃，更方便传类成员
      partitioner.overlapPartitions(shape, new ResultCollector<Integer>() {
        @Override
        public void collect(Integer r) {
          partitionID.set(r);
          context.write(partitionID, shape);
        }
      });
    } else {
      partitionID.set(partitioner.overlapPartition(shape));
      if (partitionID.get() >= 0)
        context.write(partitionID, shape);
    }
    context.progress();
  }
}

@Override
public void overlapPartitions(Shape shape, ResultCollector<Integer> matcher) {
  if (shape == null)
    return;
  Rectangle shapeMBR = shape.getMBR();
  if (shapeMBR == null)
    return;
  int col1, col2, row1, row2;
  col1 = (int)Math.floor((shapeMBR.x1 - x) / tileWidth);
  col2 = (int)Math.ceil((shapeMBR.x2 - x) / tileWidth);
  row1 = (int)Math.floor((shapeMBR.y1 - y) / tileHeight);
  row2 = (int)Math.ceil((shapeMBR.y2 - y) / tileHeight);
  
  if (col1 < 0) col1 = 0;
  if (row1 < 0) row1 = 0;
  for (int col = col1; col < col2; col++)
    for (int row = row1; row < row2; row++)
      matcher.collect(getCellNumber(col, row));
}
```

reduce过程直接以partition_id和对应的shape创建输出流，将对应的数据按行写入到输出流。对于不带索引的文件，直接写入到最终的结果中；带索引的文件会在getOrCreateDataOutput函数中得到一个临时文件的输出流，在写入结束后又把整个文件读到内存中构建局部索引（这一写一读外加文本解析的开销？），最后将结果文件写入到HDFS。

LocalIndex接口被实现的类只有RRStarLocalIndex，本地索引貌似只支持R*树。

```java
@Override
protected void reduce(IntWritable partitionID, Iterable<Shape> shapes,
    Context context) throws IOException, InterruptedException {
  LOG.info("Working on partition #"+partitionID);
  for (Shape shape : shapes) {
    context.write(partitionID, shape);
    context.progress();
  }
  // Indicate end of partition to close the file
  // 在OutputFormat中，发现小于0的id号之后表示数据写入完毕可以关闭输出流
  context.write(new IntWritable(-partitionID.get()-1), null);
  LOG.info("Done with partition #"+partitionID);
}

// IndexOutputFormat中，将数据写到对应的文件
// 看到这里可能会奇怪，LocalIndex去哪了，文件没有被索引。这里有个貌似不太高效的处理，
//   需要构建本地索引的文件首先被写入到临时文件，当写入结束（closePartiton函数中）后
//   创建了新的线程对临时文件构建本地空间索引后上传
@Override
public void write(IntWritable partitionID, S value) throws IOException {
  int id = partitionID.get();
  if (id < 0) {
    // An indicator to close a partition
    int partitionToClose = -id - 1;
    this.closePartition(partitionToClose);
  } else {
    // An actual object that we need to write
    // 通过ConcurrentHashMap存id对应的OutputStream
    OutputStream output = getOrCreateDataOutput(id);
    tempText.clear();
    value.toText(tempText);
    byte[] bytes = tempText.getBytes();
    output.write(bytes, 0, tempText.getLength());
    output.write(NEW_LINE);  // 并没有使用二进制的形式存，而是按行存的数据
    Partition partition = partitionsInfo.get(id);
    partition.recordCount++;
    partition.size += tempText.getLength() + NEW_LINE.length;
    partition.expand(value);
    if (shape == null)
      shape = (S) value.clone();
  }
}

private OutputStream getOrCreateDataOutput(int id) throws IOException {
  OutputStream out = partitionsOutput.get(id);
  if (out == null) {
    // First time to write in this partition. Store its information
    Partition partition = new Partition();

    if (localIndexClass == null) {
      // No local index needed. Write to the final file directly
      Path path = getPartitionFile(id);
      out = outFS.create(path);
      partition.filename = path.getName();
    } else {
      // Write to a temporary file that will later get indexed
      File tempFile = File.createTempFile(String.format("part-%05d", id), "lindex");
      out = new BufferedOutputStream(new FileOutputStream(tempFile));
      tempFiles.put(id, tempFile);
    }
    partition.cellId = id;
    // Set the rectangle to the opposite universe so that we can keep
    // expanding it to get the MBR of this partition
    partition.set(Double.MAX_VALUE, Double.MAX_VALUE,
        -Double.MAX_VALUE, -Double.MAX_VALUE);
    // Store in the hashtables for further user
    partitionsOutput.put(id,  out);
    partitionsInfo.put(id, partition);
  }
  return out;
}


// 省略了一些异常处理
private void closePartition(final int id) {
  final Partition partitionInfo = partitionsInfo.get(id);
  final OutputStream outStream = partitionsOutput.get(id);
  final File tempFile = tempFiles.get(id);
  Thread closeThread = new Thread() {
    @Override
    public void run() {
      try {
        outStream.close();
        
        if (localIndexClass != null) {
          // Build a local index for that file
          try {
            LocalIndex<S> localIndex = localIndexClass.newInstance();
            localIndex.setup(conf);

            Path indexedFilePath = getPartitionFile(id);
            partitionInfo.filename = indexedFilePath.getName();
            // 这个函数的逻辑见后面
			// 将tempFile读到内存后解析，通过所有行数据的MBR构建R*树，然后写入HDFS上的索引文件
			localIndex.buildLocalIndex(tempFile, indexedFilePath, shape);
            // Temporary file no longer needed
            tempFile.delete();
          }
        }
        
        if (disjoint) {
          // If data is replicated, we need to shrink down the size of the
          // partition to keep partitions disjoint
          partitionInfo.set(partitionInfo.getIntersection(partitioner.getPartition(id)));
        }
        Text partitionText = partitionInfo.toText(new Text());
        synchronized (masterFile) {
          // Write partition information to the master file
          masterFile.write(partitionText.getBytes(), 0, partitionText.getLength());
          masterFile.write(NEW_LINE);
        }
      } 
```

# 空间索引文件的组织形式

R*树存储到文件的过程。实现中并没有像常规的R树，做一套支持动态添加删除功能的访问，而只是实现了一套类似序列化的存储方式。R树的实现并没有使用树的指针形式，而是用的数组。因此序列化过程重点分成3部分：

1. 写入具体的空间数据
2. 写入对空间数据索引的r树
3. 写入元数据

这个元数据放文件末尾的方式略微有点非主流。可以参考单元测试中的LocalIndexRecordReaderTest，涉及了对空间文件构建索引后存入文件，然后调用LocalIndexRecordReader读取文件。

```java
/**
 * <ul>
 *   <li>
 *     Data Entries: First, all data entries are written in an order that is consistent
 *   with the R-tree structure. This order will guarantee that all data entries
 *   under any node (from the root to leaves) will be adjacent in that order.
 *   </li>
 *   <li>
 *     Tree structure: This part contains the structure of the tree represented
 *   by its nodes. The nodes are stored in a level order traversal. This guarantees
 *   that the root will always be the first node and that all siblings will be
 *   stored consecutively. Each node contains the following information:
 *   (1) (n) Number of children as a 32-bit integer,
 *   (2) n Pairs of (child offset, MBR=(x1, y1, x2, y2). The child offset is
 *   the offset of the beginning of the child data (node or data entry) in the
 *   tree where 0 is the offset of the first data entry.
 *   </li>
 *   <li>
 *     Tree footer: This section contains some meta data about the tree as
 *     follows. All integers are 32-bits.
 *     (1) MBR of the root as (x1, y1, x2, y2),
 *     (2) Number of data entries,
 *     (3) Number of non-leaf nodes,
 *     (4) Number of leaf nodes,
 *     (5) Tree structure offset: offset of the beginning of the tree structure section
 *     (6) Footer offset: offset of the beginning of the footer as a 32-bit integer.
 *     (7) Tree size: Total tree size in bytes including data+structure+footer
 *   </li>
 *
 * </ul>
 * @param out
 * @throws IOException
 */
public void write(DataOutput out, Serializer ser) throws IOException {
  // Tree data: write the data entries in the tree order
  // Since we write the data first, we will have to traverse the tree twice
  // first time to visit and write the data entries in the tree order,
  // and second time to visit and write the tree nodes in the tree order.
  Deque<Integer> nodesToVisit = new ArrayDeque<Integer>();
  nodesToVisit.add(root);
  int[] objectOffsets = new int[numOfDataEntries() + numOfNodes()];
  // Keep track of the offset of each data object from the beginning of the
  // data section
  int dataOffset = 0;
  // Keep track of the offset of each node from the beginning of the tree
  // structure section
  // 看起来是一波广度优先遍历，按层处理结点
  int nodeOffset = 0;
  while (!nodesToVisit.isEmpty()) {
    int node = nodesToVisit.removeFirst();
    // The node is supposed to be written in this order.
    // Measure its offset and accumulate its size
    objectOffsets[node] = nodeOffset;
    nodeOffset += 4 + (4 + 8 * 4) * Node_size(node);

    if (isLeaf.get(node)) {
      // Leaf node, write the data entries in order
      for (int child : children.get(node)) {
        objectOffsets[child] = dataOffset;
        if (ser != null)
          dataOffset += ser.serialize(out, child);
      }
    } else {
      // Internal node, recursively traverse its children
      for (int child : children.get(node))
        nodesToVisit.addLast(child);
    }
  }
  // Update node offsets as they are written after the data entries
  for (int i = 0; i < numNodes; i++)
    objectOffsets[i + numEntries] += dataOffset;

  // Tree structure: Write the nodes in tree order
  nodesToVisit.add(root);
  while (!nodesToVisit.isEmpty()) {
    int node = nodesToVisit.removeFirst();
    // (1) Number of children
    out.writeInt(Node_size(node));
    for (int child : children.get(node)) {
      // (2) Write the offset of the child
      out.writeInt(objectOffsets[child]);
      // (3) Write the MBR of each child
      out.writeDouble(x1s[child]);
      out.writeDouble(y1s[child]);
      out.writeDouble(x2s[child]);
      out.writeDouble(y2s[child]);
    }
    // If node is internal, add its children to the nodes to be visited
    if (!isLeaf.get(node)) {
      for (int child : children.get(node))
        nodesToVisit.addLast(child);
    }
  }

  // Tree footer
  int footerOffset = dataOffset + nodeOffset;
  // (1) MBR of the root
  out.writeDouble(x1s[root]);
  out.writeDouble(y1s[root]);
  out.writeDouble(x2s[root]);
  out.writeDouble(y2s[root]);
  // (2) Number of data entries
  out.writeInt(numOfDataEntries());
  // (3) Number of non-leaf nodes
  out.writeInt((int) (numOfNodes() - isLeaf.countOnes()));
  // (4) Number of leaf nodes
  out.writeInt((int) isLeaf.countOnes());
  // (5) Offset of the tree structure section
  out.writeInt(dataOffset);
  // (6) Offset of the footer
  out.writeInt(footerOffset);
  // (7) Size of the entire tree
  int footerSize = 4 * 8 + 6 * 4;
  out.writeInt(footerOffset + footerSize);
}
```

以数组形式组织的R树，在读取时直接按文件顺序读取到数组中即可。对于元数据文件放在了文件尾，LocalIndexRecordReader用了一个这样的操作，seek到文件末尾的位置读取数据：

```java
in.seek(indexEnd - 4);
int indexSize = in.readInt();
long indexStart = indexEnd - indexSize - 4;
// ...
in.seek(indexStart);
localIndex.read(in, indexStart, indexEnd, stockShape);  // 读取并构建R树（相当于反序列化）
```
