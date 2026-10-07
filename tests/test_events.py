from game.appliances import APPLIANCES
from game.events import EVENTS, apply_event
from game.levels import LEVELS, par_for
from game.ui_config import build_config


def test_no_event_leaves_appliances_unchanged():
    assert apply_event(APPLIANCES, None) == APPLIANCES
    assert apply_event(APPLIANCES, "not-an-event") == APPLIANCES


def test_event_changes_only_listed_targets():
    heat = {a.key: a for a in apply_event(APPLIANCES, "heatwave")}
    base = {a.key: a for a in APPLIANCES}
    assert heat["ac"].target_hours == 11 and heat["fan"].target_hours == 14
    assert heat["tv"] == base["tv"]
    assert heat["ac"].watts == base["ac"].watts  # only the wanted hours change


def test_events_reference_real_appliances():
    keys = {a.key for a in APPLIANCES}
    for event in EVENTS.values():
        assert event.changes and set(event.changes) <= keys


def test_config_exposes_events_and_par_per_event():
    cfg = build_config()
    assert {e["key"] for e in cfg["events"]} == set(EVENTS)
    for lv in cfg["levels"]:
        assert set(lv["par_by_event"]) == {"none", *EVENTS}
        assert all(p > 0 for p in lv["par_by_event"].values())


def test_par_falls_back_to_level_par():
    assert par_for("Medium", "no-such-event") == LEVELS["Medium"].par_score
