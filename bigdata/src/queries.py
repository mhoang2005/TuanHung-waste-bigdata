from db import WATCH_BINS


def fill_alert(value):
    return f"""CASE WHEN {value}>100 THEN 'overload' WHEN {value}>=95 THEN 'full'
                    WHEN {value}>=75 THEN 'high' ELSE 'normal' END"""


STATUS = """
WITH review_inv AS (
  SELECT DISTINCT invoice_ref, house
  FROM payment_attempt
  WHERE status='review' AND reason IN ('underpaid','amount_mismatch')
), payment_by_house AS MATERIALIZED (
  SELECT i.house, CASE
    WHEN bool_or(paid.paid_at IS NULL AND (d.clock AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= i.suspend_from) THEN 'overdue'
    WHEN bool_or(paid.paid_at IS NULL AND rev.invoice_ref IS NOT NULL) THEN 'review'
    WHEN bool_or(paid.paid_at IS NULL) THEN 'unpaid'
    ELSE 'paid' END AS payment
  FROM invoice i
  JOIN household h ON h.id=i.house
  CROSS JOIN demo d
  LEFT JOIN payment_attempt paid ON paid.invoice_ref=i.id AND paid.status='matched'
  LEFT JOIN review_inv rev ON rev.invoice_ref=i.id AND rev.house=i.house
  WHERE (%(zone)s=0 OR h.zone=%(zone)s)
  GROUP BY i.house
), status AS (
  SELECT b.id,b.house,h.zone,b.category,b.capacity_l,b.interval_h,
    (b.capacity_l*b.density_g_l)::float8 AS max_grams,
    s.grams,m.fill_pct,s.occurred AS measured,p.last_pickup,
    m.is_late OR coalesce(m.fill_pct>=75,false) AS needs,
    m.is_late,
    coalesce(p.blackout_until>=d.clock,false) AS lost,
    coalesce(pay.payment,'none') AS payment
  FROM bin b JOIN household h ON h.id=b.house JOIN physical_bin p ON p.bin=b.id CROSS JOIN demo d
  LEFT JOIN payment_by_house pay ON pay.house=b.house
  LEFT JOIN bin_state s ON s.bin=b.id AND s.occurred>=p.last_pickup
  CROSS JOIN LATERAL (
    SELECT round(100.0*s.grams/(b.capacity_l*b.density_g_l),1) AS fill_pct,
           coalesce(s.grams,0)>0 AND d.clock-p.last_pickup>=make_interval(hours=>b.interval_h) AS is_late
  ) m
  WHERE (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
)
"""+f"""
, alerts AS MATERIALIZED (
  SELECT *, {fill_alert("fill_pct")} AS fill_alert FROM status
)
"""

PAGES = {"operations","analysis","planning","finance","health"}


