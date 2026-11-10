# Data

Two datasets, each with a raw and a cleaned version. Nothing here comes from people yet: the play logs are simulated (see below).

```
data/
  raw/
    appliance_power_sources.csv      figures copied from three web pages
    playlogs/simulated_playlogs.csv  612 days played by scripted strategies
    real_playlogs/                   put browser exports here (empty for now)
  clean/
    appliance_power_clean.csv        one row per game appliance, compared with the sources
    appliance_sources_long.csv       every raw row, units converted, mapped to a game appliance
    appliance_cleaning_log.csv       what each cleaning step did
    playlogs_clean.csv               one row per valid finished day
    playlogs_cleaning_log.csv        rows removed by each rule
    summary_stats.json               every number quoted in the report
```

Rebuild everything with:
```bash
python -m tools.clean_appliance_data
python -m tools.simulate_players
python -m tools.clean_playlogs
python -m tools.analyze
python -m tools.build_report
```

## 1. Appliance power sources

**Raw** (`appliance_power_sources.csv`, 33 rows). Figures read on three pages on 10 November 2026: EnergySage (page dated 5 Aug 2024), RunWatts (29 Apr 2026) and Enphase (18 Nov 2025). Only numbers the page states are included. A page that gives no figure for an appliance has no row. Notes are our own short wording.

| Column | Meaning |
|---|---|
| row_id, source_id, source_name, url, page_updated, retrieved_on | where the row came from |
| appliance_as_named | the appliance as the page names it |
| low, high | the range as printed (equal if the page gives one number) |
| unit | `watts` or `kWh/year` |
| basis | `rated_running` (power while on), `average` or `annual` (long-run average), `idle`, `standby` |
| note | short note |

**Cleaning** (`python -m tools.clean_appliance_data`): drop duplicate rows; drop non-positive or reversed ranges; convert `kWh/year` to average watts (x 1000 / 8760); map each row to a game appliance; compare with the game's value on the same basis (the fridge as a 24-hour average, everything else as power while running). Result: 0 duplicates, 0 invalid ranges, 1 conversion, 7 rows not used by the game.

**Clean** (`appliance_power_clean.csv`): `game_key`, `game_watts`, `source_min_w`, `source_max_w`, `source_median_mid_w`, `n_sources`, `game_vs_range` (`within`, `below`, `above`) and a `design_note`. 7 of 10 game values are inside the published range. The cooktop (1200 W), water heater (2000 W) and iron (1000 W) are below.

Known issue in the raw data: two sources disagree on the fridge (annual energy implies 46 to 91 W on average; one page gives 150 to 250 W as average use). Both rows are kept.

## 2. Play logs

**One row per finished day**, 51 columns, the same layout in the browser export and in the simulated file (`game/datalog.py`, `frontend/exporter.js`, checked by a test).

| Columns | Meaning |
|---|---|
| source | `browser_player` (real export) or `simulated_bot` |
| player_id, run_id, timestamp_utc | anonymous random ids; time of the run (blank for simulated) |
| level, event | Easy, Medium or Hard; `none` or one of heatwave, guests, wfh, laundry, coldsnap |
| budget_kwh, par | the day's budget and par score |
| score, rating | official score (Python engine) and Gold, Silver, Bronze or Keep trying |
| energy_kwh, co2_kg, cost, comfort | day totals; comfort is 0 to 1 |
| offpeak_share, peak_share | share of the day's energy used off-peak and at peak |
| missing_essentials | essential appliances that fell short of their hours |
| hrs_fridge ... hrs_iron (10) | hours each appliance ran |
| kwh_h00 ... kwh_h23 (24) | energy used in each hour |
| strategy (simulated file only) | which scripted strategy played the day |

**Simulated data are not people.** `python -m tools.simulate_players` runs six scripted strategies (full comfort, casual, budget cutter, peak-aware, optimizer, essentials only) on all three levels and all six event settings, eight seeds each (one for optimizer and essentials only): 612 days. They show how habits score under the game's rules. They do not show how people play.

**Adding real data.** On the start screen choose **Export my runs (CSV)**, copy or download the file, save it in `data/raw/real_playlogs/`, and re-run the commands above. The exports are anonymous: a random id and game results only.

**Cleaning rules** (`python -m tools.clean_playlogs`, counts in `playlogs_cleaning_log.csv`): drop rows with a missing or non-numeric required field; duplicate `run_id`; unknown level or event; values outside the possible range (energy above everything on all day, comfort or shares outside 0 to 1, hours outside 0 to 24, score above 1100); rows whose CO2 differs from energy x 0.445 by more than 0.01, or whose hourly energy does not add up to the total. The simulated file loses no rows because it is generated clean. The rules are tested with deliberately broken rows, and a real browser export has been through them.

**Derived columns added by cleaning:** `is_simulated`, `over_budget`, `budget_used_pct`, `raw_file`, and `strategy` set to `human` for browser exports.

## Licence and sources
The appliance figures are facts read from the pages listed in the raw file, kept with their URLs for attribution. Check each site's terms before reusing the table beyond this coursework.
