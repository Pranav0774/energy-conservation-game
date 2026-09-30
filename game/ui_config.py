"""Bridge between the Python engine and the browser front end (frontend/)."""
from . import engine
from .appliances import APPLIANCES
from .levels import LEVELS


def build_config() -> dict:
    """Constants the front end needs so its live numbers match the engine."""
    return {
        "appliances": [
            {
                "key": a.key,
                "name": a.name,
                "watts": a.watts,
                "target_hours": a.target_hours,
                "weight": a.comfort_weight,
                "essential": a.essential,
            }
            for a in APPLIANCES
        ],
        "levels": [
            {"name": lv.name, "budget": lv.budget_kwh, "par": lv.par_score, "description": lv.description}
            for lv in LEVELS.values()
        ],
        "tariff": engine.TARIFF,
        "peak_hours": sorted(engine.PEAK_HOURS),
        "offpeak_hours": sorted(engine.OFFPEAK_HOURS),
        "co2": engine.CO2_KG_PER_KWH,
        "currency": engine.CURRENCY,
        "scoring": {
            "base": engine.BASE,
            "comfort_max": engine.COMFORT_MAX,
            "budget_bonus_max": engine.BUDGET_BONUS_MAX,
            "over_penalty": engine.OVER_BUDGET_PENALTY,
            "timing_max": engine.TIMING_MAX,
            "essential_penalty": engine.ESSENTIAL_PENALTY,
            "rating_fractions": engine.RATING_FRACTIONS,
        },
    }


def sanitize_schedule(raw: dict) -> dict[str, list[float]]:
    """Clamp a schedule sent by the browser to known appliances and 24 values in 0..1."""
    clean = {}
    for a in APPLIANCES:
        values = raw.get(a.key) or []
        row = []
        for h in range(24):
            try:
                v = float(values[h])
            except (IndexError, TypeError, ValueError):
                v = 0.0
            row.append(min(1.0, max(0.0, v)))
        clean[a.key] = row
    return clean