def operations(conn,p):
    pins = p.get("pins") or []
    if not p.get("filter") and not pins and not p.get("zone") and not p.get("category") and not p.get("house"):
        pins = list(WATCH_BINS)
        p = {**p, "pins": pins}
    use_pins = bool(pins) and not p.get("filter")
    if use_pins:
        rows_sql = """
        , top_rows AS (
          SELECT a.*, a.fill_alert AS alert, t.status AS last_task, t.truck AS assigned_truck,
                 coalesce(t.finished_at, t.started_at, t.created_at) AS task_at,
                 br.broken_truck
          FROM alerts a
          LEFT JOIN LATERAL (
            SELECT status, truck, finished_at, started_at, created_at
            FROM task WHERE task.bin=a.id ORDER BY id DESC LIMIT 1
          ) t ON true
          LEFT JOIN LATERAL (
            SELECT id AS broken_truck FROM truck WHERE zone=a.zone AND category=a.category AND status='broken' LIMIT 1
          ) br ON true
          WHERE a.id = ANY(%(pins)s)
          ORDER BY
            CASE
              WHEN a.lost THEN 1
              WHEN br.broken_truck IS NOT NULL AND a.payment <> 'overdue' AND (a.needs OR t.status = 'requeued') THEN 1
              WHEN a.fill_alert = 'overload' AND a.payment <> 'overdue' THEN 2
              WHEN a.fill_alert = 'full' AND a.payment <> 'overdue' THEN 3
              WHEN t.status IN ('partial','assigned','collecting','requeued') AND a.payment <> 'overdue' THEN 4
              WHEN a.fill_alert = 'high' AND a.payment <> 'overdue' THEN 4
              WHEN a.is_late AND a.payment <> 'overdue' THEN 5
              WHEN a.payment = 'overdue' THEN 6
              WHEN coalesce(a.fill_pct, 0) > 0 THEN 7
              ELSE 8
            END,
            coalesce(a.fill_pct, 0) DESC,
            a.is_late DESC,
            coalesce(t.finished_at, a.measured, a.last_pickup) DESC NULLS LAST,
            a.id
        )
        """
    else:
        rows_sql = """
        , ranked_alerts AS (
          SELECT a.*, a.fill_alert AS alert,
            CASE
              WHEN a.fill_alert='full' AND a.payment<>'overdue' THEN 1
              WHEN a.fill_alert='high' AND a.payment<>'overdue' THEN 2
              WHEN a.fill_alert='overload' AND a.payment<>'overdue' THEN 3
              WHEN a.payment='overdue' THEN 4
              WHEN a.is_late THEN 5
              WHEN a.lost THEN 6
              ELSE 7
            END AS bucket
          FROM alerts a
          WHERE (%(filter)s<>'lost' OR a.lost)
            AND (%(filter)s<>'need' OR (a.needs AND a.payment<>'overdue'))
            AND (%(filter)s<>'no_pickup' OR a.payment='overdue')
            AND (%(filter)s<>'stale' OR (a.is_late AND a.payment<>'overdue'))
            AND (%(filter)s NOT IN ('high','full','overload') OR (a.fill_alert=%(filter)s AND a.payment<>'overdue'))
            AND (%(filter)s NOT IN ('','all') OR a.needs OR a.payment='overdue' OR a.last_pickup IS NOT NULL)
        ), ordered_alerts AS (
          SELECT *,
            row_number() OVER (
              PARTITION BY bucket
              ORDER BY (measured IS NOT NULL) DESC, coalesce(measured, last_pickup) DESC NULLS LAST, fill_pct DESC NULLS LAST, id
            ) AS rn
          FROM ranked_alerts
        ), selected_alerts AS (
          SELECT * FROM ordered_alerts
          ORDER BY
            CASE WHEN %(filter)s IN ('','need') THEN rn ELSE 0 END,
            CASE WHEN %(filter)s IN ('','need') THEN bucket ELSE 0 END,
            (needs AND payment<>'overdue') DESC,
            fill_pct DESC NULLS LAST,
            coalesce(measured, last_pickup) DESC NULLS LAST,
            id
          LIMIT CASE WHEN %(filter)s='' THEN 30 WHEN %(filter)s='all' THEN 100 ELSE 60 END
        ), top_rows AS (
          SELECT a.*, t.status AS last_task, t.truck AS assigned_truck, t.at AS task_at, br.broken_truck
          FROM selected_alerts a
          LEFT JOIN LATERAL (
            SELECT status, truck, coalesce(finished_at, started_at, created_at) AS at
            FROM task WHERE task.bin=a.id ORDER BY id DESC LIMIT 1
          ) t ON true
          LEFT JOIN LATERAL (
            SELECT id AS broken_truck FROM truck WHERE zone=a.zone AND category=a.category AND status='broken' LIMIT 1
          ) br ON true
          WHERE (a.needs OR a.lost OR a.payment='overdue' OR t.status IS NOT NULL)
          ORDER BY """ + ("(a.needs AND a.payment<>'overdue') DESC, a.fill_pct DESC NULLS LAST, a.zone, a.id" if p.get("filter") == "all" else "a.zone, a.id") + """
        )
        """
    bundle = conn.execute(STATUS + rows_sql + """
        SELECT
          (SELECT row_to_json(t) FROM (
            SELECT count(*) AS bins,
              count(DISTINCT house) AS total_houses,
              count(DISTINCT house) FILTER(WHERE needs AND payment<>'overdue') AS houses,
              count(DISTINCT house) FILTER(WHERE coalesce(grams,0)>0 AND payment<>'overdue') AS uncollected_houses,
              count(DISTINCT house) FILTER(WHERE is_late AND payment<>'overdue') AS late_houses,
              count(DISTINCT house) FILTER(WHERE payment='overdue') AS overdue_houses,
              count(*) FILTER(WHERE fill_alert='high' AND payment<>'overdue') AS near_full,
              count(*) FILTER(WHERE fill_alert='full' AND payment<>'overdue') AS full,
              count(*) FILTER(WHERE fill_alert='overload' AND payment<>'overdue') AS overload,
              count(*) FILTER(WHERE is_late AND payment<>'overdue') AS late_pickup,
              count(*) FILTER(WHERE payment='overdue') AS overdue_bins,
              coalesce(sum(grams),0) AS grams,count(*) FILTER(WHERE lost) AS lost
            FROM alerts
          ) t) AS total,
          (SELECT coalesce(json_agg(r), '[]'::json) FROM (SELECT * FROM top_rows OFFSET 0) r) AS rows
    """,p).fetchone()
    total = bundle["total"]
    rows = bundle["rows"]
    total.update(conn.execute("""
        SELECT count(*) FILTER(WHERE status<>'standby') AS trucks,count(*) FILTER(WHERE status='broken') AS broken
        FROM truck WHERE (%(zone)s=0 OR zone=%(zone)s) AND (%(category)s='' OR category=%(category)s)
    """,p).fetchone())
    if not p.get("zone") and not p.get("category"):
        total.update(conn.execute("SELECT count(*) AS processed FROM task WHERE status IN ('completed','partial')").fetchone())
    else:
        total.update(conn.execute("""
            SELECT count(*) AS processed
            FROM task t JOIN bin b ON b.id=t.bin JOIN household h ON h.id=b.house
            WHERE t.status IN ('completed','partial')
              AND (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
        """,p).fetchone())
    events = conn.execute(f"""
        SELECT e.id,e.occurred,e.kind,e.subject,e.payload,
          CASE WHEN e.kind='sensor' THEN {fill_alert("(e.payload->>'fill_pct')::numeric")} END AS alert
        FROM event e
        LEFT JOIN bin b ON b.id=e.subject LEFT JOIN household h ON h.id=b.house
        LEFT JOIN truck t ON t.id=e.subject
        WHERE e.kind IN ('sensor','pickup','vehicle','dump','signal')
          AND (%(zone)s=0 OR coalesce(h.zone,t.zone)=%(zone)s)
          AND (%(category)s='' OR coalesce(b.category,t.category)=%(category)s)
          AND (%(filter)s<>'broken' OR e.payload->'data'->>'state' IN ('broken','recovered'))
          AND (%(filter)s<>'lost' OR e.kind='signal')
          AND (%(filter)s NOT IN ('high','full','overload')
               OR (e.kind='sensor' AND {fill_alert("(e.payload->>'fill_pct')::numeric")}=%(filter)s))
        ORDER BY e.received DESC,e.occurred DESC,e.id DESC LIMIT 30
    """,p).fetchall()
    return {"total":total,"rows":rows,"logs":events}


