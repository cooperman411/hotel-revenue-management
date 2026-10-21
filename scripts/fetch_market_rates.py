#!/usr/bin/env python3
"""Fetch market (comp-set) rates and normalize them into the market_rates schema.

Two modes:

1. API mode (default): calls the Nuitee LiteAPI hotel rates endpoint for a
   comp-set of LiteAPI hotel IDs, one one-night request per stay date, then
   normalizes per-date per-room-type medians into market_rates.csv.
   The API key comes ONLY from the NUITEELITE_API_KEY environment variable.
   It is never accepted as a CLI argument, never logged, and never written
   to any output file.

2. Manual mode (--from-csv): validates a hand-entered comp snapshot CSV and
   rewrites it into the canonical output format. This is the no-API demo path.

Output columns: observed_at,stay_date,room_type,property_rate,comp_median_rate,comp_count

Honest caveats (also documented in adapters/market-data/README.md):
- Nuitee rates are the public sell prices in its feed, not certified retail
  BAR from a rate shopper. They work as a market proxy, not as ground truth.
- Room-type normalization is the fragile part. LiteAPI returns free-text
  supplier room names; you must supply --room-map. Unmapped offers are
  skipped and counted, never guessed.
"""
import argparse
import csv
import json
import os
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

API_BASE = "https://api.liteapi.travel/v3.0"
RATES_PATH = "/hotels/rates"
OUTPUT_FIELDS = ["observed_at", "stay_date", "room_type", "property_rate", "comp_median_rate", "comp_count"]


def fail(message):
    print(f"error: {message}", file=sys.stderr)


def median(values):
    values = sorted(values)
    n = len(values)
    if n == 0:
        return None
    mid = n // 2
    if n % 2:
        return round(values[mid], 2)
    return round((values[mid - 1] + values[mid]) / 2.0, 2)


def offer_price(rate):
    """Extract the public sell price from a LiteAPI rate object.

    Prefers retailRate.total[0].amount (the publicly sold price per LiteAPI
    docs), then initialPrice[0].amount, then netRate[0].amount. Returns None
    when nothing usable is found.
    """
    for path in (["retailRate", "total"], ["initialPrice"], ["netRate"]):
        node = rate
        try:
            for key in path:
                node = node[key]
            entry = node[0]
            amount = float(entry["amount"])
            if amount > 0:
                return round(amount, 2)
        except (KeyError, IndexError, TypeError, ValueError):
            continue
    return None


def room_label(rate, offer):
    """Best available room identifier for mapping: mappedRoomId, else name."""
    for source in (offer, rate):
        if isinstance(source, dict) and source.get("mappedRoomId"):
            return str(source["mappedRoomId"])
    name = rate.get("name") or offer.get("name") or ""
    return str(name).strip()


def map_room(label, room_map):
    """Map a supplier room label to a property room_type.

    Exact match first (on mappedRoomId or full name), then case-insensitive
    substring match against the map keys. Returns None when nothing matches;
    the caller counts and skips unmapped offers instead of guessing.
    """
    if not label:
        return None
    if label in room_map:
        return room_map[label]
    lowered = label.lower()
    for key, room_type in room_map.items():
        if key and key.lower() in lowered:
            return room_type
    return None


def liteapi_post(base_url, api_key, payload, timeout):
    """POST JSON to the LiteAPI rates endpoint. Raises on transport/HTTP errors."""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        base_url + RATES_PATH,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {exc.reason}")


def fetch_date(base_url, api_key, hotel_ids, stay, args, room_map):
    """Fetch one stay date and return {(room_type): [(hotel_id, price)]}.

    Raises RuntimeError on any failure; the caller decides how to handle it.
    """
    checkin = stay.isoformat()
    checkout = (stay + timedelta(days=1)).isoformat()
    payload = {
        "hotelIds": hotel_ids,
        "occupancies": [{"adults": args.adults}],
        "currency": args.currency,
        "guestNationality": args.guest_nationality,
        "checkin": checkin,
        "checkout": checkout,
        "maxRatesPerHotel": args.max_rates_per_hotel,
        "roomMapping": True,
        "timeout": max(5, args.timeout - 2),
    }
    if args.margin is not None:
        payload["margin"] = args.margin
    data = liteapi_post(base_url, api_key, payload, args.timeout)
    prices = defaultdict(list)
    unmapped = 0
    hotels = data.get("data") if isinstance(data, dict) else None
    if not isinstance(hotels, list):
        raise RuntimeError("unexpected response shape: missing 'data' array")
    for hotel in hotels:
        hotel_id = hotel.get("hotelId", "?")
        offers = hotel.get("roomTypes") or []
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            rates = offer.get("rates") or []
            for rate in rates:
                if not isinstance(rate, dict):
                    continue
                label = room_label(rate, offer)
                room_type = map_room(label, room_map)
                if not room_type:
                    unmapped += 1
                    continue
                price = offer_price(rate)
                if price is None:
                    unmapped += 1
                    continue
                prices[room_type].append((hotel_id, price))
    return prices, unmapped


