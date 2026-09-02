# Generic CSV adapter

The generic adapter is the fallback for exports from any PMS, CRS, RMS, booking engine, or market source. Map source columns to the normalized contracts in `../../shared/schemas/` and keep one fact per row.

Required files:

- `property.json`
- `reservations.csv`
- `inventory.csv`

Optional:

- `market_rates.csv`
- historical reservation snapshots with an `as_of_date` column

Never include direct guest or employee PII. Keep source-to-normalized mappings in a separate versioned mapping file.
