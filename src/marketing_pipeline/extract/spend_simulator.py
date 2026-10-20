"""Simulate daily paid-media spend per channel and land it as daily JSON files.

SIMULATED DATA: Olist does not publish spend. Assumptions live in
config/spend_simulation.yml. Three realistic problems are injected on purpose
(duplicate day, late file, renamed field) for the staging tests to catch.
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def daily_spend(config: dict, day: date, channel: str, rng: random.Random) -> float:
    settings = config["channels"][channel]
    base = settings["base_daily_spend_brl"]
    if day >= date.fromisoformat(config["ramp_date"]):
        base *= settings["ramp_multiplier"]
    weekday_factor = config["weekday_factors"][day.weekday()]
    noise = rng.gauss(1.0, config["noise_sd"])
    return round(max(base * weekday_factor * noise, 0.0), 2)


def simulate_spend(config: dict, landing_dir: Path) -> list[Path]:
    """Write one JSON file per spend day into landing/spend/ingest_date=<delivery day>/."""
    rng = random.Random(config["seed"])
    source_root = landing_dir / "spend"
    issues = config["inject"]
    day = date.fromisoformat(config["start_date"])
    end = date.fromisoformat(config["end_date"])
    written = []

    while day <= end:
        iso = day.isoformat()
        field = "cost" if iso == issues["renamed_field_day"] else "spend"
        rows = [
            {
                "date": iso,
                "channel": channel,
                field: daily_spend(config, day, channel, rng),
                "currency": "BRL",
            }
            for channel in sorted(config["channels"])
        ]

        delay = issues["late_days"] if iso == issues["late_file_day"] else 1
        deliveries = [day + timedelta(days=delay)]
        if iso == issues["duplicate_day"]:
            deliveries.append(day + timedelta(days=2))

        for delivered in deliveries:
            target_dir = source_root / f"ingest_date={delivered.isoformat()}"
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"spend_{iso}.json"
            target.write_text(json.dumps(rows, indent=2))
            written.append(target)

        day += timedelta(days=1)
    return written


if __name__ == "__main__":
    from marketing_pipeline.utils.config import LANDING, ROOT

    config = load_config(ROOT / "config" / "spend_simulation.yml")
    files = simulate_spend(config, LANDING)
    print(
        f"Wrote {len(files)} spend files (SIMULATED) for {len(config['channels'])} paid channels"
    )
