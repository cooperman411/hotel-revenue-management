---
name: hotel-rate-optimizer
description: Prepare and explain provisional hotel rate recommendations from normalized booking and inventory exports, with offline human review and approved-only CSV outputs.
---
# Hotel rate review

Use for daily rate guidance over an explicit date range. Give the assistant access to the whole repository, including shared resources and scripts.

Read `../../HOW_TO_USE_THIS_TOOLKIT.md` for the operating path, `../../REVIEW_WORKFLOW.md` for the current engine and `../../DATA_AND_PUBLISHING.md` for mappings and approved exports. The engine is `../../scripts/review_engine.py`; current input schemas are in `../../shared/schemas/`.

1. Confirm the property, timezone, currency, analysis timestamp, date range, room types, rate plans, guardrails and approval owner.
2. Import authorized exports with checked reusable mappings. Exclude guest/employee personal information and credentials. Require reservation, inventory, property and currency consistency. Competitor exports are optional, separate evidence.
3. Run `data_workflow.py analyze` on normalized imports, or `review_engine.py` on an assembled input. Preserve the original evidence and analysis.
4. Explain current bookings, observed pickup, provisional scenarios, configured movements and gaps separately. Forecast confidence is `provisional` or `insufficient`. Empirical sellout frequency is not a calibrated probability. Configured movements are not estimated optimal prices.
5. Present the summary and editable workbook/CSV. Record explicit human decisions in JSON and export approved rates using the documented commands. Transfer spreadsheet decisions explicitly; do not imply automatic ingestion.
6. Require separate authorization and verified destination mappings before operational action. The toolkit cannot write to live PMS systems. The standard CSV is not a verified PMS upload.

Low current occupancy alone must not justify a discount. Do not introduce undocumented multipliers, invent demand or market observations, or claim accuracy, optimal pricing or revenue uplift. Missing competitors do not lower model confidence. Record audit evidence using `../../shared/methodology/evidence-rules.md` and apply `../../shared/workflows/human-review.md`.
