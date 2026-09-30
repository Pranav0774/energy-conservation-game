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
