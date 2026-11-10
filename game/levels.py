from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    name: str
    budget_kwh: float
    par_score: float  # ~best score found by an optimiser on a normal day; ratings are relative to this
    description: str


LEVELS = {
    "Easy": Level("Easy", 14.0, 809, "A relaxed budget. Avoid waste and you'll be fine."),
    "Medium": Level("Medium", 10.0, 756, "You'll have to choose what really matters."),
    "Hard": Level("Hard", 7.0, 636, "Every kWh counts. Timing and trade-offs decide the score."),
}

# About the best achievable score per level and event ("none" = a normal day), from `python -m tools.balance`.
# The search is stochastic (roughly +/-2%). It starts from scripted strategies as well as from an empty day,
# because a plain hill-climb understated the par on some event days (e.g. Easy "guests" 642 vs 777).
# Events change what the household wants, so the par differs and ratings stay fair.
PAR_BY_EVENT: dict[str, dict[str, float]] = {
    "Easy": {"none": 809, "heatwave": 806, "guests": 777, "wfh": 800, "laundry": 794, "coldsnap": 766},
    "Medium": {"none": 756, "heatwave": 750, "guests": 691, "wfh": 744, "laundry": 730, "coldsnap": 709},
    "Hard": {"none": 636, "heatwave": 629, "guests": 536, "wfh": 617, "laundry": 619, "coldsnap": 636},
}


def par_for(level_name: str, event_key: str | None) -> float:
    """Par score for a level on a given event day, falling back to the level's normal-day par."""
    level = LEVELS[level_name]
    return PAR_BY_EVENT.get(level_name, {}).get(event_key or "none", level.par_score)
