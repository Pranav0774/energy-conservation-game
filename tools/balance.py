"""Estimate the best achievable score per level and event (used to set par scores in game/levels.py).

Hill-climbs over hour toggles, then partial hours. Because a plain hill-climb from an empty day gets stuck on some
event days, it is also started from the scripted strategies in tools/simulate_players.py and the best result wins.

Run: python -m tools.balance        (prints PAR_BY_EVENT to paste into game/levels.py)
"""
import random
from concurrent.futures import ProcessPoolExecutor

from game.appliances import APPLIANCES as A
from game.engine import evaluate
from game.events import EVENTS, apply_event
from game.levels import LEVELS

KEYS = [a.key for a in A]


def search_schedule(budget: float, par: float, seed: int, appliances=A, iters: int = 12000, start=None):
    """Hill-climb to a good day. Returns (result, schedule). `start` is an optional schedule to improve."""
    rnd = random.Random(seed)
    s = {k: list(v) for k, v in start.items()} if start else {k: [1.0 if k == "fridge" else 0.0] * 24 for k in KEYS}
    cur = evaluate(s, appliances, budget, par).score

    def sweep(steps, n):
        nonlocal cur
        for _ in range(n):
            k, h = rnd.choice(KEYS), rnd.randrange(24)
            old = s[k][h]
            s[k][h] = min(1.0, max(0.0, old + rnd.choice(steps)))
            score = evaluate(s, appliances, budget, par).score
            if score >= cur:
                cur = score
            else:
                s[k][h] = old

    sweep([1.0, -1.0], iters)
    sweep([0.5, -0.5, 0.25, -0.25], iters // 2)
    return evaluate(s, appliances, budget, par), s


def search(budget: float, par: float, seed: int, appliances=A, iters: int = 12000):
    return search_schedule(budget, par, seed, appliances, iters)[0]


def best_for(level_name: str, event_key) -> int:
    """Best score found for one level and event, from scripted-strategy starts plus a from-scratch climb."""
    from tools.simulate_players import build  # imported here to avoid a circular import

    level = LEVELS[level_name]
    appliances = apply_event(A, event_key)
    best = 0
    for seed in range(2):  # from scratch
        best = max(best, search(level.budget_kwh, 800, seed, appliances).score)
    for strategy in ("peak_aware", "budget_cutter"):
        for seed in range(3):
            start = build(strategy, level, event_key, seed)
            best = max(best, evaluate(start, appliances, level.budget_kwh, 800).score)
            best = max(best, search_schedule(level.budget_kwh, 800, seed, appliances, 6000, start)[0].score)
    return best


def _task(args):
    return args, best_for(*args)


if __name__ == "__main__":
    combos = [(lv, ev) for lv in LEVELS for ev in [None, *EVENTS]]
    with ProcessPoolExecutor() as pool:
        results = dict(pool.map(_task, combos))
    print("PAR_BY_EVENT: dict[str, dict[str, float]] = {")
    for lv in LEVELS:
        row = {(ev or "none"): results[(lv, ev)] for ev in [None, *EVENTS]}
        print(f'    "{lv}": {row},'.replace("'", '"'))
    print("}")
