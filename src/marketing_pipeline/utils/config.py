"""Project paths, found the same way from anywhere (notebook, terminal, Dagster, CI).

Defaults point at the real data. CI overrides them with environment variables
(LANDING_DIR, DUCKDB_PATH) so the same code runs on the small committed sample.
"""

import os
from pathlib import Path


def _find_root() -> Path:
    here = Path(__file__).resolve()
    for folder in here.parents:
        if (folder / "pyproject.toml").exists():
            return folder
    raise FileNotFoundError("pyproject.toml not found: are you inside the project?")


ROOT = _find_root()
KAGGLE_SRC = Path(os.environ.get("KAGGLE_SRC", ROOT / "data" / "kaggle"))
LANDING = Path(os.environ.get("LANDING_DIR", ROOT / "data" / "landing"))
DB_PATH = Path(os.environ.get("DUCKDB_PATH", ROOT / "data" / "warehouse.duckdb"))
