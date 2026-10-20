"""Project paths, found the same way from anywhere (notebook, terminal, Dagster, CI)."""

from pathlib import Path


def _find_root() -> Path:
    here = Path(__file__).resolve()
    for folder in here.parents:
        if (folder / "pyproject.toml").exists():
            return folder
    raise FileNotFoundError("pyproject.toml not found: are you inside the project?")


ROOT = _find_root()
KAGGLE_SRC = ROOT / "data" / "kaggle"
LANDING = ROOT / "data" / "landing"
DB_PATH = ROOT / "data" / "warehouse.duckdb"
