"""Daily LNG send-out from GIE ALSI, cached on disk. Uses the same key as AGSI+ (AGSI_KEY), never stored."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

URL = "https://alsi.gie.eu/api"


def download(raw_dir: Path, country: str, start: str, end: str, refresh: bool = False) -> Path:
    path = raw_dir / f"alsi_{country}_{start}_{end}.json"
    if path.exists() and not refresh:
        return path
    key = os.environ.get("AGSI_KEY")
    if not key:
        raise RuntimeError("set the AGSI_KEY environment variable (free key from gie.eu)")
    rows, page, last = [], 1, 1
    while page <= last:
        r = requests.get(URL, headers={"x-key": key}, timeout=120,
                         params={"country": country, "from": start, "to": end, "size": 300, "page": page})
        r.raise_for_status()
        d = r.json()
        rows += d["data"]
        last = d["last_page"]
        page += 1
        time.sleep(1)
    raw_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf8")
    return path


def parse(path: Path) -> pd.Series:
    """LNG send-out in GWh/d by gas day."""
    df = pd.DataFrame(json.loads(path.read_text(encoding="utf8")))
    s = pd.to_numeric(df["sendOut"], errors="coerce")
    s.index = pd.to_datetime(df["gasDayStart"])
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.index.name = "gas_day"
    return s.rename("lng")
