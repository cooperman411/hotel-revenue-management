# Minimal sanitized example

Run from the toolkit root:

```text
python3 scripts/create_questionnaire.py --property-name "Demo Hotel" --output /tmp/demo-hotel-questionnaire.md
python3 scripts/validate_input.py --property examples/minimal/property.json --reservations examples/minimal/reservations.csv --inventory examples/minimal/inventory.csv
python3 scripts/calculate_history.py --reservations examples/minimal/reservations.csv --as-of 2026-09-01 --output /tmp/hotel-history.json
python3 scripts/calculate_rates.py --property examples/minimal/property.json --history /tmp/hotel-history.json --inventory examples/minimal/inventory.csv --reservations examples/minimal/reservations.csv --as-of 2026-09-01 --days 2 --output /tmp/hotel-rates.csv
python3 scripts/validate_findings.py examples/minimal/findings.json
```
