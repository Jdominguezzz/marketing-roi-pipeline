"""Dagster definitions: the whole pipeline as software-defined assets.

Run the UI with:  uv run dagster dev -m marketing_pipeline.orchestration
"""

import os
from datetime import date

import dagster as dg
import duckdb
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from marketing_pipeline.extract.fx_api import extract_fx
from marketing_pipeline.extract.kaggle_files import land_kaggle_files
from marketing_pipeline.extract.spend_simulator import load_config, simulate_spend
from marketing_pipeline.load.duckdb_loader import (
    KAGGLE_TABLES,
    latest_landed,
    load_fx,
    load_spend,
    load_table,
)
from marketing_pipeline.utils.config import DB_PATH, KAGGLE_SRC, LANDING, ROOT

# dbt finds the database through this env var, whatever folder Dagster runs from
os.environ.setdefault("DUCKDB_PATH", str(DB_PATH))

dbt_project = DbtProject(
    project_dir=ROOT / "transform", profiles_dir=ROOT / "transform"
)
dbt_project.prepare_if_dev()


# --- 1. Extract: land files ---------------------------------------------------


@dg.asset(group_name="landing", kinds={"python"})
def kaggle_files() -> dg.MaterializeResult:
    """Kaggle CSV snapshots copied into the landing zone (skipped if unchanged)."""
    landed = land_kaggle_files(KAGGLE_SRC, LANDING, date.today())
    return dg.MaterializeResult(metadata={"new_files": len(landed)})


@dg.asset(
    group_name="landing",
    kinds={"python", "api"},
    retry_policy=dg.RetryPolicy(max_retries=2, delay=30),
)
def fx_files() -> dg.MaterializeResult:
    """BRL->EUR rates from the Frankfurter API, only dates after the high-water mark."""
    landed = extract_fx(LANDING, date.today())
    return dg.MaterializeResult(
        metadata={"new_file": str(landed) if landed else "none, up to date"}
    )


@dg.asset(group_name="landing", kinds={"python"})
def spend_files() -> dg.MaterializeResult:
    """SIMULATED daily ad spend (ADR-003)."""
    config = load_config(ROOT / "config" / "spend_simulation.yml")
    files = simulate_spend(config, LANDING)
    return dg.MaterializeResult(metadata={"files": len(files), "simulated": True})


# --- 2. Load: raw tables in DuckDB (keys match the dbt sources, so lineage connects) ---

RAW_SPECS = [
    dg.AssetSpec(
        ["olist", table], deps=[kaggle_files], group_name="raw", kinds={"duckdb"}
    )
    for table in KAGGLE_TABLES
] + [
    dg.AssetSpec(
        ["ads", "ad_spend"], deps=[spend_files], group_name="raw", kinds={"duckdb"}
    ),
    dg.AssetSpec(
        ["fx", "fx_rates"], deps=[fx_files], group_name="raw", kinds={"duckdb"}
    ),
]


@dg.multi_asset(specs=RAW_SPECS)
def raw_tables():
    """Idempotent loads into DuckDB raw.* (ADR-002)."""
    con = duckdb.connect(str(DB_PATH))
    try:
        for table, file_name in KAGGLE_TABLES.items():
            rows = load_table(
                con, table, str(latest_landed(LANDING / "kaggle", file_name))
            )
            yield dg.MaterializeResult(
                asset_key=["olist", table], metadata={"rows": rows}
            )
        spend_rows = load_spend(con, LANDING / "spend")
        yield dg.MaterializeResult(
            asset_key=["ads", "ad_spend"], metadata={"rows": spend_rows}
        )
        fx_rows = load_fx(con, LANDING / "fx")
        yield dg.MaterializeResult(
            asset_key=["fx", "fx_rates"], metadata={"rows": fx_rows}
        )
    finally:
        con.close()


# --- 3. Transform: every dbt model becomes an asset, every dbt test an asset check ---


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


# --- 4. Job, schedule, definitions ------------------------------------------------

full_pipeline = dg.define_asset_job("full_pipeline", selection=dg.AssetSelection.all())

daily_06h = dg.ScheduleDefinition(
    job=full_pipeline,
    cron_schedule="0 6 * * *",
    execution_timezone="Europe/Lisbon",
)

defs = dg.Definitions(
    assets=[kaggle_files, fx_files, spend_files, raw_tables, dbt_models],
    jobs=[full_pipeline],
    schedules=[daily_06h],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
    executor=dg.in_process_executor,  # DuckDB allows one writer at a time (ADR-001)
)
