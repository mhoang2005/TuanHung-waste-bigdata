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
        SELECT 'HD-' || to_char(%s::date,'YYYYMM') || '-' || house,house,%s,%s,%s,
               (SELECT base_vnd FROM fee_config),
               jsonb_agg(jsonb_build_object('category',category,'grams',grams,'pickups',pickups,
                          'rate',vnd_kg,'cost',cost) ORDER BY category),
               (SELECT base_vnd FROM fee_config) + sum(cost)
        FROM costs GROUP BY house
    """, (month, day, month, month, day, next_month(day)))
    # October is a deliberately short opening period; a full closed month is required to resize.
    if month > date(2026, 10, 1):
        make_plan(conn, month, day)
    log(conn, "billing", "info", f"Đã chốt kỳ {month:%Y-%m}; phát hành hóa đơn cho từng hộ")
    return month


def make_plan(conn, month, day):
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
    """, (month, day, (day - month).days, (next_month(day)-day).days,
          (day - month).days, month, day))
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
        )
        INSERT INTO fleet_plan
        SELECT %s,d.zone,d.category,1,
          CASE WHEN d.stops > %s*9 THEN 2 ELSE 1 END,coalesce(t.n,0),d.grams
        FROM demand d LEFT JOIN trips t USING(zone,category)
    """, (month, day, month, day, month, (day-month).days))
    log(conn, "planning", "info", "Đã áp dụng dung tích/tần suất và tính đề xuất đội xe theo kỳ")


def simulated_payments(conn, start, end, emit):
    rows = conn.execute("""
        SELECT i.*, substring(h.id from '[0-9]+$')::int AS ordinal
        FROM invoice i JOIN household h ON h.id=i.house
        WHERE i.issued >= %s::date-40 AND i.issued <= %s::date
    """, (start.date(), end.date())).fetchall()
    for row in rows:
        profile = row["ordinal"] % 20
        if profile == 0:
            continue  # persistently unpaid
        delay = 32 if profile == 1 else (0 if profile < 5 else 1 + row["ordinal"] % 16)
        due = row["issued"] + timedelta(days=delay)
        hour = 2 + row["ordinal"] % 20
        paid_at = datetime.combine(due, datetime.min.time(), VN) + timedelta(hours=hour)
        if not start <= paid_at < end:
            continue
        tx = "TX-" + row["id"]
        data = {"tx": tx, "invoice": row["id"], "house": row["house"]}
        amount = row["total_vnd"]
        if profile == 2:
            amount += 2000
        if profile == 3 and row["ordinal"] % 100 == 3:
            data = {**data, "invoice": "SAI-" + row["id"]}
        if profile == 6 and row["ordinal"] % 100 == 6:
            data = {**data, "house": "H-SAI"}
        emit("payment", row["house"], paid_at, amount, "vnd", data=data)
        if row["ordinal"] % 100 == 4:
            emit("payment", row["house"], paid_at, amount, "vnd", data=data)
            emit("payment", row["house"], paid_at, amount+1, "vnd", data=data)
            emit("payment", row["house"], paid_at, amount, "vnd", data={**data, "tx": tx+"-B"})

