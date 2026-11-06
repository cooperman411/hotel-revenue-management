# How to use the toolkit

**In development.** All supplied examples are fictional. No real hotel data, PMS or live website has been used to validate this project. Read the [use-at-your-own-risk notice](README.md) and [MIT License](LICENSE) before use.

## 1. Define the job

Use `shared/intake/questionnaire.md` to record the property, timezone, currency, room types, scope, analysis timestamp, forecast dates, rate guardrails and human approver. Create a copy if useful:

```sh
python3 scripts/create_questionnaire.py --property-name "Example Hotel" --output /tmp/hotel-questionnaire.md
```

Keep guest and employee personal information, credentials and hotel files outside this repository. Retain originals in the hotel's restricted storage. Sending the questionnaire requires the user's authorization.

## 2. Import exports with a checked profile

Use the hotel's authorized exports. Map headers and identifiers with `examples/integration-demo/mapping-profile.json`; check property, room type, rate plan, currency and time meaning before reuse. Required tables are reservation-night facts and daily inventory. Published rates are recommended. Competitor exports are optional, remain separate evidence, and do not influence model rates or confidence. No live retrieval connector is included.

See [DATA_AND_PUBLISHING.md](DATA_AND_PUBLISHING.md) for fields and mapping rules. Each CSV import produces a JSON envelope containing `rows` and `provenance`:

```sh
python3 scripts/data_workflow.py import /private/hotel/reservations.csv /private/hotel/mapping-profile.json reservations 2026-11-07T02:00:00+00:00 /tmp/reservations.json
```

Repeat for `inventory` and, when available, `rates` and `competitors`. Use actual job paths and timestamps. Import errors identify a row and block the import. Correct the source or mapping rather than discarding rows. Imported property and currency must match the analysis configuration.

## 3. Run the offline review

Use Python 3.9 or later. Configure the property with `shared/schemas/property.json`; use an IANA timezone such as `America/Los_Angeles`. Calendar cutoffs and lead days use that property timezone, independent of the timestamp's supplied offset.

```sh
python3 scripts/data_workflow.py analyze --property /private/hotel/property.json --reservations /tmp/reservations.json --inventory /tmp/inventory.json --rates /tmp/rates.json --as-of 2026-11-07T02:00:00+00:00 --start 2026-11-20 --days 180 --output /tmp/hotel-review
```

Omit `--rates` when unavailable. The horizon is explicit and requires inventory coverage for each requested date and room type. Missing inventory is reported. Dates without enough reliable historical analogs receive `insufficient` confidence and hold the reference rate within guardrails. A missing current selling rate is flagged; the configured default becomes the reference.

An already assembled input follows `shared/schemas/analysis_input.json` and can use the same engine directly:

```sh
python3 scripts/review_engine.py examples/review-demo/input.json /tmp/hotel-review
```

See [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md) for assumptions and limits. Synthetic checks validate software behavior, not real-world accuracy.

## 4. Interpret the evidence

Open `summary.html` or `summary.md`, and `recommendations.xlsx` or `.csv`. Retain `analysis.json`. Recommendations are pending, with explicit gaps, rationale and provisional forecast fields. Reviewed inventory reliability must be supplied before a historical date can become an analog. Competitor absence does not reduce confidence.

For an audit, use `skills/hotel-revenue-audit/SKILL.md` and the shared templates to assess supplied past-performance evidence, the provisional future outlook and the hotel's process separately. The review engine does not calculate a complete historical ADR/occupancy/RevPAR audit. Have an analyst derive and document those metrics from the supplied evidence. Unsupported conclusions remain gaps.

## 5. Record human decisions

Record approve, modify, reject or defer in a JSON array using the fields in [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md). Editable spreadsheet decisions must be explicitly transferred into that array; no spreadsheet-to-JSON importer is included.

```sh
python3 scripts/review_approvals.py /tmp/hotel-review/analysis.json /private/hotel/decisions.json /tmp/approved.json
```

Keep the original analysis and decision history. Rates are not published by this command.

## 6. Export approved rates

Configure authorized reviewers, the property timezone, freshness limits and destination identifiers as shown in `examples/integration-demo/export-config.json`.

```sh
python3 scripts/data_workflow.py export /tmp/hotel-review/analysis.json /private/hotel/decisions.json /private/hotel/export-config.json 2026-11-07T03:00:00+00:00 /tmp/approved-rates
```

Only approved or modified rates enter the export. The standard CSV is an internal contract, not a verified PMS upload format. Check every field against the destination specification, preserve backups and use its own preview/confirmation process before manual import. Rate approval alone does not authorize publication. Live publishing is disabled.

## Synthetic examples and checks

```sh
python3 examples/review-demo.py
python3 examples/integration-demo/generate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

These commands use fictional local inputs and the offline mock. They do not contact hotel systems, validate predictive accuracy or authorize operational use.
