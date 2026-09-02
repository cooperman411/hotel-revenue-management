---
name: hotel-rate-optimizer
description: Generate explainable, property-specific daily hotel rate recommendations for future dates using historical behavior, on-books pace, inventory, market rates, and human review.
---

# Hotel Rate Optimizer

Use this skill when the user needs daily rate guidance, a 180/365-day rate plan, pace-based pricing, BAR recommendations, or a lightweight human-supervised RMS workflow.

## Contract

Use the normalized inputs in `../../shared/schemas/`. The deterministic engine is `../../scripts/calculate_rates.py`; its output is advisory and must be reviewed before publication.

## Workflow

1. Confirm the as-of date, horizon, room types, rate-plan scope, currency, floors/ceilings, and approval owner.
2. Validate that inputs contain no guest or employee PII and identify absent signals such as market rates, event data, or historical booking snapshots.
3. Establish property-specific baselines from history: date-of-week/season ADR, occupancy response, lead-time pace, cancellation behavior, and sample size.
4. Calculate current OTB occupancy and pace against comparable historical booking curves where snapshots exist.
5. Generate a bounded recommendation with a recommended rate, range, confidence, rationale, and explicit data gaps.
6. Apply human overrides only with a recorded reason, approver, and expiry/review date.
7. Export the recommendation register. Do not push rates to a live system without separate authorized integration and approval.

## Decision rules

- Never hard-code rules such as “Saturday +25%” or “80% occupancy +30%.” Estimate premiums and discounts from this property's own comparable observations.
- Prefer robust medians/percentiles and minimum sample sizes over unstable small segments.
- Treat comp-set data as a position signal, not as a mandate to follow competitors.
- Bound outputs by the property's configured minimum and maximum rates and keep a human-readable explanation for each change.
- If a signal is unavailable, omit it and lower confidence; do not substitute a zero or pretend the signal was observed.

## References to read as needed

- `../../shared/methodology/evidence-rules.md`
- `../../shared/methodology/data-quality.md`
- `../../shared/methodology/rate-optimization.md`
- `../../shared/workflows/rate-optimization.md`
- `../../shared/workflows/human-review.md`
