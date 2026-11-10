"""Build the submission PDFs (problem statement and final report) from the analysed data.

Every number in the text is read from data/clean/summary_stats.json or computed here, so re-running
this after new data arrives updates the report. Team names come from docs/team.json (omitted if empty).

Run: python -m tools.analyze && python -m tools.build_report
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from game.appliances import APPLIANCES
from game.events import EVENTS

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "docs" / "figures"
IMG = ROOT / "docs" / "images"
OUT = ROOT / "submission"
S = json.loads((ROOT / "data" / "clean" / "summary_stats.json").read_text(encoding="utf-8"))
REPO = "https://github.com/Pranav0774/energy-conservation-game"

# ---------- fonts and styles ----------
_fonts = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
for name, file in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
                   ("DV-BI", "DejaVuSans-BoldOblique.ttf"), ("DVM", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(_fonts / file)))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
INK, MUTED, ACCENT, LINE = colors.HexColor("#1f2933"), colors.HexColor("#5b6770"), colors.HexColor("#0b6e4f"), colors.HexColor("#c9d1d6")
base = ParagraphStyle("base", fontName="DV", fontSize=9, leading=12.6, textColor=INK, alignment=TA_LEFT, spaceAfter=5)
ST = {
    "body": base,
    "title": ParagraphStyle("title", parent=base, fontName="DV-B", fontSize=19, leading=23, spaceAfter=3),
    "sub": ParagraphStyle("sub", parent=base, fontSize=10, leading=13, textColor=MUTED, spaceAfter=8),
    "h1": ParagraphStyle("h1", parent=base, fontName="DV-B", fontSize=12.5, leading=16, spaceBefore=9, spaceAfter=4, textColor=ACCENT, keepWithNext=1),
    "h2": ParagraphStyle("h2", parent=base, fontName="DV-B", fontSize=10, leading=13, spaceBefore=5, spaceAfter=2, keepWithNext=1),
    "cap": ParagraphStyle("cap", parent=base, fontSize=7.8, leading=10.2, textColor=MUTED, spaceAfter=7),
    "cell": ParagraphStyle("cell", parent=base, fontSize=7.8, leading=10, spaceAfter=0),
    "cellb": ParagraphStyle("cellb", parent=base, fontName="DV-B", fontSize=7.8, leading=10, spaceAfter=0),
    "code": ParagraphStyle("code", parent=base, fontName="DVM", fontSize=7.8, leading=10.5, backColor=colors.HexColor("#f2f5f7"), borderPadding=(4, 5, 4, 5), spaceBefore=3, spaceAfter=8),
    "bul": ParagraphStyle("bul", parent=base, leftIndent=12, bulletIndent=2, spaceAfter=2.5),
}


def fx(text: str) -> str:
    """CO2 subscript (DejaVu has the glyph, but tags are the safe route) and XML-safe ampersands."""
    text = re.sub(r"&(?!amp;|lt;|gt;|#)", "&amp;", text)
    return text.replace("CO2", "CO<sub>2</sub>")


def P(text, style="body"):
    return Paragraph(fx(text), ST[style])


def bullets(items):
    return [Paragraph(fx(t), ST["bul"], bulletText="•") for t in items]


def table(rows, widths, header=True, align_right=()):
    data = [[Paragraph(fx(str(c)), ST["cellb" if (header and i == 0) else "cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
             ("TOPPADDING", (0, 0), (-1, -1), 2.2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
             ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f1ed")), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT)]
    t.setStyle(TableStyle(style))
    return t


def fig(path, width_cm, caption):
    from PIL import Image as PI

    w, h = PI.open(path).size
    return KeepTogether([Image(str(path), width=width_cm * cm, height=width_cm * cm * h / w), P(caption, "cap")])


def two_images(a, b, caption, width_cm=8.4):
    from PIL import Image as PI

    def im(p):
        w, h = PI.open(p).size
        return Image(str(p), width=width_cm * cm, height=width_cm * cm * h / w)

    t = Table([[im(a), im(b)]], colWidths=[width_cm * cm + 0.2 * cm] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    return KeepTogether([t, P(caption, "cap")])


def footer(title):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.9 * cm, 1.1 * cm, title)
        canvas.drawRightString(A4[0] - 1.9 * cm, 1.1 * cm, f"Page {doc.page}")
        canvas.restoreState()
    return draw


def team_names() -> list[dict]:
    f = ROOT / "docs" / "team.json"
    if not f.exists():
        return []
    return [m for m in json.loads(f.read_text(encoding="utf-8")).get("team", []) if m.get("name", "").strip()]


def join_and(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def pct(x, d=0):
    return f"{x:.{d}f}%"


# ---------- numbers used in the text ----------
M = S["strategy_medium"]
FULL, CUT, PEAK, OPT = M["full_comfort"], M["budget_cutter"], M["peak_aware"], M["optimizer"]
ENERGY_CUT_PCT = 100 * (1 - CUT["energy_kwh"] / FULL["energy_kwh"])
COST_SAVED_MED = 100 * (1 - PEAK["cost"] / CUT["cost"])
SH = S["energy_share_pct"]
BIG4 = SH["ac"] + SH["cooktop"] + SH["heater"] + SH["iron"]
PVC = S["peak_vs_cutter"]
SENS = S["sensitivity"]
EV = S["event_energy_change_pct"]
D = S["dataset"]
OB = S["over_budget_pct_by_strategy"]
N_TESTS = None


def count_tests() -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], capture_output=True, text=True, cwd=ROOT).stdout
    m = re.search(r"(\d+) tests? collected", out)
    return int(m.group(1)) if m else 0


def normal_day_pair_saving() -> float:
    d = pd.read_csv(ROOT / "data" / "clean" / "playlogs_clean.csv")
    d = d[(d["event"] == "none") & d["is_simulated"]].assign(seed=lambda x: x["run_id"].str.rsplit("-", n=1).str[-1])
    a = d[d["strategy"] == "budget_cutter"].set_index(["level", "seed"])["cost"]
    b = d[d["strategy"] == "peak_aware"].set_index(["level", "seed"])["cost"]
    return float((1 - b / a).mean() * 100)


# ---------- problem statement (about half a page) ----------
def build_problem_statement(path: Path):
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=1.8 * cm,
                            title="Problem statement: Smart Energy Conservation Game", author="Project team")
    story = [
        P("Problem statement", "title"),
        P("Project 73: Smart Energy Conservation Game", "sub"),
        P("The problem", "h1"),
        P("A household usually meets its electricity use once a month, as a bill. By then the choices behind it are hours or weeks old: how long the "
          "air conditioner ran, whether the washing was done at noon or at midnight, whether the television stayed on. Nobody gets a chance to see "
          "what a single choice cost in energy, carbon or money while there is still time to change it. It is also hard to tell which "
          "appliances matter most without measuring them."),
        P("What we set out to do", "h1"),
        P("Build a small game, in Python and web technology, that gives the player a fixed daily energy budget and asks them to run a household's "
          "appliances through one simulated day while keeping consumption low. The game must show the score, the energy consumed, the CO2 equivalent "
          "and the cost as the day unfolds. It should teach by letting the player make mistakes cheaply: go over the budget, see which appliance caused it, "
          "and try again."),
        P("Questions we want the data to answer", "h1"),
    ] + bullets([
        "Which appliances account for most of a household's daily energy, and how well do the game's power ratings match published figures?",
        "How much energy must a household give up to stay within a budget, and how much comfort does it lose in return?",
        "When energy use cannot be reduced further, how much does moving it to cheaper hours save?",
        "Do the answers hold if the game's own numbers are somewhat wrong?",
    ]) + [
        P("What we deliver", "h1"),
        P(f"A playable game with three difficulty levels and five random events; a raw and cleaned dataset (published appliance power figures and play logs); "
          f"the source code at {REPO}; a final report with graphs, inferences and a sustainable-use proposal; and a short presentation."),
    ]
    doc.build(story, onFirstPage=footer("Smart Energy Conservation Game: problem statement"), onLaterPages=footer("Smart Energy Conservation Game: problem statement"))


# ---------- final report ----------
def build_report(path: Path):
    n_tests = count_tests()
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.9 * cm, rightMargin=1.9 * cm, topMargin=1.7 * cm, bottomMargin=1.8 * cm,
                            title="Smart Energy Conservation Game: final report", author="Project team")
    W = A4[0] - 3.8 * cm
    s: list = []
    below = S["appliances"]["below"]
    names = {a.key: a.name.lower() for a in APPLIANCES}

    s += [P("Smart Energy Conservation Game", "title"),
          P("Project 73 final report. Planning a household's electricity day against a fixed budget, in real time.", "sub")]
    team = team_names()
    if team:
        s.append(P("; ".join(f"{m['name']}" + (f" ({m['role']})" if m.get("role") else "") for m in team), "sub"))

    s += [P("Abstract", "h1"),
          P(f"We built a browser game in which a player runs one household day against a fixed energy budget. Ten appliances are switched on and off in real time while "
            f"the screen shows energy, CO2 and cost. This report covers the game, the data behind it and what that data shows. We collected appliance power figures "
            f"from {D['raw_appliance_sources']} published sources ({D['raw_appliance_rows']} rows) and compared them with the game's values: {S['appliances']['within']} of {S['appliances']['total']} fall "
            f"inside the published ranges. No human play data exists yet, so the analysis uses {S['n_simulated']} days generated by six scripted household strategies. "
            f"On a Medium day (10 kWh budget), meeting the budget cut energy by {ENERGY_CUT_PCT:.0f}% against a full-comfort day and kept {CUT['comfort']*100:.0f}% of the comfort the household wanted. "
            f"Moving flexible use out of the evening peak cut cost by a further {pct(PVC['cost_saved_pct_mean'])} (95% interval {PVC['ci95'][0]:.0f} to {PVC['ci95'][1]:.0f}) "
            f"at identical energy and comfort. All of this rests on simulated players.")]

    # 1 problem
    s += [P("1. Problem and objectives", "h1"),
          P("A household meets its electricity use as a monthly bill, long after the choices behind it. Nobody sees what one hour of air conditioning cost while there is still "
            "time to act, and few people know which appliances matter. The brief asks for a game with a fixed daily energy budget, appliances to operate, and a visible score, "
            "energy consumed, CO2 equivalent and cost. Our objectives were to meet that brief, to ground the appliance numbers in published data, to find out from the data "
            "which habits save the most, and to describe how the game could be used for sustainability teaching.")]

    # 2 design
    s += [P("2. The game", "h1"),
          P("A day runs from 00:00 to 24:00 at ten real seconds per game hour (four minutes; 2× and 4× speeds exist). The player clicks appliances in an animated cutaway house to "
            "switch them on or off. The fridge starts on. Live panels show a budget ring, power now, CO2, cost, comfort and an hourly chart. At 24:00 the player gets a score, a medal, "
            "a breakdown, tips built from their own day, and a comparison with their previous run on that level. CO2 is also shown as kilometres driven, using the EPA figure of about 393 g per mile for a typical passenger car [2]."),
          two_images(IMG / "game_play.png", IMG / "game_results.png",
                     "Figure 1. Left: a Medium heatwave day at 19:50, over budget (red ring) with peak pricing active. Right: the results screen for a day that finished under budget.")]

    rows = [["Appliance", "Power (W)", "Hours wanted", "Comfort weight", "Essential"]]
    for a in APPLIANCES:
        rows.append([a.name, a.watts, a.target_hours, a.comfort_weight, "yes" if a.essential else ""])
    s += [P("Levels have budgets of 14 kWh (Easy), 10 kWh (Medium) and 7 kWh (Hard). Five random events change what the household wants that day: a heatwave (air conditioner 11 h, "
            "fan 14 h), guests (cooktop 3 h, television 7 h, lights 9 h), a work-from-home day, a laundry day and a cold snap (water heater 3 h). Prices depend on the hour: 0.08 per kWh "
            "off-peak (22:00 to 06:00), 0.15 standard, 0.30 at peak (17:00 to 22:00). CO2 is energy times 0.445 kg/kWh, the 2024 IEA global average [1]."),
          KeepTogether([table(rows, [5.2 * cm, 2.4 * cm, 3 * cm, 3.2 * cm, 2.4 * cm]),
                        P("Table 1. The ten game appliances. Running all of them for their wanted hours takes about "
                          f"{FULL['energy_kwh']:.1f} kWh, so every level forces trade-offs.", "cap")]),
          P("The score is calculated as follows and never goes below zero.", "body"),
          P("score = 300 + 500 × comfort + budget + 100 × (off-peak share − peak share) − 200 × (essentials missed)<br/>"
            "budget = 200 × (B − used)/B when under budget, and −600 × (used − B)/B when over, with B the daily budget", "code"),
          P("Comfort is the weighted share of wanted hours provided, counted over the non-essential appliances only, so running just the fridge and cooktop earns nothing. "
            "The rating (Gold, Silver, Bronze) compares the score with the best score a good plan reaches for that level and event, called par: Gold at 90% of par or more, "
            "Silver at 78%, Bronze at 65%."),
          P("The front end (HTML, CSS, JavaScript, SVG and canvas) runs the live simulation inside a Streamlit page. Python holds the rules and calculates the official score when the day ends. "
            "The browser calculates the same score live; a test compares the two on random days for every level and event.")]

    # 3 data
    ds = D["appliance_log"]
    s += [P("3. Data: collection and cleaning", "h1"), P("3.1 Appliance power figures", "h2"),
          P(f"Raw table: {D['raw_appliance_rows']} rows copied from three pages (EnergySage, RunWatts and Enphase), each with its URL, page date, the appliance name as printed, the low and high value and "
            f"the unit [3][4][5]. We also tried four U.S. Department of Energy pages; all returned errors, so nothing was taken from them. Cleaning removed "
            f"{ds['duplicate rows removed']} duplicates and {ds['rows with non-positive or reversed range removed']} impossible ranges, converted {ds['annual kWh figures converted to average watts']} yearly "
            f"energy figure (a fridge's 400 to 800 kWh a year) to average watts, and set aside {ds['rows not used by the game (standby, idle, other AC types)']} rows the game does not use (standby, idle, other air-conditioner types). "
            "Each remaining row was mapped to a game appliance and compared with the game's value on the same basis (a fridge as a 24-hour average, everything else as power while running)."),
          fig(FIG / "fig1_appliance_sources.png", 14.2,
              f"Figure 2. Game values against published ranges. {S['appliances']['within']} of {S['appliances']['total']} are inside. The cooktop (one burner against whole-oven figures), water heater (a small unit "
              "so one hour is playable) and iron (1,000 W against 1,100 to 1,800 W) are below, and the first two are deliberate simplifications."),
          P("The sources disagree with each other in places. For the fridge, the yearly energy figure implies 46 to 91 W on average, while another page gives 150 to 250 W as typical average use. "
            "The game's 60 W sits in the first range. We kept the disagreement in the table and did not pick a winner.")]

    s += [P("3.2 Play logs", "h2"),
          P(f"Each finished day is one row of {D['playlog_columns']-5} columns: player id, level, event, budget, par, score, rating, energy, CO2, cost, comfort, off-peak and peak share, "
            f"missing essentials, hours per appliance and energy per hour. The game can export a player's saved runs as an anonymous CSV (random id, no names), and a cleaning script "
            f"merges any such files with the simulated ones. Its rules drop incomplete rows, duplicate run ids, unknown levels or events, impossible values and rows whose CO2 or hourly "
            f"energy does not add up to the total. The merge of {D['playlog_log']['raw rows read']} rows removed none, because simulated rows are generated clean; the rules are exercised by "
            f"tests with deliberately broken rows and by a real browser export that passed through them."),
          P(f"No human play data has been collected yet ({S['n_human']} runs). Every result below is from {S['n_simulated']} simulated days, and the scripted players are our own invention. "
            "They are a controlled way to see how different habits score under the game's rules. They say nothing about how people actually play.")]

    strat = [["Strategy", "What it does", "Runs"],
             ["Full comfort", "Every appliance for its wanted hours at natural times; ignores the budget", S["by_strategy_runs"]["full_comfort"]],
             ["Casual", "Natural times, but a random 30% to 110% of the wanted hours", S["by_strategy_runs"]["casual_random"]],
             ["Budget cutter", "Full comfort, then removes the hours that cost least comfort per kWh until the budget is met", S["by_strategy_runs"]["budget_cutter"]],
             ["Peak-aware", "Chooses the cheapest hours each appliance can reasonably run in, then trims to the budget, peak hours first", S["by_strategy_runs"]["peak_aware"]],
             ["Optimizer", "Improves the peak-aware plan by local search (the method that sets par)", S["by_strategy_runs"]["optimizer"]],
             ["Essentials only", "Fridge and cooktop and nothing else", S["by_strategy_runs"]["essentials_only"]]]
    s += [KeepTogether([table(strat, [3.1 * cm, 11.6 * cm, 1.6 * cm]), P("Table 2. The six scripted strategies, run on every level and event (eight seeds each, one for the last two).", "cap")])]

    # 4 par
    s += [P("4. Par scores", "h1"),
          P("A rating means little unless par is right. We estimate par by searching for the best day on each level and event. Our first search started from an empty day and got stuck on some event days: "
            "a simple scripted plan beat it in 115 of 612 runs, by up to 21% (Easy with guests: 642 against 777). We rebuilt the search to start from the scripted plans as well, recomputed all 18 pars, and "
            "checked again: no strategy now beats par on any level or event. Par is still an estimate from a random search, accurate to about 2%.")]

    # 5 results
    s += [P("5. Results and inferences", "h1"),
          fig(FIG / "fig5_events_and_appliances.png", 15.6,
              f"Figure 3. Left: energy needed for a full-comfort day on each event day compared with a normal day. Right: share of a full-comfort day's energy by appliance."),
          P(f"The air conditioner alone takes {SH['ac']:.0f}% of a full-comfort day. With the cooktop ({SH['cooktop']:.0f}%), water heater ({SH['heater']:.0f}%) and iron ({SH['iron']:.0f}%) it makes {BIG4:.0f}%. "
            f"Lights, television, computer, fan and washing machine are {SH['lights']+SH['tv']+SH['computer']+SH['fan']+SH['washer']:.0f}% together. A player who spends effort on the small loads is working on the wrong end. "
            f"Events move demand by {EV['wfh']:.0f}% to {EV['heatwave']:.0f}% (heatwave {EV['heatwave']:.0f}%, cold snap {EV['coldsnap']:.0f}%), which is why par is set per event."),
          fig(FIG / "fig2_strategies.png", 16.2,
              "Figure 4. The six strategies on a Medium day without an event. Bars are means over seeds and whiskers show one standard deviation."),
          P(f"Staying within budget costs comfort. A full-comfort day uses {FULL['energy_kwh']:.1f} kWh and is over budget in {OB['full_comfort']:.0f}% of runs. The budget cutter and peak-aware strategies use "
            f"{CUT['energy_kwh']:.1f} kWh, which is {ENERGY_CUT_PCT:.0f}% less, and keep {CUT['comfort']*100:.0f}% of the wanted comfort. Casual play, with no plan, is over budget in {OB['casual_random']:.0f}% of runs. "
            f"The five strategies that provide comfort show a correlation of r = {S['comfort_energy_corr']['r']:.2f} between energy and comfort (the runs are not independent, so we report the figure as description only)."),
          fig(FIG / "fig3_tradeoff.png", 15.2,
              "Figure 5. Every simulated run. Peak-aware and budget-cutter days sit at identical points (the rings mark the budget cutter). Essentials-only days have no comfort by design."),
          fig(FIG / "fig4_hourly_profile.png", 14.6,
              "Figure 6. Mean energy per hour on a Medium day. The peak-aware strategy leaves the red evening hours almost empty and uses the green night hours."),
          P(f"Timing is a free saving. At the same energy and comfort, the peak-aware day costs {PEAK['cost']:.2f} against {CUT['cost']:.2f} for the budget cutter on a Medium day, which is {COST_SAVED_MED:.0f}% less. "
            f"Across all {PVC['n_pairs']} paired runs (same level, event and seed) the mean saving is {PVC['cost_saved_pct_mean']:.1f}% (95% interval {PVC['ci95'][0]:.1f} to {PVC['ci95'][1]:.1f}) and the score is {PVC['score_gain_mean']:.0f} points higher. "
            f"The share of energy used at peak falls from {CUT['peak_share']*100:.0f}% to {PEAK['peak_share']*100:.0f}% and the off-peak share rises from {CUT['offpeak_share']*100:.0f}% to {PEAK['offpeak_share']*100:.0f}%. "
            f"The optimizer, which starts from the peak-aware plan, reaches a score of {OPT['score']:.0f} against {PEAK['score']:.0f}, so simple rules capture almost everything the search finds."),
          fig(FIG / "fig6_savings.png", 15.2,
              "Figure 7. Peak-aware play against a full-comfort day, averaged over the six event settings and eight seeds. Most of the energy saving comes from the budget forcing cuts; the cost saving also includes timing.")]

    # 6 sustainable solution
    pv = S["peak_aware_vs_full"]["Medium"]
    nd = normal_day_pair_saving()
    s += [P("6. The sustainable solution", "h1"),
          P("The proposal is the game itself, used as a teaching and awareness tool, together with the habits the data points to. The habits, in order of effect:"),
          ] + bullets([
              f"Decide the air conditioner first. It is {SH['ac']:.0f}% of the day's energy, and one hour less saves 1.5 kWh.",
              f"Treat the water heater and iron as scheduled jobs. Together they are {SH['heater']+SH['iron']:.0f}% of the day and can move to the night at no loss of comfort. The cooktop ({SH['cooktop']:.0f}%) is tied to meal times, so plan around it.",
              f"Run flexible loads in the off-peak hours. On normal days, across the three levels, this cut cost by {nd:.0f}% on average (pairs with the same level and seed) with energy and comfort unchanged.",
              "Leave the small loads alone until the large ones are planned.",
          ]) + [
        P(f"For a sense of scale: moving from our full-comfort pattern to the budget-meeting pattern avoids about {pv['co2_saved_kg']:.1f} kg of CO2 per Medium day, or roughly {S['co2_saved_per_year_kg_medium']/1000:.1f} tonnes over a year "
          "if every day looked like the model day. Real days do not, and few households run everything at full comfort, so read this as an upper bound for the illustration and not a forecast. "
          "The cost saving from timing carries no CO2 benefit in this model, because it uses a single emission factor for every hour. On a real grid the cleanest hours may differ from the cheapest ones."),
        P("How it would be used. In a classroom, each student plays a four-minute round, compares scores, and discusses why a heatwave day is harder than a normal one. A teacher can collect the "
          "exported CSV files and run the cleaning and analysis scripts to see what a class actually does. The game runs from one command and needs no internet connection after installation. "
          "Putting it online (for example on Streamlit Community Cloud) is possible but not done or tested."),
    ]

    # 7 testing
    sens = SENS["medium"]
    s += [P("7. Testing and robustness", "h1"),
          P(f"The project has {n_tests} automated tests covering the energy, CO2, cost and score calculations, the events, the data pipeline (including broken rows and a browser export), the tips, a smoke test of the app, "
            f"and a check that the browser's scoring matches Python's on random days for every level and event. A scripted browser run played 90 full days through the real interface, each confirmed by the Python engine, with no "
            f"mismatches or script errors. We also replayed the Python peak-aware schedule through the interface: it scored {PEAK['score']:.0f} (Gold) with the same energy and cost as Python."),
          P(f"Sensitivity. Three game values sit below their published ranges. We set the {join_and([names[k] for k in SENS['below_appliances']])} to the lowest published values "
            f"({join_and([str(v) + ' W' for v in SENS['below_appliances'].values()])}) and re-ran the scripted strategies on a normal day. A full-comfort day then uses {SENS['full_comfort_kwh']:.1f} kWh "
            f"(up {100*(SENS['full_comfort_kwh']/FULL['energy_kwh']-1):.0f}%), so absolute kWh figures are approximate. The ranking of the strategies by score is unchanged "
            f"({', '.join(LABELS[k] for k in SENS['ranking_medium'])}, from best to worst) and peak-aware still costs {SENS['peak_vs_cutter_cost_saved_pct']:.1f}% less than the budget cutter. "
            "The relative findings hold; the absolute numbers should be read loosely.")]

    # 8 limitations
    s += [P("8. Limitations", "h1")] + bullets([
        "There are no human players in the data. The scripted strategies are ours, and a real person might behave quite differently.",
        "Three appliance values are below published ranges, as above. The tariff (a 1:2:4 pattern) is invented, not a real utility's, and one emission factor is used for every hour and region.",
        "A day is one isolated 24 hours. There is no weather forecast, solar panel or battery, and no carry-over between days.",
        "Par scores come from a random search and are approximate. The optimizer starts from our own scripted plan, so a cleverer human plan could beat par.",
        "The emission factor of 0.445 kg/kWh comes from search results quoting the IEA report [1]. The page itself blocks automated access, so we have not read it. It should be confirmed in a browser before submission. The other facts shown in the game were read on their pages (EPA [2], RunWatts [4]).",
        "Layout was checked in a desktop browser pane and at phone width, not on real phones or a slow college computer. The game has not been deployed online.",
    ])
    s += [P("9. Next steps", "h1"),
          P("Collect at least twenty real runs, ideally from students who have not seen the game, and re-run the analysis. The play-test kit in the repository has the observation sheet. After that, "
            "add region presets for tariff and emission factor, and a solar and battery option with a cloudy-day event.")]


    # references
    refs = [
        "[1] IEA, Electricity 2025, Emissions (2024 global average carbon intensity; not read directly, see section 8). https://www.iea.org/reports/electricity-2025/emissions",
        "[2] U.S. EPA, Greenhouse Gas Equivalencies Calculator, calculations and references (3.93e-4 metric tons CO2e per mile; read 10 Nov 2026). https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator-calculations-and-references",
        "[3] EnergySage, How many watts does it take to run a house? (updated 5 Aug 2024). https://www.energysage.com/electricity/house-watts/",
        "[4] RunWatts, Appliance wattage chart (updated 29 Apr 2026). https://www.runwatts.com/blog/appliance-wattage-chart",
        "[5] Enphase, How many watts do common home appliances use? (updated 18 Nov 2025). https://enphase.com/blog/homeowners/how-many-watts-do-common-home-appliances-use",
        f"[6] Source code, data and documents: {REPO}",
    ]
    s += [P("References", "h1")] + [Paragraph(fx(r), ST["cell"]) for r in refs]
    doc.build(s, onFirstPage=footer("Smart Energy Conservation Game: final report"), onLaterPages=footer("Smart Energy Conservation Game: final report"))


LABELS = {"full_comfort": "full comfort", "casual_random": "casual", "budget_cutter": "budget cutter", "peak_aware": "peak-aware",
          "optimizer": "optimizer", "essentials_only": "essentials only"}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    build_problem_statement(OUT / "1_problem_statement.pdf")
    build_report(OUT / "4_final_report.pdf")
    from pypdf import PdfReader

    for f in ("1_problem_statement.pdf", "4_final_report.pdf"):
        print(f, len(PdfReader(OUT / f).pages), "pages")


if __name__ == "__main__":
    main()
