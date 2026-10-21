#!/usr/bin/env python3
"""Create transparent daily and day-of-week history summaries."""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date

ACTIVE = {"booked", "checked_in", "checked_out"}

def percentile(values, quantile):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * quantile
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return round(values[low] + (values[high] - values[low]) * (position - low), 2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reservations", required=True)
    parser.add_argument("--as-of", help="Exclude stay dates on or after this date from the historical baseline")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.reservations, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    daily = defaultdict(lambda: {"rooms": 0.0, "revenue": 0.0, "adrs": []})
    dow = defaultdict(lambda: {"rooms": 0.0, "revenue": 0.0, "adrs": []})
    dow_room_type = defaultdict(lambda: defaultdict(lambda: {"rooms": 0.0, "revenue": 0.0, "adrs": []}))
    for row in rows:
        if row.get("status") not in ACTIVE:
            continue
        stay_date = date.fromisoformat(row["stay_date"][:10])
        if args.as_of and stay_date >= date.fromisoformat(args.as_of):
            continue
        room_type = row.get("room_type") or "all"
        rooms = float(row["room_nights"])
        adr = float(row["adr"])
        revenue = rooms * adr
        for key, target in ((stay_date.isoformat(), daily), (str(stay_date.weekday()), dow)):
            target[key]["rooms"] += rooms
            target[key]["revenue"] += revenue
            target[key]["adrs"].append(adr)
        segment = dow_room_type[room_type][str(stay_date.weekday())]
        segment["rooms"] += rooms
        segment["revenue"] += revenue
        segment["adrs"].append(adr)
    result = {"daily": {}, "day_of_week": {}, "day_of_week_by_room_type": {}, "source_rows": len(rows)}
    for key, value in daily.items():
        result["daily"][key] = {"room_nights": round(value["rooms"], 2), "revenue": round(value["revenue"], 2), "adr_median": percentile(value["adrs"], .5), "adr_p25": percentile(value["adrs"], .25), "adr_p75": percentile(value["adrs"], .75), "observations": len(value["adrs"])}
    for key, value in dow.items():
        result["day_of_week"][key] = {"room_nights": round(value["rooms"], 2), "revenue": round(value["revenue"], 2), "adr_median": percentile(value["adrs"], .5), "adr_p25": percentile(value["adrs"], .25), "adr_p75": percentile(value["adrs"], .75), "observations": len(value["adrs"])}
    for room_type, segments in dow_room_type.items():
        result["day_of_week_by_room_type"][room_type] = {
            key: {"room_nights": round(value["rooms"], 2), "revenue": round(value["revenue"], 2), "adr_median": percentile(value["adrs"], .5), "adr_p25": percentile(value["adrs"], .25), "adr_p75": percentile(value["adrs"], .75), "observations": len(value["adrs"])}
            for key, value in segments.items()
        }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps({"written": args.output, "daily_dates": len(daily), "day_of_week_segments": len(dow)}, indent=2))

if __name__ == "__main__":
    sys.exit(main())
