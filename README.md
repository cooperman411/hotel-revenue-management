# Hotel Revenue Management Toolkit

An AI/LLM-agnostic, human-supervised toolkit for hotel revenue audits and property-specific rate recommendations.

## Included

- `skills/hotel-revenue-audit/` — audit past performance, future outlook, and the revenue-management process.
- `skills/hotel-rate-optimizer/` — produce explainable daily rate recommendations for a configurable 180+ day horizon.
- `shared/` — intake questionnaire, normalized schemas, evidence rules, methodology, workflows, and report templates.
- `scripts/` — deterministic, dependency-light validation and calculation helpers.
- `adapters/` — generic CSV first, with Mews and market-data integration boundaries (Nuitee fetch implemented, rate shoppers documented).
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
