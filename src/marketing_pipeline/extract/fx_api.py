"""Extract BRL→EUR daily rates from the Frankfurter API (ECB data), incrementally."""

import json
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

API_URL = "https://api.frankfurter.dev/v1"
FIRST_DATE = date(2016, 9, 1)
LAST_DATE = date(2018, 10, 31)
RETRYABLE = {429, 500, 502, 503, 504}


def high_water_mark(source_root: Path) -> date | None:
    """Latest rate date already landed, or None if nothing has landed yet."""
    dates = []
    for file in source_root.glob("ingest_date=*/rates_*.json"):
        payload = json.loads(file.read_text())
        dates.extend(date.fromisoformat(day) for day in payload["rates"])
    return max(dates) if dates else None


def validate(payload: dict) -> None:
    """Raise if the response doesn't look like daily EUR rates."""
    rates = payload.get("rates")
    if not isinstance(rates, dict) or not rates:
        raise ValueError("FX response has no rates")
    for day, values in rates.items():
        date.fromisoformat(day)
        eur = values.get("EUR")
        if not isinstance(eur, (int, float)) or eur <= 0:
            raise ValueError(f"Bad EUR rate on {day}: {values}")


def fetch_rates(start: date, end: date, retries: int = 4) -> dict:
    """Call the API with retries and exponential backoff. Returns a validated payload."""
    url = f"{API_URL}/{start.isoformat()}..{end.isoformat()}"
    params = {"base": "BRL", "symbols": "EUR"}

    for attempt in range(1, retries + 1):
        try:
            response = httpx.get(url, params=params, timeout=10, follow_redirects=True)
        except httpx.TransportError as error:
            problem = f"network error: {error}"
        else:
            if response.status_code not in RETRYABLE:
                response.raise_for_status()
                payload = response.json()
                validate(payload)
                return payload
            problem = f"HTTP {response.status_code}"

        if attempt == retries:
            raise RuntimeError(f"FX API failed after {retries} attempts ({problem})")
        wait = 2**attempt
        print(f"Attempt {attempt} failed ({problem}), retrying in {wait}s")
        time.sleep(wait)


def extract_fx(landing_dir: Path, ingest_date: date) -> Path | None:
    """Land only the dates after the high-water mark. Returns the new file, or None."""
    source_root = landing_dir / "fx"
    watermark = high_water_mark(source_root)
    start = FIRST_DATE if watermark is None else watermark + timedelta(days=1)
    if start > LAST_DATE:
        return None

    payload = fetch_rates(start, LAST_DATE)
    target_dir = source_root / f"ingest_date={ingest_date.isoformat()}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"rates_{start.isoformat()}_{LAST_DATE.isoformat()}.json"
    target.write_text(json.dumps(payload, indent=2))
    return target


if __name__ == "__main__":
    from marketing_pipeline.utils.config import LANDING

    landed = extract_fx(LANDING, date.today())
    if landed is None:
        print("FX up to date: 0 API calls")
    else:
        days = len(json.loads(landed.read_text())["rates"])
        print(f"Landed {days} days of rates -> {landed.relative_to(LANDING)}")
