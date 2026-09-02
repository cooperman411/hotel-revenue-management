# Mews adapter placeholder

Implement an API-first connector that fetches only authorized commercial data and converts it to the generic CSV/JSON contract. Keep authentication, property identifiers, pagination, rate limits, and field mappings outside the skills. Do not fetch guest profiles or employee records.

Recommended boundary:

```text
Mews API -> adapter normalization -> shared schemas -> deterministic scripts -> human review
```