def analysis(conn,p):
    filters = """
        FROM daily d JOIN bin b ON b.id=d.bin JOIN household h ON h.id=b.house
        WHERE d.day >= %(month)s::date AND d.day < %(month)s::date + interval '1 month'
        AND (%(zone)s=0 OR h.zone=%(zone)s)
        AND (%(category)s='' OR b.category=%(category)s) AND (%(house)s='' OR h.id=%(house)s)
    """
    series = conn.execute("""
        SELECT d.day AS label,sum(generated_g) AS generated,sum(collected_g) AS collected,sum(pickups) AS pickups
    """+filters+" GROUP BY d.day ORDER BY d.day",p).fetchall()
    breakdown = conn.execute("""
        SELECT CASE WHEN %(zone)s=0 THEN 'Khu '||lpad(h.zone::text,2,'0') ELSE h.id END AS label,
           b.category,sum(generated_g) AS generated,sum(collected_g) AS collected,sum(pickups) AS pickups
    """+filters+" GROUP BY 1,b.category ORDER BY 1,b.category LIMIT 180",p).fetchall()
    inventory = conn.execute("""
        SELECT coalesce(sum(d.generated_g-d.collected_g),0) AS grams
        FROM daily d JOIN bin b ON b.id=d.bin JOIN household h ON h.id=b.house
        WHERE d.day < %(month)s::date + interval '1 month'
        AND (%(zone)s=0 OR h.zone=%(zone)s)
        AND (%(category)s='' OR b.category=%(category)s) AND (%(house)s='' OR h.id=%(house)s)
    """,p).fetchone()
    if not p.get("zone") and not p.get("category") and not p.get("house"):
        hourly = conn.execute("""
            SELECT EXTRACT(HOUR FROM e.occurred AT TIME ZONE 'Asia/Ho_Chi_Minh')::int AS hour,
                   count(*)::int AS pickups,
                   coalesce(sum((e.payload->>'grams')::bigint), 0)::bigint AS grams
            FROM event e
            WHERE e.kind='pickup'
              AND e.occurred >= (%(month)s::date::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')
              AND e.occurred < ((%(month)s::date + interval '1 month')::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')
            GROUP BY 1 ORDER BY 1
        """,p).fetchall()
    else:
        hourly = conn.execute("""
            SELECT EXTRACT(HOUR FROM e.occurred AT TIME ZONE 'Asia/Ho_Chi_Minh')::int AS hour,
                   count(*)::int AS pickups,
                   coalesce(sum((e.payload->>'grams')::bigint), 0)::bigint AS grams
            FROM event e
            JOIN bin b ON b.id=e.subject JOIN household h ON h.id=b.house
            WHERE e.kind='pickup'
              AND e.occurred >= (%(month)s::date::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')
              AND e.occurred < ((%(month)s::date + interval '1 month')::timestamp AT TIME ZONE 'Asia/Ho_Chi_Minh')
              AND (%(zone)s=0 OR h.zone=%(zone)s)
              AND (%(category)s='' OR b.category=%(category)s) AND (%(house)s='' OR h.id=%(house)s)
            GROUP BY 1 ORDER BY 1
        """,p).fetchall()
    zones = conn.execute("""
        SELECT h.zone,sum(generated_g) AS generated,sum(collected_g) AS collected,sum(pickups) AS pickups
    """+filters+" GROUP BY h.zone ORDER BY h.zone",p).fetchall()
    categories = conn.execute("""
        SELECT b.category,sum(generated_g) AS generated,sum(collected_g) AS collected,sum(pickups) AS pickups
    """+filters+" GROUP BY b.category ORDER BY b.category",p).fetchall()
    finance_monthly = conn.execute("""
        SELECT i.month::text AS month,
               count(*)::int AS total_cnt,
               coalesce(sum(i.total_vnd),0)::bigint AS billed_vnd,
               coalesce(sum(i.total_vnd) FILTER(WHERE paid.paid_at IS NOT NULL),0)::bigint AS collected_vnd,
               coalesce(sum(i.total_vnd) FILTER(WHERE paid.paid_at IS NULL AND (d.clock AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= i.suspend_from),0)::bigint AS overdue_vnd,
               coalesce(sum(i.total_vnd) FILTER(WHERE paid.paid_at IS NULL AND (d.clock AT TIME ZONE 'Asia/Ho_Chi_Minh')::date < i.suspend_from),0)::bigint AS pending_vnd
        FROM invoice i
        JOIN household h ON h.id=i.house
        CROSS JOIN demo d
        LEFT JOIN payment_attempt paid ON paid.invoice_ref=i.id AND paid.status='matched'
        WHERE (%(zone)s=0 OR h.zone=%(zone)s) AND (%(house)s='' OR h.id=%(house)s)
        GROUP BY i.month ORDER BY i.month
    """,p).fetchall()
    monthly_efficiency = conn.execute("""
        SELECT to_char(date_trunc('month', d.day), 'YYYY-MM-01') AS month,
               sum(d.generated_g) AS generated,sum(d.collected_g) AS collected,sum(d.pickups) AS pickups
        FROM daily d JOIN bin b ON b.id=d.bin JOIN household h ON h.id=b.house
        WHERE (%(zone)s=0 OR h.zone=%(zone)s)
          AND (%(category)s='' OR b.category=%(category)s) AND (%(house)s='' OR h.id=%(house)s)
        GROUP BY 1 ORDER BY 1
    """,p).fetchall()
    return {
        "series":series,"rows":breakdown,"inventory":inventory["grams"],
        "hourly":hourly,"zones":zones,"categories":categories,
        "finance_monthly":finance_monthly,"monthly_efficiency":monthly_efficiency
    }


