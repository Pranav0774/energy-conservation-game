"""Data pipeline: browser export layout, cleaning rules, simulated players, appliance table."""
import io
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from game.appliances import APPLIANCES
from game.datalog import columns
from game.engine import evaluate
from game.events import EVENTS, apply_event
from game.levels import LEVELS, par_for
from game.ui_config import build_config
from tools import clean_appliance_data as cad
from tools import clean_playlogs as cpl
from tools import simulate_players as sim

NODE = shutil.which("node")
ROOT = Path(__file__).parent
needs_node = pytest.mark.skipif(NODE is None, reason="Node.js is not installed")


def clean_one_level_day(strategy="peak_aware", level="Medium", event=None, seed=0):
    lv = LEVELS[level]
    schedule = sim.build(strategy, lv, event, seed)
    appliances = apply_event(APPLIANCES, event)
    res = evaluate(schedule, appliances, lv.budget_kwh, par_for(level, event))
    from game.datalog import make_row

    return make_row(source="simulated_bot", player_id="t", run_id=f"t-{strategy}-{seed}", level=level, event=event,
                    budget=lv.budget_kwh, par=par_for(level, event), result=res, schedule=schedule,
                    appliances=appliances, strategy=strategy)


def raw_frame(rows):
    return pd.read_csv(io.StringIO(pd.DataFrame(rows).to_csv(index=False)), dtype=str)


# ---------- simulated players ----------
@pytest.mark.parametrize("strategy", [s for s in sim.STRATEGIES if s != "optimizer"])
def test_strategies_make_valid_schedules(strategy):
    for lv in LEVELS.values():
        for event in [None, *EVENTS]:
            s = sim.build(strategy, lv, event, 0)
            assert set(s) == {a.key for a in APPLIANCES}
            assert all(len(v) == 24 and all(0.0 <= x <= 1.0 for x in v) for v in s.values())


def test_strategy_properties():
    lv = LEVELS["Medium"]
    full = evaluate(sim.build("full_comfort", lv, None, 0), APPLIANCES, lv.budget_kwh)
    assert full.comfort == pytest.approx(1.0) and not full.missing
    ess = evaluate(sim.build("essentials_only", lv, None, 0), APPLIANCES, lv.budget_kwh)
    assert ess.comfort == 0 and not ess.missing
    cut = evaluate(sim.build("budget_cutter", lv, None, 0), APPLIANCES, lv.budget_kwh)
    assert cut.kwh <= lv.budget_kwh + 1e-9 and not cut.missing


def test_peak_aware_costs_less_than_budget_cutter_at_same_comfort_level():
    lv = LEVELS["Medium"]
    a = evaluate(sim.build("budget_cutter", lv, None, 0), APPLIANCES, lv.budget_kwh)
    b = evaluate(sim.build("peak_aware", lv, None, 0), APPLIANCES, lv.budget_kwh)
    assert b.cost < a.cost


# ---------- play-log cleaning ----------
def test_clean_keeps_valid_rows_and_logs_counts():
    out, log = cpl.clean(raw_frame([clean_one_level_day(seed=i) for i in range(3)]))
    assert len(out) == 3 and dict(log)["clean rows kept"] == 3
    assert out["is_simulated"].all() and {"over_budget", "budget_used_pct"} <= set(out.columns)


def test_clean_drops_each_kind_of_bad_row():
    good = clean_one_level_day(seed=1)
    bad = {
        "dup": dict(good),
        "level": {**good, "run_id": "x1", "level": "Impossible"},
        "event": {**good, "run_id": "x2", "event": "volcano"},
        "neg": {**good, "run_id": "x3", "energy_kwh": -1},
        "comfort": {**good, "run_id": "x4", "comfort": 1.5},
        "co2": {**good, "run_id": "x5", "co2_kg": 99},
        "missing": {**good, "run_id": "x6", "score": ""},
        "hours": {**good, "run_id": "x7", "hrs_ac": 30},
    }
    out, log = cpl.clean(raw_frame([good, *bad.values()]))
    assert list(out["run_id"]) == [good["run_id"]]
    counts = dict(log)
    assert counts["duplicate run_id"] == 1 and counts["unknown level"] == 1 and counts["unknown event"] == 1
    assert counts["incomplete rows (a required field is missing or not a number)"] == 1


