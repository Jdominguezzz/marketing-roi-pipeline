# Marketing ROI Pipeline

**Which marketing channels bring sellers who actually generate revenue, not just cheap leads?**

An end-to-end ELT pipeline (Python · DuckDB · dbt · Dagster) on Olist's public marketplace data: leads → closed deals → seller revenue → CAC and LTV:CAC by channel.

> 🚧 Work in progress. Built in public, phase by phase.

- [Data contracts](docs/data_contracts.md): grain, keys and quality issues for every source table
- [Architecture](docs/architecture.md)
- Decisions: [ADR-001 ELT on DuckDB + dbt](docs/decisions/001-elt-duckdb-dbt.md) · [ADR-002 Idempotent raw loads](docs/decisions/002-idempotent-raw-loads.md)

## Run what exists so far
```bash
uv sync
uv run python -m marketing_pipeline.extract.kaggle_files   # land the Kaggle CSVs
uv run python -m marketing_pipeline.load.duckdb_loader     # load them into DuckDB raw.*
uv run pytest
```
Data: [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and [Marketing Funnel](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist) datasets (CC BY-NC-SA 4.0). Download them into `data/kaggle/`; raw files are not committed.
