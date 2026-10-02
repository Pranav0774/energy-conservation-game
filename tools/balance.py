"""Estimate the best achievable score per level (used to set `par_score` in game/levels.py).

Hill-climbs over hour toggles, then refines with partial hours. Run: python -m tools.balance
"""
import random

from game.appliances import APPLIANCES as A
from game.engine import evaluate
from game.levels import LEVELS

KEYS = [a.key for a in A]


def search(budget: float, par: float, seed: int, iters: int = 12000):
    rnd = random.Random(seed)
    s = {k: [1.0 if k == "fridge" else 0.0] * 24 for k in KEYS}
    cur = evaluate(s, A, budget, par).score

    def sweep(steps, n):
        nonlocal cur
        for _ in range(n):
            k, h = rnd.choice(KEYS), rnd.randrange(24)
            old = s[k][h]
            s[k][h] = min(1.0, max(0.0, old + rnd.choice(steps)))
            score = evaluate(s, A, budget, par).score
            if score >= cur:
                cur = score
            else:
                s[k][h] = old

    sweep([1.0, -1.0], iters)
    sweep([0.5, -0.5, 0.25, -0.25], iters // 2)
    return evaluate(s, A, budget, par)


if __name__ == "__main__":
    for lv in LEVELS.values():
        best = max((search(lv.budget_kwh, lv.par_score, seed) for seed in range(16)), key=lambda r: r.score)
        print(
            f"{lv.name:7} par={lv.par_score:.0f}  best={best.score}  "
            f"kwh={best.kwh:.1f}  comfort={best.comfort:.2f}  rating={best.rating}"
        )
