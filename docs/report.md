# Smart Energy Conservation Game: project report

Project 73. A small game in Python and web technology that connects programming with sustainability education.

## 1. Objective
Build a game where the player is given a fixed daily energy budget and must operate household appliances while keeping energy use low. The brief asks the game to include a score, energy consumed, CO₂ equivalent and cost.

| Brief requirement | How the game meets it |
|---|---|
| Fixed daily energy budget | Three levels: 14, 10 and 7 kWh. A ring shows the budget used and turns red when it is exceeded |
| Operate appliances while minimising energy | Ten appliances switched on and off in real time during a simulated day |
| Score | A score from 0 (theoretical maximum 1,100; good plans reach roughly 600 to 800) with a Gold, Silver or Bronze rating and a breakdown |
| Energy consumed | Shown live in kWh and per hour on a chart |
| CO₂ equivalent | Energy × 0.445 kg/kWh, shown live and as kilometres driven at the end |
| Cost | Hourly time-of-use prices: 0.08, 0.15 and 0.30 per kWh |
| Sustainability education | Tips from the player's own day, a "why it matters" panel with sourced facts, and random events that show how demand changes |

## 2. How the game works
The player runs one household day (00:00 to 24:00) in real time. One game hour lasts 10 seconds at normal speed, so a day takes 4 minutes, and 2× and 4× speeds are available. Clicking an appliance switches it on or off. Energy is counted each game minute.

Each appliance has a power rating, a number of hours the household wants it, and a comfort weight. The fridge (24 h) and cooktop (2 h) are **essential** and must reach their hours. A random event, such as a heatwave, can change what the household wants that day.

| Appliance | Power | Wanted hours | Comfort weight |
|---|---|---|---|
| Refrigerator (essential) | 60 W | 24 | 2.0 |
| Electric cooktop (essential) | 1200 W | 2 | 2.5 |
| Air conditioner | 1500 W | 8 | 3.0 |
| Ceiling fan | 60 W | 10 | 1.0 |
| Lights | 60 W | 6 | 2.0 |
| Television | 120 W | 4 | 1.5 |
| Computer | 100 W | 5 | 1.5 |
| Washing machine | 500 W | 1 | 1.5 |
| Water heater | 2000 W | 1 | 2.0 |
| Iron | 1000 W | 1 | 1.0 |

Running every appliance for its wanted hours needs about 21 kWh, so even Easy (14 kWh) forces trade-offs.

## 3. Scoring
```
energy_kWh   = sum over appliances and hours of (watts / 1000) × fraction of the hour it ran
CO2_kg       = energy_kWh × 0.445
cost         = sum over hours of (kWh in that hour) × price for that hour
comfort      = weighted average over non-essential appliances of min(hours run / hours wanted, 1)

score = 300
      + 500 × comfort
      + budget points      (under budget: 200 × (budget − used) / budget; over: −600 × (used − budget) / budget)
      + 100 × (off-peak share of energy − peak share of energy)
      − 200 × (number of essential appliances that fell short)
score is never below 0
```
Essentials do not count toward comfort. This stops a player from earning comfort points by running only the fridge and cooktop.

**Ratings** compare the score with a *par*, roughly the best score a good plan reaches at that level and event: Gold at 90% of par or more, Silver at 78%, Bronze at 65%.

**Par scores** come from `tools/balance.py`, which searches for the best day it can find by hill-climbing over hour toggles and then partial hours. Results (about the best scores found, normal day):

| Level | Budget | Par | Best plan found |
|---|---|---|---|
| Easy | 14 kWh | 800 | about 9.7 kWh, 78% comfort |
| Medium | 10 kWh | 750 | about 9.3 kWh, 78% comfort |
| Hard | 7 kWh | 640 | about 7.0 kWh, 60% comfort |

Events have their own par per level (stored in `PAR_BY_EVENT`). The search is random, so these are accurate to about ±2%.

Sanity checks on the scoring (Medium): running nothing scores 100, essentials only about 430, everything at full comfort about 200. A balanced day scores 500 to 750. No extreme strategy wins.

