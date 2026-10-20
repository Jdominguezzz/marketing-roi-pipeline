"""Build a small, deterministic sample of the real data for CI.

Keeps every won deal (so the funnel and the ROI mart are complete) plus 1,000
non-won leads, and only the orders, items, payments, customers and sellers those
deals need. Every foreign key in the sample resolves, so all dbt tests can run.

Usage:  uv run python scripts/make_sample.py
Output: data/sample/landing/{kaggle,fx}/...   (committed; derived from Olist, CC BY-NC-SA 4.0)
"""

import shutil

import duckdb

from marketing_pipeline.load.duckdb_loader import KAGGLE_TABLES, latest_landed
from marketing_pipeline.utils.config import ROOT

REAL = ROOT / "data" / "landing"
SAMPLE = ROOT / "data" / "sample" / "landing"
SAMPLE_DATE = "ingest_date=2018-09-01"


def main() -> None:
    con = duckdb.connect()
    for table, file_name in KAGGLE_TABLES.items():
        path = latest_landed(REAL / "kaggle", file_name)
        con.execute(
            f"CREATE VIEW {table} AS SELECT * FROM read_csv('{path}', all_varchar = true)"
        )

    con.execute("""
        CREATE TABLE s_leads AS
        SELECT * FROM marketing_qualified_leads
        WHERE mql_id IN (SELECT mql_id FROM closed_deals)
           OR mql_id IN (
                SELECT mql_id FROM marketing_qualified_leads
                WHERE mql_id NOT IN (SELECT mql_id FROM closed_deals)
                ORDER BY hash(mql_id) LIMIT 1000);
        CREATE TABLE s_deals AS SELECT * FROM closed_deals;
        CREATE TABLE s_orders AS
        SELECT * FROM orders WHERE order_id IN (
            SELECT order_id FROM order_items WHERE seller_id IN (SELECT seller_id FROM s_deals));
        CREATE TABLE s_items AS SELECT * FROM order_items WHERE order_id IN (SELECT order_id FROM s_orders);
        CREATE TABLE s_payments AS SELECT * FROM order_payments WHERE order_id IN (SELECT order_id FROM s_orders);
        CREATE TABLE s_customers AS SELECT * FROM customers WHERE customer_id IN (SELECT customer_id FROM s_orders);
        CREATE TABLE s_sellers AS SELECT * FROM sellers WHERE seller_id IN (SELECT seller_id FROM s_items);
    """)

    sample_tables = {
        "marketing_qualified_leads": "s_leads",
        "closed_deals": "s_deals",
        "orders": "s_orders",
        "order_items": "s_items",
        "order_payments": "s_payments",
        "customers": "s_customers",
        "sellers": "s_sellers",
    }
    target = SAMPLE / "kaggle" / SAMPLE_DATE
    target.mkdir(parents=True, exist_ok=True)
    for table, file_name in KAGGLE_TABLES.items():
        out = target / file_name
        con.execute(f"COPY {sample_tables[table]} TO '{out}' (HEADER, DELIMITER ',')")
        rows = con.execute(f"SELECT COUNT(*) FROM {sample_tables[table]}").fetchone()[0]
        print(f"{file_name:<46} {rows:>7,} rows")

    fx_target = SAMPLE / "fx" / SAMPLE_DATE
    fx_target.mkdir(parents=True, exist_ok=True)
    for fx_file in sorted((REAL / "fx").glob("ingest_date=*/rates_*.json")):
        shutil.copy2(fx_file, fx_target / fx_file.name)
    print("FX rates copied (real ECB data, 26 KB)")


if __name__ == "__main__":
    main()
