# Rate Optimization Workflow

1. Confirm the as-of date and horizon.
2. Validate `property.json`, historical/on-books reservations, inventory, and optional market rates.
3. Run `scripts/calculate_history.py --as-of <as-of-date>` to keep future on-books stays out of the historical baseline, then run `scripts/calculate_rates.py`.
4. Review each recommendation's reason, range, confidence, and data gaps.
5. Have an authorized human approve, modify, or reject recommendations.
6. Publish approved changes through the property's existing system and retain the approval record.
7. Measure pickup, ADR, occupancy, RevPAR, cancellation, and displacement outcomes; feed outcomes back into the next review.
