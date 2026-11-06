# Rate review workflow

1. Confirm property, timezone, currency, explicit analysis timestamp, forecast dates, room types, rate plans, guardrails and approval owner.
2. Import reservation, inventory and optional published-rate exports with checked mappings. Retain source provenance. Keep competitor exports separate.
3. Run `scripts/data_workflow.py analyze`, or pass an assembled current input to `scripts/review_engine.py`.
4. Review coverage, provisional scenarios, reference rates, configured movements and gaps in the report and workbook.
5. Record explicit human decisions with `scripts/review_approvals.py`; retain original analysis and decisions.
6. Generate approved-only CSV with `scripts/data_workflow.py export`. Check destination format and mappings before any separately authorized manual import.
7. Record verified destination outcomes separately. Live publishing is disabled; the included API protocol is an offline mock only.
