"""Transactional world state and a durable outbox. All weights are integer grams."""
import math
import random
from collections import defaultdict
from datetime import timedelta

from psycopg.types.json import Jsonb

from db import VN, WATCH_BINS, WATCH_IOT, log
from finance import close_period, simulated_payments

WATCH_SET = set(WATCH_BINS)

CATEGORIES = {"organic": (330, 220, 20), "recycle": (95, 65, 30), "other": (145, 135, 20)}
CODES = {"organic": "O", "recycle": "R", "other": "C"}
FRAME = timedelta(hours=12)
MAX_BLACKOUTS = 19
TRIPS_PER_FRAME = {"organic": 4, "recycle": 2, "other": 2}


def shift_start(start, zone, category, step):
    cat_idx = 0 if category == "organic" else 1 if category == "other" else 2
    slot = (zone * 31 + step * 17 + cat_idx * 13) % 100
    if slot < 20:
        # 20% gom rải rác ở các khung giờ thấp điểm (đêm khuya, trưa chiều, tối muộn)
        off_hours = (0.55, 1.25, 2.2, 3.2, 4.15, 8.2, 9.2, 10.1, 10.8) if start.hour == 0 else (
            0.55, 1.25, 2.2, 3.2, 4.15, 9.15, 10.1, 10.75)
        minutes = round(off_hours[(zone + step + cat_idx) % len(off_hours)] * 60)
        return start + timedelta(minutes=minutes)
    cat_shift = cat_idx * 18
    if start.hour == 0:
        peak_min = (zone * 13 + cat_shift) % 85
    else:
        peak_min = (zone * 17 + cat_shift * 2) % 175
    return start + timedelta(hours=5, minutes=peak_min)


def seed_catalog(conn, seed):
    if conn.execute("SELECT 1 FROM household LIMIT 1").fetchone():
        return
    rng = random.Random(seed)
    with conn.cursor() as cursor:
        houses = [(f"H-{i:04d}", (i-1)//60+1, rng.choices([1,2,3,4,5,6],[1,3,5,6,3,1])[0],
                   round(rng.uniform(.1,2),3), round(rng.uniform(.1,2),3), round(rng.uniform(.65,1.35),3))
                  for i in range(1,3601)]
        cursor.executemany("INSERT INTO household VALUES(%s,%s,%s,%s,%s,%s)", houses)
        cursor.executemany("INSERT INTO bin(id,house,category,capacity_l,density_g_l) VALUES(%s,%s,%s,%s,%s)",
                           [(f"{h[0]}-{CODES[k]}",h[0],k,v[2],v[1]) for h in houses for k,v in CATEGORIES.items()])
        cursor.execute("INSERT INTO physical_bin(bin,last_pickup) SELECT id, (SELECT clock FROM demo) FROM bin")
        cursor.executemany("INSERT INTO truck(id,zone,category,capacity_g) VALUES(%s,%s,%s,%s)",
                           [(f"X-{zone:02d}-{CODES[cat]}",zone,cat,capacity)
                            for zone in range(1,61) for cat,capacity in zip(CATEGORIES,(22000,13000,18000))])
    log(conn, "simulator", "info", "Đã nạp danh mục 60 khu, 3.600 hộ, 10.800 thùng và 180 xe nhỏ")


def backlog(conn):
    return conn.execute("""
        SELECT EXISTS(
            SELECT 1 FROM kafka_produced p LEFT JOIN kafka_cursor c USING(topic,part)
            WHERE p.kafka_offset > coalesce(c.kafka_offset,-1)
        ) AS waiting
    """).fetchone()["waiting"]


