# Full demo: Harbor View Inn (synthetic)

A realistic, testable dataset for the hotel revenue skills: a 10-room
boutique hotel (7 standard, 3 deluxe) with 92 days of stay history
(2026-06-01 to 2026-08-31), weekly ADR seasonality, a July 4th peak, a
mid-June soft spell, cancellations and no-shows, group blocks, out-of-order
days, future on-the-books reservations, and a 4-property comp-set snapshot.

Everything is synthetic and deterministic (seed 42), so runs are
reproducible. No PII. Regenerate with `python3 examples/full-demo/generate.py`.

Run the full pipeline from the toolkit root:

```text
python3 scripts/validate_input.py \
  --property examples/full-demo/property.json \
  --reservations examples/full-demo/reservations.csv \
  --inventory examples/full-demo/inventory.csv

python3 scripts/calculate_history.py \
  --reservations examples/full-demo/reservations.csv \
  --as-of 2026-09-01 \
  --output /tmp/hotel-history.json

python3 scripts/fetch_market_rates.py \
  --from-csv examples/full-demo/comp_snapshot.csv \
  --output /tmp/hotel-market.csv

python3 scripts/calculate_rates.py \
  --property examples/full-demo/property.json \
  --history /tmp/hotel-history.json \
  --inventory examples/full-demo/inventory.csv \
  --reservations examples/full-demo/reservations.csv \
  --market-rates /tmp/hotel-market.csv \
  --as-of 2026-09-01 --days 7 \
  --output /tmp/hotel-rates.csv

python3 scripts/validate_findings.py examples/full-demo/findings.json
```

Expected results: input validation passes with 404 reservation rows and
212 inventory rows; history covers 92 dates with a clear Friday/Saturday ADR
premium; rate recommendations come back with a mix of high and medium
confidence (high appears where market data plus 30+ observations exist);
findings validate per the evidence rules.