## 4. Design and architecture
```
Browser (frontend/)                      Python (game/, app.py)
  game.js     simulation, house, HUD       engine.py     official energy/CO2/cost/score
  scoring.js  scoring formulas             events.py     random events
  tips.js     personalised tips            levels.py     budgets and par scores
  styles.css  layout and animation         appliances.py appliance data
  index.html  structure                    ui_config.py  sends the constants to the browser
```
- Streamlit hosts the game as a custom component, so it starts with one command.
- Python sends the appliance table, tariff, events, levels and scoring constants to the browser, so there is one source of truth.
- The browser runs the live game and calculates the score as it goes. When the day ends it sends the schedule to Python, which calculates the official score. The result screen shows the Python score. If Python does not answer within 8 seconds, the browser score is shown and labelled.
- Progress (last 20 runs per level) is stored in the browser with `localStorage`. There are no accounts and no server database.

Graphics are hand-written SVG and CSS (animated house, sky that changes with the time, glows and airflow on appliances) plus a canvas chart. There are no image files or external libraries, so it works offline.

## 5. Sustainability content
- **Grid emissions:** 0.445 kg CO₂ per kWh, the IEA global average for 2024.
- **Learning panel:** the day's CO₂ is shown as distance driven, using the EPA estimate of about 400 g per mile for a typical car, and as a yearly total. One sourced fact is shown each time (LED lighting, standby power, car emissions, off-peak use).
- **Tips:** each tip re-scores a changed copy of the player's own day, so the numbers are exact. For example, in one test run the game said that running the air conditioner one hour less would have saved 1.5 kWh and gained about 31 points.
- **Events:** heatwaves, guests, work-from-home, laundry day and a cold snap show how everyday conditions change demand.
- Sources and their check status are in [research.md](research.md).

## 6. Testing
| What | How | Result |
|---|---|---|
| Energy, CO₂, cost, comfort, essentials, ratings | 42 automated tests (`python -m pytest`) | All pass |
| Browser scoring equals Python scoring | `frontend/scoring.js` run in Node against `game/engine.py`, 60 random days for every level and event combination | Match |
| Personalised tips | Well-formed on 120 random days and specific on hand-made days | Pass |
| App loads | Streamlit `AppTest` smoke test | Pass |
| Whole game through the real UI | Scripted browser run of 54 full days across all levels and events, each confirmed by the Python engine | 0 mismatches, 0 errors, scores from 0 to 648 |
| Game flow | Reset between days, pause, number-key toggles, help panel, saved progress across a page reload, events undone after a day | Pass |
| Layouts | Desktop and phone-sized panes | Checked in a Chromium pane |

Versions used: Python 3.14, Streamlit 1.64, Node 24 (Node is only needed for the parity tests; they are skipped if it is missing).

## 7. Player feedback
*To be completed after play-testing with real players. Use [playtest_kit.md](playtest_kit.md) and paste the summary table here.*

| Player | Level | Score | Main comment | Change made |
|---|---|---|---|---|
| | | | | |

## 8. Limitations
- **No real-player testing is recorded yet.** Whether the pace (4 minutes per day), the wording and the difficulty feel right is untested.
- **Devices:** checked in a desktop browser pane and at phone width, not on real phones or on a slow college computer.
- **Data are illustrative.** Appliance powers are rounded typical values, and the tariff is an invented 1:2:4 pattern, not a real utility's.
- **One CO₂ factor** is used for every user. Real grids differ widely by country and time of day.
- **Standby-power fact** came from a secondary source citing the U.S. Department of Energy and should be checked against the primary page before submission.
- **Par scores** are estimated by a random search and are only approximate.
- **Progress is per browser.** It is not shared between devices and is lost if site data is cleared.
- **Rating depends on the optimiser's best plan,** so a clever human plan could beat par.

## 9. Future work
- Solar panel and battery options, with a cloudy-day event.
- Region presets for tariff and CO₂ factor.
- A daily challenge with a fixed event and a shared leaderboard.
- Sound effects and an accessibility pass (screen-reader labels for the house, a high-contrast theme).
- Use hourly emission data so cleaner hours of the day are worth more.

## 10. Running and deploying
- Run locally: `python -m pip install -r requirements.txt` then `python -m streamlit run app.py`.
- Run tests: `python -m pip install -r requirements-dev.txt` then `python -m pytest`.
- Deploy: the project is ready for Streamlit Community Cloud (main file `app.py`, dependencies in `requirements.txt`). Deployment has not been done or tested.

## 11. Team
*Fill in each member's name and contribution before submitting.*

| Name | Contribution |
|---|---|
| | |
