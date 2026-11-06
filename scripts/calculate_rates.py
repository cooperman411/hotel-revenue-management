#!/usr/bin/env python3
"""Generate bounded, explainable daily recommendations from normalized CSV/JSON inputs."""
import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

def clamp(value, lower, upper):
    return max(lower, min(upper, value))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--property", required=True)
    parser.add_argument("--history", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--reservations", required=True)
    parser.add_argument("--market-rates")
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.property, encoding="utf-8") as f: prop = json.load(f)
    with open(args.history, encoding="utf-8") as f: history = json.load(f)
    with open(args.inventory, newline="", encoding="utf-8-sig") as f: inventory = list(csv.DictReader(f))
    with open(args.reservations, newline="", encoding="utf-8-sig") as f: reservations = list(csv.DictReader(f))
    market = {}
    if args.market_rates:
        with open(args.market_rates, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                market[(row["stay_date"][:10], row["room_type"])] = row
    policy = prop["rate_policy"]
    lower = float(policy["min_rate"])
    upper = float(policy["max_rate"])
    cap = float(policy.get("adjustment_cap_pct", .25))
    otb = defaultdict(float)
    # A date-only analysis is the end of that calendar day at the property.
    # Never substitute today's state for the state known at the cutoff.
    cutoff = datetime.combine(date.fromisoformat(args.as_of) + timedelta(days=1), time.min,
                              tzinfo=ZoneInfo(prop["timezone"]))
    for row in reservations:
        if not row.get("booked_at"):
            raise ValueError("reservation missing booked_at; on-the-books state cannot be reconstructed")
        booked_at = datetime.fromisoformat(row["booked_at"].replace("Z", "+00:00"))
        if booked_at.tzinfo is None:
            raise ValueError("booked_at requires a timezone offset")
        if booked_at >= cutoff:
            continue
        if row.get("status") == "booked" and row["stay_date"][:10] >= args.as_of:
            otb[(row["stay_date"][:10], row["room_type"])] += float(row["room_nights"])
    output = []
    start = date.fromisoformat(args.as_of)
    for offset in range(args.days):
        stay_date = start + timedelta(days=offset)
        day = stay_date.isoformat()
        dow = str(stay_date.weekday())
        for row in inventory:
            if row["stay_date"][:10] != day:
                continue
            room_type = row["room_type"]
            sellable = float(row["sellable_rooms"])
            booked = otb[(day, room_type)]
            occupancy = booked / sellable if sellable else 0.0
            segment = history.get("day_of_week", {}).get(dow, {})
            type_segment = history.get("day_of_week_by_room_type", {}).get(room_type, {}).get(dow, {})
            if type_segment.get("adr_median"):
                baseline = type_segment["adr_median"]
                observations = int(type_segment.get("observations", 0))
                reasons = [f"room-type DOW median baseline ${baseline:.2f}"]
            elif segment.get("adr_median"):
                baseline = segment["adr_median"]
                observations = int(segment.get("observations", 0))
                reasons = [f"property DOW median baseline ${baseline:.2f} (pooled, no room-type history)"]
            else:
                baseline = float(policy["default_rate"])
                observations = 0
                reasons = ["configured default baseline; no comparable history"]
            baseline = float(baseline)
            adjustment = 0.0
            if observations >= 10:
                if occupancy >= .80:
                    adjustment += min(cap, .10)
                    reasons.append(f"OTB occupancy {occupancy:.0%} is high")
                elif occupancy <= .30:
                    adjustment -= min(cap, .10)
                    reasons.append(f"OTB occupancy {occupancy:.0%} is low")
            else:
                reasons.append(f"only {observations} comparable observations")
            if sellable and booked >= .90 * sellable:
                adjustment += min(cap, .10)
                reasons.append("remaining inventory is scarce")
            market_row = market.get((day, room_type))
            if market_row and float(market_row.get("comp_median_rate", 0)) > 0:
                comp = float(market_row["comp_median_rate"])
                market_adjustment = clamp((comp * .98) / baseline - 1, -.10, .10)
                adjustment += market_adjustment
                reasons.append(f"market median ${comp:.2f} suggests {market_adjustment:+.0%} position adjustment")
            adjustment = clamp(adjustment, -cap, cap)
            recommended = clamp(baseline * (1 + adjustment), lower, upper)
            spread = max(5.0, recommended * (.05 if observations >= 10 else .10))
            confidence = "high" if observations >= 30 and market_row else ("medium" if observations >= 10 else "low")
            output.append({"recommendation_id": f"{day}-{room_type}", "stay_date": day, "room_type": room_type, "recommended_rate": round(recommended, 2), "low_rate": round(clamp(recommended - spread, lower, upper), 2), "high_rate": round(clamp(recommended + spread, lower, upper), 2), "otb_occupancy": round(occupancy, 4), "historical_observations": observations, "confidence": confidence, "rationale": "; ".join(reasons), "human_decision": "pending"})
    fields = list(output[0]) if output else ["recommendation_id"]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output)
    print(json.dumps({"written": args.output, "recommendations": len(output), "as_of": args.as_of, "days": args.days}, indent=2))

if __name__ == "__main__":
    sys.exit(main())
