# ADR-004: Dagster (software-defined assets) for orchestration

- **Status:** Accepted · 2026-10-20
- **Context:** The pipeline has three extract steps, one load step and 20+ dbt models with 80+ tests. It needs a schedule, retries on the API, a single lineage view from source to mart, and it must respect DuckDB's single-writer limit.
- **Options considered:**
  1. **cron + a shell script:** runs things, but knows nothing about data: no lineage, no retries per step, no history.
  2. **Airflow:** the industry standard, task-based (DAGs of operators). Strong when the work is mostly calling external systems; heavier to run locally, and dbt models stay one opaque task unless extra tooling is added.
  3. **Dagster (chosen):** asset-based. You declare the tables that should exist; Dagster works out the order.
- **Decision:** Dagster with `dagster-dbt`.
  - Landing steps and raw loads are Python assets; raw asset keys match the dbt sources (`olist/…`, `ads/ad_spend`, `fx/fx_rates`), so the graph connects end to end.
  - Every dbt model becomes an asset and every dbt test an asset check, automatically from the manifest.
  - `RetryPolicy` on the FX API asset; a daily schedule at 06:00 Europe/Lisbon.
  - `in_process_executor`: steps run one at a time, because DuckDB allows one writer at a time (ADR-001).
- **Consequences:**
  - ➕ One lineage graph from API call to `mart_channel_summary`; failures stop only what depends on them.
  - ➕ dbt test results show up next to the assets they protect.
  - ➖ No parallelism (accepted for ~120 MB).
  - ➖ Not done yet: daily partitions and backfills on the FX and spend assets (next step).
  - ➖ Airflow is more common in job ads; the concepts (DAG, retries, schedules, idempotent tasks) transfer directly.
