# Provisional rate guidance

Use `scripts/review_engine.py` and [REVIEW_WORKFLOW.md](../../REVIEW_WORKFLOW.md). Reconstruct bookings at equivalent lead times for reliable completed historical dates matching room type, weekday and adjacent month within two years. Exclude sold-out dates and dates with unpicked group blocks. Add empirical net future pickup to current bookings, scaled by inventory.

At least five analogs are required for provisional P10/P50/P90 demand, expected occupancy and empirical sellout frequency. These are uncalibrated scenarios, not validated unconstrained-demand probabilities. Fewer analogs produce insufficient support and no forecast-driven movement.

Use a fresh published rate as the reference when available, otherwise flag the configured default reference. Configured compression and expected-occupancy thresholds determine bounded movements within rate floors and ceilings. These are explicit decision rules, not estimated optimal prices. Low current occupancy alone never triggers a discount. Competitor exports remain separate evidence and do not change rates or confidence.

The engine does not establish elasticity, contribution-based displacement, forecast accuracy or revenue uplift. Every recommendation starts pending and requires an identified human decision. Live rate publishing is disabled.
