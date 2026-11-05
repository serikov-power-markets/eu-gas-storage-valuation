"""German daily gas balance from ENTSOG, ALSI and AGSI+, and what supplies the extra gas on cold days.

The same physical flow appears several times on the ENTSOG platform: under each operator of a shared
pipeline and again at the virtual interconnection point that aggregates it. A plain sum doubles
imports, so each corridor is counted once through the list below, chosen on 2024 and checked against
the Bundesnetzagentur annual figures for 2023 to 2025.

Implied demand = imports - exports + production + LNG send-out + net storage withdrawal.
Line pack changes, biogas and metering differences are not observed and stay in the demand figure.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CORRIDORS = {
    ("import", "NO"): ["de-tso-0009itp-00525entry", "de-tso-0009itp-00080entry", "de-tso-0005itp-00081entry"],
    ("import", "NL"): ["de-tso-0002itp-10010entry", "de-tso-0005itp-10012entry"],
    ("import", "BE"): ["de-tso-0009itp-00614entry"],
    ("import", "AT"): ["de-tso-0009itp-00539entry"],
    ("import", "CH"): ["de-tso-0007itp-00544entry"],
    ("import", "CZ"): ["de-tso-0009itp-00538entry"],
    ("import", "DK"): ["de-tso-0005itp-10011entry"],
    ("import", "FR"): ["de-tso-0004itp-00540entry"],
    ("import", "PL"): ["de-tso-0001itp-00096entry", "de-tso-0003itp-00497entry"],
    ("export", "NL"): ["de-tso-0005itp-10012exit"],
    ("export", "AT"): ["de-tso-0009itp-00539exit", "de-tso-0009itp-00019exit", "de-tso-0010itp-00227exit", "de-tso-0010itp-00291exit"],
    ("export", "CH"): ["de-tso-0007itp-00544exit"],
    ("export", "CZ"): ["de-tso-0001itp-00537exit", "de-tso-0009itp-00538exit"],
    ("export", "DK"): ["de-tso-0005itp-10011exit"],
    ("export", "PL"): ["de-tso-0001itp-00096exit", "de-tso-0003itp-00497exit"],
    ("export", "BE"): ["de-tso-0009itp-00614exit"],
    ("export", "FR"): ["de-tso-0004itp-00540exit"],
}

# Bundesnetzagentur annual reviews, TWh. None where the review gives no figure.
OFFICIAL = {
    2023: {"imports": 968, "exports": 187, "consumption": 811.5, "lng": None, "production": None},
    2024: {"imports": 865, "exports": 89, "consumption": 844, "lng": 69, "production": 36},
    2025: {"imports": 1031, "exports": 221, "consumption": 864, "lng": 106, "production": 34},
}


def corridor_flows(flows: pd.DataFrame) -> pd.DataFrame:
    """GWh/d by (flow, neighbor). A missing report counts as zero on that day."""
    out = {}
    for name, keys in CORRIDORS.items():
        missing = [k for k in keys if k not in flows.columns]
        if missing:
            raise KeyError(f"{name}: {missing}")
        out[name] = flows[keys].fillna(0.0).sum(axis=1)
    return pd.DataFrame(out)


def balance(flows: pd.DataFrame, production_keys: list[str], lng: pd.Series, net_withdrawal: pd.Series) -> pd.DataFrame:
    """Daily balance in GWh/d on the days all sources report."""
    c = corridor_flows(flows)
    df = pd.DataFrame({
        "norway": c[("import", "NO")],
        "netherlands": c[("import", "NL")],
        "belgium": c[("import", "BE")],
        "other_imports": c["import"].drop(columns=["NO", "NL", "BE"]).sum(axis=1),
        "exports": c["export"].sum(axis=1),
        "production": flows[production_keys].fillna(0.0).sum(axis=1),
    })
    df["lng"] = lng.reindex(df.index)
    df["storage"] = net_withdrawal.reindex(df.index)
    df = df.dropna()
    df["demand"] = (df[["norway", "netherlands", "belgium", "other_imports", "production", "lng", "storage"]].sum(axis=1) - df["exports"])
    return df


def official_check(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, off in OFFICIAL.items():
        y = df[df.index.year == year]
        if len(y) < 360:
            continue
        pipe = y[["norway", "netherlands", "belgium", "other_imports"]].sum().sum() / 1000
        imports = pipe + y["lng"].sum() / 1000
        rows.append({
            "year": year,
            "imports_incl_lng": round(imports, 1), "imports_official": off["imports"],
            "exports": round(y["exports"].sum() / 1000, 1), "exports_official": off["exports"],
            "lng": round(y["lng"].sum() / 1000, 1), "lng_official": off["lng"],
            "production": round(y["production"].sum() / 1000, 1), "production_official": off["production"],
            "demand": round(y["demand"].sum() / 1000, 1), "consumption_official": off["consumption"],
            "demand_error_pct": round(100 * (y["demand"].sum() / 1000 / off["consumption"] - 1), 1),
        })
    return pd.DataFrame(rows).set_index("year")


SOURCES = ["storage", "norway", "netherlands", "belgium", "other_imports", "lng", "production", "neg_exports"]


def swing_shares(df: pd.DataFrame, hdd: pd.Series) -> pd.DataFrame:
    """OLS slope of each balance item on degree days, GWh/d per degree day, with month and weekend controls.

    The slopes of the supply items add up to the slope of demand by construction, so the share says
    which source carried the weather-driven part of demand in the sample.
    """
    x = df.assign(neg_exports=-df["exports"]).join(hdd.rename("hdd"), how="inner")
    x = x[_season(x.index)].dropna()
    X = pd.get_dummies(x.index.month, prefix="m", dtype=float).set_index(x.index)
    X["weekend"] = (x.index.dayofweek >= 5).astype(float)
    X["hdd"] = x["hdd"]
    rows = {}
    for col in SOURCES + ["demand"]:
        beta, *_ = np.linalg.lstsq(X.to_numpy(), x[col].to_numpy(), rcond=None)
        rows[col] = beta[list(X.columns).index("hdd")]
    s = pd.Series(rows)
    return pd.DataFrame({"gwh_d_per_hdd": s.round(1), "share_of_demand_slope": (s / s["demand"]).round(3)})


def _season(idx: pd.DatetimeIndex) -> np.ndarray:
    m, d = idx.month, idx.day
    return ((m == 10) & (d >= 15)) | (m >= 11) | (m <= 3)


def winter_table(df: pd.DataFrame, hdd: pd.Series) -> pd.DataFrame:
    """TWh by winter (15 October to 31 March), with the supply excluding storage and mean degree days."""
    x = df.join(hdd.rename("hdd"), how="left")
    x = x[_season(x.index)]
    winter = np.where(x.index.month >= 7, x.index.year, x.index.year - 1)
    g = x.groupby(winter)
    t = g[["norway", "netherlands", "belgium", "other_imports", "lng", "production", "exports", "storage", "demand"]].sum().div(1000).round(1)
    t["net_supply"] = (t[["norway", "netherlands", "belgium", "other_imports", "lng", "production"]].sum(axis=1) - t["exports"]).round(1)
    t["mean_hdd"] = g["hdd"].mean().round(2)
    t["days"] = g.size()
    return t
