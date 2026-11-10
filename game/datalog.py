"""Column layout for play-log data (one row per finished day).

The browser exports the same layout (frontend/exporter.js); tests/test_data_pipeline.py checks they agree.
"""
from .appliances import APPLIANCES, Appliance
from .engine import Result, hourly_kwh, period_shares

BASE_COLUMNS = [
    "source", "player_id", "run_id", "timestamp_utc", "level", "event", "budget_kwh", "par", "score", "rating",
    "energy_kwh", "co2_kg", "cost", "comfort", "offpeak_share", "peak_share", "missing_essentials",
]


def columns(appliances: list[Appliance] = APPLIANCES) -> list[str]:
    return BASE_COLUMNS + ["hrs_" + a.key for a in appliances] + [f"kwh_h{h:02d}" for h in range(24)]


def make_row(
    *, source: str, player_id: str, run_id: str, level: str, event: str | None, budget: float, par: float,
    result: Result, schedule: dict[str, list[float]], appliances: list[Appliance] = APPLIANCES,
    timestamp_utc: str = "", strategy: str = "",
) -> dict:
    """A log row built from the Python engine's result for a day (used for the simulated players)."""
    off, peak = period_shares(schedule, appliances)
    row = {
        "source": source, "player_id": player_id, "run_id": run_id, "timestamp_utc": timestamp_utc,
        "level": level, "event": event or "none", "budget_kwh": budget, "par": par, "score": result.score,
        "rating": result.rating, "energy_kwh": round(result.kwh, 4), "co2_kg": round(result.co2, 4),
        "cost": round(result.cost, 4), "comfort": round(result.comfort, 4), "offpeak_share": round(off, 4),
        "peak_share": round(peak, 4), "missing_essentials": len(result.missing), "strategy": strategy,
    }
    for a in appliances:
        row["hrs_" + a.key] = round(sum(float(x) for x in schedule[a.key]), 3)
    for h, k in enumerate(hourly_kwh(schedule, appliances)):
        row[f"kwh_h{h:02d}"] = round(k, 4)
    return row
