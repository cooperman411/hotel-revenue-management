# Generic CSV imports

Use `scripts/data_workflow.py import` with a checked reusable mapping profile. Supported tables are reservations, inventory, published rates and optional competitor exports. Outputs contain normalized `rows` and source `provenance`.

Read [DATA_AND_PUBLISHING.md](../../DATA_AND_PUBLISHING.md) for the current fields, privacy rules, mappings and commands. `data_workflow.py analyze` joins normalized internal-data imports and runs the offline review engine. Competitors remain separate review evidence. No live PMS connector is included.
