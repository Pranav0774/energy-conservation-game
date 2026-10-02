from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    name: str
    budget_kwh: float
    par_score: float  # ~best score found by an optimiser; ratings are relative to this
    description: str


LEVELS = {
    "Easy": Level("Easy", 14.0, 800, "A relaxed budget. Avoid waste and you'll be fine."),
    "Medium": Level("Medium", 10.0, 750, "You'll have to choose what really matters."),
    "Hard": Level("Hard", 7.0, 640, "Every kWh counts. Timing and trade-offs decide the score."),
}
