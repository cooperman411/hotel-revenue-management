#!/usr/bin/env python3
"""Normalize a comp snapshot CSV into the market_rates schema.

This script is a test-fixture and demo helper only. It takes a CSV with
columns stay_date,room_type,comp_median_rate,comp_count,property_rate,
validates it, and rewrites it into the canonical market_rates.csv format
for calculate_rates.py --market-rates. The full demo uses it with the
synthetic Harbor View Inn comp snapshot in examples/full-demo/.

It is not a production comp source. Real comp data comes from a subscribed
rate shopping tool export, or from the Veetal Connect API once that adapter
is built. See adapters/market-data/README.md.

Output columns: observed_at,stay_date,room_type,property_rate,comp_median_rate,comp_count
"""
import argparse
import csv
import json
import sys
from datetime import date, datetime, timezone

OUTPUT_FIELDS = ["observed_at", "stay_date", "room_type", "property_rate", "comp_median_rate", "comp_count"]


def fail(message):
    print(f"error: {message}", file=sys.stderr)


def normalize_mode(args):
    observed_at = args.observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(args.from_csv, newline="", encoding="utf-8-sig") as f:
        incoming = list(csv.DictReader(f))
    required = {"stay_date", "room_type", "comp_median_rate"}
    fields = set(incoming[0].keys()) if incoming else set()
    missing = required - fields
    if missing:
        fail(f"input CSV is missing required columns: {sorted(missing)}")
        return 1
    rows = []
    for line_number, row in enumerate(incoming, start=2):
        try:
            stay = date.fromisoformat(row["stay_date"][:10]).isoformat()
        except ValueError:
            fail(f"line {line_number}: bad stay_date {row.get('stay_date')!r}")
            return 1
        room_type = (row.get("room_type") or "").strip()
        if not room_type:
            fail(f"line {line_number}: empty room_type")
            return 1
        try:
            comp_median = round(float(row["comp_median_rate"]), 2)
        except (TypeError, ValueError):
            fail(f"line {line_number}: bad comp_median_rate {row.get('comp_median_rate')!r}")
            return 1
        if comp_median <= 0:
            fail(f"line {line_number}: comp_median_rate must be greater than 0")
            return 1
        try:
            comp_count = int(float(row.get("comp_count") or 0))
            property_rate = round(float(row.get("property_rate") or 0), 2)
        except (TypeError, ValueError):
            fail(f"line {line_number}: bad comp_count or property_rate")
            return 1
        if comp_count < 0 or property_rate < 0:
            fail(f"line {line_number}: comp_count and property_rate must not be negative")
            return 1
        rows.append({
            "observed_at": observed_at,
            "stay_date": stay,
            "room_type": room_type,
            "property_rate": property_rate,
            "comp_median_rate": comp_median,
            "comp_count": comp_count,
        })
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "written": args.output,
        "mode": "manual-csv",
        "rows": len(rows),
        "dates": sorted({r["stay_date"] for r in rows}),
    }, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Normalize a comp snapshot CSV into market_rates.csv "
                    "for calculate_rates.py --market-rates. Test-fixture and "
                    "demo use only; not a production comp source.")
    parser.add_argument("--from-csv", required=True,
                        help="comp snapshot CSV with columns "
                             "stay_date,room_type,comp_median_rate,comp_count,property_rate")
    parser.add_argument("--observed-at",
                        help="override the observed_at timestamp (default: now, UTC)")
    parser.add_argument("--output", required=True, help="output market_rates.csv path")
    args = parser.parse_args()
    return normalize_mode(args)


if __name__ == "__main__":
    sys.exit(main())
