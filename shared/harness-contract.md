# AI/LLM-agnostic Harness Contract

The harness may be a script, notebook, workflow tool, agent, or LLM. It must preserve the same boundaries:

```text
inputs -> validation -> deterministic calculations -> structured findings -> human decision -> approved action
```

## Input envelope

```json
{
  "run_id": "string",
  "as_of_date": "YYYY-MM-DD",
  "property": "property.json",
  "reservations": "reservations.csv",
  "inventory": "inventory.csv",
  "market_rates": "market_rates.csv"
}
```

`market_rates` is optional. A missing file is an explicit data gap.

## Output envelope

```json
{
  "run_id": "string",
  "status": "needs_review",
  "findings": [],
  "recommendations": [],
  "data_gaps": [],
  "human_review": {"decision": "pending", "reviewer": null, "timestamp": null}
}
```

The model layer may summarize or explain but must not alter source facts, hide data gaps, or turn pending recommendations into approved actions. Any publisher is a separate, authorized integration.
