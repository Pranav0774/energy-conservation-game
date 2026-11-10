"""Clean raw play logs (simulated bots and real browser exports) into one analysis-ready table.

Inputs : every *.csv under data/raw/playlogs/ (simulated) and data/raw/real_playlogs/ (browser exports)
Outputs: data/clean/playlogs_clean.csv   one row per valid finished day
         data/clean/playlogs_cleaning_log.csv   how many rows each rule removed
Run    : python -m tools.clean_playlogs
"""
from pathlib import Path

import pandas as pd

from game.appliances import APPLIANCES
from game.datalog import columns
from game.engine import CO2_KG_PER_KWH
from game.events import EVENTS
from game.levels import LEVELS

ROOT = Path(__file__).resolve().parent.parent
RAW_DIRS = [ROOT / "data" / "raw" / "playlogs", ROOT / "data" / "raw" / "real_playlogs"]
OUT = ROOT / "data" / "clean"
MAX_KWH = sum(a.watts for a in APPLIANCES) * 24 / 1000  # everything on all day
MAX_SCORE = 1100  # base 300 + comfort 500 + budget 200 + timing 100
REQUIRED = [
    "run_id", "level", "score", "energy_kwh", "co2_kg", "cost", "comfort", "offpeak_share", "peak_share",
    "missing_essentials", *["hrs_" + a.key for a in APPLIANCES], *[f"kwh_h{h:02d}" for h in range(24)],
]
NUMERIC = [c for c in columns() if c not in {"source", "player_id", "run_id", "timestamp_utc", "level", "event", "rating"}]


def read_raw(dirs: list[Path] = RAW_DIRS) -> pd.DataFrame:
    frames = []
    for d in dirs:
        for path in sorted(d.glob("*.csv")) if d.exists() else []:
            df = pd.read_csv(path, dtype=str)
            df["raw_file"] = path.name
            frames.append(df)
    if not frames:
        raise FileNotFoundError("no raw play logs found. Run python -m tools.simulate_players first")
    return pd.concat(frames, ignore_index=True)


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, int]]]:
    log = [("raw rows read", len(raw))]
    df = raw.copy()

    def drop(mask: pd.Series, reason: str) -> None:
        nonlocal df
        log.append((reason, int(mask.sum())))
        df = df[~mask]

    for col in columns():  # columns missing entirely (older exports) become empty, then fail the REQUIRED check
        if col not in df.columns:
            df[col] = pd.NA
    if "strategy" not in df.columns:
        df["strategy"] = ""
    if "raw_file" not in df.columns:
        df["raw_file"] = ""
    df["strategy"] = df["strategy"].fillna("").replace("", "human")

    df[NUMERIC] = df[NUMERIC].apply(pd.to_numeric, errors="coerce")
    df["event"] = df["event"].fillna("none").replace("", "none")

    drop(df[REQUIRED].isna().any(axis=1), "incomplete rows (a required field is missing or not a number)")
    drop(df.duplicated(subset="run_id", keep="first"), "duplicate run_id")
    drop(~df["level"].isin(LEVELS), "unknown level")
    drop(~df["event"].isin(["none", *EVENTS]), "unknown event")
    hrs = df[["hrs_" + a.key for a in APPLIANCES]]
    drop(
        (df["energy_kwh"] < 0) | (df["energy_kwh"] > MAX_KWH) | (df["score"] < 0) | (df["score"] > MAX_SCORE)
        | df["comfort"].lt(0) | df["comfort"].gt(1) | (hrs.lt(0) | hrs.gt(24)).any(axis=1)
        | df[["offpeak_share", "peak_share"]].lt(0).any(axis=1) | df[["offpeak_share", "peak_share"]].gt(1).any(axis=1),
        "values outside the possible range",
    )
    hourly = df[[f"kwh_h{h:02d}" for h in range(24)]].sum(axis=1)
    drop(
        ((df["co2_kg"] - df["energy_kwh"] * CO2_KG_PER_KWH).abs() > 0.01) | ((hourly - df["energy_kwh"]).abs() > 0.01),
        "inconsistent totals (CO2 or hourly energy does not match total energy)",
    )

    df = df.copy()
    df["is_simulated"] = df["source"].eq("simulated_bot")
    df["over_budget"] = df["energy_kwh"] > df["budget_kwh"]
    df["budget_used_pct"] = (100 * df["energy_kwh"] / df["budget_kwh"]).round(1)
    df["day_type"] = df["event"]
    keep = columns() + ["strategy", "is_simulated", "over_budget", "budget_used_pct", "raw_file"]
    out = df[keep].reset_index(drop=True)
    log.append(("clean rows kept", len(out)))
    return out, log


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out, log = clean(read_raw())
    out.to_csv(OUT / "playlogs_clean.csv", index=False)
    pd.DataFrame(log, columns=["step", "rows"]).to_csv(OUT / "playlogs_cleaning_log.csv", index=False)
    for step, n in log:
        print(f"- {step}: {n}")
    print(out.groupby(["is_simulated"]).size().to_string())


if __name__ == "__main__":
    main()
