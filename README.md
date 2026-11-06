# Hotel Revenue Management Toolkit

**Status: in development.** This project has not been used or tested with real hotel data, PMS systems, competitor feeds or live websites. Included examples and automated checks use synthetic data only.

**Use at your own risk.** This project is in development and has not been validated with real hotel data or live systems. You are responsible for checking inputs, calculations, recommendations, destination mappings and every operational change. Incorrect outputs or imports can cause financial loss, data loss, or unintended changes to hotel rates and systems. Preserve recoverable backups, verify the destination system's import and recovery procedures, and independently review every change before operational use. The software and documentation are provided without warranty under the [MIT License](LICENSE), which includes a limitation of author liability.

The toolkit supports evidence-based hotel revenue audits and provisional daily rate guidance. It uses reusable CSV imports, an offline empirical pickup engine, review reports, editable XLSX/CSV outputs, recorded human decisions and approved-rate CSV exports. Live PMS retrieval, live competitor retrieval and live rate publishing are not implemented. The only API destination is an offline mock.

## Why this exists

I wanted to explore how an independent hotel could get a useful revenue review from the data it can already export, without first buying a full revenue-management system or market-data subscription. This toolkit turns those files into a provisional outlook, rate recommendations, and a review pack a revenue manager can inspect and challenge. It makes the evidence, gaps, and limits visible so the next human decision is easier.

It favors understandable files, practical steps, and tools that remain useful across different AI assistants and hotel systems. A person reviews each recommendation, records a decision, and controls any later import.

## What makes this different

This is an offline, human-reviewed toolkit for working from hotel exports; it is not a live RMS or automated pricing service. It does not fetch competitor rates, continuously optimize prices, or write to a live PMS. The current engine uses empirical pickup from comparable historical dates and configured guardrails to produce provisional guidance. It keeps uncertainty visible, requires an explicit human decision, and exports only approved values for a separate, hotel-controlled import process.

## Start

Copy this prompt into your AI assistant:

```text
Help me use the Hotel Revenue Management Toolkit in this repository:
https://github.com/cooperman411/hotel-revenue-management

Read README.md and HOW_TO_USE_THIS_TOOLKIT.md, then guide me through an offline review using my hotel's authorized data exports. Explain the required files and any data gaps before analysis. Do not treat recommendations as validated forecasts or attempt live PMS changes.
```

If your assistant cannot open the repository, provide it with the relevant files from this folder. Read [How to use the toolkit](HOW_TO_USE_THIS_TOOLKIT.md) for the full workflow. [Review workflow](REVIEW_WORKFLOW.md) explains the calculation and approval contract. [Data imports and publishing](DATA_AND_PUBLISHING.md) covers reusable mappings, export checks and the offline publication protocol.

- `skills/hotel-revenue-audit/`: interpret supplied evidence for past performance, future outlook and the revenue-management process.
- `skills/hotel-rate-optimizer/`: run and explain provisional rate recommendations for an explicit date range.
- `shared/`: intake, current schemas, methodology and report templates.
- `scripts/`: CSV normalization, empirical review, report generation, human decisions and approved exports.
- `examples/review-demo/` and `examples/integration-demo/`: fictional inputs and outputs.
- `tests/`: offline calculation, mapping and approval checks.

Give an assistant access to the whole repository so the skills can read their shared resources. No particular AI provider or PMS is required. Preserve original evidence outside the repository and keep credentials and hotel/client data out of source control.

## Method and limits

The engine reconstructs bookings at comparable lead times and applies empirical future pickup from reliable, completed, unsold-out historical dates. Configured rate rules bound movements. Outputs use `provisional` or `insufficient` confidence. These labels do not establish forecast accuracy, optimal prices or revenue uplift. Optional competitor exports remain separate review evidence and do not affect the engine's rates or confidence.

A human reviews every recommendation. Approving a rate does not authorize publication. The toolkit cannot make live PMS writes; any manual import must follow the hotel's own review, backup and confirmation process.

## Other public projects by Cooperman411

These are separate projects. They are not prerequisites, dependencies, or additional instructions for using this repository.

- [Hotel Group Sourcing Skill](https://github.com/cooperman411/hotel-group-rfp): An AI-assisted workflow for hotel group RFPs, proposal tracking, comparison, and decision reporting.
- [PT/OS One](https://github.com/cooperman411/plain-text-os-one): A single plain-text document you give an AI assistant to carry forward your preferences, projects, decisions, and recurring tasks.
- [PT/OS Workspace](https://github.com/cooperman411/plain-text-os): A collection of plain-text files an AI assistant can read and update to organize projects, priorities, and workflows.
- [AteBit.Tech](https://github.com/cooperman411/AteBitTech): A curated directory of retro and vintage computing resources.

## License

[MIT License](LICENSE). Copyright (c) 2026 Cooperman411.
