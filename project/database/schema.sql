-- Smart Waste v1. Run as the owner of database waste_lab.
-- Deliberately uses serving tables, not an OLAP warehouse. Historical events live in HDFS.
BEGIN;

CREATE TABLE IF NOT EXISTS areas (
    area_id text PRIMARY KEY,
    area_name text NOT NULL,
    population integer NOT NULL CHECK (population >= 0),
    households integer NOT NULL CHECK (households >= 0)
);
CREATE TABLE IF NOT EXISTS teams (
    team_id text PRIMARY KEY,
    team_name text NOT NULL
);
CREATE TABLE IF NOT EXISTS bins (
    bin_id text PRIMARY KEY,
    area_id text NOT NULL,
    waste_type text NOT NULL CHECK (waste_type IN ('domestic', 'industrial')),
    capacity_l numeric(12,3) NOT NULL CHECK (capacity_l > 0),
    population integer DEFAULT 0 CHECK (population >= 0),
    households integer DEFAULT 0 CHECK (households >= 0),
    max_capacity_l numeric(12,3) NOT NULL CHECK (max_capacity_l >= capacity_l),
    team_id text,
    pickups_per_day integer NOT NULL DEFAULT 1 CHECK (pickups_per_day BETWEEN 1 AND 24),
    active boolean NOT NULL DEFAULT true
);
-- Area population on bins is compatibility metadata only. Never sum it over bins.
CREATE INDEX IF NOT EXISTS bins_area_type_idx ON bins (area_id, waste_type);

CREATE TABLE IF NOT EXISTS households (
    household_id text PRIMARY KEY,
    area_id text NOT NULL,
    residents integer NOT NULL DEFAULT 1 CHECK (residents >= 0)
);
CREATE TABLE IF NOT EXISTS facilities (
    facility_id text PRIMARY KEY,
    area_id text NOT NULL,
    facility_name text NOT NULL
);

CREATE TABLE IF NOT EXISTS bin_status (
    bin_id text PRIMARY KEY,
    last_event_time timestamptz NOT NULL,
    fill_pct double precision CHECK (fill_pct BETWEEN 0 AND 100),
    weight_kg double precision CHECK (weight_kg >= 0),
    status text NOT NULL DEFAULT 'normal',
    updated_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE INDEX IF NOT EXISTS bin_status_time_idx ON bin_status (last_event_time DESC);

CREATE TABLE IF NOT EXISTS alerts (
    alert_key text PRIMARY KEY,
    bin_id text NOT NULL,
    alert_type text NOT NULL,
    opened_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    closed_at timestamptz,
    active boolean NOT NULL DEFAULT true,
    detail text NOT NULL DEFAULT '',
    CHECK (closed_at IS NULL OR closed_at >= opened_at)
);
CREATE INDEX IF NOT EXISTS alerts_active_idx ON alerts (active, alert_type, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS alerts_bin_idx ON alerts (bin_id, opened_at DESC);

CREATE TABLE IF NOT EXISTS daily_area_metrics (
    day date NOT NULL,
    area_id text NOT NULL,
    waste_type text NOT NULL CHECK (waste_type IN ('domestic', 'industrial')),
    event_count bigint NOT NULL DEFAULT 0 CHECK (event_count >= 0),
    generated_kg double precision CHECK (generated_kg >= 0),
    collected_kg double precision NOT NULL DEFAULT 0 CHECK (collected_kg >= 0),
    avg_fill_pct double precision,
    p95_fill_pct double precision,
    full_episodes bigint NOT NULL DEFAULT 0 CHECK (full_episodes >= 0),
    quality_rejected bigint NOT NULL DEFAULT 0 CHECK (quality_rejected >= 0),
    kg_per_person double precision,
    estimated_cost double precision CHECK (estimated_cost >= 0),
    PRIMARY KEY (day, area_id, waste_type)
);

CREATE TABLE IF NOT EXISTS capacity_scenarios (
    period_start date NOT NULL,
    bin_id text NOT NULL,
    capacity_l double precision NOT NULL CHECK (capacity_l > 0),
    pickups_per_day integer NOT NULL CHECK (pickups_per_day BETWEEN 1 AND 24),
    overflow_l double precision NOT NULL CHECK (overflow_l >= 0),
    overflow_hours double precision NOT NULL CHECK (overflow_hours >= 0),
    estimated_daily_cost double precision NOT NULL CHECK (estimated_daily_cost >= 0),
    feasible boolean NOT NULL,
    recommended boolean NOT NULL DEFAULT false,
    PRIMARY KEY (period_start, bin_id, capacity_l, pickups_per_day)
);
CREATE INDEX IF NOT EXISTS capacity_recommendation_idx ON capacity_scenarios (recommended, period_start DESC);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id text PRIMARY KEY,
    application_name text NOT NULL,
    started_at timestamptz NOT NULL,
    finished_at timestamptz,
    status text NOT NULL,
    input_rows bigint,
    accepted_rows bigint,
    rejected_rows bigint,
    detail text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS household_fees (
    period_start date NOT NULL,
    period_end date NOT NULL,
    household_id text NOT NULL,
    area_id text NOT NULL,
    measured_kg double precision NOT NULL CHECK (measured_kg >= 0),
    base_fee double precision NOT NULL CHECK (base_fee >= 0),
    price_per_kg double precision NOT NULL CHECK (price_per_kg >= 0),
    total_fee double precision NOT NULL CHECK (total_fee >= 0),
    PRIMARY KEY (period_start, period_end, household_id),
    CHECK (period_end >= period_start)
);

CREATE OR REPLACE VIEW v_bin_current AS
SELECT b.bin_id, b.area_id, COALESCE(a.area_name,b.area_id) AS area_name,
       b.waste_type, b.capacity_l, b.max_capacity_l, b.team_id,
       s.fill_pct, s.weight_kg, s.status, s.last_event_time, s.updated_at,
       extract(epoch FROM (clock_timestamp() - s.last_event_time)) AS age_seconds
FROM bins b
LEFT JOIN areas a USING (area_id)
LEFT JOIN bin_status s USING (bin_id)
WHERE b.active;

CREATE OR REPLACE VIEW v_latest_recommendations AS
SELECT c.*, b.area_id, b.waste_type, b.capacity_l AS current_capacity_l,
       b.pickups_per_day AS current_pickups_per_day
FROM capacity_scenarios c JOIN bins b USING (bin_id)
WHERE c.recommended
  AND c.period_start = (SELECT max(period_start) FROM capacity_scenarios);

COMMIT;
