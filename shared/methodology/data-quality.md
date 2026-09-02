# Data Quality

Before analysis, check:

- required columns and data types;
- unique property/date/room-type keys where required;
- arrival/departure ordering and non-negative room nights;
- rate and room-night plausibility;
- duplicate reservation facts and duplicate snapshots;
- status vocabulary and cancellation treatment;
- inventory reconciliation: sellable rooms, out-of-order, sold, and remaining availability;
- date/timezone consistency and currency.

Errors block calculations. Warnings lower confidence and appear in the report. The toolkit does not silently repair contradictory inventory or reservation facts.
