#!/bin/bash

echo link note to /content

# 解决windows上使用git bash时，默认调用了windows的bash命令问题，而没有使用git bash的find命令
# 获取bash的目录路径（git bash的路径，find命令也在此路径
BASH_DIR=$(dirname $(which bash))
export PATH=$BASH_DIR:$PATH

# 进入脚本所在的路径而非运行的路径
cd "$(dirname "$0")"

for noteType in life technical research
do
    noteTypePath=./$noteType
    toLnFileDir="../content/posts/"$noteType
    if [ ! -d $toLnFileDir ]; then
        mkdir $toLnFileDir
    fi
    rm -rf $toLnFileDir/*
    for file in $(find $noteTypePath -name "*.md" -type f)
    do
        if [ ${file: 0-9:9} = "/index.md" ]; then
                toLnFile=${file%/*} 
        else
                toLnFile=$file
        fi
        cp -r $toLnFile $toLnFileDir 
        echo DONE cp -r $toLnFile $toLnFileDir
    done
done


