# Week 2: balance and play-test record

## Balance (`python -m tools.balance`)
A hill-climbing optimiser searches for the best day it can find at each level (16 random starts, hour toggles then partial hours). Par scores in `game/levels.py` are set from this.

| Level | Budget | Best score found | Par used | Notes |
|---|---|---|---|---|
| Easy | 14 kWh | 810 | 800 | Best plan uses 9.7 kWh at 78% comfort |
| Medium | 10 kWh | 749 | 750 | 9.3 kWh at 78% comfort |
| Hard | 7 kWh | 636 | 640 | 7.0 kWh at 60% comfort. Par lowered from 660 |

Degenerate strategies score poorly at every level (Medium): running nothing 100, essentials only about 430, everything at full comfort about 200. A balanced plan scores 500–750.

The optimiser is stochastic, so treat its numbers as "about" values. Re-run it if appliance data, tariffs or scoring weights change.

## Automated checks
- `tests/test_engine.py`: energy, CO₂, cost, comfort, essentials, scoring, ratings, config bridge.
- `tests/test_frontend_parity.py`: runs `frontend/scoring.js` in Node on 200 random days per level and requires the same results as `game/engine.py` (skipped if Node is not installed).

## Scripted play-tests through the real UI
Played in the browser through the actual game code (`window.__game.advance` fast-forwards time):

| Check | Result |
|---|---|
| Full Hard day: start, switch appliances hourly, reach 24:00 | Score 543, Silver, Python engine confirmed the same score |
| "Play again" returns to menu with a clean day (fridge on, all else off, clock 00:00) | Pass |
| Change level for the second day (Easy) and play it through | Score 657, Silver, confirmed by Python |
| Pause holds the clock | Pass |
| Number keys toggle appliances | Pass |
| Result screen if the engine does not answer | Falls back to "Scored in your browser" after 8 s |

## Not yet done (needs people)
- Play-test with 3–5 real players (planned for Week 3/4): do they understand the budget ring, peak pricing and the essentials rule? Is 4 minutes per day right?
- Try on a slow college PC and a phone.
- Tune the tips wording after seeing real plays.

## Known limits
- Layout was checked in a Chromium pane at phone-ish and desktop widths, not on real devices.
- The live "on pace" estimate uses average use so far, so it is jumpy early in the day.

## Week 3 checks
| Check | Result |
|---|---|
| Heatwave day through the real UI: banner shown, AC target 11 h, scored by Python | Browser and Python scores equal (467) |
| Event changes undone after "Play again" (AC target back to 8 h, banner hidden) | Pass |
| Second run saved and compared with the first | "New personal best", energy -13%, score +96, cost shown |
| Browser vs Python scoring on every level x event combination (60 random days each) | Pass |
| Tips: well-formed on 120 random days; specific tips on hand-made days (over budget, missing fridge, washer at peak) | Pass |
