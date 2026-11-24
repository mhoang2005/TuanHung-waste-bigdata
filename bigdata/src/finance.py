from datetime import date, datetime, timedelta

from db import VN, log


def next_month(day):
    return (day.replace(day=28) + timedelta(days=4)).replace(day=1)


def close_period(conn, day):
    month = (day - timedelta(days=1)).replace(day=1)
    conn.execute("INSERT INTO closed_month VALUES (%s, %s::date::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')",
                 (month, day))
    conn.execute("""
        WITH totals AS (
          SELECT b.id,b.house,b.category,coalesce(sum(d.collected_g),0) AS grams,
                 coalesce(sum(d.pickups),0) AS pickups
          FROM bin b LEFT JOIN daily d ON d.bin=b.id AND d.day >= %s AND d.day < %s
          GROUP BY b.id
        ), costs AS (
          SELECT t.*,p.vnd_kg,round(t.grams*p.vnd_kg/1000.0)::int AS cost
          FROM totals t JOIN tariff p USING(category)
        )
        INSERT INTO invoice
        SELECT 'HD-' || to_char(%s::date,'YYYYMM') || '-' || house,house,%s,%s,
               CASE WHEN substring(house from '[0-9]+$')::int %% 100 IN (0, 19, 20, 40)
                         AND house NOT IN ('H-0120', 'H-0340') THEN %s::date
                    ELSE %s END,
               (SELECT base_vnd FROM fee_config),
               jsonb_agg(jsonb_build_object('category',category,'grams',grams,'pickups',pickups,
                          'rate',vnd_kg,'cost',cost) ORDER BY category),
               (SELECT base_vnd FROM fee_config) + sum(cost)
        FROM costs GROUP BY house
    """, (month, day, month, month, day, day, next_month(day)))
    make_plan(conn, month, day)
    log(conn, "billing", "info", f"Đã chốt kỳ {month:%Y-%m}; phát hành hóa đơn cho từng hộ")
    return month


def make_plan(conn, month, day):
    active_days = max(1, (day - max(month, date(2026, 10, 30))).days)
    conn.execute("""
        WITH history AS (
          SELECT bin,sum(generated_g) AS generated,sum(pickups) AS pickups FROM daily
          WHERE day >= %s AND day < %s GROUP BY bin
        ), demand AS (
          SELECT b.*,p.grams,
            coalesce(history.generated,0)*b.interval_h/(%s*24.0*b.capacity_l*b.density_g_l) AS ratio,
            coalesce(history.pickups,0) AS pickups,
            round(coalesce(history.generated,0)*%s::numeric/%s)::bigint AS forecast_g
          FROM bin b JOIN physical_bin p ON p.bin=b.id LEFT JOIN history ON history.bin=b.id
        ), proposal AS (
          SELECT *,CASE WHEN ratio > .80 THEN least(100,capacity_l+5)
                        WHEN ratio < .25 THEN greatest(10,capacity_l-5)
                        ELSE capacity_l END AS suggested_l,
                   CASE WHEN ratio > .80 THEN greatest(24,interval_h-24)
                        WHEN ratio < .25 THEN least(120,interval_h+24) ELSE interval_h END AS suggested_h
          FROM demand
        )
        INSERT INTO plan
        SELECT %s,id,%s,capacity_l,suggested_l,interval_h,suggested_h,
            CASE WHEN ratio > .80 THEN 'Lượng phát sinh cao'
                 WHEN ratio < .25 THEN 'Lượng phát sinh thấp' ELSE 'Nhu cầu ổn định' END
            || ' · ' || pickups || ' lượt gom trong kỳ',
            CASE WHEN grams > suggested_l*density_g_l AND suggested_l < capacity_l THEN 'blocked_capacity'
                 WHEN (capacity_l,interval_h) = (suggested_l,suggested_h) THEN 'unchanged'
                 ELSE 'applied' END, forecast_g
        FROM proposal
        ON CONFLICT(month,bin) DO NOTHING
    """, (month, day, active_days, (next_month(day)-day).days,
          active_days, month, day))
    conn.execute("""
        UPDATE bin b SET capacity_l=p.after_l,interval_h=p.after_h
        FROM plan p WHERE p.bin=b.id AND p.month=%s AND p.result='applied'
    """, (month,))
    conn.execute("""
        WITH demand AS (
          SELECT h.zone,b.category,sum(d.collected_g) AS grams,sum(d.pickups) AS stops
          FROM daily d JOIN bin b ON b.id=d.bin JOIN household h ON h.id=b.house
          WHERE d.day >= %s AND d.day < %s GROUP BY h.zone,b.category
        ), trips AS (
          SELECT t.zone,t.category,count(*) AS n
          FROM event e JOIN truck t ON e.subject=t.id
          WHERE kind='dump'
            AND (e.occurred AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= %s
            AND (e.occurred AT TIME ZONE 'Asia/Ho_Chi_Minh')::date < %s
          GROUP BY t.zone,t.category
        ), current_fleet AS (
          SELECT zone,category,count(*) FILTER(WHERE status<>'standby') AS active_cnt
          FROM truck GROUP BY zone,category
        )
        INSERT INTO fleet_plan
        SELECT %s,d.zone,d.category,coalesce(c.active_cnt,1),
          CASE WHEN coalesce(t.n,0) > %s*4.8 OR (d.zone <= 4 AND d.category='organic') THEN 2 ELSE 1 END,
          coalesce(t.n,0),d.grams
        FROM demand d LEFT JOIN trips t USING(zone,category)
        LEFT JOIN current_fleet c USING(zone,category)
        ON CONFLICT(month,zone,category) DO NOTHING
    """, (month, day, month, day, month, active_days))
    conn.execute("""
        INSERT INTO truck(id,zone,category,capacity_g,status)
        SELECT 'X-'||lpad(f.zone::text,2,'0')||'-'||
               CASE f.category WHEN 'organic' THEN 'O' WHEN 'recycle' THEN 'R' ELSE 'C' END||'-2',
               f.zone,f.category,
               CASE f.category WHEN 'organic' THEN 22000 WHEN 'recycle' THEN 13000 ELSE 18000 END,
               'idle'
        FROM fleet_plan f WHERE f.month=%s AND f.suggested=2
        ON CONFLICT(id) DO UPDATE SET status=CASE WHEN truck.status='standby' THEN 'idle' ELSE truck.status END
    """, (month,))
    conn.execute("""
        UPDATE truck t SET status='standby'
        FROM fleet_plan f
        WHERE f.month=%s AND f.zone=t.zone AND f.category=t.category AND f.suggested=1
          AND t.id LIKE '%%-2' AND t.load_g=0 AND t.status='idle'
          AND NOT EXISTS(SELECT 1 FROM task k WHERE k.truck=t.id AND k.status IN ('assigned','collecting'))
    """, (month,))
    log(conn, "planning", "info", "Đã tự động điều chỉnh dung tích/tần suất và tăng/giảm số lượng xe theo khu")


