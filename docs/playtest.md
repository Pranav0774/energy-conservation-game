# Week 2: balance and play-test record

## Balance (`python -m tools.balance`)
A hill-climbing optimiser searches for the best day it can find at each level (16 random starts, hour toggles then partial hours). Par scores in `game/levels.py` are set from this.

| Level | Budget | Best score found | Par used | Notes |
|---|---|---|---|---|
| Easy | 14 kWh | 809 | 809 | Rebuilt in Week 5 (see below) |
| Medium | 10 kWh | 756 | 756 | |
| Hard | 7 kWh | 636 | 636 | |

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
- Play-test with 3–5 real players using [playtest_kit.md](playtest_kit.md): do they understand the budget ring, peak pricing and the essentials rule? Is 4 minutes per day right?
- Try on a slow college PC and a real phone.
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

## Week 4 checks
| Check | Result |
|---|---|
| Soak test: 36 random full days through the real UI (3 levels x 6 event settings x 2) | Every day confirmed by the Python engine, 0 score or rating mismatches, 0 JavaScript errors. Scores were all 0 because random play overshoots the budget, so this only proved the plumbing |
| Soak test with realistic sparse days: 54 full days | 0 unconfirmed, 0 mismatches, 0 "undefined/NaN" in result text, 0 errors. Scores 0 to 648 (40 non-zero), ratings Silver 2, Bronze 3, Keep trying 49 |
| Help panel opens from the start screen, closes with the button | Pass |
| App smoke test and script-order test | Pass (42 tests in total) |
| Tab hidden pauses the day | Implemented, **not tested** (the test browser cannot hide its tab) |
| Real players | **Not done.** Use the play-test kit |

## Par correction (data work)
Scripted strategies in `tools/simulate_players.py` showed that the Week 3 par scores were too low on some event days: a simple plan beat them in 115 of 612 runs, by up to 21% (Easy with guests: par 642, plan 776). The search in `tools/balance.py` now also starts from the scripted plans, and all 18 pars were recomputed. After that no strategy beats par on any level or event. Normal-day par moved by at most 9 points (Easy 800 to 809, Medium 750 to 756, Hard 640 to 636). Ratings can differ slightly from those in earlier weeks.

## Data checks
| Check | Result |
|---|---|
| A real browser CSV export (3 finished days) through `tools/clean_playlogs.py` | All 3 rows kept; CO2 and hourly totals consistent |
| Replay of the Python peak-aware Medium schedule through the live interface | Score 753 (Gold), 9.28 kWh, $1.10, identical to Python |
| Export dialog with no saved runs | Shows "No runs saved yet" and disables Download |
| Download button in the embedded page | Not confirmed: the test browser cannot show downloads. The dialog also shows the CSV as text to copy |

