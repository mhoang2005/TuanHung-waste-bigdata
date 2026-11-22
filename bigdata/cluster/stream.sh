#!/bin/bash
set -e
exec /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --driver-memory 640m --executor-memory 640m \
  --conf spark.driver.host=stream \
  --conf spark.driver.bindAddress=0.0.0.0 \
  --conf spark.executor.cores=2 --conf spark.cores.max=4 \
  --conf spark.scheduler.minRegisteredResourcesRatio=1 \
  --conf spark.scheduler.maxRegisteredResourcesWaitingTime=35s \
  --conf spark.sql.shuffle.partitions=4 \
  --conf spark.sql.session.timeZone=UTC \
  --conf spark.hadoop.dfs.replication=2 \
  --conf spark.hadoop.dfs.client.use.datanode.hostname=true \
  --jars "$(find /opt/connectors -name '*.jar' -printf '%p,' | sed 's/,$//')" /code/stream.py

