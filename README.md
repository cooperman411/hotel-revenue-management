# Hotel Revenue Management Toolkit

> **Status: In development.**
>
> This toolkit is a work in progress. It runs end to end on a synthetic demo hotel, with validation, historical analysis, and explainable daily rate recommendations, and human review before any pricing change. Live market-data retrieval is not built yet: Veetal is specified but not implemented, and there is no live Mews connector or live rate-shopper retrieval. See `HOW_TO_USE_THIS_TOOLKIT.md` for what works now and what does not.

An AI/LLM-agnostic, human-supervised toolkit for hotel revenue audits and property-specific rate recommendations.

## Included

- `skills/hotel-revenue-audit/` — audit past performance, future outlook, and the revenue-management process.
- `skills/hotel-rate-optimizer/` — produce explainable daily rate recommendations for a configurable 180+ day horizon.
- `shared/` — intake questionnaire, normalized schemas, evidence rules, methodology, workflows, and report templates.
- `scripts/` — deterministic, dependency-light validation and calculation helpers.
- `adapters/` - generic CSV first, with Mews and market-data integration boundaries (Veetal Connect API specified but not implemented yet, rate shoppers documented).
- `reference-only/` — notes about the supplied Hospitality Manager / revenue-management reference.
- `HOW_TO_USE_THIS_TOOLKIT.md` — human operating guide from questionnaire through approved action.

## Architecture

The toolkit separates evidence collection, deterministic calculations, and interpretation:

1. Import from an API when a supported adapter is available; otherwise export CSV files into the generic CSV adapter.
2. Validate and normalize data without guest or employee PII.
3. Run deterministic calculations for history, pace, availability, market position, and rate recommendations.
4. Have an AI/LLM or analyst interpret structured outputs using the relevant skill and references.
5. Require human review before publishing rates, restrictions, or action plans.

No model, vendor, PMS, CRS, or RMS is required. JSON and CSV contracts are the stable interface.

## Operating principles

- Evidence before explanation; confidence and data gaps are explicit.
- Historical patterns are segmented by property, room type, date, day of week, season, lead time, channel, and occupancy where sample size allows.
- Recommendations are bounded by property-configured floors, ceilings, inventory scarcity, pace, market position, and human overrides.
- A missing signal is not treated as a zero signal.
- The toolkit recommends; an authorized human approves and publishes.

## Offline Review Outputs

See [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md) for the provisional empirical pickup engine, sample HTML report, editable XLSX/CSV, human decisions and approved-rate record. This workflow does not yet complete the full research specification.

## Data Imports and Approved Publishing

See [DATA_AND_PUBLISHING.md](DATA_AND_PUBLISHING.md) for reusable CSV mapping, required export fields, approved-only rate exports, and the offline publishing protocol. Live PMS publishing remains disabled. No PMS-specific CSV format is currently verified.
