import pytest

from game.appliances import APPLIANCES
from game.engine import (
    CO2_KG_PER_KWH,
    TARIFF,
    co2_kg,
    cost,
    energy_kwh,
    evaluate,
    hourly_kwh,
    missing_essentials,
    tariff_period,
)


def empty():
    return {a.key: [False] * 24 for a in APPLIANCES}


def only(key, hours):
    s = empty()
    for h in hours:
        s[key][h] = True
    return s


def test_energy_kwh():
    s = only("ac", [12, 13])  # 1500 W for 2 h
    assert energy_kwh(s, APPLIANCES) == pytest.approx(3.0)


def test_hourly_profile():
    s = only("heater", [7])
    hourly = hourly_kwh(s, APPLIANCES)
    assert hourly[7] == pytest.approx(2.0)
    assert sum(hourly) == pytest.approx(2.0)


def test_co2():
    assert co2_kg(10) == pytest.approx(10 * CO2_KG_PER_KWH)


def test_tariff_periods():
    assert tariff_period(18) == "peak"
    assert tariff_period(2) == "offpeak"
    assert tariff_period(12) == "standard"


def test_cost_uses_time_of_use():
    peak = cost(only("washer", [18]), APPLIANCES)
    off = cost(only("washer", [2]), APPLIANCES)
    assert peak == pytest.approx(0.5 * TARIFF["peak"])
    assert off == pytest.approx(0.5 * TARIFF["offpeak"])
    assert off < peak


def test_missing_essentials():
    names = {a.key for a in missing_essentials(empty(), APPLIANCES)}
    assert names == {"fridge", "cooktop"}
    s = empty()
    s["fridge"] = [True] * 24
    s["cooktop"][8] = s["cooktop"][19] = True
    assert missing_essentials(s, APPLIANCES) == []


def balanced():
    s = empty()
    s["fridge"] = [True] * 24
    for h in (7, 13):
        s["cooktop"][h] = True
    for h in (14, 15):
        s["ac"][h] = True
    for h in range(10, 20):
        s["fan"][h] = True
    for h in (6, 19):
        s["lights"][h] = True
    return s


def test_score_over_budget_is_worse():
    ok = evaluate(balanced(), APPLIANCES, budget_kwh=10)
    over = evaluate(balanced(), APPLIANCES, budget_kwh=3)
    assert ok.score > over.score


def test_missing_essentials_penalised():
    good = balanced()
    bad = balanced()
    bad["fridge"] = [False] * 24
    assert evaluate(good, APPLIANCES, 10).score > evaluate(bad, APPLIANCES, 10).score


def test_off_peak_timing_bonus():
    a = empty(); a["fridge"] = [True] * 24; a["washer"][2] = True
    b = empty(); b["fridge"] = [True] * 24; b["washer"][18] = True
    assert evaluate(a, APPLIANCES, 10).timing_pts > evaluate(b, APPLIANCES, 10).timing_pts


def test_essentials_only_earns_no_comfort():
    s = empty()
    s["fridge"] = [True] * 24
    s["cooktop"][7] = s["cooktop"][12] = True
    r = evaluate(s, APPLIANCES, 10)
    assert r.comfort == 0
    assert r.rating == "Keep trying"


def test_rating_is_relative_to_par():
    from game.engine import rate

    assert rate(560, par_score=660) == "Silver"
    assert rate(500, par_score=800) == "Keep trying"
    assert rate(700, par_score=750) == "Gold"


def test_score_never_negative():
    s = {a.key: [True] * 24 for a in APPLIANCES}
    assert evaluate(s, APPLIANCES, 5).score == 0
