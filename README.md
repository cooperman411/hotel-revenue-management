# Hotel Revenue Management Toolkit

Use authorized hotel exports to review revenue performance and prepare provisional daily rate recommendations. Review the results offline and export approved rates for a separate, hotel-controlled import.

**In development.** The toolkit has been tested only with synthetic data.

## Start

Paste this prompt into your AI assistant.

```text
Help me use the Hotel Revenue Management Toolkit in this repository.
https://github.com/cooperman411/hotel-revenue-management

Read README.md and HOW_TO_USE_THIS_TOOLKIT.md. Check my authorized hotel exports and explain any data gaps. Guide me through an offline review. Treat rate recommendations as provisional.
```

If your assistant cannot open the repository, provide the relevant files, including the shared resources the skills reference. Keep original hotel records in private storage and keep credentials and hotel data out of source control.

## Why This Exists

I wanted to see what an independent hotel could learn from the data it can already export. The toolkit turns those files into a provisional outlook and a review report. A revenue manager can inspect the evidence, see where data is missing, and decide which rates to approve. The toolkit works across AI assistants and uses files the hotel can retain.

## What the Toolkit Includes

- `skills/hotel-revenue-audit/` reviews evidence on past performance, the outlook, and the hotel's revenue process.
- `skills/hotel-rate-optimizer/` prepares and explains provisional rate recommendations for a specified date range.
- `shared/` contains intake guides, data formats, methodology, and report templates.
- `scripts/` handles CSV imports, offline calculations, reports, editable XLSX or CSV outputs, approval records, and approved-rate CSV exports.
- `examples/review-demo/` and `examples/integration-demo/` contain fictional inputs and outputs.
- `tests/` checks offline calculations, mappings, and approvals.

See [How to Use the Toolkit](HOW_TO_USE_THIS_TOOLKIT.md), [Review Workflow](REVIEW_WORKFLOW.md), and [Data Imports and Publishing](DATA_AND_PUBLISHING.md).

## Method and Limits

The toolkit uses booking activity from comparable historical dates to estimate how many more bookings may arrive. It uses completed dates with reliable data and excludes sold-out dates. Configured rate rules limit changes. The engine reports confidence as `provisional` or `insufficient`. Treat these as review labels and verify the evidence before relying on the output. Competitor exports can inform human review and remain separate from rate calculations.

The toolkit runs offline and uses an offline mock as its only API destination. Supply authorized hotel exports and include competitor exports if available.

## Before Operational Use

Check inputs, calculations, and recommendations independently. Record a decision for each rate before export. Before importing approved rates, verify the destination mappings. Preserve recoverable backups and follow the hotel's import, confirmation, and recovery procedures.

Errors can change rates, damage data, or cause financial loss. Use the toolkit at your own risk under the [MIT License](LICENSE), which limits liability and provides the software and documentation without warranty.

## Public Projects

- [AteBit.Tech](https://github.com/cooperman411/AteBitTech)
- [AI Sales Prospecting & Outreach](https://github.com/cooperman411/ai-sales-prospecting-outreach)
- [AI Social Publishing for Muse](https://github.com/cooperman411/ai-social-publishing)
- [Hotel Group Sourcing Skill](https://github.com/cooperman411/hotel-group-rfp)
- [Hotel Revenue Management Toolkit](https://github.com/cooperman411/hotel-revenue-management)
- [PT/OS One](https://github.com/cooperman411/plain-text-os-one)
- [PT/OS Workspace](https://github.com/cooperman411/plain-text-os)

## License

[MIT License](LICENSE). Copyright (c) 2026 Cooperman411.
