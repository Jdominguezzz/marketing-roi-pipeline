"""Load landed files into DuckDB's raw schema, idempotently."""

from pathlib import Path

import duckdb

KAGGLE_TABLES = {
    "marketing_qualified_leads": "olist_marketing_qualified_leads_dataset.csv",
    "closed_deals": "olist_closed_deals_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
}


def latest_landed(source_root: Path, file_name: str) -> Path:
    """Return the most recently landed copy of a snapshot file."""
    candidates = sorted(source_root.glob(f"ingest_date=*/{file_name}"))
    if not candidates:
        raise FileNotFoundError(f"{file_name} has not been landed in {source_root}")
    return candidates[-1]


def load_table(con: duckdb.DuckDBPyConnection, table: str, pattern: str) -> int:
    """Rebuild raw.<table> from the files matching pattern. Returns the row count."""
    if not table.isidentifier():
        raise ValueError(f"Invalid table name: {table!r}")
    path_sql = str(pattern).replace("'", "''")

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.{table} AS
        SELECT
            * EXCLUDE (filename),
            filename          AS _source_file,
            current_timestamp AS _loaded_at
        FROM read_csv('{path_sql}', header = true, all_varchar = true, filename = true)
    """)
    return con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]


def load_spend(con: duckdb.DuckDBPyConnection, source_root: Path) -> int:
    """Rebuild raw.ad_spend from ALL daily spend files (incremental source)."""
    path_sql = str(source_root / "*" / "*.json").replace("'", "''")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.ad_spend AS
        SELECT
            * EXCLUDE (filename),
            filename          AS _source_file,
            current_timestamp AS _loaded_at
        FROM read_json('{path_sql}', format = 'array', union_by_name = true,
                       hive_partitioning = true, filename = true)
    """)
    return con.execute("SELECT COUNT(*) FROM raw.ad_spend").fetchone()[0]


def load_fx(con: duckdb.DuckDBPyConnection, source_root: Path) -> int:
    """Rebuild raw.fx_rates: one row per date from the nested API responses."""
    path_sql = str(source_root / "*" / "*.json").replace("'", "''")
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.fx_rates AS
        SELECT
            rate.key          AS rate_date,
            rate.value.EUR    AS brl_eur,
            base,
            _source_file,
            current_timestamp AS _loaded_at
        FROM (
            SELECT base, filename AS _source_file, unnest(map_entries(rates)) AS rate
            FROM read_json('{path_sql}', filename = true, columns = {{
                'base': 'VARCHAR', 'start_date': 'VARCHAR', 'end_date': 'VARCHAR',
                'rates': 'MAP(VARCHAR, STRUCT(EUR DOUBLE))'}})
        )
    """)
    return con.execute("SELECT COUNT(*) FROM raw.fx_rates").fetchone()[0]


if __name__ == "__main__":
    from marketing_pipeline.utils.config import DB_PATH, LANDING

    con = duckdb.connect(str(DB_PATH))
    for table, file_name in KAGGLE_TABLES.items():
        path = latest_landed(LANDING / "kaggle", file_name)
        rows = load_table(con, table, str(path))
        print(f"raw.{table:<26} {rows:>8,} rows  <- {path.parent.name}")
    print(
        f"raw.{'ad_spend':<26} {load_spend(con, LANDING / 'spend'):>8,} rows  <- all daily files (SIMULATED)"
    )
    print(
        f"raw.{'fx_rates':<26} {load_fx(con, LANDING / 'fx'):>8,} rows  <- Frankfurter API"
    )
    con.close()
