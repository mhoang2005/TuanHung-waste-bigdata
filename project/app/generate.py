"""Deterministic synthetic IoT events; file generation and Kafka replay are separate.

The simulator records deposits and collection quantities. Sensor measurements are
snapshots, so summing sensor weight is deliberately never a waste-total metric.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def references(count: int):
    areas = [dict(area_id=f"A{i:03}", area_name=name, population=1800 + i * 300,
                  households=450 + i * 75) for i, name in enumerate(
        ["Trung tâm", "Khu dân cư Bắc", "Khu dân cư Nam", "Khu công nghiệp"], 1)]
    bins = []
    for i in range(count):
        industrial = i % 4 == 3
        area = areas[3 if industrial else i % 3]
        bins.append(dict(bin_id=f"B{i+1:06}", area_id=area["area_id"],
                         waste_type="industrial" if industrial else "domestic",
                         capacity_l=[240, 360, 660][i % 3], max_capacity_l=660,
                         population=area["population"], households=area["households"],
                         team_id=f"T{1+(i % 2):02}",
                         density_kg_l=0.25 if industrial else 0.12,
                         facility_id=f"F{i+1:04}" if industrial else ""))
    teams = [dict(team_id=f"T{i:02}", team_name=f"Đội thu gom {i}") for i in (1, 2)]
    return areas, bins, teams


def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate(args):
    target = Path(args.output)
    target.mkdir(parents=True, exist_ok=True)
    areas, bins, teams = references(args.bins)
    write_csv(target / "areas.csv", areas)
    write_csv(target / "bins.csv", bins)
    write_csv(target / "teams.csv", teams)
    (target / "reference.json").write_text(json.dumps(dict(areas=areas, bins=bins, teams=teams),
                                                      ensure_ascii=False, indent=2), encoding="utf-8")
    start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    rng = random.Random(args.seed)
    stock = {b["bin_id"]: 0.0 for b in bins}
    due = {}
    counters = Counter()
    totals = Counter()
    serial = 0
    pending = []
    steps = int(args.days * 1440 / args.interval_minutes)

    def event(bin_ref, kind, time, **payload):
        nonlocal serial
        serial += 1
        return dict(event_id=f"E{args.seed:04}-{serial:012}", bin_id=bin_ref["bin_id"],
                    event_type=kind, event_time=utc(time), schema_version=1, **payload)

    path = target / "events.ndjson"
    with path.open("w", encoding="utf-8") as handle:
        def emit(record, mutation=True):
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
            counters[record["event_type"]] += 1
            counters["total"] += 1
            if mutation and args.inject_errors and serial % 317 == 0:
                handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
                counters["duplicates_injected"] += 1
                counters["total"] += 1
            if mutation and args.inject_errors and serial % 701 == 0:
                bad = dict(record, event_id=f"BAD-{serial:012}")
                if serial % 2:
                    bad["fill_pct"] = 145.0
                else:
                    bad["bin_id"] = "UNKNOWN"
                bad["event_type"] = "sensor_reading"
                handle.write(json.dumps(bad, separators=(",", ":")) + "\n")
                counters["invalid_injected"] += 1
                counters["total"] += 1

        # Explicit zero-stock reading at the period boundary supports mass balance.
        for b in bins:
            emit(event(b, "sensor_reading", start, fill_pct=0.0, weight_kg=0.0,
                       battery_pct=100, temperature_c=27.0), mutation=False)
        for step in range(1, steps + 1):
            now = start + timedelta(minutes=step * args.interval_minutes)
            hour = now.hour + now.minute / 60
            for b in bins:
                bin_id = b["bin_id"]
                # Repeatable morning/evening peaks and a declared rare public event.
                shape = 0.35 + 1.2 * math.exp(-((hour - 8) / 2.5) ** 2) + math.exp(-((hour - 18) / 3) ** 2)
                multiplier = 2.5 if b["area_id"] == "A001" and step > steps // 2 and 17 <= hour < 22 else 1.0
                mean_l = (3.8 if b["waste_type"] == "domestic" else 7.0) * args.interval_minutes / 5
                added_l = round(mean_l * shape * multiplier * rng.uniform(0.45, 1.55), 4)
                added_kg = round(added_l * b["density_kg_l"], 4)
                stock[bin_id] += added_l
                totals["generated_kg"] += added_kg
                emit(event(b, "waste_deposit", now, added_l=added_l, added_kg=added_kg,
                           household_id="" if b["waste_type"] == "industrial" else f"H{1 + step % 50:04}",
                           facility_id=b["facility_id"]))
                fill = min(100.0, round(stock[bin_id] / b["capacity_l"] * 100, 3))
                # One bin loses readings for an explicit two-hour interval; deposits
                # continue so ground truth and observable events remain distinct.
                outage = args.inject_errors and bin_id == "B000001" and 12 <= (now - start).total_seconds()/3600 < 14
                if not outage:
                    reading = event(b, "sensor_reading", now, fill_pct=fill,
                                    weight_kg=round(stock[bin_id] * b["density_kg_l"], 4),
                                    battery_pct=max(35, 100 - step // 80),
                                    temperature_c=round(26 + 4 * math.sin(hour/24 * 2 * math.pi) + rng.uniform(-0.5, .5), 2))
                    # Delayed messages retain original event_time and event_id.
                    if args.inject_errors and serial % 499 == 0:
                        pending.append((step + 4, reading))
                        counters["delayed_injected"] += 1
                    else:
                        emit(reading)
                else:
                    counters["missing_readings_injected"] += 1
                if fill >= 90 and bin_id not in due:
                    due[bin_id] = step + 2 + (int(bin_id[1:]) % 3)
                scheduled = now.minute == 0 and now.hour in (8, 16, 22)
                if (due.get(bin_id, steps + 10) <= step or scheduled) and stock[bin_id] > 0:
                    collected_kg = round(stock[bin_id] * b["density_kg_l"], 4)
                    emit(event(b, "pickup_completed", now, collected_kg=collected_kg,
                               collected_l=round(stock[bin_id], 4), fill_pct=0.0, weight_kg=0.0,
                               team_id=b["team_id"]))
                    totals["collected_kg"] += collected_kg
                    stock[bin_id] = 0.0
                    due.pop(bin_id, None)
            ready = [r for index, r in pending if index <= step]
            pending = [(index, r) for index, r in pending if index > step]
            for record in ready:
                emit(record, mutation=False)
        for _, record in pending:
            emit(record, mutation=False)
        # A sensor snapshot after the final collection/event is the end boundary.
        end = start + timedelta(days=args.days)
        for b in bins:
            emit(event(b, "sensor_reading", end, fill_pct=min(100, round(stock[b["bin_id"]] / b["capacity_l"] * 100, 3)),
                       weight_kg=round(stock[b["bin_id"]] * b["density_kg_l"], 4),
                       battery_pct=99, temperature_c=27.0), mutation=False)
    totals["inventory_end_kg"] = round(sum(stock[b["bin_id"]] * b["density_kg_l"] for b in bins), 4)
    truth = dict(seed=args.seed, bin_count=args.bins, days=args.days, interval_minutes=args.interval_minutes,
                 start=utc(start), end=utc(start + timedelta(days=args.days)), counts=dict(counters),
                 mass_balance=dict(totals), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 assumptions=["No unmeasured removal or material loss; sensor fill saturates at 100%.",
                              "Mass beyond nominal capacity remains in measured stock until pickup.",
                              "Deposits provide simulator ground truth; snapshot weights are not additive."])
    (target / "ground_truth.json").write_text(json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(truth, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/demo")
    parser.add_argument("--bins", type=int, default=24)
    parser.add_argument("--days", type=float, default=2)
    parser.add_argument("--interval-minutes", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--start", default="2026-10-01T00:00:00Z")
    parser.add_argument("--inject-errors", action="store_true")
    args = parser.parse_args()
    if args.bins < 1 or args.days <= 0 or args.interval_minutes < 1:
        parser.error("bins, days, interval-minutes must be positive")
    generate(args)


if __name__ == "__main__":
    main()
