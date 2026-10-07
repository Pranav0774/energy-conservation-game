"""Estimate the best achievable score per level (used to set `par_score` in game/levels.py).

Hill-climbs over hour toggles, then refines with partial hours. Run: python -m tools.balance
"""
import random

from game.appliances import APPLIANCES as A
from game.engine import evaluate
from game.events import EVENTS, apply_event
from game.levels import LEVELS

KEYS = [a.key for a in A]


def search(budget: float, par: float, seed: int, appliances=A, iters: int = 12000):
    rnd = random.Random(seed)
    s = {k: [1.0 if k == "fridge" else 0.0] * 24 for k in KEYS}
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
    return evaluate(s, appliances, budget, par)


def best_score(budget: float, appliances, seeds: int = 8) -> int:
    return max(search(budget, 800, s, appliances).score for s in range(seeds))


if __name__ == "__main__":
    # Prints the par table to paste into game/levels.py (PAR_BY_EVENT).
    print("PAR_BY_EVENT = {")
    for lv in LEVELS.values():
        row = {"none": best_score(lv.budget_kwh, A)}
        for key in EVENTS:
            row[key] = best_score(lv.budget_kwh, apply_event(A, key))
        print(f'    "{lv.name}": {row},')
    print("}")
