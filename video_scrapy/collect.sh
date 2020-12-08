#!/bin/bash

INTERVAL=5
PREFIX=$INTERVAL-sec-status
# 删除该文件即可退出
RUNFILE=/opt/videoSearchSystem/video_scrapy/collect_running
while test -e $RUNFILE; do
    exists = $(cat movie.log | grep -c 存在)
    update = $(cat movie.log | grep -c 更新)
    insert = $(cat movie.log | grep -c 插入)
    # sleep=$(date +%s.%N | awk "{print $INTERVAL - (\$1 % $INTERVAL)}")
    sleep $INTERVAL
    echo "$exists $update $insert" >> $PREFIX-scrapy-status
done
echo Exiting because $RUNFILE does not exist.
