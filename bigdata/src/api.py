from contextlib import asynccontextmanager
from datetime import date
from html import escape
import json
import threading
import time
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from db import VN, connect, log
import queries
from runner import loop, prepare_topics, publish, pump, simulate
from simulation import CATEGORIES

health_lock = threading.Lock()
health_cache = {"at": 0, "status": {}}


@asynccontextmanager
async def lifespan(_app):
    prepare_topics()
    stop = threading.Event()
    for component, action, interval in [("simulator", simulate, 2.2), ("ingest", pump, .3)]:
        threading.Thread(target=loop, args=(stop, component, action, interval), daemon=True).start()
    yield
    stop.set()


app = FastAPI(title="Waste Big Data API", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory="/web"), name="assets")


@app.get("/")
def home():
    return FileResponse("/web/index.html")


@app.post("/api/events", status_code=202)
def events(records: list[dict]):
    if not 1 <= len(records) <= 2000:
        raise HTTPException(400,"Mỗi yêu cầu nhận 1–2.000 sự kiện")
    try:
        return {"offsets": publish(records)}
    except RuntimeError as error:
        raise HTTPException(503,str(error)) from error


@app.get("/api/control")
def status():
    with connect() as conn:
        state = conn.execute("SELECT mode,clock,step,scenario,waiting FROM demo").fetchone()
        state["clock"] = state["clock"].astimezone(VN)
        state["months"] = [str(r["month"]) for r in conn.execute("SELECT month FROM closed_month ORDER BY month")]
        return state


@app.post("/api/control/{action}")
def control(action: str):
    states = {"start":"running","pause":"paused","stop":"stopped"}
    if action not in states and action not in ("peak","incident"):
        raise HTTPException(404,"Lệnh demo không hợp lệ")
    with connect() as conn:
        if action in states:
            changed = conn.execute("UPDATE demo SET mode=%s,waiting=NULL WHERE mode<>%s RETURNING mode",
                                   (states[action],states[action])).fetchone()
            if changed:
                log(conn,"control","info",f"Chế độ demo: {states[action]}")
        else:
            conn.execute("UPDATE demo SET scenario=%s WHERE id",(action,))
            log(conn,"control","info",f"Kịch bản đã xếp cho khung kế tiếp: {action}")
    return status()


def read_json(url):
    with urlopen(url,timeout=1.5) as response:
        return json.load(response)


def service_status():
    with health_lock:
        if time.monotonic()-health_cache["at"] < 5:
            return health_cache["status"]
        components = {"PostgreSQL":"Đang kết nối","API":"Đang nhận yêu cầu"}
        try:
            from confluent_kafka.admin import AdminClient
            from runner import BROKER
            meta = AdminClient(BROKER).list_topics(timeout=1.5)
            components["Kafka"] = f"{len(meta.brokers)} broker · " + " / ".join(
                f"{len(meta.topics[t].partitions)} partition" for t in sorted(meta.topics)
                if t.startswith("waste-"))
        except Exception:
            components["Kafka"] = "Không kết nối"
        try:
            master = read_json("http://spark-master:8080/json/")
            workers = sum(worker["state"] == "ALIVE" for worker in master["workers"])
            components["Spark"] = f"{workers}/2 worker · {len(master['activeapps'])} ứng dụng"
        except Exception:
            components["Spark"] = "Không kết nối"
        try:
            bean = read_json("http://namenode:9870/jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState")["beans"][0]
            components["HDFS"] = f"{bean['NumLiveDataNodes']}/2 DataNode · RF mục tiêu 2"
        except Exception:
            components["HDFS"] = "Không kết nối"
        try:
            apps = read_json("http://stream:4040/api/v1/applications")
            executors = read_json(f"http://stream:4040/api/v1/applications/{apps[0]['id']}/executors")
            active = [x for x in executors if x["id"] != "driver" and x["isActive"]]
            components["Spark executor"] = " · ".join(
                f"#{e['id']} ({e['completedTasks']} task)" for e in active) or "Chờ cấp tài nguyên"
        except Exception:
            components["Spark executor"] = "Chờ ứng dụng"
        health_cache.update(at=time.monotonic(), status=components)
        return components


