"""Tests for the FX extractor. They never call the real API."""

import json
from datetime import date

import pytest

from marketing_pipeline.extract.fx_api import high_water_mark, validate


def test_validate_accepts_good_payload():
    validate({"rates": {"2018-01-02": {"EUR": 0.25}}})


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"rates": {}},
        {"rates": {"2018-01-02": {"EUR": -1}}},
        {"rates": {"2018-01-02": {}}},
        {"rates": {"not-a-date": {"EUR": 0.25}}},
    ],
)
def test_validate_rejects_bad_payloads(payload):
    with pytest.raises(ValueError):
        validate(payload)


def test_high_water_mark(tmp_path):
    assert high_water_mark(tmp_path) is None

    folder = tmp_path / "ingest_date=2026-10-20"
    folder.mkdir()
    rates = {"rates": {"2018-01-02": {"EUR": 0.25}, "2018-01-03": {"EUR": 0.26}}}
    (folder / "rates_test.json").write_text(json.dumps(rates))

    assert high_water_mark(tmp_path) == date(2018, 1, 3)
