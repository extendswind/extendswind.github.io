#!/bin/bash

echo link note to /content

# 进入脚本所在的路径而非运行的路径
cd "$(dirname "$0")"

for noteType in life technical research
do
    path=./$noteType
    lnFile="../content/posts/"$noteType
    rm -f $lnFile/*
    for file in $(find $path -name "*.md" -type f)
    do
        if [ ${file: 0-9:9} = "/index.md" ]; then
                toLnFile="../../../myNote/"${file%/*} 
        else
                toLnFile="../../../myNote/"$file
        fi
        ln -s $toLnFile $lnFile # 可以考虑用copy
    done
done


