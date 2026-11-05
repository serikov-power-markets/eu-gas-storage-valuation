import numpy as np
import pandas as pd

from gasstor import balance, entsog


def flows(days=40, seed=0):
    idx = pd.date_range("2024-12-01", periods=days)
    rng = np.random.default_rng(seed)
    keys = sorted({k for v in balance.CORRIDORS.values() for k in v}) + ["prod1"]
    return pd.DataFrame(rng.uniform(0, 100, (days, len(keys))), index=idx, columns=keys)


def test_each_corridor_key_counts_once():
    keys = [k for v in balance.CORRIDORS.values() for k in v]
    assert len(keys) == len(set(keys))


def test_balance_identity():
    f = flows()
    lng = pd.Series(50.0, index=f.index)
    stor = pd.Series(np.linspace(-100, 100, len(f)), index=f.index)
    df = balance.balance(f, ["prod1"], lng, stor)
    imports = df[["norway", "netherlands", "belgium", "other_imports"]].sum(axis=1)
    assert np.allclose(df["demand"], imports + df["production"] + df["lng"] + df["storage"] - df["exports"])
    c = balance.corridor_flows(f)
    assert np.allclose(df["norway"], f[balance.CORRIDORS[("import", "NO")]].sum(axis=1))
    assert np.allclose(df["exports"], c["export"].sum(axis=1))


def test_swing_shares_add_up_and_find_storage():
    f = flows(150)
    idx = pd.date_range("2024-11-01", periods=150)
    f.index = idx
    hdd = pd.Series(np.random.default_rng(1).uniform(0, 25, 150), index=idx)
    stor = 100.0 * hdd
    lng = pd.Series(50.0, index=idx)
    df = balance.balance(f, ["prod1"], lng, stor)
    s = balance.swing_shares(df, hdd)
    assert abs(s.loc["storage", "gwh_d_per_hdd"] - 100.0) < 25
    assert abs(s.loc[balance.SOURCES, "share_of_demand_slope"].sum() - 1.0) < 0.02


def test_tidy_prefers_confirmed_and_converts_units():
    rows = [{"day": "2024-01-01", "value": 2e6, "unit": "kWh/d", "status": "Provisional"},
            {"day": "2024-01-01", "value": 3e6, "unit": "kWh/d", "status": "Confirmed"},
            {"day": "2024-01-02", "value": None, "unit": "kWh/d", "status": "Confirmed"}]
    s = entsog.tidy(rows)
    assert s.tolist() == [3.0]


def test_border_directions_skip_storage_and_domestic_points():
    rows = [
        {"fromCountryKey": "NO", "toCountryKey": "DE", "pointKey": "ITP-1", "pointLabel": "A", "fromInfrastructureTypeLabel": "Transmission", "toInfrastructureTypeLabel": "Transmission",
         "fromOperatorKey": "NO-TSO", "fromPointKey": "ITP-1", "fromDirectionKey": "exit", "toOperatorKey": "DE-TSO", "toPointKey": "ITP-1", "toDirectionKey": "entry"},
        {"fromCountryKey": "NL", "toCountryKey": "DE", "pointKey": "UGS-1", "pointLabel": "B", "fromInfrastructureTypeLabel": "Transmission", "toInfrastructureTypeLabel": "Transmission"},
        {"fromCountryKey": "DE", "toCountryKey": "DE", "pointKey": "ITP-2", "pointLabel": "C"},
    ]
    d = entsog.border_directions(rows)
    assert set(d["key"]) == {"no-tsoitp-1exit", "de-tsoitp-1entry"}
    assert set(d["flow"]) == {"import"} and set(d["neighbor"]) == {"NO"}
