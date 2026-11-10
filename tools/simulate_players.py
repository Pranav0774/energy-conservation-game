"""Generate SIMULATED play logs from scripted "bot" strategies, using the Python game engine.

These are not human players. They are a controlled way to study how different household behaviours score on
every level and event, and they are labelled source = "simulated_bot" everywhere. Real browser exports go in
data/raw/real_playlogs/ and are handled by the same cleaning script.

Run: python -m tools.simulate_players   ->  data/raw/playlogs/simulated_playlogs.csv
"""
import csv
import random
from pathlib import Path

from game.appliances import APPLIANCES
from game.datalog import columns, make_row
from game.engine import evaluate, tariff_period
from game.events import EVENTS, apply_event
from game.levels import LEVELS, par_for

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "playlogs" / "simulated_playlogs.csv"
SEEDS = 8
EVENT_KEYS = [None, *EVENTS]
PRICE = {"offpeak": 0, "standard": 1, "peak": 2}

# Hours of the day a household would naturally use each appliance, most likely first.
NATURAL = {
    "fridge": list(range(24)),
    "cooktop": [7, 12, 19, 8, 13, 18],
    "ac": [14, 15, 16, 13, 17, 18, 19, 20, 12, 21, 22, 11],
    "fan": [12, 13, 14, 15, 16, 11, 10, 17, 18, 19, 20, 21, 9, 22],
    "lights": [19, 20, 21, 6, 18, 22, 5, 7, 23, 17],
    "tv": [20, 21, 19, 22, 18, 17, 16, 15],
    "computer": [10, 11, 14, 15, 9, 16, 13, 17, 20, 21],
    "washer": [10, 11, 9],
    "heater": [6, 7, 19, 20],
    "iron": [17, 18, 8],
}
# Hours each appliance can reasonably run (used by the peak-aware strategy).
WINDOW = {
    "fridge": range(24), "cooktop": [6, 7, 8, 9, 11, 12, 13, 14, 17, 18, 19, 20, 21],
    "ac": [0, 1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    "fan": range(24), "lights": [5, 6, 7, 17, 18, 19, 20, 21, 22, 23],
    "tv": range(7, 24), "computer": range(8, 23), "washer": range(24), "heater": range(24), "iron": range(24),
}
STRATEGIES = ["full_comfort", "essentials_only", "casual_random", "budget_cutter", "peak_aware", "optimizer"]


def empty() -> dict[str, list[float]]:
    return {a.key: [0.0] * 24 for a in APPLIANCES}


def jitter(order: list[int], rnd: random.Random) -> list[int]:
    order = order[:]
    for _ in range(2):  # a couple of neighbouring swaps so seeds differ a little
        i = rnd.randrange(len(order) - 1)
        order[i], order[i + 1] = order[i + 1], order[i]
    return order


def natural_schedule(appliances, rnd) -> dict[str, list[float]]:
    s = empty()
    for a in appliances:
        for h in jitter(NATURAL[a.key], rnd)[: min(a.target_hours, 24)]:
            s[a.key][h] = 1.0
    return s


def kwh(schedule, appliances) -> float:
    return sum(a.watts / 1000 * sum(schedule[a.key]) for a in appliances)


def trim_to_budget(schedule, appliances, budget, prefer_peak_first):
    """Remove optional appliance-hours until energy fits the budget, giving up the least comfort per kWh saved."""
    for _ in range(500):
        if kwh(schedule, appliances) <= budget:
            break
        best = None
        for a in appliances:
            if a.essential or sum(schedule[a.key]) <= 0:
                continue
            loss_per_kwh = (a.comfort_weight / a.target_hours) / (a.watts / 1000)
            if best is None or loss_per_kwh < best[0]:
                best = (loss_per_kwh, a)
        if best is None:
            break
        a = best[1]
        on = [h for h in range(24) if schedule[a.key][h] > 0]
        if prefer_peak_first:
            on.sort(key=lambda h: (-PRICE[tariff_period(h)], -h))
        else:
            on.sort(reverse=True)
        schedule[a.key][on[0]] = 0.0
    return schedule


def peak_aware_schedule(appliances, rnd):
    s = empty()
    for a in appliances:
        # cheapest hours first; ties broken at random so flexible loads spread across the off-peak hours
        # instead of all piling into hour 0
        tie = {h: rnd.random() for h in WINDOW[a.key]}
        window = sorted(WINDOW[a.key], key=lambda h: (PRICE[tariff_period(h)], tie[h]))
        for h in window[: min(a.target_hours, 24)]:
            s[a.key][h] = 1.0
    return s


def build(strategy, level, event, seed):
    rnd = random.Random(f"{strategy}|{level.name}|{event}|{seed}")
    appliances = apply_event(APPLIANCES, event)
    budget = level.budget_kwh
    if strategy == "full_comfort":
        return natural_schedule(appliances, rnd)
    if strategy == "essentials_only":
        s = empty()
        s["fridge"] = [1.0] * 24
        for h in NATURAL["cooktop"][: next(a.target_hours for a in appliances if a.key == "cooktop")]:
            s["cooktop"][h] = 1.0
        return s
    if strategy == "casual_random":
        s = natural_schedule(appliances, rnd)
        for a in appliances:
            if a.essential:
                continue
            keep = max(0, round(sum(s[a.key]) * rnd.uniform(0.3, 1.1)))
            hours = [h for h in range(24) if s[a.key][h] > 0]
            rnd.shuffle(hours)
            for h in hours[keep:]:
                s[a.key][h] = 0.0
        return s
    if strategy == "budget_cutter":
        return trim_to_budget(natural_schedule(appliances, rnd), appliances, budget, prefer_peak_first=False)
    if strategy == "peak_aware":
        return trim_to_budget(peak_aware_schedule(appliances, rnd), appliances, budget, prefer_peak_first=True)
    if strategy == "optimizer":
        from tools.balance import search_schedule  # imported here: it is slow and only needed for this strategy

        # best-effort reference: improve the peak-aware plan by local search (same method that sets par scores)
        start = build("peak_aware", level, event, seed)
        return search_schedule(budget, par_for(level.name, event), seed, appliances, iters=6000, start=start)[1]
    raise ValueError(strategy)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cols = columns() + ["strategy"]
    n = 0
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for strategy in STRATEGIES:
            seeds = 1 if strategy in ("optimizer", "essentials_only") else SEEDS
            for level in LEVELS.values():
                for event in EVENT_KEYS:
                    for seed in range(seeds):
                        schedule = build(strategy, level, event, seed)
                        appliances = apply_event(APPLIANCES, event)
                        par = par_for(level.name, event)
                        res = evaluate(schedule, appliances, level.budget_kwh, par)
                        w.writerow(make_row(
                            source="simulated_bot", player_id=f"bot_{strategy}_{seed}",
                            run_id=f"sim-{strategy}-{level.name}-{event or 'none'}-{seed}", level=level.name,
                            event=event, budget=level.budget_kwh, par=par, result=res, schedule=schedule,
                            appliances=appliances, strategy=strategy,
                        ))
                        n += 1
    print(f"wrote {n} simulated runs to {OUT}")


if __name__ == "__main__":
    main()
