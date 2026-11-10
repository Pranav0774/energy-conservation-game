# User guide

## What the game is
You run a household's electricity for one day. You have a fixed energy budget and ten appliances. Your job is to keep the household comfortable without going over the budget, and to use power when it is cheap.

## Starting
1. Run `python -m streamlit run app.py` and open the address it prints (usually http://localhost:8501).
2. Pick a level:
   - **Easy**: 14 kWh budget
   - **Medium**: 10 kWh budget
   - **Hard**: 7 kWh budget
3. Leave **Random events** on for variety, or switch it off for a plain day.
4. Press **Start the day**.

## Playing
- The clock runs from 00:00 to 24:00. At normal speed a day takes about 4 minutes. Use **2×** or **4×** to go faster.
- Click an appliance in the house, or its card under the house, to switch it on or off. Keys **1** to **0** do the same for the cards from left to right. **Space** pauses.
- The **fridge** starts on. Everything else starts off.
- Each card shows how many hours the appliance has run against how many hours the household wants.

### What the screen shows
| Item | Meaning |
|---|---|
| Energy budget ring | Energy used so far against your budget. Green, then amber at 75%, then red over budget |
| On pace | A projection of the day's total if you keep using power at the average rate so far (shown after 03:00) |
| Power now | Combined power of everything switched on, in kW |
| CO₂ equivalent | Energy used × 0.445 kg per kWh |
| Cost so far | Energy priced by the hour (see the price badge) |
| Comfort | How much of what the household wants you have provided |
| Must run today | Fridge (24 h) and cooktop (2 h). Fall short and you lose points |
| Chart | Energy per hour, stacked by appliance, with a line for the running total against your budget |

### Prices
| Time | Price per kWh |
|---|---|
| 22:00–06:00 (off-peak) | 0.08 |
| 06:00–17:00 (standard) | 0.15 |
| 17:00–22:00 (peak) | 0.30 |

### Random events
An event changes how long the household wants certain appliances today. The banner on the house and highlighted cards show what changed.

| Event | What the household wants |
|---|---|
| Heatwave | Air conditioner 11 h, fan 14 h |
| Guests visiting | Cooktop 3 h, TV 7 h, lights 9 h |
| Work-from-home day | Computer 9 h, lights 8 h |
| Laundry day | Washing machine 2 h, iron 2 h |
| Cold snap | Water heater 3 h |

## Scoring
Score = 300 + comfort (up to 500) + budget (−600 to +200) + timing (−100 to +100) − 200 for each essential appliance that fell short. The score never goes below 0.

- **Comfort:** the share of wanted hours you provided for the non-essential appliances.
- **Budget:** a bonus for finishing under budget, a penalty that grows quickly for going over.
- **Timing:** a bonus when more of your energy is used off-peak than at peak.

Your **rating** compares your score with the best score a good plan reaches at that level and event: Gold 90% or more, Silver 78% or more, Bronze 65% or more.

## After the day
- **Score breakdown:** where your points came from.
- **What to try next:** tips based on your own day, with the points or money a change would have gained.
- **Your progress:** change in energy, score and cost since your last run on this level. Scores are saved in your browser only.
- **Why it matters:** your CO₂ as kilometres driven, and a short sourced fact.

## Tips for a high score
1. Keep the fridge on all day and give the cooktop its two hours.
2. The air conditioner and water heater use the most energy. Decide on them first.
3. Do laundry, water heating and ironing between 22:00 and 06:00.
4. Avoid the 17:00–22:00 peak for anything the household can do without.
5. Finish a little under budget rather than far under. Comfort earns more points than leftover energy.

## Saving your runs as data
On the start screen, **Export my runs (CSV)** shows every run saved in this browser as a CSV. It is anonymous: a random id and your game results, no name or email. Use **Download CSV**, or select the text and copy it into a file ending in `.csv`. If you are helping with the project, send the file to the team. **Clear saved scores** deletes the saved runs and the random id.

## Troubleshooting
| Problem | Fix |
|---|---|
| Page shows an old version or a Python error about `par_score` | Press Ctrl+C in the terminal, start the game again, then refresh. Streamlit does not always reload files in `game/` |
| `streamlit` is not recognised | Use `python -m streamlit run app.py` |
| Result says "Scored in your browser" | The Python engine did not answer in 8 seconds. The score is still correct (both use the same formulas) |
| Scores or bests are missing | Your browser blocks local storage, or you cleared site data. The game still works, it just cannot remember |
| Port 8501 is busy | Streamlit uses the next free port. Open the address it prints |
