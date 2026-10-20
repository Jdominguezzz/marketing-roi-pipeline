"""Land the Kaggle CSVs into the immutable landing zone.

Target layout: data/landing/kaggle/ingest_date=YYYY-MM-DD/<file>.csv
"""

import hashlib
import shutil
from datetime import date
from pathlib import Path


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def land_kaggle_files(
    src_dir: Path, landing_dir: Path, ingest_date: date
) -> list[Path]:
    """Copy each CSV to landing_dir/kaggle/ingest_date=<date>/, skipping files already landed."""
    source_root = landing_dir / "kaggle"
    target_dir = source_root / f"ingest_date={ingest_date.isoformat()}"
    copied = []

    for src in sorted(src_dir.rglob("*.csv")):
        if any(part.startswith(".") for part in src.relative_to(src_dir).parts):
            continue
        src_hash = _md5(src)
        previous = source_root.glob(f"ingest_date=*/{src.name}")
        if any(_md5(p) == src_hash for p in previous):
            continue

        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / src.name
        shutil.copy2(src, target)
        copied.append(target)

    return copied


if __name__ == "__main__":
    from marketing_pipeline.utils.config import KAGGLE_SRC, LANDING

    landed = land_kaggle_files(KAGGLE_SRC, LANDING, date.today())
    print(f"Landed {len(landed)} new file(s)")
    for path in landed:
        print(" ", path.name)
