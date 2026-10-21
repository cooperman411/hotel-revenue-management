# Market-Data Adapter

The market-data adapter is the boundary between external market signals and
the toolkit's deterministic rate engine. It is source-agnostic: any source
that can produce the `market_rates` schema contract is accepted, and sources
are interchangeable without changing the engine.

## The contract

Normalize observations into `shared/schemas/market_rates.json`:

- `observed_at` - when the data was collected (date-time);
- `stay_date` - the future stay date the rate applies to (date);
- `room_type` - the property's own room type (standard, deluxe, suite);
- `property_rate` - the property's own rate for that date and room type,
  when known; 0 is allowed and is treated as a data gap, not as a real rate;
- `comp_median_rate` - the median observed competitor rate for that date
  and room type; must be greater than 0 to be used;
- `comp_count` - how many competitor hotels contributed to the median.

The engine uses `comp_median_rate` as a position signal only. It applies at
most a 10 percent adjustment toward or away from the comp median, and it
treats a missing market file as an explicit data gap (confidence drops, the
rate is not faked as zero). See `scripts/calculate_rates.py` and
`shared/methodology/rate-optimization.md`.

## Recommended sources

1. **Hotel rate shoppers (primary recommended path).** Lighthouse
   (formerly OTA Insight), RateGain, and similar rate-intelligence tools are
   built specifically for comp-set pricing. They normalize competitor rates
   by stay date and room category, which is exactly what this schema wants.
   Export their comp-set report, map it to the schema (CSV column order is
   documented below), and feed it to `calculate_rates.py --market-rates`.
2. **Nuitee LiteAPI (implemented path).** `scripts/fetch_market_rates.py`
   calls the Nuitee LiteAPI hotel rates endpoint and normalizes per-date,
   per-room-type medians from a comp-set hotel list. A free sandbox with
   production-like test data is available for development and demos. Two
   honest caveats, stated here on purpose:
   - Nuitee rates are wholesale-style sellable rates, not retail BAR. They
     work as a market proxy, but they are not Expedia or Booking.com retail
     prices. Say what they are in any demo or report.
   - Room-type normalization is the fragile part. Nuitee returns room
     offers; you must map supplier room names or codes to your property's
     room types with a `--room-map` config. Where mapping is uncertain,
     record fewer observations rather than confident guesses.
3. **Manual CSV (no-API path).** For a first engagement or a demo, a
   hand-entered comp snapshot is completely acceptable. The same script
   accepts `--from-csv` with columns
   `stay_date,room_type,comp_median_rate,comp_count,property_rate` and
   rewrites it into the canonical output format with validation.
4. **DataForSEO (experimental, demand signals only).** DataForSEO is a
   generic SEO and search-results data vendor, not a hotel industry tool.
   It is not named as a rate source: its results page prices are lead-in
   prices, not room-type prices, and large-scale harvesting sits in a terms
   gray zone. It remains an experimental option for event and demand
   signals, not for rate data.

## Evidence rules (apply to every source)

- Record source, `observed_at` freshness, and `comp_count` coverage on every
  row. A single-hotel "median" is a weak signal; say so in the data-gap
  report rather than hiding it.
- Record collection errors (timeouts, partial dates, unmapped rooms) and
  omit failed dates instead of filling them with guesses. Partial success
  must be explicit.
- Never treat scraped, wholesale, or incomplete data as ground truth. The
  engine already bounds market influence and lowers confidence when data is
  thin; the adapter's job is to give it honest inputs.
- Never include guest or employee PII. Market data is property-level and
  public by nature; keep it that way.

## Output format

The adapter writes `market_rates.csv` with exactly this header:

```text
observed_at,stay_date,room_type,property_rate,comp_median_rate,comp_count
```

Example row:

```text
2026-09-01T09:00:00Z,2026-09-05,standard,0,228.50,4
```

Feed it to the rate engine with:

```text
python3 scripts/calculate_rates.py \
  --property inputs/property.json \
  --history work/history.json \
  --inventory inputs/inventory.csv \
  --reservations inputs/reservations.csv \
  --market-rates inputs/market_rates.csv \
  --as-of 2026-09-01 \
  --days 180 \
  --output outputs/rate-recommendations.csv
```
