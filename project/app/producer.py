"""Replay generated NDJSON to Kafka, keyed by bin_id, with durable acknowledgments."""
import argparse
import json
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--bootstrap", default="192.168.180.101:9092,192.168.180.102:9092,192.168.180.103:9092")
    parser.add_argument("--topic", default="waste-events")
    parser.add_argument("--rate", type=float, default=400, help="messages/second; zero means maximum")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--report", default="producer-result.json")
    args = parser.parse_args()
    from confluent_kafka import Producer
    producer = Producer({"bootstrap.servers": args.bootstrap, "client.id": "waste-python-simulator",
                         "enable.idempotence": True, "acks": "all", "compression.type": "lz4",
                         "linger.ms": 20, "delivery.timeout.ms": 120000})
    sent = 0
    delivered = 0
    failures = []
    partitions = {}
    started = time.monotonic()

    def delivery(err, msg):
        nonlocal delivered
        if err:
            failures.append(str(err))
        else:
            delivered += 1
            partitions[str(msg.partition())] = partitions.get(str(msg.partition()), 0) + 1

    with Path(args.input).open(encoding="utf-8") as source:
        for line in source:
            if args.limit and sent >= args.limit:
                break
            record = json.loads(line)
            while True:
                try:
                    producer.produce(args.topic, key=str(record.get("bin_id", "UNKNOWN")).encode(),
                                     value=line.strip().encode(), callback=delivery)
                    break
                except BufferError:
                    producer.poll(0.1)
            sent += 1
            producer.poll(0)
            if args.rate > 0:
                remaining = sent / args.rate - (time.monotonic() - started)
                if remaining > 0:
                    time.sleep(min(remaining, 0.1))
            if sent % 10000 == 0:
                print(json.dumps(dict(sent=sent, delivered=delivered, errors=len(failures))), flush=True)
    outstanding = producer.flush(125)
    elapsed = time.monotonic() - started
    result = dict(sent=sent, delivered=delivered, failures=failures[:20], outstanding=outstanding,
                  partition_counts=partitions, elapsed_seconds=round(elapsed, 3),
                  delivered_per_second=round(delivered / elapsed, 3) if elapsed else 0)
    Path(args.report).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if failures or outstanding or delivered != sent:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