def frame(conn, state, publish):
    start = state["clock"].astimezone(VN)
    end = start + FRAME
    day = start.date()
    if day.day == 1 and start.hour == 0:
        if backlog(conn):
            conn.execute("UPDATE demo SET waiting='closing_period' WHERE id")
            return
        period = (day - timedelta(days=1)).replace(day=1)
        if not conn.execute("SELECT 1 FROM closed_month WHERE month=%s", (period,)).fetchone():
            close_period(conn, day)

    step = state["step"]
    rng = random.Random(f'{state["seed"]}/{step}')
    output = []
    last = end - timedelta(seconds=1)

    def emit(kind, subject, occurred, amount=None, unit=None, capacity=None, data=None, delay=False):
        emitted = occurred + timedelta(hours=5) if delay else occurred
        event = {"id": f"E-{step:06d}-{len(output):06d}", "kind": kind, "subject": subject,
                 "at": occurred.isoformat(), "emitted": emitted.isoformat(), "amount": amount, "unit": unit,
                 "capacity_g": capacity, "data": data}
        output.append(event)
        return event

    bins = conn.execute("""
        SELECT b.*,h.zone,h.people,h.x,h.y,h.profile,p.grams,p.last_pickup,p.blackout_until,
               s.grams AS measured,s.occurred AS measured_at
        FROM bin b JOIN household h ON h.id=b.house JOIN physical_bin p ON p.bin=b.id
        LEFT JOIN bin_state s ON s.bin=b.id ORDER BY b.id
    """).fetchall()
    by_id = {b["id"]: b for b in bins}
    candidate = defaultdict(list)
    active = {row["bin"] for row in conn.execute("SELECT bin FROM task WHERE status IN ('assigned','collecting')")}
    blocked = {row["house"] for row in conn.execute("SELECT DISTINCT house FROM invoice_status WHERE status='overdue'")}
    before = {b["id"]: (b["grams"],b["last_pickup"],b["blackout_until"]) for b in bins}
    active_blackouts = sum(bool(b["blackout_until"] and b["blackout_until"] > start) for b in bins)
    auto_incident = (step % 2 == 1)
    iot_target = WATCH_IOT[(step // 2) % len(WATCH_IOT)]
    auto_peak = (step % 6 == 0)
    fair = auto_peak or (day.day == 7 and day.month == 11)
    if step == 0:
        log(conn, "simulator", "info", "Bắt đầu kịch bản demo tổng hợp từ 30/10.")
    for b in bins:
        capacity = b["capacity_l"]*b["density_g_l"]
        category = b["category"]
        is_watch = b["id"] in WATCH_SET
        queued = False
        if b["house"] not in blocked and b["id"] not in active and b["measured"] and b["grams"]:
            age = (start-b["last_pickup"]).total_seconds()/3600
            fill = b["measured"]*100/capacity
            if b["measured_at"] >= b["last_pickup"] and (fill >= 75 or age >= b["interval_h"]):
                b["priority"] = min(fill, 160)*.14 + min(age/b["interval_h"],3)*5 + min(b["measured"]/1000,10)
                if is_watch:
                    b["priority"] += 12
                candidate[b["zone"],category].append(b)
                queued = True
        chance = {"organic": .58,"recycle": .32,"other": .42}[category]
        chance *= (1.12 if start.hour else .8) * (1.1 if start.weekday() >= 5 else 1)
        boost = 2.0 if fair and b["zone"] <= 6 else 1
        if is_watch:
            boost *= 2.2 if category == "organic" else 2.8
        # Leave morning/evening peak collection windows after household deposits.
        truck_at = shift_start(start, b["zone"], category, step)
        max_dep = max(600, min(17_400, int((truck_at - start).total_seconds()) - 300))
        at = start + timedelta(seconds=rng.randint(60, max_dep))
        max_grams = round(capacity * 1.2)
        deposit_prob = 0.96 if is_watch else min(.92, chance * boost)
        if b["grams"] < max_grams and rng.random() < deposit_prob:
            raw_mass = max(5, round(rng.gammavariate(3,1/3)*CATEGORIES[category][0]*b["people"]
                                    *float(b["profile"])*boost*(.83 + b["zone"]%7*.05)))
            if is_watch:
                raw_mass = max(raw_mass, round(capacity * rng.uniform(0.22, 0.42)))
            mass = min(raw_mass, max_grams - b["grams"])
            b["grams"] += mass
            emit("deposit", b["id"], at, mass, "g")
        if b["blackout_until"] and b["blackout_until"] > start:
            continue
        if b["blackout_until"]:
            emit("signal",b["id"],at,data={"state":"restored"})
            b["blackout_until"] = None
        watch_blackout = auto_incident and b["id"] == iot_target
        forced_blackout = auto_incident and (b["id"] not in WATCH_SET and b["id"].endswith("1-O") and b["zone"] <= 8)
        random_blackout = b["id"] not in WATCH_SET and rng.random() < .00008
        if watch_blackout or ((forced_blackout and active_blackouts < MAX_BLACKOUTS - 1) or
                              (random_blackout and active_blackouts < MAX_BLACKOUTS - 2)):
            b["blackout_until"] = end if b["id"] in WATCH_SET else end + timedelta(hours=24)
            active_blackouts += 1
            emit("signal",b["id"],at,data={"state":"lost"})
            continue
        if is_watch or rng.random() < .26 or (b["grams"] >= capacity*.75 and rng.random() < .45):
            sensor_cap = min(last, truck_at - timedelta(seconds=30))
            sample_at = min(sensor_cap, at + timedelta(seconds=rng.randint(20,1800)))
            kg = rng.random() < .3
            sample = emit("sensor", b["id"], sample_at, b["grams"]/1000 if kg else b["grams"],
                          "kg" if kg else "g", capacity, delay=not is_watch and rng.random() < .008)
            anomaly = 1.0 if is_watch else rng.random()
            if anomaly < .003:
                sample["amount"] = None
            elif anomaly < .006:
                sample["unit"] = "lb"
            elif anomaly < .014:
                output.append(sample.copy())
            if is_watch and not queued and b["house"] not in blocked and b["id"] not in active and b["grams"]:
                fill_now = b["grams"]*100/capacity
                age_now = (truck_at - b["last_pickup"]).total_seconds()/3600
                if fill_now >= 75 or age_now >= b["interval_h"]:
                    b["priority"] = min(fill_now, 160)*.14 + min(age_now/b["interval_h"],3)*5 + min(b["grams"]/1000,10) + 12
                    candidate[b["zone"],category].append(b)
                    queued = True

    route(conn, start, end, "incident" if auto_incident else "normal", by_id, candidate, blocked, emit, step)
    if auto_peak:
        available = [b for b in bins if not b["blackout_until"]]
        for n,b in enumerate(available[:3600]):
            emit("sensor", b["id"], last-timedelta(seconds=n % 60), b["grams"], "g",
                 b["capacity_l"]*b["density_g_l"], data={"state":"peak"})
        log(conn,"simulator","info","Cao điểm tự động: bổ sung 3.600 số đo cảm biến đồng loạt")

    simulated_payments(conn,start,end,emit,step)
    ordered_events = sorted(output, key=lambda e: (e["at"], e["id"]))
    offsets = publish(ordered_events)
    with conn.cursor() as cur:
        cur.executemany("UPDATE physical_bin SET grams=%s,last_pickup=%s,blackout_until=%s WHERE bin=%s",
                        [(*after,b["id"]) for b in bins
                         if (after := (b["grams"],b["last_pickup"],b["blackout_until"])) != before[b["id"]]])
        if offsets:
            cur.executemany("""
                INSERT INTO kafka_produced VALUES(%s,%s,%s)
                ON CONFLICT(topic,part) DO UPDATE SET kafka_offset=greatest(excluded.kafka_offset,kafka_produced.kafka_offset)
            """, [(topic, part, offset) for (topic, part), offset in offsets.items()])
    conn.execute("UPDATE demo SET clock=%s,step=step+1,waiting=NULL,scenario='normal' WHERE id", (end,))


def distance(x,y,a,b):
    return math.hypot(float(x-a),float(y-b))


def route(conn,start,end,scenario,bins,candidates,blocked,emit,step=0):
    tasks = defaultdict(list)
    for task in conn.execute("SELECT * FROM task WHERE status='assigned' ORDER BY rank"):
        tasks[task["truck"]].append(task)
    trucks = conn.execute("SELECT * FROM truck WHERE status<>'standby' ORDER BY id").fetchall()
    forced = scenario == "incident"
    target_zone = (step // 2) % 10 + 1
    target_cat = "other" if target_zone in (3, 6, 9) else "organic"
    for t in trucks:
        vehicle = t["id"]
        at = shift_start(start, t["zone"], t["category"], step)
        queue = tasks[vehicle]
        changed = t["status"] == "broken"
        if changed:
            if start < t["recover_at"]:
                continue
            t.update(status="idle",recover_at=None)
            emit("vehicle",vehicle,at,data={"state":"recovered"})
            log(conn,"routing","info",f"{vehicle} đã hồi phục và tiếp tục điều phối")
        options = candidates[t["zone"],t["category"]]
        for _ in range(TRIPS_PER_FRAME[t["category"]]):
            if not queue and not options and not t["load_g"]:
                break
            assign_stops(conn,t,queue,options,bins,at,emit)
            hit_incident = forced and ((t["zone"], t["category"]) == (target_zone, target_cat) or t["zone"] > target_zone)
            at = collect_trip(conn,t,queue,bins,blocked,at,end,hit_incident,emit)
            changed = True
            if t["status"] == "broken":
                forced = False
                break
        if changed:
            conn.execute("""
                UPDATE truck SET load_g=%(load_g)s,dumped_g=%(dumped_g)s,km=%(km)s,trips=%(trips)s,
                    x=%(x)s,y=%(y)s,status=%(status)s,recover_at=%(recover_at)s,broken_h=%(broken_h)s WHERE id=%(id)s
            """,t)


def assign_stops(conn,truck,queue,options,bins,at,emit):
    origin = bins[queue[-1]["bin"]] if queue else truck
    x,y = origin["x"],origin["y"]
    for _ in range(min(5-len(queue),len(options))):
        b = max(options,key=lambda b:(b["priority"]-3*distance(x,y,b["x"],b["y"]),b["id"]))
        options.remove(b)
        task = conn.execute("""
            INSERT INTO task(truck,bin,status,rank,created_at) VALUES(%s,%s,'assigned',%s,%s)
            RETURNING id,bin,rank
        """,(truck["id"],b["id"],queue[-1]["rank"]+1 if queue else 0,at)).fetchone()
        queue.append(task)
        emit("vehicle",truck["id"],at,data={"state":"assigned","bin":b["id"]})
        x,y = b["x"],b["y"]


def collect_trip(conn,t,queue,bins,blocked,at,end,forced,emit):
    vehicle = t["id"]
    picked_up = False
    while queue:
        job = queue[0]
        b = bins[job["bin"]]
        if b["house"] in blocked:
            conn.execute("UPDATE task SET status='suspended',finished_at=%s WHERE id=%s",(at,job["id"]))
            queue.pop(0)
            continue
        if forced and picked_up:
            t.update(status="broken",recover_at=end,broken_h=t["broken_h"]+12)
            emit("vehicle",vehicle,at,data={"state":"broken","reason":"simulated_fault","bin":b["id"]})
            log(conn,"routing","warning",f"{vehicle} hỏng; hàng trên xe được giữ lại, điểm chưa gom được mở lại")
            conn.execute("UPDATE task SET status='requeued',finished_at=%s WHERE truck=%s AND status='assigned'",
                         (at,vehicle))
            return at
        available = t["capacity_g"]-t["load_g"]
        if not available:
            break
        queue.pop(0)
        km = round(distance(t["x"],t["y"],b["x"],b["y"]),3)
        t["km"] += type(t["km"])(str(km))
        t.update(x=b["x"],y=b["y"])
        at += timedelta(minutes=3)
        emit("vehicle",vehicle,at,data={"state":"arrived","bin":b["id"],"km":km})
        collected = min(b["grams"],available)
        if not collected:
            conn.execute("UPDATE task SET status='empty',finished_at=%s WHERE id=%s",(at,job["id"]))
            continue
        emit("vehicle",vehicle,at+timedelta(seconds=1),data={"state":"collecting","bin":b["id"]})
        at += timedelta(seconds=20)
        b["grams"] -= collected
        b["last_pickup"] = at
        t["load_g"] += collected
        picked_up = True
        status = "partial" if b["grams"] else "completed"
        emit("pickup",b["id"],at,collected,"g",data={"truck":vehicle,"state":status})
        if not b["blackout_until"]:
            emit("sensor",b["id"],at+timedelta(seconds=1),b["grams"],"g",b["capacity_l"]*b["density_g_l"])
        conn.execute("""
            UPDATE task SET status=%s,started_at=%s,finished_at=%s,collected_g=%s WHERE id=%s
        """,(status,at,at+timedelta(seconds=30),collected,job["id"]))
    if t["load_g"]:
        km = round(math.hypot(float(t["x"]),float(t["y"])),3)
        t["km"] += type(t["km"])(str(km))
        at += timedelta(minutes=15)
        emit("vehicle",vehicle,at,data={"state":"returning","km":km})
        at += timedelta(minutes=5)
        emit("dump",vehicle,at,t["load_g"],"g",data={"state":"unloaded"})
        t.update(dumped_g=t["dumped_g"]+t["load_g"],load_g=0,trips=t["trips"]+1,x=0,y=0)
    return at

