CREATE TABLE demo (
    id boolean PRIMARY KEY DEFAULT true CHECK (id),
    mode text NOT NULL DEFAULT 'stopped' CHECK (mode IN ('running','paused','stopped')),
    clock timestamptz NOT NULL DEFAULT '2026-10-30 00:00:00+07',
    step integer NOT NULL DEFAULT 0,
    seed integer NOT NULL DEFAULT 12,
    scenario text NOT NULL DEFAULT 'normal',
    waiting text
);
INSERT INTO demo DEFAULT VALUES;

CREATE TABLE household (
    id text PRIMARY KEY, zone integer NOT NULL, people integer NOT NULL,
    x numeric NOT NULL, y numeric NOT NULL, profile numeric NOT NULL
);
CREATE TABLE bin (
    id text PRIMARY KEY, house text NOT NULL REFERENCES household,
    category text NOT NULL CHECK (category IN ('organic','recycle','other')),
    capacity_l integer NOT NULL, density_g_l integer NOT NULL,
    interval_h integer NOT NULL DEFAULT 72, UNIQUE (house, category)
);
CREATE TABLE physical_bin (
    bin text PRIMARY KEY REFERENCES bin, grams integer NOT NULL DEFAULT 0 CHECK (grams >= 0),
    last_pickup timestamptz NOT NULL, blackout_until timestamptz
);
CREATE TABLE truck (
    id text PRIMARY KEY, zone integer NOT NULL, category text NOT NULL,
    capacity_g integer NOT NULL, load_g integer NOT NULL DEFAULT 0,
    dumped_g bigint NOT NULL DEFAULT 0, km numeric NOT NULL DEFAULT 0,
    trips integer NOT NULL DEFAULT 0, broken_h integer NOT NULL DEFAULT 0,
    x numeric NOT NULL DEFAULT 0, y numeric NOT NULL DEFAULT 0,
    status text NOT NULL DEFAULT 'idle', recover_at timestamptz,
    CHECK (load_g BETWEEN 0 AND capacity_g)
);
CREATE TABLE task (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    truck text NOT NULL REFERENCES truck, bin text NOT NULL REFERENCES bin,
    status text NOT NULL, rank integer NOT NULL, created_at timestamptz NOT NULL,
    started_at timestamptz, finished_at timestamptz, collected_g integer
);
CREATE UNIQUE INDEX one_active_stop ON task(bin) WHERE status IN ('assigned','collecting');
CREATE INDEX task_truck_idx ON task(truck,status,rank);
CREATE INDEX task_bin_history ON task(bin,id DESC);

CREATE TABLE outbox (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    body jsonb NOT NULL, due timestamptz NOT NULL,
    topic text, part integer, kafka_offset bigint
);
CREATE INDEX outbox_pending ON outbox(due,id) WHERE kafka_offset IS NULL;
CREATE TABLE kafka_cursor (
    topic text NOT NULL, part integer NOT NULL, kafka_offset bigint NOT NULL,
    PRIMARY KEY(topic,part)
);
CREATE TABLE event (
    id text PRIMARY KEY, kind text NOT NULL, subject text NOT NULL,
    occurred timestamptz NOT NULL, payload jsonb NOT NULL, received timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX event_recent ON event(received DESC);
CREATE INDEX event_kind_recent ON event(kind,received DESC);
CREATE TABLE bin_state (
    bin text PRIMARY KEY REFERENCES bin, occurred timestamptz NOT NULL,
    grams integer NOT NULL, fill_pct numeric NOT NULL, event_id text NOT NULL
);
CREATE TABLE daily (
    day date NOT NULL, bin text NOT NULL REFERENCES bin,
    generated_g bigint NOT NULL, collected_g bigint NOT NULL, pickups integer NOT NULL,
    PRIMARY KEY(day,bin)
);
CREATE INDEX daily_bin_day ON daily(bin,day);
CREATE TABLE microbatch (
    id bigint PRIMARY KEY, processed timestamptz NOT NULL DEFAULT now(),
    input integer NOT NULL, clean integer NOT NULL, quarantine integer NOT NULL,
    duplicates integer NOT NULL, late integer NOT NULL,
    latency_ms integer NOT NULL, duration_ms integer NOT NULL
);
CREATE TABLE quality_log (
    topic text NOT NULL, part integer NOT NULL, kafka_offset bigint NOT NULL,
    reason text NOT NULL, raw text, received timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY(topic,part,kafka_offset)
);
CREATE INDEX quality_recent ON quality_log(received DESC);
CREATE TABLE system_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, at timestamptz NOT NULL DEFAULT now(),
    component text NOT NULL, level text NOT NULL, message text NOT NULL
);

