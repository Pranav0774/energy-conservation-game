"""The browser (frontend/scoring.js) and Python (game/engine.py) must score a day identically."""
import json
import random
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path

import pytest

from game.appliances import APPLIANCES
from game.engine import evaluate
from game.events import EVENTS, apply_event
from game.levels import LEVELS, par_for
from game.ui_config import build_config

NODE = shutil.which("node")
ROOT = Path(__file__).parent
EVENT_KEYS = [None, *EVENTS]


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


def run_node(script: str, payload: dict):
    out = subprocess.run([NODE, str(ROOT / script)], input=json.dumps(payload), capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


def js_config_for(event_key):
    """The config as the browser sees it on an event day (target hours overridden)."""
    cfg = build_config()
    event = EVENTS.get(event_key or "")
    if event:
        for a in cfg["appliances"]:
            a["target_hours"] = event.changes.get(a["key"], a["target_hours"])
    return cfg


@pytest.mark.skipif(NODE is None, reason="Node.js is not installed")
@pytest.mark.parametrize("event_key", EVENT_KEYS)
@pytest.mark.parametrize("level_name", list(LEVELS))
def test_js_and_python_scores_match(level_name, event_key):
    rnd = random.Random(42)
    cases = [random_day(rnd) for _ in range(60)]
    level = LEVELS[level_name]
    par = par_for(level_name, event_key)
    js_level = {**next(lv for lv in build_config()["levels"] if lv["name"] == level_name), "par": par}
    js_results = run_node("parity.js", {"cfg": js_config_for(event_key), "level": js_level, "cases": cases})

    appliances = apply_event(APPLIANCES, event_key)
    for minutes, js in zip(cases, js_results):
        schedule = {k: [m / 60 for m in row] for k, row in minutes.items()}
        py = evaluate(schedule, appliances, level.budget_kwh, par)
        assert js["kwh"] == pytest.approx(py.kwh)
        assert js["co2"] == pytest.approx(py.co2)
        assert js["cost"] == pytest.approx(py.cost)
        assert js["comfort"] == pytest.approx(py.comfort)
        assert js["missing"] == py.missing
        assert abs(js["score"] - py.score) <= 1  # Math.round vs Python's banker's rounding at .5
        if js["score"] == py.score:
            assert js["rating"] == py.rating


@pytest.mark.skipif(NODE is None, reason="Node.js is not installed")
def test_tips_are_well_formed_and_specific():
    rnd = random.Random(7)
    cfg = build_config()
    lv = next(l for l in cfg["levels"] if l["name"] == "Medium")
    days = [random_day(rnd) for _ in range(120)]
    # hand-made days that must trigger specific tips
    over = {a.key: [60] * 24 for a in APPLIANCES}
    no_fridge = {a.key: [0] * 24 for a in APPLIANCES}
    peak_washer = {a.key: [0] * 24 for a in APPLIANCES}
    peak_washer["fridge"] = [60] * 24
    peak_washer["washer"][18] = 60
    peak_washer["washer"][19] = 60
    days += [over, no_fridge, peak_washer]

    tips = run_node("tips_check.js", {"cfg": cfg, "level": lv, "days": days})
    for day_tips in tips:
        assert len(day_tips) <= 4
        for tip in day_tips:
            assert isinstance(tip, str) and tip
            assert "undefined" not in tip and "NaN" not in tip and "Infinity" not in tip
    assert any("over budget" in t for t in tips[-3]), "all-on day should say over budget"
    assert any("Essentials fell short" in t for t in tips[-2]), "no fridge should flag essentials"
    assert any("17:00–22:00 peak" in t and "washing machine" in t for t in tips[-1]), "peak washer what-if"