def health(conn):
    batches = conn.execute("SELECT * FROM microbatch ORDER BY id DESC LIMIT 25").fetchall()
    totals = conn.execute("""
        SELECT coalesce(sum(input),0) AS input,coalesce(sum(clean),0) AS clean,
          coalesce(sum(quarantine),0) AS rejected,coalesce(sum(duplicates),0) AS duplicates,
          coalesce(sum(late),0) AS late FROM microbatch
    """).fetchone()
    queue = conn.execute("""
        SELECT count(*) FILTER(WHERE o.kafka_offset IS NULL) AS outbox,
               count(*) FILTER(WHERE o.kafka_offset > coalesce(c.kafka_offset,-1)) AS unprocessed
        FROM outbox o LEFT JOIN kafka_cursor c USING(topic,part)
    """).fetchone()
    logs = conn.execute("SELECT * FROM system_log ORDER BY id DESC LIMIT 50").fetchall()
    quality = conn.execute("SELECT * FROM quality_log ORDER BY received DESC,topic,part,kafka_offset DESC LIMIT 50").fetchall()
    return {"components":service_status(),"batches":batches,"total":totals,"queue":queue,
            "logs":logs,"quality":quality}


@app.get("/api/view/{page}")
def view(page: str, zone: int = Query(0, ge=0, le=60), category: str = "", house: str = "",
         month: date | None = None, filter: str = "", offset: int = Query(0, ge=0)):
    if page not in queries.PAGES or category not in ("",*CATEGORIES):
        raise HTTPException(404,"Trang hoặc loại rác không hợp lệ")
    with connect() as conn:
        if page == "health":
            return health(conn)
        if month is None:
            month = conn.execute("""
              SELECT coalesce(max(month),'2026-10-01') AS month FROM closed_month
            """).fetchone()["month"]
        return getattr(queries,page)(conn,dict(zone=zone,category=category,house=house.strip().upper(),
                                               month=month.replace(day=1),filter=filter,offset=offset))


@app.get("/invoice/{invoice_id}", response_class=HTMLResponse)
def print_invoice(invoice_id: str):
    with connect() as conn:
        row = conn.execute("SELECT * FROM invoice_status WHERE id=%s",(invoice_id,)).fetchone()
    if not row:
        raise HTTPException(404,"Không tìm thấy hóa đơn")
    types = {"organic":"Hữu cơ","recycle":"Tái chế","other":"Còn lại"}
    detail = "".join(
        f"<tr><td>{types[x['category']]}</td><td>{x['pickups']}</td><td>{x['grams']/1000:,.3f}</td>"
        f"<td>{x['rate']:,}</td><td>{x['cost']:,}</td></tr>" for x in row["detail"])
    return f"""<!doctype html><html lang="vi"><meta charset="utf-8"><title>{escape(row['id'])}</title>
    <style>body{{font:16px system-ui;max-width:760px;margin:50px auto;padding:20px;color:#14302b}}
    table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:12px;text-align:left}}
    @media print{{button{{display:none}}}}</style>
    <h1>Hóa đơn phí thu gom</h1><p>Dữ liệu mô phỏng · {escape(row['id'])}</p>
    <p>Hộ {escape(row['house'])} · Khu {row['zone']:02d} · Kỳ {row['month']:%m/%Y}</p>
    <p>Phát hành {row['issued']:%d/%m/%Y} · Ngày bắt đầu tạm ngưng nếu đủ điều kiện {row['suspend_from']:%d/%m/%Y}</p>
    <table><thead><tr><th>Loại rác</th><th>Lượt gom</th><th>Kg đã gom</th><th>đ/kg</th><th>Thành tiền (đ)</th></tr>
    </thead><tbody>{detail}</tbody></table>
    <p>Phí cơ bản {row['base_vnd']:,} đ</p><h2>Tổng cộng {row['total_vnd']:,} đ</h2>
    <button onclick="print()">In / Lưu PDF</button></html>"""


@app.get("/api/audit")
def audit():
    with connect() as conn:
        return conn.execute("""
          SELECT (SELECT coalesce(sum(generated_g),0) FROM daily) AS generated_g,
                 (SELECT coalesce(sum(collected_g),0) FROM daily) AS collected_g,
                 (SELECT sum(grams) FROM physical_bin) AS bins_g,
                 (SELECT sum(load_g) FROM truck) AS truck_g,
                 (SELECT sum(dumped_g) FROM truck) AS dumped_g,
                 (SELECT count(*) FROM invoice) AS invoices,
                 (SELECT count(*) FROM payment_attempt WHERE status='matched') AS paid,
                 (SELECT count(*) FROM invoice_status WHERE status='overdue') AS overdue,
                 (SELECT count(*) FROM outbox o LEFT JOIN kafka_cursor c USING(topic,part)
                    WHERE o.kafka_offset IS NULL OR o.kafka_offset>coalesce(c.kafka_offset,-1)) AS pending
        """).fetchone()