def simulated_payments(conn, start, end, emit, step=0):
    late_house = "H-0120" if step == 71 else ("H-0340" if step == 73 else None)
    if late_house:
        unpaid = conn.execute("""
            SELECT i.* FROM invoice i
            WHERE i.house = %s
              AND NOT EXISTS (
                SELECT 1 FROM payment_attempt p
                WHERE p.invoice_ref = i.id AND p.status = 'matched'
              )
            ORDER BY i.month
        """, (late_house,)).fetchall()
        paid_at = start + timedelta(minutes=10)
        for inv in unpaid:
            tx = f"TX-{inv['id']}-LATE"
            emit("payment", late_house, paid_at, inv["total_vnd"], "vnd",
                 data={"tx": tx, "invoice": inv["id"], "house": late_house})
        if unpaid:
            bin_code = "H-0120-C (Khu 02)" if late_house == "H-0120" else "H-0340-R (Khu 06)"
            log(conn, "billing", "info",
                f"Hộ {late_house} đã thanh toán bù {len(unpaid)} hóa đơn quá hạn; mở lại thu gom thùng {bin_code}")

    rows = conn.execute("""
        SELECT i.*, substring(h.id from '[0-9]+$')::int AS ordinal
        FROM invoice i JOIN household h ON h.id=i.house
        WHERE i.issued >= %s::date-40 AND i.issued <= %s::date
    """, (start.date(), end.date())).fetchall()
    for row in rows:
        profile = row["ordinal"] % 100
        if profile in (0, 20, 40) and row["house"] not in ("H-0120", "H-0340"):
            continue  # 3% cố định không thanh toán -> ngừng gom sau 1 tháng
        delay = 0 if profile in (5, 19, 25) else 1 + row["ordinal"] % 24
        due = row["issued"] + timedelta(days=delay)
        hour = 2 + row["ordinal"] % 20
        paid_at = datetime.combine(due, datetime.min.time(), VN) + timedelta(hours=hour)
        if not start <= paid_at < end:
            continue
        tx = "TX-" + row["id"]
        data = {"tx": tx, "invoice": row["id"], "house": row["house"]}
        amount = row["total_vnd"]
        if profile == 19:
            amount = max(1000, amount - 2000)  # 1% đóng thiếu -> ngừng gom sau 1 tháng
        elif profile in (5, 25):
            amount += 2000  # 2% đóng thừa tiền -> vẫn gom, liên hệ hoàn tiền thừa
        if row["ordinal"] % 200 == 7:
            data = {**data, "invoice": "SAI-" + row["id"]}  # 0.5% sai mã HĐ
        if row["ordinal"] % 200 == 6:
            data = {**data, "house": "H-SAI"}  # 0.5% sai mã hộ
        emit("payment", row["house"], paid_at, amount, "vnd", data=data)
        if row["ordinal"] % 100 == 4:
            emit("payment", row["house"], paid_at, amount, "vnd", data=data)

