# Competitor export import

Use a hotel's existing, authorized rate-shopper export. The reusable mapping profile in `scripts/data_workflow.py` normalizes columns and identifiers; no provider-specific layout or live retrieval connector is included.

The current row contract is `shared/schemas/competitors.json`. Preserve hotel, date, room class, rate plan, currency, occupancy, length of stay, tax basis, cancellation terms, meal plan, channel, observation timestamp, source, reliability and availability. The importer rejects mismatched product conditions and stale observations. An unavailable offer does not prove physical sellout.

Competitor records remain a separate evidence file for human comparison. They do not alter recommendations or confidence in the empirical engine. A hotel with no competitor data can use the full internal-data workflow.

See [data imports](../../DATA_AND_PUBLISHING.md) for the current import contract and rights checks. Do not invent missing product conditions or request credentials in repository files.
