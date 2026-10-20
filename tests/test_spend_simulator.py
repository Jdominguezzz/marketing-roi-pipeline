"""Tests for the spend simulator and the spend loader, on a tiny 5-day config."""

import duckdb

from marketing_pipeline.extract.spend_simulator import simulate_spend
from marketing_pipeline.load.duckdb_loader import load_spend

CONFIG = {
    "seed": 7,
    "start_date": "2018-01-01",
    "end_date": "2018-01-05",
    "ramp_date": "2018-01-03",
    "noise_sd": 0.1,
    "weekday_factors": [1, 1, 1, 1, 1, 1, 1],
    "channels": {"paid_search": {"base_daily_spend_brl": 100, "ramp_multiplier": 2}},
    "inject": {
        "duplicate_day": "2018-01-02",
        "late_file_day": "2018-01-04",
        "late_days": 6,
        "renamed_field_day": "2018-01-05",
    },
}


def test_same_seed_gives_same_files(tmp_path):
    run_a = simulate_spend(CONFIG, tmp_path / "a")
    run_b = simulate_spend(CONFIG, tmp_path / "b")
    assert [p.read_text() for p in run_a] == [p.read_text() for p in run_b]


def test_injected_problems_exist(tmp_path):
    files = simulate_spend(CONFIG, tmp_path)
    names = [(p.parent.name, p.name) for p in files]

    assert len(files) == 6
    assert sum(name == "spend_2018-01-02.json" for _, name in names) == 2
    assert ("ingest_date=2018-01-10", "spend_2018-01-04.json") in names
    renamed = tmp_path / "spend" / "ingest_date=2018-01-06" / "spend_2018-01-05.json"
    assert '"cost"' in renamed.read_text()


def test_spend_loader_keeps_drift_visible(tmp_path):
    simulate_spend(CONFIG, tmp_path)
    con = duckdb.connect()
    assert load_spend(con, tmp_path / "spend") == 6
    columns = {row[0] for row in con.execute("DESCRIBE raw.ad_spend").fetchall()}
    assert {"spend", "cost", "ingest_date", "_source_file"} <= columns