def test_clean_defaults_strategy_to_human_for_browser_exports():
    row = clean_one_level_day(seed=2)
    row.update(source="browser_player", strategy="")
    out, _ = cpl.clean(raw_frame([row]))
    assert out.loc[0, "strategy"] == "human" and not out.loc[0, "is_simulated"]


def test_clean_rejects_legacy_rows_without_new_columns():
    legacy = pd.DataFrame([{"level": "Medium", "score": 500, "energy_kwh": 8.0, "run_id": "old1"}]).astype(str)
    out, log = cpl.clean(legacy)
    assert out.empty and dict(log)["incomplete rows (a required field is missing or not a number)"] == 1


# ---------- browser export matches Python layout ----------
def run_export(store):
    cfg = build_config()
    out = subprocess.run([NODE, str(ROOT / "export_check.js")], input=json.dumps({"store": store, "appliances": cfg["appliances"]}),
                         capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


@needs_node
def test_browser_export_columns_match_python_columns():
    assert run_export({})["columns"] == columns()


@needs_node
def test_browser_export_round_trips_through_cleaning():
    hourly = [0.06] * 24
    run = {"id": "abc123", "ts": 1760000000000, "score": 512, "rating": "Bronze", "event": None, "budget": 10.0,
           "par": 750, "kwh": 1.44, "co2": 0.6408, "cost": 0.2, "comfort": 0.0, "missing": 1, "off": 0.25, "peak": 0.21,
           "hrs": {a.key: (24 if a.key == "fridge" else 0) for a in APPLIANCES}, "kwh_h": hourly}
    legacy = {"score": 400, "kwh": 5.0, "co2": 2.2, "cost": 1.0, "rating": "Keep trying", "event": "heatwave", "ts": 1}
    exported = run_export({"_pid": "p1", "_v": 2, "Medium": {"runs": [legacy, run]}})
    assert exported["runs"] == 2
    out, log = cpl.clean(pd.read_csv(io.StringIO(exported["csv"]), dtype=str))
    assert list(out["run_id"]) == ["abc123"]  # the legacy row has no per-appliance data, so it is dropped
    assert out.loc[0, "source"] == "browser_player" and out.loc[0, "player_id"] == "p1"
    assert out.loc[0, "event"] == "none" and out.loc[0, "strategy"] == "human"


# ---------- appliance table ----------
def test_appliance_cleaning_converts_annual_energy_and_drops_bad_rows():
    raw = pd.DataFrame([
        {"row_id": 1, "source_id": "A", "appliance_as_named": "Refrigerator (annual energy)", "low": 400, "high": 800, "unit": "kWh/year", "basis": "annual"},
        {"row_id": 2, "source_id": "A", "appliance_as_named": "Refrigerator (annual energy)", "low": 400, "high": 800, "unit": "kWh/year", "basis": "annual"},
        {"row_id": 3, "source_id": "B", "appliance_as_named": "Clothes iron", "low": 1800, "high": 1100, "unit": "watts", "basis": "rated_running"},
        {"row_id": 4, "source_id": "B", "appliance_as_named": "Clothes iron", "low": 1100, "high": 1800, "unit": "watts", "basis": "rated_running"},
    ])
    summary, long, log = cad.clean(raw)
    counts = dict(log)
    assert counts["duplicate rows removed"] == 1 and counts["rows with non-positive or reversed range removed"] == 1
    fridge = long[long["game_key"] == "fridge"].iloc[0]
    assert fridge["low_w"] == pytest.approx(400 * 1000 / 8760)
    iron = summary[summary["game_key"] == "iron"].iloc[0]
    assert iron["game_vs_range"] == "below" and iron["source_min_w"] == 1100


def test_real_appliance_table_covers_every_game_appliance():
    summary, _, _ = cad.clean(cad.load_raw())
    assert set(summary["game_key"]) == {a.key for a in APPLIANCES}
    assert (summary["n_rows"] > 0).all()
    assert all(r["game_vs_range"] in {"within", "below", "above"} for _, r in summary.iterrows())


def test_par_table_is_complete_and_matches_level_par():
    for lv in LEVELS.values():
        assert par_for(lv.name, None) == lv.par_score
        for event in EVENTS:
            assert par_for(lv.name, event) > 0
