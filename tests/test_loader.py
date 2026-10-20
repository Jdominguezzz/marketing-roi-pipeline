"""Tests for the extract and load steps. tmp_path keeps them away from real data."""

from datetime import date
from pathlib import Path

import duckdb

from marketing_pipeline.extract.kaggle_files import land_kaggle_files
from marketing_pipeline.load.duckdb_loader import load_table

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_is_idempotent(tmp_path):
    con = duckdb.connect(str(tmp_path / "test.duckdb"))
    first = load_table(con, "tiny", str(FIXTURES / "tiny.csv"))
    second = load_table(con, "tiny", str(FIXTURES / "tiny.csv"))
    assert first == second == 3


def test_raw_keeps_text_and_lineage(tmp_path):
    con = duckdb.connect(str(tmp_path / "test.duckdb"))
    load_table(con, "tiny", str(FIXTURES / "tiny.csv"))
    columns = dict(
        con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'tiny'"
        ).fetchall()
    )
    assert columns["amount"] == "VARCHAR"
    assert "_source_file" in columns
    assert "_loaded_at" in columns


def test_empty_file_loads_zero_rows(tmp_path):
    con = duckdb.connect(str(tmp_path / "test.duckdb"))
    assert load_table(con, "empty", str(FIXTURES / "empty.csv")) == 0


def test_landing_skips_identical_and_hidden_files(tmp_path):
    src = tmp_path / "src"
    (src / ".ipynb_checkpoints").mkdir(parents=True)
    (src / "a.csv").write_text("id\n1\n")
    (src / ".ipynb_checkpoints" / "a-checkpoint.csv").write_text("id\n1\n")
    landing = tmp_path / "landing"

    first = land_kaggle_files(src, landing, date(2026, 10, 20))
    second = land_kaggle_files(src, landing, date(2026, 10, 21))

    assert [p.name for p in first] == ["a.csv"]
    assert second == []
