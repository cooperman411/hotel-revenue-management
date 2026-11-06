# Data Imports and Approved Rate Outputs

## Readiness

CSV imports work for reservation-night history, inventory, published rates and customer-authorized competitor exports. Reusable profiles map source headers and identifiers. Standard approved-rate CSV export works. Destination-specific CSV mapping is implemented and tested with a fictional format only. No PMS-specific import format is verified or shipped. The API protocol has a tested offline mock, exact preview approval and a durable attempt ledger. Live API publishing is disabled, with no provider adapter or network transport.

Forecasts remain provisional. Imports, exports and mock publication checks do not establish predictive accuracy.

## First Use

Ask your AI assistant or analyst to configure the property and save a mapping profile using `examples/integration-demo/mapping-profile.json`. Give them the system's unedited export and its field definitions. Check the proposed property, room type and rate plan matches. Confirm currency, time zones, inventory meaning and who may approve rates. The property and export configuration must name the same IANA timezone; analysis and export calendar cutoffs use it. Reuse the checked profile on later runs. Recheck it when export columns or system identifiers change.

| Data | Requirement | What to Request |
|---|---|---|
| Property setup | Required | Stable identifier, currency, time zone, room types and permitted rate rules |
| Reservation history and current bookings | Required | Anonymous stable reservation key, one row per stay night, rooms per night, room type, rate plan, status, booking timestamp with UTC offset, ADR and currency |
| Cancellations and no-shows | Required when present | Effective timestamps; do not use today's status as historical state |
| Inventory | Required | Every stay date and room type, sellable rooms already net of out-of-order rooms |
| Published selling rates | Recommended | Date, room type, rate plan, rate, currency and observation timestamp; achieved ADR is not a current selling rate |
| Physical and out-of-order inventory | Recommended | Counts for reconciliation; unpicked group holds exclude rooms already booked |
| Historical reliability | Recommended | Explicit reviewed reliability flag before dates can enter the empirical forecast |
| Financial detail | Optional | Acquisition cost, tax basis, ancillary contribution and group contribution for future contribution analysis |
| Demand evidence | Optional | Booking snapshots, segments, events, denials, channel and refundability; current import/forecast support is limited to documented mapped fields |
| Competitor exports | Optional | Product conditions, observation time, source and availability; see below |

Remove guest names, email addresses, payment and employee information before import. Keep the original export in the hotel's restricted storage. The normalized output includes its filename, hash and profile hash, but does not copy unrelated source columns. The tool fails on an invalid row and reports its row number. Correct the source or mapping and rerun; it does not silently discard bad rows.

## Routine Use

1. Refresh reservation, inventory and published-rate exports. Import each with the saved profile.
2. Run the review analysis. Open the HTML summary and the priority-sorted workbook described in `REVIEW_WORKFLOW.md`.
3. Record approve, modify, reject or defer, the reviewer, time and reason. Retain the original analysis.
4. Generate the approved-rate CSV. Check its destination property, room types, rate plans, dates and amounts before manual entry or import.
5. Follow the destination system's own preview and confirmation process. Verify the rates afterward and retain the system receipt. CSV export itself does not mean publication succeeded.
6. If an approved connection is supported in the future, review the exact publication batch and separately authorize that batch. Rate approval alone never authorizes publication.

The current toolkit is script-based. An assistant or analyst runs the commands; the manager can review the report and spreadsheet without reading schemas or Python.

## Competitor Strategy

Use a hotel's existing, legally authorized rate-shopper export first. This can come from Lighthouse, RateGain, Amadeus, PriceLabs or another source. No provider-specific column layout is assumed. Map the export once; routine runs import the actual export rather than a manually assembled spreadsheet. If necessary product conditions are absent, request a more detailed authorized export. Do not fill them by guesswork.

Match currency, room class, rate plan, occupancy, length of stay, tax/fee basis, cancellation terms and meal plan. Keep channel, observation time, source, source hotel and availability. The importer rejects stale observations and incompatible conditions. An unavailable offer is not proof that the hotel is physically sold out. Competitor records are preserved separately for review; they do not mechanically alter the provisional pricing model. A hotel with no competitor data can run the full internal-data workflow.

No live commercial API provider is implemented. Any future connection needs documented terms, product comparability and account authorization.

## Approved CSV and Audit

The standard file contains destination property, stay date, room type, rate plan, approved rate, currency, recommendation ID and approval reference. It is an internal contract, not a universal PMS upload. The separate audit keeps the original analysis hash, original recommendation, modified amount, reviewer, review time, reason and destination mappings. Pending, deferred and rejected records are excluded. Missing mappings, unauthorized reviewer names, stale analysis/approval, invalid dates and duplicate destination changes stop export.

Reviewer names are checked against local configuration. This is a local approval record, not identity authentication. Protect the configuration, original analysis and decision files with the hotel's normal access controls. A future live connector must use authenticated reviewer roles and tamper-evident storage.

A destination CSV profile names output columns and their approved-contract sources. `format_export` requires a documented specification, verifier and verified status, checks required columns and rejects unsupported field sources. No real provider format is currently verified. An integrator must additionally implement and test the provider's date, currency, rounding, length-of-stay, tax and identifier constraints. Until then, use the standard file for controlled manual entry or mapping.

## API Protocol and Safeguards

`publishing.py` only accepts its offline `MockDestination`. It cannot connect to a PMS. A preview shows destination, property, dates, room/rate-plan identifiers, current rates, new rates, count and warnings. It includes a hash of the exact batch. Mock execution requires a separate identified authorization for that hash, with a 15-minute expiry. Changed current rates, unknown rates or a changed preview block execution. The mock stores each attempt in SQLite before writing, prevents repeats, reads back successful writes and records verified, failed or uncertain outcomes. There are no automatic retries. Partial failures remain visible in the audit.

Before a live adapter can be enabled, implement a documented provider write/read contract, authenticated connection and reviewer roles, validated property mappings, secret-manager credentials, freshness checks immediately before writes, shared durable idempotency/audit storage and provider-specific readback. Review timeout and rollback behavior using a provider sandbox. Credentials must stay outside repository files, exports and reports. Rates-only adapters must never change availability, restrictions or unrelated plans. No live adapter is shipped here.

If a write is uncertain or fails, stop automatic processing for that change. Read the destination state, reconcile the audit, and obtain a fresh explicit decision before any correction. The audit retains the previous verified rate for a human-controlled reversal; no reversal is automatic.

## Technical Examples

```sh
python3 examples/integration-demo/generate.py
python3 scripts/data_workflow.py import examples/integration-demo/reservations.csv examples/integration-demo/mapping-profile.json reservations 2026-11-07T02:00:00+00:00 /tmp/reservations.json
python3 scripts/data_workflow.py export examples/review-demo/analysis.json examples/review-demo/decisions.json examples/integration-demo/export-config.json 2026-11-07T02:00:00+00:00 /tmp/approved-rates
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

These dates and approvals are fictional fixtures. Routine use must supply the current analysis and time. `assemble_analysis` joins normalized reservation, inventory and optional rate imports into the offline review analysis, verifying import property and currency against the property configuration. The `analyze` command exposes this path; see `HOW_TO_USE_THIS_TOOLKIT.md`. Competitor records remain a separate evidence file. Sample CSVs, normalization results, publication preview, approved export and mock audit are in `examples/integration-demo/`. SQLite ledgers created during tests are temporary and are not committed.
