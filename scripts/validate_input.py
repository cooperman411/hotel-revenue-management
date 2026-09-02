#!/usr/bin/env python3
"""Validate the minimal normalized hotel RM input contract using only the stdlib."""
import argparse
import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

PII_TOKENS = {"name", "email", "phone", "address", "payment", "loyalty", "room_number", "employee"}
REQ_RES = {"reservation_key", "stay_date", "room_type", "room_nights", "adr", "status", "booked_at"}
REQ_INV = {"stay_date", "room_type", "sellable_rooms"}

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"{path}: no data rows")
    return rows

def check_date(value, label):
    try:
        date.fromisoformat(value[:10])
    except Exception as exc:
        raise ValueError(f"{label}: invalid date {value!r}") from exc

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--property", required=True)
    parser.add_argument("--reservations", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--market-rates")
    args = parser.parse_args()
    errors, warnings = [], []
    try:
        prop = json.loads(Path(args.property).read_text(encoding="utf-8"))
        for key in ("property_id", "currency", "timezone", "room_types", "rate_policy"):
            if key not in prop:
                errors.append(f"property missing {key}")
        policy = prop.get("rate_policy", {})
        if policy.get("min_rate", 0) > policy.get("max_rate", 0):
            errors.append("rate_policy min_rate exceeds max_rate")
    except Exception as exc:
        errors.append(f"property: {exc}")
        prop = {}
    try:
        reservations = read_csv(args.reservations)
    except Exception as exc:
        reservations = []
        errors.append(str(exc))
    try:
        inventory = read_csv(args.inventory)
    except Exception as exc:
        inventory = []
        errors.append(str(exc))
    for label, rows, required in (("reservations", reservations, REQ_RES), ("inventory", inventory, REQ_INV)):
        if rows:
            missing = required - set(rows[0])
            if missing:
                errors.append(f"{label} missing columns: {', '.join(sorted(missing))}")
            for column in rows[0]:
                if any(token in column.lower() for token in PII_TOKENS):
                    errors.append(f"{label} contains prohibited PII-like column: {column}")
    for index, row in enumerate(reservations, 2):
        try:
            check_date(row["stay_date"], f"reservations row {index} stay_date")
            datetime.fromisoformat(row["booked_at"].replace("Z", "+00:00"))
            if float(row["room_nights"]) < 0 or float(row["adr"]) < 0:
                raise ValueError("negative room_nights or adr")
            if row["status"] not in {"booked", "checked_in", "checked_out", "cancelled", "no_show"}:
                raise ValueError("unknown status")
        except Exception as exc:
            errors.append(f"reservations row {index}: {exc}")
    for index, row in enumerate(inventory, 2):
        try:
            check_date(row["stay_date"], f"inventory row {index} stay_date")
            if int(row["sellable_rooms"]) < 0:
                raise ValueError("negative sellable_rooms")
        except Exception as exc:
            errors.append(f"inventory row {index}: {exc}")
    if not any(row.get("status") in {"booked", "checked_in", "checked_out"} for row in reservations):
        warnings.append("no active or completed reservations")
    result = {"valid": not errors, "errors": errors, "warnings": warnings, "reservation_rows": len(reservations), "inventory_rows": len(inventory)}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
