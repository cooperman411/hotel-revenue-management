#!/usr/bin/env python3
"""Generate a deterministic synthetic 92-day dataset for Harbor View Inn.

A 10-room boutique hotel (7 standard, 3 deluxe) with weekly seasonality,
a July 4th peak, and a soft mid-June period. Deterministic (seeded RNG),
no PII. Produces property.json, reservations.csv, inventory.csv.

Run from the toolkit root:
    python3 examples/full-demo/generate.py
"""
import csv
import json
import random
from datetime import date, timedelta

SEED = 42
rng = random.Random(SEED)

START = date(2026, 6, 1)
DAYS = 92  # through 2026-08-31
AS_OF = date(2026, 9, 1)

OCC_BY_DOW = {0: 0.45, 1: 0.55, 2: 0.60, 3: 0.55, 4: 0.85, 5: 0.92, 6: 0.50}
ADR_BASE = {"standard": 189, "deluxe": 269}
ADR_DOW_BUMP = {0: 0, 1: 8, 2: 12, 3: 10, 4: 28, 5: 42, 6: 6}
ROOMS = {"standard": 7, "deluxe": 3}


def demand(day):
    occ = OCC_BY_DOW[day.weekday()]
    mult, bump = 1.0, 0
    if date(2026, 7, 3) <= day <= date(2026, 7, 5):   # July 4th weekend
        mult, bump = 1.12, 66
    if date(2026, 6, 14) <= day <= date(2026, 6, 24):  # soft spell
        mult, bump = 0.62, -14
    return occ * mult, bump


def pick_stays(room_type, day, occupied_rooms):
    """Split occupied rooms into stays with plausible lengths of stay."""
    stays, remaining = [], occupied_rooms
    while remaining > 0:
        los = rng.choice([1, 1, 1, 2, 2, 3])
        los = min(los, remaining)
        stays.append(los)
        remaining -= los
    return stays


def main():
    root = START
    reservations, inventory, rid = [], [], 0

    for offset in range(DAYS):
        day = root + timedelta(days=offset)
        dow = day.weekday()
        occ, adr_bump = demand(day)
        group_std = 2 if dow in (4, 5) and day.month == 6 and offset % 3 == 0 else 0
        ooo_std = 1 if date(2026, 7, 13) <= day <= date(2026, 7, 15) else 0
        for room_type, rooms in ROOMS.items():
            sellable = rooms
            group_block = group_std if room_type == "standard" else 0
            ooo = ooo_std if room_type == "standard" else 0
            available = sellable - group_block - ooo
            target = int(round(available * min(occ, 1.0)))
            taken = 0
            for los in pick_stays(room_type, day, target):
                taken += los
                if taken > available:
                    break
                status = "checked_out"
                roll = rng.random()
                if roll < 0.08:
                    status = "cancelled"
                elif roll < 0.10:
                    status = "no_show"
                plan_roll = rng.random()
                adr = ADR_BASE[room_type] + ADR_DOW_BUMP[dow] + adr_bump
                adr = max(99, adr + rng.randint(-10, 10))
                if plan_roll < 0.20:
                    plan = "ADVANCE"
                    adr = round(adr * 0.90)
                    lead = rng.randint(21, 45)
                elif plan_roll < 0.30 and dow in (1, 2, 3):
                    plan = "CORPORATE"
                    adr = round(adr * 0.85)
                    lead = rng.randint(2, 10)
                else:
                    plan = "BAR"
                    lead = rng.randint(0, 21)
                channel = rng.choice(["direct", "direct", "ota", "gds"])
                rid += 1
                reservations.append({
                    "reservation_key": f"r-{rid:04d}",
                    "stay_date": day.isoformat(),
                    "room_type": room_type,
                    "room_nights": los,
                    "adr": adr,
                    "status": status,
                    "booked_at": (day - timedelta(days=lead)).isoformat() + "T12:00:00+00:00",
                    "channel": channel,
                    "rate_plan": plan,
                })
            inventory.append({
                "stay_date": day.isoformat(),
                "room_type": room_type,
                "sellable_rooms": sellable,
                "out_of_order_rooms": ooo,
                "group_block_rooms": group_block,
            })

    # Future bookings (on-the-books) for the rate-optimizer path, as of 2026-09-01
    for i in range(1, 15):
        day = date(2026, 9, 1) + timedelta(days=i)
        if i % 2 == 0:
            rid += 1
            reservations.append({
                "reservation_key": f"r-{rid:04d}",
                "stay_date": day.isoformat(),
                "room_type": "standard",
                "room_nights": 2,
                "adr": 209,
                "status": "booked",
                "booked_at": "2026-08-25T12:00:00+00:00",
                "channel": "direct",
                "rate_plan": "BAR",
            })
        for room_type in ROOMS:
            inventory.append({
                "stay_date": day.isoformat(),
                "room_type": room_type,
                "sellable_rooms": ROOMS[room_type],
                "out_of_order_rooms": 0,
                "group_block_rooms": 0,
            })

    base = "examples/full-demo"
    with open(f"{base}/reservations.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(reservations[0].keys()))
        writer.writeheader()
        writer.writerows(reservations)
    with open(f"{base}/inventory.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(inventory[0].keys()))
        writer.writeheader()
        writer.writerows(inventory)
    prop = {
        "property_id": "harbor-view-inn",
        "property_name": "Harbor View Inn",
        "currency": "USD",
        "timezone": "America/Los_Angeles",
        "room_types": [{"room_type": rt, "sellable_rooms": n} for rt, n in ROOMS.items()],
        "rate_policy": {"min_rate": 129, "max_rate": 499, "default_rate": 199,
                        "adjustment_cap_pct": 0.25},
    }
    with open(f"{base}/property.json", "w", encoding="utf-8") as f:
        json.dump(prop, f, indent=2)
    print(f"reservations: {len(reservations)} rows, inventory: {len(inventory)} rows")


if __name__ == "__main__":
    main()
