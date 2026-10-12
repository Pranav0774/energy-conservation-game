# Demo script (about 5 minutes)

## Before you start (2 minutes, off camera)
- Run the game and check it opens: `python -m streamlit run app.py`.
- Use a fresh browser profile or press **Clear saved scores** on the start screen, so the demo shows "Not played yet".
- Have the browser at full screen. Close other tabs (the game pauses itself if the tab is hidden).
- Know which level you will play. **Medium** is a good default.
- If the network is unreliable, run it locally. Nothing in the game needs the internet.

## Run of show

| Time | On screen | Say |
|---|---|---|
| 0:00 | Start screen | "This is the Smart Energy Conservation Game. You run a household's electricity for one day under a fixed budget, and you are scored on energy, CO₂, cost and comfort." |
| 0:30 | Click **How to play** | Read the goal in one sentence: "Stay under the budget, keep the fridge and cooktop running, keep people comfortable." Close it. |
| 0:50 | Pick **Medium**, leave events on, **Start the day**, click **2×** | "A day takes about four minutes at normal speed. At 2× it takes two, which fits a demo." |
| 1:10 | Banner and cards (if an event is active) | "Today's event changes what the household wants. The highlighted cards show the new targets." If no event, say "Some days have events like a heatwave." |
| 1:20 | Click the cooktop around 07:00, then lights, fan and computer | "Each appliance has a real wattage. The ring shows how much of the budget I've used." |
| 1:50 | Chart | "This chart shows energy per hour by appliance. The line is my running total against the budget." |
| 2:15 | Around 17:00 the toast says peak pricing | "Peak pricing starts at 17:00 and costs four times as much as night power. I'll hold the water heater and washer for tonight." |
| 2:40 | After 22:00, switch on the washer and water heater | "Now it is off-peak, so the same energy costs a fraction. The game rewards this in the timing score." |
| 3:00 | Results screen (day ends about 2:50) | Point to the medal. "Python scores the day, using the same formulas as the browser." Show the **Score breakdown**. |
| 3:30 | **What to try next** | "These tips come from my own day. Each one says how many points or how much money the change would have gained." |
| 4:00 | **Your progress** and **Why it matters** | "Run it again and it compares with my last run. The CO₂ is shown as kilometres driven, with the source for each fact." |
| 4:30 | **Play again**, show the start screen best | "That's the loop. Aim to beat your score." |

The whole demo is about 5 minutes, which leaves time for questions. Do not leave appliances on for long stretches while talking, or the budget ring will turn red before you reach the results.

## Points to make if there is time
- **Why it is real time:** the day runs on a clock, so choices have consequences as the hours pass.
- **Engineering:** Python holds the rules and does the official scoring. A test runs the browser's scoring against Python's on random days for every level and event, and they match.
- **Fairness:** each level and event has its own par score from an optimiser, so ratings stay meaningful.

## Questions to expect
| Question | Short answer |
|---|---|
| Where do the wattages come from? | Typical ranges from consumer energy guides, rounded for the game. See `docs/research.md` |
| Which CO₂ factor do you use? | 0.445 kg per kWh, the 2024 IEA global average. It is one constant and can be changed for a country |
| Is the tariff real? | No. It is an illustrative 1:2:4 time-of-use pattern |
| Does it save my scores? | Yes, in your browser only (no accounts, no server) |
| What if the Python engine is down? | The result still shows after 8 seconds, scored in the browser, and says so |

## If something goes wrong
- **Blank page:** wait a few seconds, then refresh. Streamlit can be slow to start.
- **Old screen or a `par_score` error:** stop the server (Ctrl+C), start it again, refresh.
- **Out of time:** press **4×** and let the day finish.
