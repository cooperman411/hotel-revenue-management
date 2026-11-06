# Offline Revenue Review

Run with Python 3.9 or later. No paid services, external calls or live publishing are used.

```sh
python3 examples/review-demo.py
python3 scripts/review_engine.py examples/review-demo/input.json /tmp/revenue-review
python3 -m unittest discover -s tests -v
```

Open `examples/review-demo/summary.html` or `summary.md`. The XLSX has a summary and recommendations sorted by priority. Each row has editable decision, approved rate, reviewer, timestamp and notes columns. CSV is available for other spreadsheet applications. Blank current rates remain blank. Percentages are decimal fractions. The workbook contains calculated values, rather than formulas requiring a specific spreadsheet application.

## Input Contract

The versioned offline engine takes one JSON document as illustrated by `examples/review-demo/input.json`. Preserve the original export separately. Property, currency, explicit timestamp with offset, requested start date, horizon, inventory and reservations are required. Current rate snapshots are optional and must be no older than 24 hours. Inventory is already net of out-of-order rooms; physical inventory, when supplied, must reconcile. `unpicked_group_rooms` means rooms held beyond reservations already counted. Never provide total group rooms in that field.

Reservations can contain individual `stay_date` facts or `arrival` and exclusive `departure` dates. `rooms` is the number of rooms per night. Legacy `room_nights` is accepted only as a per-night count. Do not pass a whole-stay room-night total as the rooms for every night. Conflicting duplicates fail validation; identical records are deduplicated. Cancellation and no-show records require effective timestamps. Date-only booking times and timestamps without offsets are rejected.

Only completed, explicitly reliable historical inventory dates are used. The engine matches room type, weekday and adjacent calendar month within two years. It excludes sold-out dates because their observed bookings do not establish unconstrained demand. At equivalent lead times it reconstructs bookings and subtracts effective cancellations/no-shows, then adds empirical net future pickup to today's bookings. P10/P50/P90, empirical sellout frequency and expected excess rooms describe this provisional scenario distribution. They are not calibrated probabilities or a validated estimate of unconstrained demand. At least five analogous dates are required. Mark `history_reliable` only after checking closure periods, inventory changes and data completeness.

Rate movements use the configured reference, floors, ceilings and movement cap. A verified current rate is the reference when available. A configured compression probability triggers the permitted increase; weak expected occupancy permits half the cap as a decrease. These configurable rules require property validation and are not estimated optimal prices. Low current occupancy alone never triggers a discount. Historical accepted prices are not assumed optimal. Pickup and acceleration are reported as evidence; they are not extrapolated indefinitely.

## Human Review

All recommendations begin pending. Reports and spreadsheets confer no approval. Export explicit decisions as a JSON array with `recommendation_id`, `decision` (`approve`, `modify`, `reject`, `defer`), `reviewer`, an offset-aware `review_timestamp`, and `notes`. A modification also requires `approved_rate`. Non-approval decisions require notes. The original analysis must be retained unchanged.

```sh
python3 scripts/review_approvals.py examples/review-demo/analysis.json examples/review-demo/decisions.json /tmp/approved.json
```

The output preserves original recommendations and decisions in `approval_records`. Only approved and modified values enter `approved_rates`. This is an offline record of an identified human decision, not an authentication system. A later integration must verify reviewer authorization, current inventory/rate freshness, unchanged recommendation provenance and destination mappings before publishing. No generic CSV is assumed compatible with a PMS.

## Limits Requiring Real Data

The synthetic suite verifies calculation and approval behavior. It does not establish predictive accuracy, price elasticity, revenue uplift or probability calibration. Rolling property backtests, season/event alignment, structural-break detection, empirically calibrated cancellation models, weighted analog selection and contribution-based group displacement remain to be implemented and validated. The engine reports group commitments conservatively without inventing wash or ancillary contribution. Competitor feeds are unused; missing competitors never reduce confidence. No rate-shopping vendor is implemented.

The older `calculate_rates.py` remains a legacy occupancy-rule implementation with a booking-date leakage fix. Use this review workflow for the new outputs. Do not treat legacy confidence labels as validated forecasts. The existing history and CSV adapters have not been fully migrated to the new contract.