def planning(conn,p):
    rows = conn.execute("""
        SELECT b.id,b.house,h.zone,b.category,b.capacity_l,b.interval_h,p.before_l,p.after_l,p.before_h,p.after_h,
               p.reason,p.effective,p.result,p.forecast_g
        FROM bin b JOIN household h ON h.id=b.house
        LEFT JOIN plan p ON p.bin=b.id AND p.month=%(month)s::date
        WHERE (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
          AND (%(house)s='' OR b.house=%(house)s)
        ORDER BY h.zone, (p.result IN ('applied','blocked_capacity')) DESC NULLS LAST, b.id LIMIT 100
    """,p).fetchall()
    trucks = conn.execute("""
        SELECT t.*,f.current_vehicles,f.suggested,f.collected_g,f.trips AS period_trips,
            round(t.dumped_g*100.0/nullif(t.trips::bigint*t.capacity_g,0),1) AS utilization_pct
        FROM truck t LEFT JOIN fleet_plan f ON f.zone=t.zone AND f.category=t.category AND f.month=%(month)s::date
        WHERE (%(zone)s=0 OR t.zone=%(zone)s) AND (%(category)s='' OR t.category=%(category)s)
        ORDER BY (f.current_vehicles<>f.suggested) DESC NULLS LAST,(t.status='broken') DESC,t.zone,t.id LIMIT 100
    """,p).fetchall()
    totals = conn.execute("""
        SELECT count(*) AS completed,round(avg(extract(epoch FROM (started_at-created_at))/3600),1) AS wait_h,
               sum(collected_g) AS grams FROM task t JOIN bin b ON b.id=t.bin JOIN household h ON h.id=b.house
        WHERE (t.finished_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= %(month)s::date
          AND (t.finished_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date < %(month)s::date+interval '1 month'
          AND (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
          AND t.status IN ('completed','partial')
    """,p).fetchone()
    return {"rows":rows,"trucks":trucks,"total":totals}


