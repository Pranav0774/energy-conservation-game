from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    name: str
    budget_kwh: float
    par_score: float  # ~best score found by an optimiser on a normal day; ratings are relative to this
    description: str


LEVELS = {
    "Easy": Level("Easy", 14.0, 800, "A relaxed budget. Avoid waste and you'll be fine."),
    "Medium": Level("Medium", 10.0, 750, "You'll have to choose what really matters."),
    "Hard": Level("Hard", 7.0, 640, "Every kWh counts. Timing and trade-offs decide the score."),
}

# About the best achievable score per level and event ("none" = a normal day), from `python -m tools.balance`.
# The search is stochastic (roughly +/-2%), so "none" keeps the values chosen in Week 2.
# Events change what the household wants, so the par differs and ratings stay fair.
PAR_BY_EVENT: dict[str, dict[str, float]] = {
    "Easy": {"none": 800, "heatwave": 801, "guests": 642, "wfh": 802, "laundry": 800, "coldsnap": 766},
    "Medium": {"none": 750, "heatwave": 747, "guests": 607, "wfh": 733, "laundry": 728, "coldsnap": 703},
    "Hard": {"none": 640, "heatwave": 615, "guests": 527, "wfh": 595, "laundry": 605, "coldsnap": 621},
}


def par_for(level_name: str, event_key: str | None) -> float:
    """Par score for a level on a given event day, falling back to the level's normal-day par."""
    level = LEVELS[level_name]
    return PAR_BY_EVENT.get(level_name, {}).get(event_key or "none", level.par_score)
