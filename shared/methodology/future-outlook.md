# Future outlook

Use current inventory, bookings known at the analysis timestamp and the provisional empirical pickup outputs described in [REVIEW_WORKFLOW.md](../../REVIEW_WORKFLOW.md). Calendar cutoffs and lead days use the property timezone.

Distinguish current bookings, observed pickup, empirical scenarios and judgment. Forecast confidence is `provisional` or `insufficient`; no calibrated probability or forecast accuracy is established. Missing inventory and unreliable or sparse history remain explicit gaps. Unpicked group blocks exclude reservations already counted and are conservatively assumed to materialize fully.

Events, channel mix, group contribution and competitor conditions can inform a separate human assessment when supplied. They are not hidden inputs to the current model. Do not invent scenarios or claim modeled effects for unsupported signals.
