---
name: hotel-revenue-audit
description: Audit a hotel's past performance, future outlook, and revenue-management process from structured evidence while protecting PII and separating facts, inferences, and recommendations.
---

# Hotel Revenue Audit

Use this skill when the user needs a hotel revenue audit, performance diagnosis, pace/outlook review, RM process review, data-gap assessment, or an evidence-based action plan.

## Contract

Use the normalized inputs in `../../shared/schemas/` and the evidence rules in `../../shared/methodology/evidence-rules.md`. API exports and generic CSV exports are equivalent after normalization; do not assume a particular PMS, CRS, RMS, or AI provider.

## Workflow

1. Read the intake and identify property context, date scope, comparison sets, objectives, and human decision rights.
2. Validate files and reject direct guest/employee PII. Report missing fields before drawing conclusions.
3. Follow `../../HOW_TO_USE_THIS_TOOLKIT.md` to import evidence and run the provisional future review. Derive descriptive historical metrics transparently from supplied evidence; the engine does not calculate a complete historical audit.
4. Audit three dimensions separately: past performance, future outlook, and RM process maturity.
5. Classify every statement as observed, derived, inferred, or recommended; attach source fields, period, sample size, and descriptive evidence strength. Forecast confidence remains `provisional` or `insufficient` under `../../REVIEW_WORKFLOW.md`.
6. Produce the relevant template from `../../shared/templates/` and an action register with owner, timing, expected impact, and validation metric.
7. Stop short of publishing rates or restrictions. A human must approve operational changes.

## References to read as needed

- `../../shared/methodology/evidence-rules.md`
- `../../shared/methodology/data-quality.md`
- `../../shared/methodology/historical-performance.md`
- `../../shared/methodology/future-outlook.md`
- `../../shared/methodology/rm-process.md`
- `../../shared/workflows/audit.md`

Do not use arbitrary day-of-week or occupancy multipliers. If the evidence does not support a property-specific pattern, state that limitation and recommend a test.
