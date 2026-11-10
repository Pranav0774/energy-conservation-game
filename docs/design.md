# Game design document (Week 1)

## Goal
Teach energy conservation. The player plans one household day (24 hours) under a fixed energy budget, choosing when each appliance runs, and is scored on energy consumed, CO₂ equivalent, cost and comfort.

## Core loop (real time)
1. Choose a difficulty (sets the daily budget) and press **Start the day**.
2. One game day (24 h) plays out live in about 4 minutes at 1× (10 s per game hour; 2× and 4× speeds; pause with Space). Change `SEC_PER_HOUR` in `frontend/game.js` to adjust.
3. Click an appliance in the animated house, or its card below, to switch it on or off. The sky, lighting and tariff change with the time of day.
4. Live feedback: energy (kWh) against the budget ring, power now (kW), CO₂ (kg), cost, comfort (%), a live hourly chart and toast alerts (peak pricing starts, 80% of budget, over budget).
5. At 24:00 the results screen shows score, rating, breakdown and tips.

## Architecture
- `frontend/` is a small web app (HTML, CSS, JavaScript, SVG, canvas) shown inside Streamlit as a custom component. It runs the simulation in the browser.
- `app.py` sends it the appliance table, levels, tariff and scoring constants from Python (`game/ui_config.py`), so there is one source of truth.
- When the day ends the browser sends the schedule back and `game/engine.py` calculates the official score. The browser also calculates it live with the same formulas (checked to match).

## Appliances
Ten appliances (see `game/appliances.py`). Each has wattage, a wanted number of hours (`target_hours`) and a comfort weight. **Essential** appliances (refrigerator 24 h, cooktop 2 h) must reach their target hours or the player is penalised.

## Levels
| Level | Budget | Par score |
|---|---|---|
| Easy | 14 kWh | 809 |
| Medium | 10 kWh | 756 |
| Hard | 7 kWh | 636 |

Full-comfort use is 21.3 kWh, so every level forces trade-offs. Par is about the best score found by a local search that starts from scripted strategies as well as from an empty day (809 / 756 / 636 on a normal day, with a separate par for each event); see [playtest.md](playtest.md) and `python -m tools.balance`.

## Calculations (`game/engine.py`)
- Energy: sum over appliances and hours of watts / 1000.
- CO₂: kWh × 0.445 kg/kWh.
- Cost: per-hour kWh × tariff for that hour (off-peak 0.08, standard 0.15, peak 0.30).
- Comfort: weighted share of wanted hours met, over non-essential appliances only.

## Score
`score = 300 + comfort_pts + budget_pts + timing_pts − essential_penalty`, floored at 0.

| Part | Formula |
|---|---|
| Comfort | 500 × comfort ratio |
| Budget, under budget | 200 × (budget − used) / budget |
| Budget, over budget | −600 × (used − budget) / budget |
| Timing | 100 × (off-peak share − peak share of energy) |
| Essentials | −200 per essential appliance under target |

**Rating** is relative to the level's par: Gold ≥ 90%, Silver ≥ 78%, Bronze ≥ 65%, otherwise "Keep trying".

Design checks (Medium): running nothing scores 100, essentials only 428, full comfort 202, so neither extreme wins. A balanced plan scores 500–755.

## Screens
- **Start:** difficulty cards (with your best score), random-events switch, Start button.
- **Play:** header with the clock, pause and speed; animated house; budget ring, power, CO₂, cost, comfort and essentials; live hourly chart; appliance cards.
- **Results:** medal and score, four metric tiles, score breakdown, personalized tips, progress against the last run, "why it matters".

## Week 3 additions
### Random events
At the start of a day there is an 80% chance (if "Random events" is on) of one event. An event changes what the household *wants* (target hours), not the rules or the budget. A banner and highlighted appliance cards show what changed.

| Event | Wanted hours today |
|---|---|
| Heatwave | Air conditioner 11 h, ceiling fan 14 h |
| Guests visiting | Cooktop 3 h, TV 7 h, lights 9 h |
| Work-from-home day | Computer 9 h, lights 8 h |
| Laundry day | Washing machine 2 h, iron 2 h |
| Cold snap | Water heater 3 h |

Python applies the same changes when scoring (`game/events.py`). Par is computed per level and event (`PAR_BY_EVENT` in `game/levels.py`, from `python -m tools.balance`) so ratings stay fair.

### Personalized tips (`frontend/tips.js`)
Up to four tips from the player's actual day. "What if" numbers re-score a modified copy of the day, so they are exact: running the biggest appliance one hour less, shifting a peak-hour appliance to night, lights on in daylight, comfort left unused while under budget, essentials missed.

### Progress
Each finished run is saved in the browser (`localStorage`, last 20 runs per level). The result screen compares energy, score and cost with the previous run on that level and flags a new personal best. The start screen shows each level's best. If the browser blocks storage, progress is kept only until the page is closed.

### Learning panel
CO₂ shown as distance driven and as a yearly total, plus one fact (sources in [research.md](research.md)). A "Did you know?" message also appears mid-morning during play.

## Data export and analysis
Each finished day is saved with its hours per appliance and energy per hour (last 200 runs per level, in the browser). **Export my runs (CSV)** on the start screen turns them into the play-log layout described in [../data/README.md](../data/README.md). `tools/simulate_players.py` makes simulated days with the same layout, `tools/clean_playlogs.py` cleans both, and `tools/analyze.py` draws the report's graphs.

## Still to do (Week 4)
Play-testing with real players, polish, project report and demo. See [playtest.md](playtest.md).
