"""Kafka -> Spark on YARN -> HDFS + PostgreSQL, with explicit quality rules.

Three queries share one Spark application/executor pool: raw archive, quarantine,
and accepted events. Checkpoints must be retained; --run-id must change if a clean
checkpoint is intentionally created. Clean foreachBatch files overwrite a stable
batch path on retries; PostgreSQL commits outputs and a batch marker together.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import timezone
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap", default="192.168.200.11:9092,192.168.200.12:9092,192.168.200.13:9092")
    parser.add_argument("--topic", default="waste-events")
    parser.add_argument("--hdfs", default="hdfs://192.168.200.11:9000/waste")
    parser.add_argument("--reference", required=True, help="reference.json accessible to the driver")
    parser.add_argument("--pg-dsn", default=os.environ.get("WASTE_PG_DSN", ""))
    parser.add_argument("--run-id", default="v1")
    parser.add_argument("--trigger-seconds", type=int, default=15)
    parser.add_argument("--max-offsets", type=int, default=6000)
    parser.add_argument("--watermark", default="30 minutes")
    parser.add_argument("--available-now", action="store_true")
    parser.add_argument("--duration-seconds", type=int, default=0)
    parser.add_argument("--progress-file", default=os.environ.get("WASTE_PROGRESS_FILE", ""))
    return parser.parse_args()


def main():
    args = parse_args()
    from pyspark.sql import SparkSession, functions as F, types as T, Window
    from pyspark.sql.streaming import StreamingQueryListener
    spark = (SparkSession.builder.appName("SmartWaste-Streaming")
             .config("spark.sql.session.timeZone", "UTC")
             .config("spark.sql.shuffle.partitions", "6")
             .config("spark.sql.adaptive.enabled", "false").getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    ref = json.loads(Path(args.reference).read_text(encoding="utf-8"))
    bins = spark.createDataFrame([(b["bin_id"], b["area_id"], b["waste_type"], float(b["capacity_l"]))
                                 for b in ref["bins"]], "ref_bin_id string, area_id string, waste_type string, capacity_l double")
    raw = (spark.readStream.format("kafka").option("kafka.bootstrap.servers", args.bootstrap)
           .option("subscribe", args.topic).option("startingOffsets", "earliest")
           .option("maxOffsetsPerTrigger", args.max_offsets).option("failOnDataLoss", "true").load()
           .select(F.col("value").cast("string").alias("raw_json"),
                   F.col("key").cast("string").alias("kafka_key"), "topic", "partition", "offset",
                   F.col("timestamp").alias("kafka_timestamp"))
           .withColumn("ingested_at", F.current_timestamp())
           .withColumn("ingest_date", F.to_date("ingested_at")))
    fields = ["event_id", "bin_id", "event_type", "event_time", "schema_version", "fill_pct", "fill_unit",
              "weight_kg", "weight_unit", "added_l", "added_kg", "collected_l", "collected_kg",
              "battery_pct", "temperature_c", "household_id", "facility_id", "team_id"]
    schema = T.StructType([T.StructField(n, T.StringType(), True) for n in fields] +
                          [T.StructField("_corrupt_record", T.StringType(), True)])
    normalized = raw.withColumn("p", F.from_json("raw_json", schema, {"mode": "PERMISSIVE"}))
    normalized = normalized.select("*", "p.*").drop("p")
    normalized = (normalized.withColumn("bin_id", F.upper(F.trim("bin_id")))
                  .withColumn("event_id", F.trim("event_id"))
                  .withColumn("event_type", F.lower(F.trim("event_type")))
                  .withColumn("event_time_text", F.col("event_time"))
                  .withColumn("event_time", F.try_to_timestamp("event_time")))
    for name in ["fill_pct", "weight_kg", "added_l", "added_kg", "collected_l", "collected_kg", "battery_pct", "temperature_c"]:
        normalized = normalized.withColumn(name, F.expr(f"try_cast({name} as double)"))
    normalized = (normalized.withColumn("fill_pct", F.when(F.lower(F.col("fill_unit")) == "ratio", F.col("fill_pct") * 100).otherwise(F.col("fill_pct")))
                  .withColumn("weight_kg", F.when(F.lower(F.col("weight_unit")) == "g", F.col("weight_kg") / 1000).otherwise(F.col("weight_kg")))
                  .join(F.broadcast(bins), F.col("bin_id") == F.col("ref_bin_id"), "left")
                  .drop("ref_bin_id"))
    is_sensor = F.col("event_type") == "sensor_reading"
    is_pickup = F.col("event_type") == "pickup_completed"
    is_deposit = F.col("event_type") == "waste_deposit"
    bad = F.concat_ws(";",
        F.when(F.col("_corrupt_record").isNotNull(), "malformed_json"),
        F.when(F.col("event_id").isNull() | (F.length("event_id") == 0), "missing_event_id"),
        F.when(F.col("bin_id").isNull() | F.col("area_id").isNull(), "unknown_or_missing_bin"),
        F.when(F.col("event_time").isNull(), "invalid_event_time"),
        F.when(~F.coalesce(F.col("event_type").isin("sensor_reading", "pickup_completed", "waste_deposit"), F.lit(False)), "unknown_event_type"),
        F.when(is_sensor & (F.col("fill_pct").isNull() | (F.col("fill_pct") < 0) | (F.col("fill_pct") > 100) | F.isnan("fill_pct")), "invalid_fill_pct"),
        F.when((is_sensor | is_pickup) & (F.col("weight_kg").isNull() | (F.col("weight_kg") < 0) | (F.col("weight_kg") > 15000) | F.isnan("weight_kg")), "invalid_weight_kg"),
        F.when(is_pickup & (F.col("collected_kg").isNull() | (F.col("collected_kg") < 0) | F.isnan("collected_kg")), "invalid_collected_kg"),
        F.when(is_deposit & (F.col("added_kg").isNull() | (F.col("added_kg") < 0) | F.col("added_l").isNull() | (F.col("added_l") < 0) | F.isnan("added_kg") | F.isnan("added_l")), "invalid_deposit_quantity"),
        F.when(F.col("fill_unit").isNotNull() & ~F.lower(F.col("fill_unit")).isin("percent", "ratio"), "unknown_fill_unit"),
        F.when(F.col("weight_unit").isNotNull() & ~F.lower(F.col("weight_unit")).isin("kg", "g"), "unknown_weight_unit"))
    normalized = normalized.withColumn("quality_reason", bad).withColumn("event_date", F.to_date("event_time"))
    valid = (normalized.filter(F.col("quality_reason") == "")
             .withWatermark("event_time", args.watermark).dropDuplicatesWithinWatermark(["event_id"]))
    invalid = normalized.filter(F.col("quality_reason") != "")
    base = args.hdfs.rstrip("/")
    trigger = {"availableNow": True} if args.available_now else {"processingTime": f"{args.trigger_seconds} seconds"}
    queries = []

    if args.progress_file:
        class Progress(StreamingQueryListener):
            def onQueryStarted(self, event):
                pass
            def onQueryTerminated(self, event):
                pass
            def onQueryIdle(self, event):
                pass
            def onQueryProgress(self, event):
                progress = json.loads(event.progress.json)
                if progress.get("name") != f"waste-clean-{args.run_id}":
                    return
                output = dict(batch_id=progress["batchId"], num_input_rows=progress["numInputRows"],
                              processed_rows_per_second=progress["processedRowsPerSecond"],
                              batch_duration_ms=progress.get("durationMs", {}).get("triggerExecution", 0),
                              updated_at=time.time(), raw_progress=progress)
                target = Path(args.progress_file)
                target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.with_suffix(".tmp")
                temp.write_text(json.dumps(output), encoding="utf-8")
                temp.replace(target)
        spark.streams.addListener(Progress())

    def process_batch(frame, batch_id):
        cached = frame.persist()
        count = cached.count()
        if count == 0:
            cached.unpersist()
            return
        # Stable retry path. _SUCCESS is produced only after completed Spark output.
        path = f"{base}/clean/{args.run_id}/batch_id={batch_id:08d}"
        cached.drop("_corrupt_record").write.mode("overwrite").partitionBy("event_date", "waste_type").parquet(path)
        if not args.pg_dsn:
            cached.unpersist()
            return
        import psycopg
        run_key = f"stream-{args.run_id}-{batch_id:08d}"
        with psycopg.connect(args.pg_dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pipeline_runs WHERE run_id=%s AND status='success'", (run_key,))
                if cursor.fetchone():
                    cached.unpersist()
                    return
                cursor.execute("SELECT bin_id,alert_key FROM alerts WHERE active AND alert_type='full'")
                previous = {row[0]: row[1] for row in cursor.fetchall()}
                previous_rows = [(b["bin_id"], 1 if b["bin_id"] in previous else 0) for b in ref["bins"]]
                prior = spark.createDataFrame(previous_rows, "bin_id string, prior_state int")
                status_events = cached.filter(F.col("event_type").isin("sensor_reading", "pickup_completed"))
                ordered = Window.partitionBy("bin_id").orderBy("event_time", "partition", "offset")
                marked = (status_events.join(F.broadcast(prior), "bin_id")
                          .withColumn("marker", F.when(is_pickup | (F.col("fill_pct") < 70), 0)
                                      .when(F.col("fill_pct") >= 90, 1))
                          .withColumn("full_state", F.coalesce(F.last("marker", ignorenulls=True).over(ordered.rowsBetween(Window.unboundedPreceding, Window.currentRow)), F.col("prior_state")))
                          .withColumn("previous_state", F.coalesce(F.lag("full_state").over(ordered), F.col("prior_state"))))
                transitions = (marked.filter(F.col("full_state") != F.col("previous_state"))
                               .select("bin_id", "event_time", "event_id", "full_state", "offset")
                               .orderBy("event_time", "offset").collect())
                for row in transitions:
                    if row.full_state == 1:
                        key = f"full:{row.bin_id}:{row.event_id}"
                        cursor.execute("""INSERT INTO alerts(alert_key,bin_id,alert_type,opened_at,last_seen_at,detail)
                                          VALUES(%s,%s,'full',%s,%s,'fill >=90%%; close after pickup or fill <70%%')
                                          ON CONFLICT(alert_key) DO NOTHING""", (key, row.bin_id, row.event_time, row.event_time))
                    else:
                        cursor.execute("""UPDATE alerts SET active=false,closed_at=%s,last_seen_at=%s
                                          WHERE bin_id=%s AND alert_type='full' AND active AND opened_at<=%s""",
                                       (row.event_time, row.event_time, row.bin_id, row.event_time))
                latest = (marked.withColumn("rn", F.row_number().over(Window.partitionBy("bin_id").orderBy(F.col("event_time").desc(), F.col("offset").desc())))
                          .filter("rn=1").select("bin_id", "event_time", "fill_pct", "weight_kg", "full_state").collect())
                for row in latest:
                    cursor.execute("""INSERT INTO bin_status(bin_id,last_event_time,fill_pct,weight_kg,status)
                                      VALUES(%s,%s,%s,%s,%s) ON CONFLICT(bin_id) DO UPDATE SET
                                      last_event_time=EXCLUDED.last_event_time,fill_pct=EXCLUDED.fill_pct,
                                      weight_kg=EXCLUDED.weight_kg,status=EXCLUDED.status,updated_at=clock_timestamp()
                                      WHERE EXCLUDED.last_event_time>=bin_status.last_event_time""",
                                   (row.bin_id, row.event_time, row.fill_pct, row.weight_kg, "full" if row.full_state else "normal"))
                    cursor.execute("UPDATE alerts SET last_seen_at=GREATEST(last_seen_at,%s) WHERE bin_id=%s AND alert_type='full' AND active", (row.event_time, row.bin_id))
                cursor.execute("""INSERT INTO pipeline_runs(run_id,application_name,started_at,finished_at,status,accepted_rows,detail)
                                  VALUES(%s,'SmartWaste-Streaming',clock_timestamp(),clock_timestamp(),'success',%s,%s)
                                  ON CONFLICT(run_id) DO NOTHING""", (run_key, count, f"clean path={path}"))
        cached.unpersist()
        print(json.dumps(dict(batch_id=batch_id, accepted_rows=count, clean_path=path)), flush=True)

    queries.append(raw.writeStream.queryName(f"waste-raw-{args.run_id}").format("parquet")
                   .outputMode("append").partitionBy("ingest_date")
                   .option("path", f"{base}/raw/{args.run_id}")
                   .option("checkpointLocation", f"{base}/checkpoints/{args.run_id}/raw").trigger(**trigger).start())
    queries.append(invalid.drop("_corrupt_record").writeStream.queryName(f"waste-quarantine-{args.run_id}").format("parquet")
                   .outputMode("append").partitionBy("ingest_date")
                   .option("path", f"{base}/quarantine/{args.run_id}")
                   .option("checkpointLocation", f"{base}/checkpoints/{args.run_id}/quarantine").trigger(**trigger).start())
    queries.append(valid.writeStream.queryName(f"waste-clean-{args.run_id}").foreachBatch(process_batch)
                   .option("checkpointLocation", f"{base}/checkpoints/{args.run_id}/clean").trigger(**trigger).start())
    try:
        if args.available_now:
            for query in queries:
                query.awaitTermination()
        elif args.duration_seconds:
            deadline = time.monotonic() + args.duration_seconds
            while time.monotonic() < deadline and any(q.isActive for q in queries):
                spark.streams.awaitAnyTermination(1)
        else:
            spark.streams.awaitAnyTermination()
    finally:
        for query in queries:
            if query.isActive:
                query.stop()
        spark.stop()


if __name__ == "__main__":
    main()
