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
| Easy | 14 kWh | 800 |
| Medium | 10 kWh | 750 |
| Hard | 7 kWh | 660 |

Full-comfort use is 21.3 kWh, so every level forces trade-offs. Par is the best score a hill-climbing optimiser found (about 798 / 755 / 666).

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
- **Sidebar:** difficulty, daily budget, tariff legend, reset.
- **Main:** appliance grid, four live metrics, budget bar, warnings.
- **Results:** rating and score, breakdown table, stacked hourly chart shaded by peak/off-peak, biggest-consumer tip, savings message.

## Out of scope for Week 1 (planned)
Random events, solar option, personalised tip list, high scores (Week 3); playtesting and report (Week 4).
