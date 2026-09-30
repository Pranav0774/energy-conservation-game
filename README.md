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
1. Pick a difficulty in the sidebar.
2. Tick the hours each appliance runs. The fridge starts on.
3. Stay under the daily budget, keep essentials (fridge, cooktop) running, and keep comfort high.
4. Run heavy appliances off-peak (22:00–06:00) to lower cost and earn timing points.
5. Press **Finish the day** for your score and rating.

## Project layout
```
app.py              Streamlit UI
game/appliances.py  appliance data
game/engine.py      energy, CO2, cost, scoring
game/levels.py      difficulty levels
tests/              unit tests
docs/               research.md, design.md
```

See [docs/design.md](docs/design.md) for the scoring rules and [docs/research.md](docs/research.md) for data sources.
