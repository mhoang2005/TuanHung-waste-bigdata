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
from runner import loop, prepare_topics, recreate_topics, simulate
from simulation import CATEGORIES

health_lock = threading.Lock()
health_cache = {"at": 0, "status": {}}


@asynccontextmanager
async def lifespan(_app):
    prepare_topics()
    stop = threading.Event()
    threading.Thread(target=loop, args=(stop, "simulator", simulate, 3.6), daemon=True).start()
    yield
    stop.set()


app = FastAPI(title="Trạm Điều Phối Rác Tuấn Hùng API", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory="/web"), name="assets")


@app.get("/")
def home():
    return FileResponse("/web/index.html")


@app.get("/api/control")
def status():
    with connect() as conn:
        state = conn.execute("SELECT mode,clock,step,scenario,waiting FROM demo").fetchone()
        state["clock"] = state["clock"].astimezone(VN)
        state["months"] = [str(r["month"]) for r in conn.execute("SELECT month FROM closed_month ORDER BY month")]
        has_base = conn.execute("SELECT to_regclass('base.demo') IS NOT NULL AS ok").fetchone()["ok"]
        state["base_step"] = conn.execute("SELECT step FROM base.demo").fetchone()["step"] if has_base else None
        return state


@app.post("/api/control/{action}")
def control(action: str):
    if action == "reset":
        with connect() as conn:
            if not conn.execute("SELECT to_regclass('base.demo') IS NOT NULL AS ok").fetchone()["ok"]:
                raise HTTPException(409, "Chưa có dữ liệu mốc chuẩn (baseline)")
            cur_w = conn.execute("SELECT waiting FROM demo").fetchone()["waiting"]
            if cur_w != "reset_kafka":
                conn.execute("UPDATE demo SET mode='paused', waiting='resetting' WHERE id")
        deadline = time.monotonic() + 90
        ready = (cur_w == "reset_kafka")
        while not ready and time.monotonic() < deadline:
            with connect() as conn:
                w = conn.execute("SELECT waiting FROM demo").fetchone()["waiting"]
            if w == "reset_kafka":
                ready = True
                break
            time.sleep(0.3)
        if not ready:
            with connect() as conn:
                conn.execute("UPDATE demo SET mode='paused', waiting=NULL WHERE id")
            raise HTTPException(504, "Spark chưa kịp phản hồi lệnh reset, thử lại sau vài giây")
        recreate_topics()
        with connect() as conn:
            conn.execute("UPDATE demo SET mode='paused', waiting=NULL WHERE id")
            log(conn, "control", "info", "Đã đặt lại dữ liệu demo về mốc chuẩn ban đầu")
        return status()

    states = {"start": "running", "pause": "paused"}
    if action not in states:
        raise HTTPException(404, "Lệnh demo không hợp lệ")
    if action == "start":
        with connect() as conn:
            cur = conn.execute("SELECT step, waiting FROM demo").fetchone()
            if cur["waiting"] == "resetting":
                raise HTTPException(409, "Hệ thống đang đặt lại dữ liệu, vui lòng đợi vài giây")
            need_reset = cur["waiting"] == "reset_kafka"
            if not need_reset and conn.execute("SELECT to_regclass('base.demo') IS NOT NULL AS ok").fetchone()["ok"]:
                base_step = conn.execute("SELECT step FROM base.demo").fetchone()["step"]
                need_reset = cur["step"] >= base_step + 180
        if need_reset:
            control("reset")
    with connect() as conn:
        cur = conn.execute("SELECT waiting FROM demo").fetchone()
        if cur["waiting"] in ("resetting", "reset_kafka"):
            raise HTTPException(409, "Hệ thống đang đặt lại dữ liệu, vui lòng đợi vài giây")
        changed = conn.execute("UPDATE demo SET mode=%s,waiting=NULL WHERE mode<>%s OR waiting IS NOT NULL RETURNING mode",
                               (states[action], states[action])).fetchone()
        if changed:
            log(conn, "control", "info", f"Chế độ demo: {states[action]}")
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
            mb = round(bean.get("CapacityUsed", 0) / (1024 * 1024), 1)
            components["HDFS"] = f"{bean['NumLiveDataNodes']}/2 DataNode · {bean.get('FilesTotal',0):,} file ({mb} MB) · RF=2"
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
        SELECT 0 AS outbox,
               coalesce(sum(greatest(0, p.kafka_offset - coalesce(c.kafka_offset,-1))), 0) AS unprocessed
        FROM kafka_produced p LEFT JOIN kafka_cursor c USING(topic,part)
    """).fetchone()
    logs = conn.execute("SELECT * FROM system_log ORDER BY id DESC LIMIT 50").fetchall()
    quality = conn.execute("SELECT * FROM quality_log ORDER BY received DESC,topic,part,kafka_offset DESC LIMIT 50").fetchall()
    return {"components":service_status(),"batches":batches,"total":totals,"queue":queue,
            "logs":logs,"quality":quality}


@app.get("/api/view/{page}")
def view(page: str, zone: int = Query(0, ge=0, le=60), category: str = "", house: str = "",
         month: date | None = None, filter: str = "", offset: int = Query(0, ge=0), pins: str = ""):
    if page not in queries.PAGES or category not in ("",*CATEGORIES):
        raise HTTPException(404,"Trang hoặc loại rác không hợp lệ")
    with connect() as conn:
        if page == "health":
            return health(conn)
        if month is None:
            month = conn.execute("""
              SELECT coalesce(max(month),'2026-10-01') AS month FROM closed_month
            """).fetchone()["month"]
        pin_list = [x.strip().upper() for x in pins.split(",") if x.strip()][:60] if pins else []
        return getattr(queries,page)(conn,dict(zone=zone,category=category,house=house.strip().upper(),
                                               month=month.replace(day=1),filter=filter,offset=offset,pins=pin_list))


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
    return f"""<!doctype html><html lang="vi"><meta charset="utf-8"><title>{escape(row['id'])} | Trạm Điều Phối Rác Tuấn Hùng</title>
    <style>body{{font:16px system-ui;max-width:760px;margin:50px auto;padding:20px;color:#14302b}}
    table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:12px;text-align:left}}
    @media print{{button{{display:none}}}}</style>
    <h1>Hóa đơn phí thu gom rác — Trạm Điều Phối Rác Tuấn Hùng</h1><p>Đơn vị điều phối & thu gom rác Tuấn Hùng · Mã HĐ: {escape(row['id'])}</p>
    <p>Hộ {escape(row['house'])} · Khu {row['zone']:02d} · Kỳ {row['month']:%m/%Y}</p>
    <p>Phát hành {row['issued']:%d/%m/%Y} · Ngày bắt đầu tạm ngưng nếu đủ điều kiện {row['suspend_from']:%d/%m/%Y}</p>
    <table><thead><tr><th>Loại rác</th><th>Lượt gom</th><th>Kg đã gom</th><th>đ/kg</th><th>Thành tiền (đ)</th></tr>
    </thead><tbody>{detail}</tbody></table>
    <p>Phí cơ bản {row['base_vnd']:,} đ</p><h2>Tổng cộng {row['total_vnd']:,} đ</h2>
    <p style="font-size:14px;color:#4a635d;border-top:1px dashed #ccc;padding-top:12px">
    <b>Quy định thanh toán:</b> Chuyển đúng số tiền kèm nội dung là mã hóa đơn <b>{escape(row['id'])}</b>.
    Hóa đơn không thanh toán hoặc thanh toán thiếu sẽ bị ngừng thu gom rác từ ngày <b>{row['suspend_from']:%d/%m/%Y}</b>.<br>
    <b>Liên hệ hoàn tiền thừa / xử lý chuyển sai:</b> Phòng Tài chính - Đối soát Trạm Điều Phối Rác Tuấn Hùng · SĐT: <b>0392196240</b> · Email: <b>doisoat@tuanhung.vn</b></p>
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
                 (SELECT coalesce(sum(greatest(0, p.kafka_offset - coalesce(c.kafka_offset,-1))), 0)
                    FROM kafka_produced p LEFT JOIN kafka_cursor c USING(topic,part)) AS pending
        """).fetchone()

