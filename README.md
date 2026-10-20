# Marketing ROI Pipeline

**Which marketing channels bring sellers who actually generate revenue, not just cheap leads?**

An end-to-end ELT pipeline (Python · DuckDB · dbt · Dagster) on Olist's public marketplace data: leads → closed deals → seller revenue → CAC and LTV:CAC by channel.

> 🚧 Work in progress. Built in public, phase by phase.

- [Data contracts](docs/data_contracts.md): grain, keys and quality issues for every source table
- [Architecture](docs/architecture.md)
- Decisions: [ADR-001 ELT on DuckDB + dbt](docs/decisions/001-elt-duckdb-dbt.md) · [ADR-002 Idempotent raw loads](docs/decisions/002-idempotent-raw-loads.md) · [ADR-003 Simulated ad spend](docs/decisions/003-simulated-ad-spend.md)

> ⚠️ **Ad spend is simulated.** Olist does not publish marketing spend. Spend is generated from [config/spend_simulation.yml](config/spend_simulation.yml), calibrated to real lead volume (see ADR-003). Leads, deals, orders and FX rates are real.

## Run what exists so far
```bash
uv sync
uv run python -m marketing_pipeline.extract.kaggle_files    # land the Kaggle CSVs
uv run python -m marketing_pipeline.extract.fx_api          # BRL→EUR rates, incremental
uv run python -m marketing_pipeline.extract.spend_simulator # simulated daily ad spend
uv run python -m marketing_pipeline.load.duckdb_loader      # load everything into DuckDB raw.*
uv run pytest
```
Data: [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and [Marketing Funnel](https://www.kaggle.com/datasets/olistbr/marketing-funnel-olist) datasets (CC BY-NC-SA 4.0). Download them into `data/kaggle/`; raw files are not committed.
