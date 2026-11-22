#!/bin/bash
set -e
if [ "$1" = namenode ] && [ ! -f /data/name/current/VERSION ]; then
  hdfs namenode -format -nonInteractive
fi
exec hdfs "$1"

