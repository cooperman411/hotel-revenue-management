# Evidence Rules

Every finding must include:

- classification: `observed`, `derived`, `inferred`, or `recommended`;
- source file/table and fields;
- date range and as-of date;
- segment definition;
- sample size or coverage;
- evidence_strength: `high`, `medium`, or `low`, describing support for a descriptive finding;
- data gaps and assumptions.

Observed facts come directly from supplied data. Derived metrics use transparent arithmetic. Inferences connect multiple observed/derived facts and must say so. Recommendations are decisions to test or take, not facts.

Minimum expectations:

- Do not generalize from a segment with fewer than 10 comparable stay dates or 30 room nights without labeling low evidence strength.
- Compare like with like: room type, rate-plan family, channel, season, stay date, and booking window.
- Use median and percentile summaries when outliers or event dates distort averages.
- Treat missingness as unknown. Never convert unavailable market, event, or pace data into zero.
- Preserve the input's as-of date; a future recommendation cannot use information that would not have been known on that date.

Forecast outputs use `provisional` or `insufficient` confidence, as defined in `REVIEW_WORKFLOW.md`. Descriptive evidence strength is not a forecast-accuracy rating.
