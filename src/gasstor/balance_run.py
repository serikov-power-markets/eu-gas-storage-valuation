"""v0.3: German daily gas balance, check against official totals, weather swing and winter table.

Needs AGSI_KEY and network access on the first run. Writes results/balance/.
Usage: python -m gasstor.balance_run
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import agsi, alsi, balance, entsog, weather

ROOT = Path(__file__).resolve().parents[2]
RAW, RES = ROOT / "data" / "raw", ROOT / "results" / "balance"
START, END = "2022-12-01", "2026-11-03"


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    rows = entsog.interconnections(RAW)
    keys = sorted({k for v in balance.CORRIDORS.values() for k in v})
    prod = entsog.production_directions(rows)
    dirs = pd.concat([pd.DataFrame({"key": keys}), prod[["key"]]], ignore_index=True)
    flows = entsog.flows(dirs, RAW, range(2023, 2027))
    prod_keys = [k for k in prod["key"] if k in flows.columns]
    lng = alsi.parse(alsi.download(RAW, "de", START, END))
    storage = agsi.load(RAW, "de", end=END)
    t = weather.load(RAW)
    hdd = weather.hdd(t)

    df = balance.balance(flows, prod_keys, lng, storage["netWithdrawal"])
    df = df[df.index <= pd.Timestamp(END)]
    df.round(1).to_csv(RES / "daily_balance_gwh.csv")
    check = balance.official_check(df)
    check.to_csv(RES / "official_check.csv")
    print(check.T.to_string())

    all_swing = balance.swing_shares(df, hdd)
    all_swing.to_csv(RES / "weather_swing.csv")
    print(all_swing.to_string())
    table = balance.winter_table(df, hdd)
    table.to_csv(RES / "winters.csv")
    print(table.T.to_string())

    x = df.join(hdd.rename("hdd"), how="inner")
    x = x[balance._season(x.index)]
    cold = x[x["hdd"] >= x["hdd"].quantile(0.9)]
    mild = x[x["hdd"] <= x["hdd"].quantile(0.1)]
    items = ["storage", "norway", "netherlands", "belgium", "other_imports", "lng", "production", "exports", "demand"]
    stack = pd.DataFrame({"coldest_tenth": cold[items].mean(), "mildest_tenth": mild[items].mean()}).round(0)
    stack["change"] = stack["coldest_tenth"] - stack["mildest_tenth"]
    stack.to_csv(RES / "cold_day_stack.csv")
    print(stack.to_string())
    summary = {"first_day": str(df.index[0].date()), "last_day": str(df.index[-1].date()), "days": len(df),
               "max_demand_gwh": float(df["demand"].max()), "demand_negative_days": int((df["demand"] < 0).sum()),
               "hdd_threshold_coldest": float(x["hdd"].quantile(0.9))}
    (RES / "summary.json").write_text(json.dumps(summary, indent=1))
    print(summary)


if __name__ == "__main__":
    main()
