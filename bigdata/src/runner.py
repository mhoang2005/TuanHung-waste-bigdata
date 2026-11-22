import json
import threading
import time
from urllib.request import Request, urlopen

from confluent_kafka import KafkaError, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from db import TOPICS, connect, log
from simulation import frame, seed_catalog

BROKER = {"bootstrap.servers": "kafka:9092"}
producer = Producer({**BROKER, "enable.idempotence": True, "delivery.timeout.ms": 10000, "linger.ms": 15})
send_lock = threading.Lock()
SEND_BATCH_SIZE = 550
SEND_RATE = 1100
MAX_KAFKA_BACKLOG = 16000


def prepare_topics():
    admin = AdminClient(BROKER)
    existing = admin.list_topics(timeout=6).topics
    missing = [NewTopic(t, num_partitions=4, replication_factor=1) for t in TOPICS if t not in existing]
    if not missing:
        return
    futures = admin.create_topics(missing)
    for future in futures.values():
        try:
            future.result(6)
        except KafkaException as error:
            if error.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
                raise


def publish(records):
    results = {}
    errors = []

    def delivered(index, err, msg):
        if err:
            errors.append(str(err))
        else:
            results[index] = [msg.topic(), msg.partition(), msg.offset()]

    with send_lock:
        for index, body in enumerate(records):
            payment = str(body.get("kind")).strip().lower() == "payment"
            topic = TOPICS[int(payment)]
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            key = (data.get("invoice") or body.get("subject")) if payment else body.get("subject")
            producer.produce(topic, key=str(key or "invalid").strip().upper(),
                             value=json.dumps(body, separators=(",", ":"), ensure_ascii=False),
                             on_delivery=lambda err,msg,i=index: delivered(i,err,msg))
        if producer.flush(12) or errors:
            raise RuntimeError(errors[0] if errors else "Kafka chưa xác nhận đủ sự kiện")
    return [results[i] for i in range(len(records))]


def pump():
    with connect() as conn:
        items = conn.execute("""
            SELECT id,body FROM outbox WHERE kafka_offset IS NULL AND due <= (SELECT clock FROM demo)
            ORDER BY id LIMIT %s
        """, (SEND_BATCH_SIZE,)).fetchall()
    if not items:
        return False
    started = time.monotonic()
    request = Request("http://127.0.0.1:8000/api/events",
                      data=json.dumps([item["body"] for item in items]).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=18) as response:
        ack = json.load(response)["offsets"]
    with connect() as conn:
        conn.execute("""
            UPDATE outbox o SET topic=x.t,part=x.p,kafka_offset=x.k
            FROM unnest(%s::bigint[],%s::text[],%s::int[],%s::bigint[]) AS x(id,t,p,k) WHERE o.id=x.id
        """, ([r["id"] for r in items], *map(list, zip(*ack))))
    time.sleep(max(0, len(items) / SEND_RATE - (time.monotonic() - started)))
    return True


def simulate():
    with connect() as conn:
        state = conn.execute("SELECT * FROM demo FOR UPDATE").fetchone()
        seed_catalog(conn, state["seed"])
        if state["mode"] != "running":
            return
        # Spark advances this cursor only after HDFS and the serving transaction succeed.
        conn.execute("""
            DELETE FROM outbox o USING kafka_cursor c
            WHERE o.topic=c.topic AND o.part=c.part AND o.kafka_offset<=c.kafka_offset
        """)
        pending = conn.execute("""
            SELECT count(*) AS n FROM (
              SELECT 1 FROM outbox o LEFT JOIN kafka_cursor c USING(topic,part)
              WHERE o.kafka_offset > coalesce(c.kafka_offset,-1) LIMIT %s
            ) pending
        """, (MAX_KAFKA_BACKLOG,)).fetchone()["n"]
        if pending >= MAX_KAFKA_BACKLOG:
            conn.execute("UPDATE demo SET waiting='pipeline' WHERE id")
            return
        sending = conn.execute("""
            SELECT EXISTS(SELECT 1 FROM outbox WHERE kafka_offset IS NULL AND due <= %s) AS pending
        """, (state["clock"],)).fetchone()["pending"]
        if sending:
            if state["waiting"] == "pipeline":
                conn.execute("UPDATE demo SET waiting=NULL WHERE id")
            return
        frame(conn, state)


def loop(stop, component, task, idle):
    last_error = None
    while not stop.is_set():
        try:
            active = task()
            if last_error:
                with connect() as conn:
                    log(conn,component,"info","Đã phục hồi")
            last_error = None
            if not active:
                stop.wait(idle)
        except Exception as error:
            message = str(error)[:500]
            if last_error != message:
                print(f"{component}: {message}", flush=True)
                try:
                    with connect() as conn:
                        log(conn,component,"error",message)
                except Exception:
                    pass
                last_error = message
            stop.wait(2)

