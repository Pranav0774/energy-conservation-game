# Research notes (Week 1)

## 1. Grid CO₂ factor
The game uses **0.445 kg CO₂ per kWh**, the IEA global average carbon intensity of electricity generation in 2024 (445 g CO₂/kWh; IEA forecasts about 400 g by 2027).
- Source: [IEA, Electricity 2025 – Emissions](https://www.iea.org/reports/electricity-2025/emissions)
- Country-level values: [IEA Emissions Factors database](https://www.iea.org/data-and-statistics/data-product/emissions-factors-2025)
- US comparison: [EIA FAQ on CO₂ per kWh](https://www.eia.gov/tools/faqs/faq.php?id=74&t=11)

The value is one constant (`CO2_KG_PER_KWH` in `game/engine.py`). Replace it with the figure for your own country if the game is used locally.

## 2. Appliance power ratings
Typical ranges from consumer energy guides. The game picks a single representative value for each appliance and rounds it for readability.

| Appliance | Game value | Typical range found | Note |
|---|---|---|---|
| Refrigerator | 60 W | 100–800 kWh/year, runs 24/7 | Average draw, about 1.4 kWh/day |
| Electric cooktop | 1200 W | 1000–2000 W per burner | Simplified to one ring |
| Air conditioner (window) | 1500 W | 500–1500 W window; 3000–5000 W central | Top of the window range, the biggest load in the game |
| Ceiling fan | 60 W | 30–100 W | |
| Lights | 60 W | Whole-home LED lighting | |
| Television | 120 W | 50–200 W | |
| Computer | 100 W | 60–250 W | |
| Washing machine | 500 W | 350–500 W front-load, 500–1000 W top-load | |
| Water heater | 2000 W | 4000–5500 W tank; 1500–3000 W small or instant | Uses a smaller unit so one hour is playable |
| Iron | 1000 W | 1000–1800 W | |

Sources: [RunWatts appliance wattage chart](https://www.runwatts.com/blog/appliance-wattage-chart), [EnergySage](https://www.energysage.com/electricity/house-watts/), [Enphase](https://enphase.com/blog/homeowners/how-many-watts-do-common-home-appliances-use).

Values are game-scaled approximations. They are meant for teaching relative sizes (AC and water heating dominate), not for auditing a real home.

## 3. Time-of-use tariff
Game tariff (illustrative, not tied to one utility):

| Period | Hours | Price per kWh |
|---|---|---|
| Off-peak | 22:00–06:00 | 0.08 |
| Standard | 06:00–17:00 | 0.15 |
| Peak | 17:00–22:00 | 0.30 |

The 1:2:4 ratio (off-peak : standard : peak) is broadly typical of time-of-use plans and is chosen so shifting loads clearly pays off. Currency symbol and prices are constants in `game/engine.py`.

## 4. Open questions
- Target region (for CO₂ factor, currency and tariff).
- Whether a solar panel or battery option is wanted in Week 3.

## 5. Facts in the "Why it matters" panel
Shown at the end of each day and once during play. What was checked, and how:

| Fact | Source | Status |
|---|---|---|
| A typical passenger car emits about 393 g CO2 per mile (about 244 g per km) | [U.S. EPA, Greenhouse Gas Equivalencies Calculator](https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references) | **Read on the page (10 Nov 2026).** It gives 3.93 x 10^-4 metric tons CO2e per mile, from 8,887 g CO2 per gallon and 22.8 mpg. The gram figure is our conversion. An earlier draft said 400 g, which was rounded from search results |
| A 9 W LED bulb can replace a 60 W incandescent bulb (85% less power) | [RunWatts appliance chart](https://www.runwatts.com/blog/appliance-wattage-chart) | **Read on the page.** The 85% is arithmetic: 1 - 9/60 |
| A sleeping laptop uses about 1 to 5 W and a Wi-Fi router left on about 5 to 15 W | [RunWatts appliance chart](https://www.runwatts.com/blog/appliance-wattage-chart) | **Read on the page** |
| Many electricity plans charge less at night; moving flexible jobs there cuts the bill without cutting comfort | This project's simulations (report, section 5) | Our own result, under our invented tariff |

Removed after checking: "LEDs use at least 75% less energy and last 25 times longer" and "standby power is 5 to 10% of residential electricity use", both attributed to the U.S. Department of Energy. They came from search-result summaries. The energy.gov pages we tried (`/energysaver/led-lighting`, `/energysaver/standby-power`, `/energysaver/reduce-standby-power-and-phantom-loads`, `/energysaver/estimating-appliance-and-home-electronic-energy-use`) returned 404, so we could not confirm them. They can be added back if someone finds the current DOE page.

## 6. Emission factor status
0.445 kg CO2 per kWh is the global average for 2024 as reported in search results quoting the IEA report "Electricity 2025", section Emissions (https://www.iea.org/reports/electricity-2025/emissions). **We have not read that page ourselves:** it blocks automated access (HTTP 403 and a bot check). Open it in a normal browser and confirm the 2024 value before submitting. If it differs, change `CO2_KG_PER_KWH` in `game/engine.py`, re-run `python -m tools.simulate_players`, `python -m tools.clean_playlogs`, `python -m tools.analyze` and `python -m tools.build_report`.
