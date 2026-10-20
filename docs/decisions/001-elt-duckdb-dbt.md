# ADR-001: ELT on DuckDB + dbt

- **Status:** Accepted · 2026-10-20
- **Context:** The project joins 4 sources (two Olist CSV datasets, an FX API and simulated ad spend) to measure CAC and LTV:CAC by marketing channel. It must run free on a laptop, be reproducible by anyone who clones the repo, and use the same patterns as a company data stack. The data contracts showed that most of the work is cleaning and joining across different grains, and that business rules will change (observation end date, LTV window, revenue definition).
- **Options considered:**
  1. **pandas scripts or notebooks.** Fastest to start, but transformations aren't testable as data contracts, there's no lineage, and the logic ends up in one large file.
  2. **Postgres + hand-written SQL.** A real database, but it needs a server running, and it's a row-oriented engine built for transactions, not analytics.
  3. **BigQuery + dbt.** Closest to many companies' setups, but it needs a cloud account and billing set up, and a reviewer can't run it without credentials.
  4. **DuckDB + dbt (chosen).**
- **Decision:** Load raw data first (ELT), then transform inside DuckDB with dbt in layers: raw → staging → intermediate → marts.
  - ELT keeps raw data replayable. When a business rule changes, I change the SQL and rebuild, with no re-extraction.
  - DuckDB is an in-process, columnar OLAP engine: one file, no server, zero cost, the same analytical design as cloud warehouses.
  - dbt turns every model into a versioned `SELECT` with automatic lineage, and turns the data contracts into tests (`unique`, `not_null`, `relationships`) that block bad data.
- **Consequences:**
  - ➕ Runs with `make` on any laptop and in CI, no credentials needed.
  - ➕ Moves to BigQuery or Snowflake by swapping the dbt adapter (`dbt-duckdb` → `dbt-bigquery`). The models stay almost the same.
  - ➖ DuckDB is single-writer and runs on one machine. It doesn't fit many concurrent users or data larger than one machine can handle. Acceptable here: about 120 MB of data and one pipeline writing.
  - ➖ There's no shared server for a team or a BI tool to connect to. The serving layer will read the DuckDB file directly, or exported marts.
