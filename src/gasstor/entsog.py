"""Daily physical gas flows at German cross-border and production points from the ENTSOG platform.

No key is needed. Raw answers are cached per point direction and year. Values are published in
kWh/d and converted here to GWh/d. A flow is reported by the operator on each side of a border, so
both sides are downloaded and compared.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

URL = "https://transparency.entsog.eu/api/v1/"
HEADERS = {"User-Agent": "research-reader/1.0"}
COUNTRY = "DE"


def interconnections(raw_dir: Path, refresh: bool = False) -> list[dict]:
    path = raw_dir / "entsog" / "interconnections.json"
    if path.exists() and not refresh:
        return json.loads(path.read_text(encoding="utf8"))
    r = requests.get(URL + "interconnections", params={"limit": -1}, headers=HEADERS, timeout=180)
    r.raise_for_status()
    rows = r.json()["interconnections"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows), encoding="utf8")
    return rows


def border_directions(rows: list[dict], country: str = COUNTRY) -> pd.DataFrame:
    """One row per reported direction at the transmission borders of a country.

    flow is "import" or "export" seen from the country; side says who reports it. Storage facilities
    connected across a border (points named UGS) are left out, because AGSI+ already holds them.
    """
    out = []
    for i in rows:
        a, b = i.get("fromCountryKey"), i.get("toCountryKey")
        if not a or not b or a == b or country not in (a, b):
            continue
        if not str(i.get("pointKey", "")).startswith("ITP"):
            continue
        if i.get("fromInfrastructureTypeLabel") != "Transmission" or i.get("toInfrastructureTypeLabel") != "Transmission":
            continue
        flow = "import" if b == country else "export"
        neighbor = a if flow == "import" else b
        for end, side in (("from", "home" if a == country else "foreign"), ("to", "home" if b == country else "foreign")):
            op, point, direction = i.get(f"{end}OperatorKey"), i.get(f"{end}PointKey"), i.get(f"{end}DirectionKey")
            if op and point and direction:
                out.append({"key": f"{op}{point}{direction}".lower(), "operator": op, "point": point,
                            "label": i.get("pointLabel"), "direction": direction, "flow": flow,
                            "neighbor": neighbor, "side": side})
    return pd.DataFrame(out).drop_duplicates(["key", "flow", "neighbor", "side"]).reset_index(drop=True)


def production_directions(rows: list[dict], country: str = COUNTRY) -> pd.DataFrame:
    out = []
    for i in rows:
        if i.get("fromInfrastructureTypeLabel") == "Production" and i.get("toCountryKey") == country:
            op, point, direction = i.get("toOperatorKey"), i.get("toPointKey"), i.get("toDirectionKey")
            if op and point and direction:
                out.append({"key": f"{op}{point}{direction}".lower(), "operator": op, "point": point,
                            "label": i.get("pointLabel"), "direction": direction, "flow": "production",
                            "neighbor": country, "side": "home"})
    return pd.DataFrame(out).drop_duplicates("key").reset_index(drop=True) if out else pd.DataFrame()


def _year(key: str, year: int, cache: Path, pause: float) -> list[dict]:
    path = cache / f"{key}_{year}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf8"))
    params = {"from": f"{year}-01-01", "to": f"{year}-12-31", "indicator": "Physical Flow",
              "periodType": "day", "timezone": "CET", "limit": -1, "pointDirection": key}
    rows = []
    for attempt in range(4):
        try:
            r = requests.get(URL + "operationaldatas", params=params, headers=HEADERS, timeout=180)
            if r.status_code == 404:
                break
            r.raise_for_status()
            rows = [{"day": x["periodFrom"][:10], "value": x["value"], "unit": x["unit"], "status": x.get("flowStatus")}
                    for x in r.json().get("operationaldatas", [])]
            break
        except (requests.RequestException, ValueError):
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))
    path.write_text(json.dumps(rows), encoding="utf8")
    time.sleep(pause)
    return rows


def tidy(rows: list[dict]) -> pd.Series:
    """Daily GWh/d. Where a day has a confirmed and a provisional value, the confirmed one wins."""
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame(rows)
    df = df[df["value"].notna()]
    if df.empty:
        return pd.Series(dtype=float)
    units = set(df["unit"])
    if units - {"kWh/d"}:
        raise ValueError(f"unexpected units: {units}")
    df["rank"] = (df["status"] == "Confirmed").astype(int)
    df = df.sort_values(["day", "rank"]).drop_duplicates("day", keep="last")
    s = pd.to_numeric(df["value"]) / 1e6
    s.index = pd.to_datetime(df["day"])
    return s.sort_index()


def flows(directions: pd.DataFrame, raw_dir: Path, years: range, pause: float = 0.3) -> pd.DataFrame:
    """GWh/d, one column per direction key."""
    cache = raw_dir / "entsog" / "flows"
    cache.mkdir(parents=True, exist_ok=True)
    data = {}
    for key in directions["key"].unique():
        rows = [r for y in years for r in _year(key, y, cache, pause)]
        data[key] = tidy(rows)
    out = pd.DataFrame(data)
    out.index = pd.to_datetime(out.index)
    return out.sort_index()