def finance(conn,p):
    where = """WHERE month=%(month)s::date AND (%(zone)s=0 OR zone=%(zone)s)
      AND (%(house)s='' OR house=%(house)s)"""
    totals = conn.execute("""
        SELECT status,count(*) AS count,sum(total_vnd) AS amount FROM invoice_status
    """+where+" GROUP BY status",p).fetchall()
    rows = conn.execute("""
        SELECT id,house,zone,month,issued,suspend_from,total_vnd,status,paid_at FROM invoice_status
    """+where+""" AND (%(filter)s='' OR status=%(filter)s)
      ORDER BY zone,house LIMIT 100 OFFSET %(offset)s""",p).fetchall()
    payments = conn.execute("""
        SELECT p.* FROM payment_attempt p JOIN event e ON e.id=p.event_id
        LEFT JOIN household h ON h.id=p.house
        WHERE (%(zone)s=0 OR h.zone=%(zone)s) AND (%(house)s='' OR p.house=%(house)s)
          AND (%(month)s::date = (SELECT coalesce(max(month),'2026-10-01') FROM closed_month)
             OR p.invoice_ref LIKE '%%'||to_char(%(month)s::date,'YYYYMM')||'%%'
             OR (p.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date BETWEEN %(month)s::date AND %(month)s::date+interval '2 months')
        ORDER BY e.received DESC,p.paid_at DESC,p.event_id DESC LIMIT 50
    """,p).fetchall()
    return {"total":totals,"rows":rows,"logs":payments}

