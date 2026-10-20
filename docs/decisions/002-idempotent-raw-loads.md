# ADR-002: Idempotent raw loads with CREATE OR REPLACE

- **Status:** Accepted · 2026-10-20
- **Context:** Pipelines fail and get retried. A load that appends on every run duplicates rows, and duplicated rows silently inflate revenue and CAC. The Kaggle sources are **snapshots**: each delivery is the full table, so only the latest landed version should be loaded. The ad-spend and FX sources (Phase 2) will be **incremental**: each file adds new rows.
- **Options considered:**
  1. **Append (`INSERT INTO`)**: simplest, but not idempotent; every retry duplicates.
  2. **Delete-then-insert by `_source_file`**: idempotent and only touches the changed file; more code, and needed when a table is too big to rebuild.
  3. **`CREATE OR REPLACE TABLE` from the landed files (chosen)**: each run rebuilds `raw.<table>` from scratch.
- **Decision:** Option 3. For snapshot sources, load only the latest `ingest_date` partition of each file. Land files only when their md5 hash is new, and skip hidden files and folders (e.g. Jupyter checkpoints). Load every column as VARCHAR, plus `_source_file` and `_loaded_at` lineage columns.
- **Consequences:**
  - ➕ Running once or ten times gives the same table, proven by `test_load_is_idempotent`.
  - ➕ Lineage columns tell us which file every row came from.
  - ➕ VARCHAR in raw keeps values exactly as received (zip prefixes keep their leading zeros); types are set in staging.
  - ➖ A full rebuild re-reads every file on every run. Fine for ~120 MB; for large or append-heavy sources we'd switch to option 2 or a dbt incremental model.
  - ➖ Table names are interpolated into SQL, so they're validated with `str.isidentifier()` to prevent SQL injection.
