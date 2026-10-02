"""The browser (frontend/scoring.js) and Python (game/engine.py) must score a day identically."""
import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from game.appliances import APPLIANCES
from game.engine import evaluate
from game.levels import LEVELS
from game.ui_config import build_config

NODE = shutil.which("node")
ROOT = Path(__file__).parent


def random_day(rnd: random.Random) -> dict[str, list[int]]:
    """A random day as whole minutes per hour, the way the live game records it."""
    day = {a.key: [0] * 24 for a in APPLIANCES}
    for a in APPLIANCES:
        density = rnd.random()
        for h in range(24):
            if rnd.random() < density:
                day[a.key][h] = rnd.choice([60, 60, 45, 30, 15, 7, 1])
    if rnd.random() < 0.7:
        day["fridge"] = [60] * 24
    return day


@pytest.mark.skipif(NODE is None, reason="Node.js is not installed")
@pytest.mark.parametrize("level_name", list(LEVELS))
def test_js_and_python_scores_match(level_name):
    rnd = random.Random(42)
    cases = [random_day(rnd) for _ in range(200)]
    level = LEVELS[level_name]
    cfg = build_config()
    js_level = next(lv for lv in cfg["levels"] if lv["name"] == level_name)

    out = subprocess.run(
        [NODE, str(ROOT / "parity.js")],
        input=json.dumps({"cfg": cfg, "level": js_level, "cases": cases}),
        capture_output=True,
        text=True,
        check=True,
    )
    js_results = json.loads(out.stdout)

    for minutes, js in zip(cases, js_results):
        schedule = {k: [m / 60 for m in row] for k, row in minutes.items()}
        py = evaluate(schedule, APPLIANCES, level.budget_kwh, level.par_score)
        assert js["kwh"] == pytest.approx(py.kwh)
        assert js["co2"] == pytest.approx(py.co2)
        assert js["cost"] == pytest.approx(py.cost)
        assert js["comfort"] == pytest.approx(py.comfort)
        assert js["missing"] == py.missing
        assert abs(js["score"] - py.score) <= 1  # Math.round vs Python's banker's rounding at .5
        if js["score"] == py.score:
            assert js["rating"] == py.rating
