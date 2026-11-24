import json
import threading
import time

from confluent_kafka import KafkaError, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from db import TOPICS, connect, log
from simulation import frame, seed_catalog

BROKER = {"bootstrap.servers": "kafka:9092"}
producer = Producer({**BROKER, "enable.idempotence": True, "delivery.timeout.ms": 15000, "linger.ms": 15})
send_lock = threading.Lock()
MAX_KAFKA_BACKLOG = 40000


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


def recreate_topics():
    global producer
    admin = AdminClient(BROKER)
    existing = admin.list_topics(timeout=6).topics
    present = [t for t in TOPICS if t in existing]
    if present:
        futures = admin.delete_topics(present, operation_timeout=10)
        for future in futures.values():
            try:
                future.result(10)
            except KafkaException as error:
                if error.args[0].code() != KafkaError.UNKNOWN_TOPIC_OR_PART:
                    raise
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        current = admin.list_topics(timeout=5).topics
        if not any(t in current for t in TOPICS):
            break
        time.sleep(0.3)
    while True:
        try:
            prepare_topics()
            with send_lock:
                producer = Producer({**BROKER, "enable.idempotence": True, "delivery.timeout.ms": 15000, "linger.ms": 15})
            return
        except KafkaException as error:
            if error.args[0].code() == KafkaError.TOPIC_ALREADY_EXISTS and time.monotonic() < deadline:
                time.sleep(0.3)
                continue
            raise


def publish(records):
    if not records:
        return {}
    offsets = {}
    errors = []

    def delivered(err, msg):
        if err:
            errors.append(str(err))
        else:
            key = (msg.topic(), msg.partition())
            if msg.offset() > offsets.get(key, -1):
                offsets[key] = msg.offset()

    with send_lock:
        for index, body in enumerate(records):
            payment = str(body.get("kind")).strip().lower() == "payment"
            topic = TOPICS[int(payment)]
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            key = (data.get("invoice") or body.get("subject")) if payment else body.get("subject")
            producer.produce(topic, key=str(key or "invalid").strip().upper(),
                             value=json.dumps(body, separators=(",", ":"), ensure_ascii=False),
                             on_delivery=delivered)
            if index % 1000 == 999:
                producer.poll(0)
        if producer.flush(15) or errors:
            raise RuntimeError(errors[0] if errors else "Kafka chưa xác nhận đủ sự kiện")
    return offsets


def simulate():
    with connect() as conn:
        state = conn.execute("SELECT * FROM demo FOR UPDATE").fetchone()
        if state["waiting"] in ("resetting", "reset_kafka"):
            return
        seed_catalog(conn, state["seed"])
        if state["mode"] != "running":
            return
        if conn.execute("SELECT to_regclass('base.demo') IS NOT NULL AS ok").fetchone()["ok"]:
            base_step = conn.execute("SELECT step FROM base.demo").fetchone()["step"]
            if state["step"] >= base_step + 180:
                conn.execute("UPDATE demo SET mode='paused', waiting='cycle_done' WHERE id")
                log(conn, "control", "info", "Đã hoàn tất 1 chu kỳ demo (90 ngày mô phỏng); bấm 'Đặt lại demo' hoặc 'Bật demo' để chạy chu kỳ mới")
                return
        pending = conn.execute("""
            SELECT coalesce(sum(greatest(0, p.kafka_offset - coalesce(c.kafka_offset, -1))), 0) AS n
            FROM kafka_produced p LEFT JOIN kafka_cursor c USING(topic, part)
        """).fetchone()["n"]
        if pending >= MAX_KAFKA_BACKLOG:
            conn.execute("UPDATE demo SET waiting='pipeline' WHERE id")
            return
        if state["waiting"] == "pipeline":
            conn.execute("UPDATE demo SET waiting=NULL WHERE id")
        frame(conn, state, publish)


def loop(stop, component, task, idle):
    last_error = None
    while not stop.is_set():
        try:
            active = task()
            if last_error:
                with connect() as conn:
                    log(conn, component, "info", "Đã phục hồi")
            last_error = None
            if not active:
                stop.wait(idle)
        except Exception as error:
            message = str(error)[:500]
            if last_error != message:
                print(f"{component}: {message}", flush=True)
                try:
                    with connect() as conn:
                        log(conn, component, "error", message)
                except Exception:
                    pass
                last_error = message
            stop.wait(2)
