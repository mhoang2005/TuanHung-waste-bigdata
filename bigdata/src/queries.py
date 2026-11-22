def fill_alert(value):
    return f"""CASE WHEN {value}>100 THEN 'overload' WHEN {value}>=95 THEN 'full'
                    WHEN {value}>=75 THEN 'high' ELSE 'normal' END"""


STATUS = """
WITH payment_by_house AS MATERIALIZED (
  SELECT house, CASE
    WHEN bool_or(status='overdue') THEN 'overdue'
    WHEN bool_or(status='review') THEN 'review'
    WHEN bool_or(status='unpaid') THEN 'unpaid'
    ELSE 'paid' END AS payment
  FROM invoice_status
  WHERE (%(zone)s=0 OR zone=%(zone)s)
  GROUP BY house
), status AS (
  SELECT b.id,b.house,h.zone,b.category,b.capacity_l,b.interval_h,
    s.grams,m.fill_pct,s.occurred AS measured,p.last_pickup,
    m.is_late OR coalesce(m.fill_pct>=75,false) AS needs,
    m.is_late,
    coalesce(p.blackout_until>d.clock,false) AS lost,
    coalesce(pay.payment,'none') AS payment,
    t.status AS last_task
  FROM bin b JOIN household h ON h.id=b.house JOIN physical_bin p ON p.bin=b.id CROSS JOIN demo d
  LEFT JOIN payment_by_house pay ON pay.house=b.house
  LEFT JOIN bin_state s ON s.bin=b.id AND s.occurred>=p.last_pickup
  CROSS JOIN LATERAL (
    SELECT round(100.0*s.grams/(b.capacity_l*b.density_g_l),1) AS fill_pct,
           coalesce(s.grams,0)>0 AND d.clock-p.last_pickup>=make_interval(hours=>b.interval_h) AS is_late
  ) m
  LEFT JOIN LATERAL (SELECT status FROM task WHERE task.bin=b.id ORDER BY id DESC LIMIT 1) t ON true
  WHERE (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
)
"""+f"""
, alerts AS (
  SELECT *, {fill_alert("fill_pct")} AS fill_alert FROM status
)
"""

PAGES = {"operations","analysis","planning","finance","health"}


def operations(conn,p):
    total = conn.execute(STATUS+"""
        SELECT count(*) AS bins,count(DISTINCT house) FILTER(WHERE needs AND payment<>'overdue') AS houses,
          count(*) FILTER(WHERE fill_alert='high') AS near_full,
          count(*) FILTER(WHERE fill_alert='full') AS full,
          count(*) FILTER(WHERE fill_alert='overload') AS overload,
          count(*) FILTER(WHERE is_late) AS late_pickup,
          coalesce(sum(grams),0) AS grams,count(*) FILTER(WHERE lost) AS lost
        FROM alerts
    """,p).fetchone()
    total.update(conn.execute("""
        SELECT count(*) AS trucks,count(*) FILTER(WHERE status='broken') AS broken
        FROM truck WHERE (%(zone)s=0 OR zone=%(zone)s) AND (%(category)s='' OR category=%(category)s)
    """,p).fetchone())
    total.update(conn.execute("""
        SELECT count(*) AS processed
        FROM task t JOIN bin b ON b.id=t.bin JOIN household h ON h.id=b.house
        WHERE t.status IN ('completed','partial')
          AND (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
    """,p).fetchone())
    rows = conn.execute(STATUS+"""
        SELECT *,fill_alert AS alert
        FROM alerts WHERE (needs OR lost OR payment='overdue' OR last_task IS NOT NULL)
          AND (%(filter)s<>'lost' OR lost)
          AND (%(filter)s<>'need' OR (needs AND payment<>'overdue'))
          AND (%(filter)s<>'no_pickup' OR payment='overdue')
          AND (%(filter)s<>'stale' OR is_late)
          AND (%(filter)s NOT IN ('high','full','overload') OR fill_alert=%(filter)s)
        ORDER BY (needs AND payment<>'overdue') DESC,fill_pct DESC NULLS LAST,id LIMIT 100
    """,p).fetchall()
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
        SELECT d.day AS label,sum(generated_g) AS generated,sum(collected_g) AS collected
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
    return {"series":series,"rows":breakdown,"inventory":inventory["grams"]}


def planning(conn,p):
    rows = conn.execute("""
        SELECT b.id,b.house,h.zone,b.category,b.capacity_l,b.interval_h,p.before_l,p.after_l,p.before_h,p.after_h,
               p.reason,p.effective,p.result,p.forecast_g
        FROM bin b JOIN household h ON h.id=b.house
        LEFT JOIN plan p ON p.bin=b.id AND p.month=%(month)s::date
        WHERE (%(zone)s=0 OR h.zone=%(zone)s) AND (%(category)s='' OR b.category=%(category)s)
          AND (%(house)s='' OR b.house=%(house)s)
        ORDER BY (p.result='applied') DESC NULLS LAST,b.id LIMIT 100
    """,p).fetchall()
    trucks = conn.execute("""
        SELECT t.*,f.suggested,f.collected_g,f.trips AS period_trips,
            round(t.dumped_g*100.0/nullif(t.trips::bigint*t.capacity_g,0),1) AS utilization_pct
        FROM truck t LEFT JOIN fleet_plan f ON f.zone=t.zone AND f.category=t.category AND f.month=%(month)s::date
        WHERE (%(zone)s=0 OR t.zone=%(zone)s) AND (%(category)s='' OR t.category=%(category)s)
        ORDER BY (t.status='broken') DESC,t.id LIMIT 100
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
          AND (p.invoice_ref LIKE '%%'||to_char(%(month)s::date,'YYYYMM')||'%%'
             OR (p.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date BETWEEN %(month)s::date AND %(month)s::date+interval '2 months')
        ORDER BY e.received DESC,p.paid_at DESC,p.event_id DESC LIMIT 50
    """,p).fetchall()
    return {"total":totals,"rows":rows,"logs":payments}

