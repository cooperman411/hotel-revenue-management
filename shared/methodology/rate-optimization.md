# Rate Optimization Methodology

The baseline is property-specific historical ADR for comparable stay dates, primarily by room type, day of week, and month/season. The engine then applies bounded, explainable adjustments only when supported by available evidence:

1. current OTB occupancy relative to historical occupancy distribution;
2. pace versus historical snapshots, if snapshots exist;
3. inventory scarcity and remaining availability;
4. comp-set median position, if market rates are supplied;
5. room-type scarcity and configured floor/ceiling.

Adjustments are capped by configuration and are not universal multipliers. A missing signal contributes no adjustment and reduces confidence. The output is a recommendation and range, never an automatic live-rate change.

The first engine is intentionally statistical and explainable. A future model may estimate elasticity or optimize expected contribution, but it must be back-tested, monitored for drift, and kept subordinate to human approval.