CREATE TABLE tariff (
    category text PRIMARY KEY, vnd_kg integer NOT NULL CHECK(vnd_kg >= 0)
);
INSERT INTO tariff VALUES ('organic',750),('recycle',250),('other',1100);
CREATE TABLE fee_config (
    id boolean PRIMARY KEY DEFAULT true CHECK(id), base_vnd integer NOT NULL CHECK(base_vnd >= 0)
);
INSERT INTO fee_config VALUES (true,15000);
CREATE TABLE closed_month (month date PRIMARY KEY, closed_at timestamptz NOT NULL);
CREATE TABLE invoice (
    id text PRIMARY KEY, house text NOT NULL REFERENCES household, month date NOT NULL,
    issued date NOT NULL, suspend_from date NOT NULL, base_vnd integer NOT NULL,
    detail jsonb NOT NULL, total_vnd integer NOT NULL CHECK(total_vnd > 0),
    UNIQUE(house,month)
);
CREATE TABLE transaction_key (
    tx text PRIMARY KEY, fingerprint jsonb NOT NULL
);
CREATE TABLE payment_attempt (
    event_id text PRIMARY KEY REFERENCES event, tx text NOT NULL, house text NOT NULL,
    invoice_ref text NOT NULL, amount integer NOT NULL, paid_at timestamptz NOT NULL,
    status text NOT NULL, reason text NOT NULL
);
CREATE UNIQUE INDEX payment_one_match ON payment_attempt(invoice_ref) WHERE status='matched';
CREATE INDEX payment_invoice_idx ON payment_attempt(invoice_ref,status);
CREATE INDEX payment_recent ON payment_attempt(paid_at DESC);

CREATE VIEW invoice_status AS
SELECT i.*, h.zone, paid.paid_at, CASE
  WHEN paid.paid_at IS NOT NULL THEN 'paid'
  WHEN EXISTS(SELECT 1 FROM payment_attempt a WHERE a.invoice_ref=i.id AND a.house=i.house
              AND a.status='review' AND a.reason='amount_mismatch') THEN 'review'
  WHEN (d.clock AT TIME ZONE 'Asia/Ho_Chi_Minh')::date >= i.suspend_from
       AND EXISTS(SELECT 1 FROM closed_month m WHERE m.month=i.suspend_from-interval '1 month') THEN 'overdue'
  ELSE 'unpaid' END AS status
FROM invoice i JOIN household h ON h.id=i.house CROSS JOIN demo d
LEFT JOIN payment_attempt paid ON paid.invoice_ref=i.id AND paid.status='matched';

CREATE TABLE plan (
    month date NOT NULL, bin text NOT NULL REFERENCES bin, effective date NOT NULL,
    before_l integer NOT NULL, after_l integer NOT NULL, before_h integer NOT NULL,
    after_h integer NOT NULL, reason text NOT NULL, result text NOT NULL, forecast_g bigint NOT NULL,
    PRIMARY KEY(month,bin)
);
CREATE TABLE fleet_plan (
    month date NOT NULL, zone integer NOT NULL, category text NOT NULL,
    current_vehicles integer NOT NULL, suggested integer NOT NULL, trips bigint NOT NULL,
    collected_g bigint NOT NULL, PRIMARY KEY(month,zone,category)
);