def api_mode(args):
    api_key = os.environ.get("NUITEELITE_API_KEY")
    if not api_key:
        fail("NUITEELITE_API_KEY is not set. Export it before running; "
             "the key is never accepted as a CLI argument.")
        return 1
    if args.live and not api_key.startswith("prod_"):
        fail("--live requires a production key (expected a 'prod_' prefix). "
             "Use your 'sand_' sandbox key without --live.")
        return 1
    base_url = args.base_url or API_BASE
    room_map = {}
    if args.room_map:
        with open(args.room_map, encoding="utf-8") as f:
            room_map = json.load(f)
        if not isinstance(room_map, dict):
            fail("--room-map must be a JSON object mapping supplier room labels to room_type values")
            return 1
    else:
        print("warning: no --room-map supplied; all offers will be counted as unmapped "
              "and skipped. This keeps the output honest but empty.", file=sys.stderr)

    if args.checkin and args.checkout:
        start = date.fromisoformat(args.checkin)
        end = date.fromisoformat(args.checkout)
    else:
        start = date.fromisoformat(args.as_of)
        end = start + timedelta(days=args.days)
    hotel_ids = [h.strip() for h in args.hotel_ids.split(",") if h.strip()]
    if not hotel_ids:
        fail("--hotel-ids is empty")
        return 1

    observed_at = args.observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    failed_dates = []
    total_unmapped = 0
    stay = start
    while stay < end:
        try:
            prices, unmapped = fetch_date(base_url, api_key, hotel_ids, stay, args, room_map)
            total_unmapped += unmapped
            for room_type, entries in prices.items():
                hotels_with_data = len({hotel_id for hotel_id, _ in entries})
                comp_median = median([price for _, price in entries])
                if comp_median:
                    rows.append({
                        "observed_at": observed_at,
                        "stay_date": stay.isoformat(),
                        "room_type": room_type,
                        "property_rate": 0,
                        "comp_median_rate": comp_median,
                        "comp_count": hotels_with_data,
                    })
        except RuntimeError as exc:
            failed_dates.append(stay.isoformat())
            fail(f"{stay.isoformat()}: {exc}")
        stay += timedelta(days=1)

    succeeded = (end - start).days - len(failed_dates)
    if succeeded == 0:
        fail("no dates succeeded; nothing written")
        return 1
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "written": args.output,
        "mode": "nuitee-liteapi" + ("-live" if args.live else "-sandbox"),
        "dates_requested": (end - start).days,
        "dates_succeeded": succeeded,
        "failed_dates": failed_dates,
        "rows": len(rows),
        "unmapped_offers_skipped": total_unmapped,
        "note": "property_rate is 0 (data gap); Nuitee prices are feed sell prices, not certified retail BAR",
    }
    print(json.dumps(summary, indent=2))
    return 0


def manual_mode(args):
    observed_at = args.observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(args.from_csv, newline="", encoding="utf-8-sig") as f:
        incoming = list(csv.DictReader(f))
    required = {"stay_date", "room_type", "comp_median_rate"}
    fields = set(incoming[0].keys()) if incoming else set()
    missing = required - fields
    if missing:
        fail(f"manual CSV is missing required columns: {sorted(missing)}")
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
        description="Fetch comp-set market rates (Nuitee LiteAPI or manual CSV) "
                    "and write market_rates.csv for calculate_rates.py --market-rates.")
    parser.add_argument("--from-csv",
                        help="manual mode: hand-entered comp snapshot CSV with columns "
                             "stay_date,room_type,comp_median_rate,comp_count,property_rate")
    parser.add_argument("--hotel-ids",
                        help="comma-separated LiteAPI hotel IDs forming the comp set")
    parser.add_argument("--as-of", default=date.today().isoformat(),
                        help="first stay date when --checkin/--checkout are not given")
    parser.add_argument("--days", type=int, default=14,
                        help="horizon in days from --as-of (API mode, default 14)")
    parser.add_argument("--checkin", help="first stay date (YYYY-MM-DD), overrides --as-of/--days")
    parser.add_argument("--checkout", help="stay date after the last requested date (YYYY-MM-DD)")
    parser.add_argument("--adults", type=int, default=2)
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--guest-nationality", default="US")
    parser.add_argument("--room-map",
                        help="JSON object mapping supplier room labels (or mappedRoomId) to room_type values")
    parser.add_argument("--max-rates-per-hotel", type=int, default=100)
    parser.add_argument("--margin", type=float, default=None,
                        help="optional LiteAPI margin override; omit to use the account default")
    parser.add_argument("--timeout", type=int, default=30, help="per-request timeout in seconds")
    parser.add_argument("--base-url", default=None,
                        help="override the LiteAPI base URL (default https://api.liteapi.travel/v3.0). "
                             "LiteAPI separates sandbox and production by key prefix (sand_ vs prod_).")
    parser.add_argument("--live", action="store_true",
                        help="safety gate: require a prod_ key; without it the script assumes sandbox")
    parser.add_argument("--observed-at",
                        help="override the observed_at timestamp (default: now, UTC)")
    parser.add_argument("--output", required=True, help="output market_rates.csv path")
    args = parser.parse_args()
    if args.from_csv:
        return manual_mode(args)
    if not args.hotel_ids:
        fail("--hotel-ids is required in API mode (or use --from-csv for manual mode)")
        return 1
    return api_mode(args)


if __name__ == "__main__":
    sys.exit(main())
