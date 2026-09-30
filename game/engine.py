"""Energy, CO2, cost and score calculations for the conservation game.

A schedule maps an appliance key to 24 numbers, one per hour of the day. Each number is the
fraction of that hour the appliance ran (True/1.0 = the whole hour, 0.5 = thirty minutes).
"""
from dataclasses import dataclass

from .appliances import Appliance

CO2_KG_PER_KWH = 0.445  # IEA global average, 2024 (see docs/research.md); edit for your region
CURRENCY = "$"
TARIFF = {"peak": 0.30, "standard": 0.15, "offpeak": 0.08}  # currency per kWh
PEAK_HOURS = set(range(17, 22))
OFFPEAK_HOURS = set(range(22, 24)) | set(range(0, 6))

# Score = BASE + comfort + budget + timing - essentials. See docs/design.md.
BASE = 300.0
COMFORT_MAX = 500.0
BUDGET_BONUS_MAX = 200.0
OVER_BUDGET_PENALTY = 600.0
TIMING_MAX = 100.0
ESSENTIAL_PENALTY = 200.0
RATING_FRACTIONS = {"Gold": 0.90, "Silver": 0.78, "Bronze": 0.65}  # of the level's par score

EPS = 1e-6

Schedule = dict[str, list[float]]


def tariff_period(hour: int) -> str:
    if hour in PEAK_HOURS:
        return "peak"
    if hour in OFFPEAK_HOURS:
        return "offpeak"
    return "standard"


def hours_on(schedule: Schedule, key: str) -> float:
    return sum(float(x) for x in schedule.get(key, []))


def hourly_kwh(schedule: Schedule, appliances: list[Appliance]) -> list[float]:
    out = [0.0] * 24
    for a in appliances:
        for h, on in enumerate(schedule.get(a.key, [0.0] * 24)):
            out[h] += a.watts / 1000 * float(on)
    return out


def energy_kwh(schedule: Schedule, appliances: list[Appliance]) -> float:
    return sum(hourly_kwh(schedule, appliances))


def co2_kg(kwh: float) -> float:
    return kwh * CO2_KG_PER_KWH


def cost(schedule: Schedule, appliances: list[Appliance]) -> float:
    return sum(kwh * TARIFF[tariff_period(h)] for h, kwh in enumerate(hourly_kwh(schedule, appliances)))


def comfort_ratio(schedule: Schedule, appliances: list[Appliance]) -> float:
    """Weighted share (0..1) of the wanted appliance-hours that were met.

    Only discretionary appliances count: essentials are enforced by a penalty instead, so
    running just the fridge and cooktop can't earn comfort points.
    """
    optional = [a for a in appliances if not a.essential]
    total = sum(a.comfort_weight for a in optional)
    met = sum(a.comfort_weight * min(hours_on(schedule, a.key), a.target_hours) / a.target_hours for a in optional)
    return met / total if total else 0.0


def missing_essentials(schedule: Schedule, appliances: list[Appliance]) -> list[Appliance]:
    return [a for a in appliances if a.essential and hours_on(schedule, a.key) < a.target_hours - EPS]


def period_shares(schedule: Schedule, appliances: list[Appliance]) -> tuple[float, float]:
    """(offpeak_share, peak_share) of the energy used."""
    hourly = hourly_kwh(schedule, appliances)
    total = sum(hourly)
    if total == 0:
        return 0.0, 0.0
    off = sum(k for h, k in enumerate(hourly) if h in OFFPEAK_HOURS)
    peak = sum(k for h, k in enumerate(hourly) if h in PEAK_HOURS)
    return off / total, peak / total


@dataclass
class Result:
    kwh: float
    co2: float
    cost: float
    budget_kwh: float
    comfort: float
    missing: list[str]
    base_pts: float
    comfort_pts: float
    budget_pts: float
    timing_pts: float
    essential_pen: float
    score: int
    rating: str


def rate(score: int, par_score: float = 800) -> str:
    """Rating relative to the level's par (roughly the best score a good plan can reach)."""
    for name, fraction in RATING_FRACTIONS.items():
        if score >= fraction * par_score:
            return name
    return "Keep trying"


def evaluate(
    schedule: Schedule, appliances: list[Appliance], budget_kwh: float, par_score: float = 800
) -> Result:
    kwh = energy_kwh(schedule, appliances)
    comfort = comfort_ratio(schedule, appliances)
    missing = missing_essentials(schedule, appliances)
    off, peak = period_shares(schedule, appliances)

    comfort_pts = COMFORT_MAX * comfort
    if kwh <= budget_kwh:
        budget_pts = BUDGET_BONUS_MAX * (budget_kwh - kwh) / budget_kwh
    else:
        budget_pts = -OVER_BUDGET_PENALTY * (kwh - budget_kwh) / budget_kwh
    timing_pts = TIMING_MAX * (off - peak)
    essential_pen = ESSENTIAL_PENALTY * len(missing)

    score = max(0, round(BASE + comfort_pts + budget_pts + timing_pts - essential_pen))
    return Result(
        kwh=kwh,
        co2=co2_kg(kwh),
        cost=cost(schedule, appliances),
        budget_kwh=budget_kwh,
        comfort=comfort,
        missing=[a.name for a in missing],
        base_pts=BASE,
        comfort_pts=comfort_pts,
        budget_pts=budget_pts,
        timing_pts=timing_pts,
        essential_pen=essential_pen,
        score=score,
        rating=rate(score, par_score),
    )
