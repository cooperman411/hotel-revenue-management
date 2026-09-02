# How to Use the Hotel Revenue Management Toolkit

## What this toolkit does

This toolkit helps a human revenue manager, consultant, or hotel owner:

1. collect the right information from a hotel;
2. audit past performance, future outlook, and the revenue-management process;
3. calculate explainable daily rate guidance for the next 180 or more days;
4. review the evidence and approve, change, or reject recommendations.

It is a decision-support toolkit, not an autonomous revenue manager. It does not publish rates, change restrictions, or log in to a hotel's systems without a separately authorized integration and human approval.

## The short version

```text
Send questionnaire -> receive exports/API data -> validate and normalize
-> calculate history and rate guidance -> review findings
-> human approves actions -> publish through the hotel's system
```

## Step 1: Create and send the hotel questionnaire

Yes. The toolkit contains the questionnaire at:

`shared/intake/questionnaire.md`

It can also create a clean, sendable copy:

```text
python3 scripts/create_questionnaire.py --property-name "Example Hotel" --output work/example-hotel-questionnaire.md
```

The generated questionnaire asks for property context, the hotel's current revenue process, available systems, historical reports, future inventory, market data, approval rights, and data-governance constraints. It does not ask for guest or employee personal information.

The questionnaire is normally sent by email or shared document. The hotel does not need to install this toolkit to answer it.

## Step 2: Decide how the hotel will provide data

There are two supported operating paths.

### A. API-first path

The preferred long-term path is an approved adapter that retrieves only the commercial data needed for the analysis and converts it into the shared schemas.

The current project includes placeholders for:

- Mews — PMS/API adapter boundary is documented, but the live connector is not implemented yet.
- DataForSEO — market-rate/event research adapter boundary is documented, but the live connector is not implemented yet.

An API login or token should be supplied only through the approved connector's secret-management process. Do not paste credentials into questionnaires, CSV files, Markdown, prompts, or reports. The current toolkit does not request or store API credentials.

### B. Export fallback path — usable now

The hotel exports the relevant reports from its PMS, CRS, booking engine, channel manager, or RMS. A human maps those exports into the generic CSV format.

Required normalized inputs:

- `property.json` — property, room types, currency, and rate guardrails;
- `reservations.csv` — pseudonymous reservation facts, stay date, room type, room nights, ADR, status, booking timestamp, and optional channel/rate plan;
- `inventory.csv` — daily sellable inventory by room type.

Optional inputs:

- `market_rates.csv` — time-stamped property and comp-set rates;
- historical booking snapshots — needed for a stronger pace/forecast comparison;
- event/calendar data — useful for compression and demand explanations.

The hotel may send reports in another format first. A human analyst must map and normalize them before the deterministic scripts use them. PDFs and screenshots can be evidence for a human review, but they are not currently a direct input to the calculation scripts.

## Step 3: Protect the data

Do not provide:

- guest names, email addresses, phone numbers, addresses, payment details, loyalty IDs, room numbers, or free-text guest notes;
- employee names, personal contact information, or employee records;
- API passwords, access tokens, or secret keys.

Use a pseudonymous reservation key such as `r-001`. The toolkit needs commercial facts, not identities.

## Step 4: Validate the package

From the toolkit folder, run:

```text
python3 scripts/validate_input.py \
  --property inputs/property.json \
  --reservations inputs/reservations.csv \
  --inventory inputs/inventory.csv
```

Errors stop the analysis. Warnings are carried into the report and lower confidence. The validator checks required fields, dates, rates, statuses, inventory values, and PII-like column names.

## Step 5: Run the hotel revenue audit

First calculate a historical baseline using the audit as-of date. Excluding future stay dates prevents look-ahead leakage:

```text
python3 scripts/calculate_history.py \
  --reservations inputs/reservations.csv \
  --as-of 2026-09-01 \
  --output work/history.json
```

Then use the audit skill with the shared methodology and templates to produce:

- an executive summary;
- a full audit of past performance;
- a future-outlook review;
- an RM-process assessment;
- a data-gap report;
- an action register.

An AI/LLM may summarize and explain the structured evidence, but it must label observed facts, derived metrics, inferences, and recommendations separately.

## Step 6: Create the rate plan

Run the deterministic rate engine for the desired horizon:

```text
python3 scripts/calculate_rates.py \
  --property inputs/property.json \
  --history work/history.json \
  --inventory inputs/inventory.csv \
  --reservations inputs/reservations.csv \
  --market-rates inputs/market_rates.csv \
  --as-of 2026-09-01 \
  --days 180 \
  --output outputs/rate-recommendations.csv
```

The market-rates option is optional. If it is unavailable, the output says so through its confidence and rationale rather than pretending the market signal is zero.

Each recommendation includes:

- stay date and room type;
- recommended rate and a bounded low/high range;
- current OTB occupancy;
- historical observation count;
- confidence;
- a human-readable rationale;
- `human_decision: pending`.

The engine uses property-specific historical baselines and bounded adjustments for supported signals. It does not assume that every Saturday deserves the same premium or that a fixed occupancy percentage always means the same price change.

## Step 7: Human review and publication

An authorized reviewer examines the recommendations, especially low-confidence or high-impact dates. The reviewer can:

- approve the recommendation;
- modify it and record why;
- reject it;
- defer it pending better data.

The approval record should contain the recommendation ID, decision, reviewer, timestamp, reason, and published value. Only after that review does a human publish approved changes in the hotel's PMS, CRS, booking engine, or RMS.

## What is automated today

Ready now:

- questionnaire template and questionnaire generator;
- generic CSV/JSON data contract;
- PII-aware input validation;
- historical ADR summary by date and day of week;
- bounded daily rate recommendations;
- evidence metadata validation;
- human-review templates and workflows.

Not implemented yet:

- live Mews login/API retrieval;
- live DataForSEO retrieval;
- automatic PDF/report extraction;
- direct rate publication to a PMS, CRS, or RMS;
- a machine-learned elasticity model;
- automatic event or weather feeds.

Those are adapter or product-integration projects, not assumptions hidden inside the skills.

## Recommended first engagement

For a first hotel, use a small, controlled run:

1. send the questionnaire;
2. collect 12–24 months of sanitized reservation and inventory exports plus current on-books data;
3. run an audit for the last completed period and an outlook from the agreed as-of date;
4. generate 180 days of recommendations;
5. review and manually publish only a small test group of dates;
6. compare pickup, ADR, occupancy, RevPAR, cancellations, and displacement outcomes;
7. expand only after the hotel trusts the evidence and approval process.

This creates a useful human/LLM-assisted RMS workflow without making unsupported promises about precision.
