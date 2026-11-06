# Assistant-neutral execution contract

Keep original evidence, normalized inputs, deterministic analysis, interpretation, human decisions and approved exports separate. The current input is `shared/schemas/analysis_input.json`; property, reservation, inventory, published-rate and competitor row contracts are in the same folder.

CSV imports carry `rows` and provenance, including property, currency, source hash, mapping-profile hash and import timestamp. `scripts/data_workflow.py analyze` verifies their property and currency before joining internal data. An assembled input can call `scripts/review_engine.py` directly. Competitors remain separate evidence.

The engine writes `analysis.json`, `summary.md`, `summary.html`, `recommendations.csv`, `recommendations.xlsx` and an empty approval record. Forecast confidence is `provisional` or `insufficient`. Descriptive audit findings use `evidence_strength` to describe source support, not forecast accuracy.

Keep analysis unchanged when recording human decisions. `review_approvals.py` records decisions; `data_workflow.py export` produces approved-only CSV and an audit. Rate approval and publication authorization are separate. `publishing.py` accepts only its offline mock destination; live writing is disabled.

An assistant may explain evidence but must not alter source facts, hide gaps or convert pending recommendations into approved changes. See the [operating guide](../HOW_TO_USE_THIS_TOOLKIT.md).
