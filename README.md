# Smart Energy Conservation Game

A Streamlit game where you plan a household's day under a fixed energy budget. It shows score, energy consumed, CO₂ equivalent and cost, and connects programming with sustainability education.

## Run
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Then open http://localhost:8501.

## Test
```bash
python -m pytest
```

## How to play
1. Pick a difficulty and press **Start the day**. The day plays out live.
2. Click appliances in the house (or press 1–0) to switch them on and off. The fridge starts on. Space pauses.
3. Stay under the daily budget, keep essentials (fridge, cooktop) running, and keep comfort high.
4. Run heavy appliances off-peak (22:00–06:00) to lower cost and earn timing points.
5. A random event (heatwave, guests, work-from-home, laundry day, cold snap) may change what the household wants. Turn events off on the start screen if you prefer.
6. At the end of the day you get your score, rating, personalized tips, a comparison with your last run and a short "why it matters" panel.

## Project layout
```
app.py              Streamlit shell; scores the finished day with the Python engine
frontend/           real-time game UI (index.html, styles.css, game.js, scoring.js, tips.js)
game/appliances.py  appliance data
game/engine.py      energy, CO2, cost, scoring
game/levels.py      difficulty levels and par scores
game/events.py      random day events
game/ui_config.py   constants sent to the front end
tests/              unit tests + browser/Python scoring parity test
tools/balance.py    estimates best achievable score per level
docs/               research.md, design.md, playtest.md
```

Note: after editing files in `game/`, stop Streamlit (Ctrl+C) and start it again.

See [docs/design.md](docs/design.md) for the scoring rules and [docs/research.md](docs/research.md) for data sources.
