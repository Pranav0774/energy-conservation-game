"""Clean the raw appliance power table and compare it with the values the game uses.

Input : data/raw/appliance_power_sources.csv  (figures copied from three web pages)
Output: data/clean/appliance_power_clean.csv  (one row per game appliance)
        data/clean/appliance_sources_long.csv (every raw row mapped, units converted)
Run   : python -m tools.clean_appliance_data
"""
from pathlib import Path

import pandas as pd

from game.appliances import APPLIANCES

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "appliance_power_sources.csv"
OUT = ROOT / "data" / "clean"
HOURS_PER_YEAR = 8760

# raw "appliance_as_named" -> game appliance key (None = not used by the game)
MAPPING = {
    "Refrigerator": "fridge", "Refrigerator (compressor running)": "fridge",
    "Refrigerator (annual energy)": "fridge", "Refrigerator (actual average use)": "fridge",
    "Oven/stove": "cooktop", "Electric oven": "cooktop",
    "Window AC unit": "ac", "Window AC": "ac",
    "Ceiling fan": "fan",
    "Light bulbs": "lights", "LED bulb": "lights",
    "TV": "tv", "LED TV": "tv",
    "Computer": "computer", "Laptop (in use)": "computer", "Desktop computer (heavy use)": "computer",
    "Washing machine": "washer", "Washing machine (front-load)": "washer", "Washing machine (top-load)": "washer",
    "Electric water heater (tank)": "heater",
    "Clothes iron": "iron",
}
# Which raw rows are comparable with the game's number for each appliance. The game's fridge value is a
# 24-hour average, so it is compared with average-type rows; everything else is power while running.
GAME_BASIS = {a.key: "rated_running" for a in APPLIANCES}
GAME_BASIS["fridge"] = "average"
# Why a game value is deliberately different from the sources (shown in the report).
DESIGN_NOTES = {
    "cooktop": "sources give whole oven/stove; the game models one burner",
    "heater": "game uses a small or instant unit so one hour is playable; sources give tank elements",
    "lights": "game value is a whole-home lighting circuit; sources give per bulb",
    "iron": "game value is slightly below the sources' range",
}


def load_raw(path: Path = RAW) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"note": "string"})
    required = ["row_id", "source_id", "appliance_as_named", "low", "high", "unit", "basis"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    return df


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[tuple[str, int]]]:
    log = []
    n0 = len(df)
    df = df.drop_duplicates(subset=["source_id", "appliance_as_named", "low", "high", "unit"])
    log.append(("duplicate rows removed", n0 - len(df)))

    n1 = len(df)
    df = df[(df["low"] > 0) & (df["high"] >= df["low"])]
    log.append(("rows with non-positive or reversed range removed", n1 - len(df)))

    df = df.copy()
    annual = df["unit"].eq("kWh/year")
    for col in ("low", "high"):
        df[col + "_w"] = df[col].where(~annual, df[col] * 1000 / HOURS_PER_YEAR)  # kWh/year -> average watts
    df["unit_clean"] = "W"
    df["basis_clean"] = df["basis"].replace({"annual": "average"})
    log.append(("annual kWh figures converted to average watts", int(annual.sum())))
    df["mid_w"] = (df["low_w"] + df["high_w"]) / 2
    df["game_key"] = df["appliance_as_named"].map(MAPPING)
    log.append(("rows not used by the game (standby, idle, other AC types)", int(df["game_key"].isna().sum())))
    long = df.drop(columns=["low", "high", "unit", "basis"]).rename(columns={"basis_clean": "basis", "unit_clean": "unit"})

    rows = []
    for a in APPLIANCES:
        sub = long[(long["game_key"] == a.key) & (long["basis"] == GAME_BASIS[a.key])]
        if sub.empty:
            rows.append({"game_key": a.key, "game_appliance": a.name, "game_watts": a.watts, "n_rows": 0})
            continue
        lo, hi = sub["low_w"].min(), sub["high_w"].max()
        rows.append({
            "game_key": a.key, "game_appliance": a.name, "game_watts": a.watts, "basis": GAME_BASIS[a.key],
            "n_rows": len(sub), "n_sources": sub["source_id"].nunique(),
            "source_min_w": round(lo, 1), "source_max_w": round(hi, 1),
            "source_median_mid_w": round(sub["mid_w"].median(), 1),
            "game_within_range": bool(lo <= a.watts <= hi),
            "game_vs_range": "within" if lo <= a.watts <= hi else ("below" if a.watts < lo else "above"),
            "design_note": DESIGN_NOTES.get(a.key, ""),
        })
    return pd.DataFrame(rows), long, log


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary, long, log = clean(load_raw())
    summary.to_csv(OUT / "appliance_power_clean.csv", index=False)
    long.to_csv(OUT / "appliance_sources_long.csv", index=False)
    pd.DataFrame(log, columns=["step", "rows"]).to_csv(OUT / "appliance_cleaning_log.csv", index=False)
    print(summary[["game_key", "game_watts", "source_min_w", "source_max_w", "game_vs_range"]].to_string(index=False))
    for step, n in log:
        print(f"- {step}: {n}")


if __name__ == "__main__":
    main()
