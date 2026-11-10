# Submission

| # | Deliverable | File |
|---|---|---|
| 1 | Problem statement (half a page) | `1_problem_statement.pdf` |
| 2 | Raw and cleaned dataset | `2_dataset/` (`raw/`, `clean/`, `README.md` with the data dictionary) |
| 3 | Source code with README | `3_source_code/` (repo link and `source_code.zip`) |
| 4 | Final report (6 pages, graphs, inferences, sustainable solution) | `4_final_report.pdf` |
| 5 | Presentation (5 content slides plus title and thanks) | `5_presentation.pptx` |

## Before you hand it in
1. **Add the team's names.** Fill in `docs/team.json`, then run `python -m tools.build_report` and `node tools/build_deck.js`. Until then the report and slides name nobody.
2. **Confirm the emission factor.** Open https://www.iea.org/reports/electricity-2025/emissions in a browser and check the 2024 global value is 445 g CO2/kWh. The page blocks automated reading, so we could not.
3. **Make the repository readable by graders**, or send `3_source_code/source_code.zip` (the repository is private).
4. **Say what the data are.** The play-log results come from six scripted strategies, not people. If you collect real runs, add the exported CSVs to `data/raw/real_playlogs/` and re-run the pipeline below, then check the report text still matches.

## Rebuild everything
```bash
python -m tools.clean_appliance_data
python -m tools.simulate_players
python -m tools.clean_playlogs
python -m tools.analyze
python -m tools.build_report
cd tools && npm install && cd ..      # once, for the slides
node tools/build_deck.js
python -m tools.package_submission
```
The report text is written for simulated data only. After adding real runs, re-read sections 3.2, 5 and 8 and the abstract.
