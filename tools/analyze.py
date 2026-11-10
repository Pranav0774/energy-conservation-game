"""Analyse the cleaned data: draw the report's graphs and write every number the report quotes.

Reads : data/clean/playlogs_clean.csv, data/clean/appliance_power_clean.csv
Writes: docs/figures/*.png and data/clean/summary_stats.json
Run   : python -m tools.analyze
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from game.appliances import APPLIANCES
from game.engine import CO2_KG_PER_KWH, OFFPEAK_HOURS, PEAK_HOURS
from game.events import EVENTS

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "clean"
FIG = ROOT / "docs" / "figures"
ORDER = ["full_comfort", "casual_random", "budget_cutter", "peak_aware", "optimizer", "essentials_only"]
LABEL = {"full_comfort": "Full comfort", "casual_random": "Casual", "budget_cutter": "Budget cutter",
         "peak_aware": "Peak-aware", "optimizer": "Optimizer", "essentials_only": "Essentials only", "human": "Human players"}
COLOR = {"full_comfort": "#D55E00", "casual_random": "#CC79A7", "budget_cutter": "#E69F00", "peak_aware": "#009E73",
         "optimizer": "#0072B2", "essentials_only": "#7f7f7f", "human": "#000000"}
EVENT_LABEL = {"none": "Normal day", **{k: e.name for k, e in EVENTS.items()}}
NAMES = {a.key: a.name for a in APPLIANCES}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 9.5, "axes.labelsize": 8.5, "figure.dpi": 100,
    "savefig.dpi": 200, "savefig.bbox": "tight", "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
})


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / name, facecolor="white")
    plt.close(fig)


def ci95(x) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return float("nan"), float("nan")
    m, se = x.mean(), stats.sem(x)
    h = se * stats.t.ppf(0.975, len(x) - 1)
    return float(m - h), float(m + h)


def fig_appliances(app: pd.DataFrame):
    app = app.iloc[::-1].reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(6.5, 3.3))
    for i, r in app.iterrows():
        ax.barh(i, r["source_max_w"] - r["source_min_w"], left=r["source_min_w"], height=0.5, color="#bcd4e6")
        ok = r["game_vs_range"] == "within"
        ax.plot(r["game_watts"], i, marker="D", ms=7, color="#009E73" if ok else "#D55E00", zorder=3)
    ax.set_yticks(range(len(app)), [NAMES[k] for k in app["game_key"]])
    ax.set_xscale("log")
    ax.set_xlabel("Power (W, log scale)")
    ax.set_title("Game appliance power against the ranges in three published sources")
    ax.plot([], [], "s", color="#bcd4e6", label="Source range (min to max)")
    ax.plot([], [], "D", color="#009E73", label="Game value, inside range")
    ax.plot([], [], "D", color="#D55E00", label="Game value, below range (simplified on purpose)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=3, frameon=False, fontsize=7.5)
    save(fig, "fig1_appliance_sources.png")


def fig_strategies(sim: pd.DataFrame):
    d = sim[(sim["level"] == "Medium") & (sim["event"] == "none")]
    metrics = [("energy_kwh", "Energy (kWh)"), ("cost", "Cost ($)"), ("comfort", "Comfort (0-1)"), ("score", "Score")]
    fig, axes = plt.subplots(1, 4, figsize=(6.9, 2.9), sharey=True)
    ys = np.arange(len(ORDER))[::-1]
    for ax, (col, title) in zip(axes, metrics):
        g = d.groupby("strategy")[col].agg(["mean", "std"]).reindex(ORDER)
        ax.barh(ys, g["mean"], xerr=g["std"].fillna(0), color=[COLOR[s] for s in ORDER], height=0.65,
                error_kw={"elinewidth": 0.8, "capsize": 2})
        for y, m, sd in zip(ys, g["mean"], g["std"].fillna(0)):
            ax.text(m + sd + g["mean"].max() * 0.02, y, f"{m:.2f}" if col in ("cost", "comfort") else f"{m:.1f}" if col == "energy_kwh" else f"{m:.0f}", va="center", fontsize=7,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6})
        ax.set_title(title)
        ax.grid(axis="y", alpha=0)
        if col == "energy_kwh":
            ax.axvline(10, color="black", ls="--", lw=1)
            ax.text(10, ys[0] + 0.55, "budget 10", fontsize=7, ha="center")
        ax.set_xlim(0, (g["mean"] + g["std"].fillna(0)).max() * 1.35)
    axes[0].set_yticks(ys, [LABEL[s] for s in ORDER])
    fig.suptitle("Six household strategies on a Medium day (10 kWh budget): mean and spread over seeds", fontsize=9.5, fontweight="bold", y=1.02)
    fig.tight_layout()
    save(fig, "fig2_strategies.png")


def fig_tradeoff(sim: pd.DataFrame, human: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    for s in ORDER:
        g = sim[sim["strategy"] == s]
        if s == "budget_cutter":  # same energy and comfort as peak-aware, so draw it as a ring around those dots
            ax.scatter(g["energy_kwh"], g["comfort"], s=60, facecolors="none", edgecolors=COLOR[s], linewidths=1.1, label=LABEL[s])
        else:
            ax.scatter(g["energy_kwh"], g["comfort"], s=16, alpha=0.7, color=COLOR[s], label=LABEL[s], edgecolor="none")
    if len(human):
        ax.scatter(human["energy_kwh"], human["comfort"], s=30, marker="x", color="black", label=LABEL["human"])
    for b in (7, 10, 14):
        ax.axvline(b, color="black", ls=":", lw=0.9)
        ax.text(b, 1.04, f"{b} kWh", ha="center", fontsize=7.5)
    ax.set_xlabel("Energy used in the day (kWh)")
    ax.set_ylabel("Comfort (share of wanted hours provided)")
    ax.set_ylim(-0.03, 1.1)
    ax.set_title("Comfort costs energy: every run on all levels and events", pad=14)
    ax.legend(ncol=3, frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "fig3_tradeoff.png")


def fig_hourly(sim: pd.DataFrame):
    d = sim[(sim["level"] == "Medium") & (sim["event"] == "none")]
    cols = [f"kwh_h{h:02d}" for h in range(24)]
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    for h in range(24):
        if h in PEAK_HOURS:
            ax.axvspan(h - 0.5, h + 0.5, color="#f4c7c3", alpha=0.45, lw=0)
        elif h in OFFPEAK_HOURS:
            ax.axvspan(h - 0.5, h + 0.5, color="#cfe8d5", alpha=0.55, lw=0)
    for s in ("full_comfort", "budget_cutter", "peak_aware"):
        ax.plot(range(24), d[d["strategy"] == s][cols].mean().values, marker="o", ms=3, lw=1.6, color=COLOR[s], label=LABEL[s])
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hour of day (red = peak price, green = off-peak)")
    ax.set_ylabel("Mean energy per hour (kWh)")
    ax.set_title("Peak-aware play moves energy out of the expensive evening hours")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "fig4_hourly_profile.png")


def fig_events(sim: pd.DataFrame, appl_share: pd.DataFrame):
    full = sim[sim["strategy"] == "full_comfort"].groupby("event")["energy_kwh"].mean()
    base = full["none"]
    order = ["none", *EVENTS]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.9, 3.0), gridspec_kw={"width_ratios": [1, 1.15]})
    vals = [(full[e] / base - 1) * 100 for e in order]
    a1.barh(range(len(order))[::-1], vals, color=["#7f7f7f" if e == "none" else "#D55E00" for e in order], height=0.6)
    for y, v in zip(range(len(order))[::-1], vals):
        a1.text(v + 0.4, y, f"{v:+.0f}%", va="center", fontsize=7.5)
    a1.set_yticks(range(len(order))[::-1], [EVENT_LABEL[e] for e in order])
    a1.set_xlabel("Energy for a full-comfort day vs a normal day (%)")
    a1.set_title("Events raise demand")
    a1.set_xlim(0, max(vals) * 1.25)
    a1.grid(axis="y", alpha=0)
    s = appl_share.sort_values("share")
    a2.barh(range(len(s)), s["share"] * 100, color="#0072B2", height=0.6)
    for y, v in enumerate(s["share"] * 100):
        a2.text(v + 0.5, y, f"{v:.0f}%", va="center", fontsize=7.5)
    a2.set_yticks(range(len(s)), [NAMES[k] for k in s.index])
    a2.set_xlabel("Share of a full-comfort day's energy (%)")
    a2.set_title("Where the energy goes")
    a2.grid(axis="y", alpha=0)
    a2.set_xlim(0, s["share"].max() * 100 * 1.2)
    fig.tight_layout()
    save(fig, "fig5_events_and_appliances.png")


def fig_savings(sv: pd.DataFrame):
    fig, axes = plt.subplots(1, 3, figsize=(6.9, 2.7))
    levels = list(sv.index)
    x = np.arange(len(levels))
    for ax, col, title, unit in zip(axes, ["energy_saved_pct", "co2_saved_kg", "cost_saved_pct"],
                                    ["Energy saved", "CO2 avoided per day", "Cost saved"], ["%", "kg", "%"]):
        ax.bar(x, sv[col], color="#009E73", width=0.6)
        for xi, v in zip(x, sv[col]):
            ax.text(xi, v, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
        ax.set_xticks(x, levels)
        ax.set_title(f"{title} ({unit})")
        ax.grid(axis="x", alpha=0)
        ax.set_ylim(0, sv[col].max() * 1.2)
    fig.suptitle("Peak-aware play vs full comfort (mean over events and seeds)", fontsize=9.5, fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "fig6_savings.png")


def sensitivity(app: pd.DataFrame) -> dict:
    """Re-run the scripted strategies with the three below-range appliances set to their source minimum."""
    from dataclasses import replace

    from game.engine import evaluate
    from game.events import apply_event
    from game.levels import LEVELS, par_for
    import tools.simulate_players as sim

    low = {r["game_key"]: int(round(r["source_min_w"])) for _, r in app.iterrows() if r["game_vs_range"] == "below"}
    variant = [replace(a, watts=low[a.key]) if a.key in low else a for a in APPLIANCES]
    original = sim.APPLIANCES
    rows = []
    sim.APPLIANCES = variant  # build() reads this module-level list
    try:
        for strategy in [s for s in sim.STRATEGIES if s != "optimizer"]:
            for level in LEVELS.values():
                for seed in range(sim.SEEDS if strategy not in ("essentials_only",) else 1):
                    schedule = sim.build(strategy, level, None, seed)
                    res = evaluate(schedule, variant, level.budget_kwh, par_for(level.name, None))
                    rows.append({"strategy": strategy, "level": level.name, "seed": seed, "score": res.score, "kwh": res.kwh, "cost": res.cost, "comfort": res.comfort})
    finally:
        sim.APPLIANCES = original
    df = pd.DataFrame(rows)
    m = df[df["level"] == "Medium"].groupby("strategy")[["score", "kwh", "cost", "comfort"]].mean()
    ranking = m.sort_values("score", ascending=False).index.tolist()
    a = df[df["strategy"] == "budget_cutter"].set_index(["level", "seed"])
    b = df[df["strategy"] == "peak_aware"].set_index(["level", "seed"])
    saved = (1 - b["cost"] / a["cost"]) * 100
    fc = df[(df["strategy"] == "full_comfort") & (df["level"] == "Medium")]["kwh"].mean()
    return {"below_appliances": low, "full_comfort_kwh": round(float(fc), 2), "ranking_medium": ranking,
            "peak_vs_cutter_cost_saved_pct": round(float(saved.mean()), 1),
            "medium": {s: {k: round(float(v), 2) for k, v in r.items()} for s, r in m.iterrows()}}


def main() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(CLEAN / "playlogs_clean.csv")
    app = pd.read_csv(CLEAN / "appliance_power_clean.csv")
    sim, human = d[d["is_simulated"]], d[~d["is_simulated"]]
    out: dict = {"n_runs": len(d), "n_simulated": len(sim), "n_human": len(human),
                 "n_human_players": int(human["player_id"].nunique()) if len(human) else 0,
                 "n_strategies": int(sim["strategy"].nunique()), "co2_factor": CO2_KG_PER_KWH}

    # appliance table vs game
    out["appliances"] = {
        "within": int((app["game_vs_range"] == "within").sum()), "total": int(len(app)),
        "below": app.loc[app["game_vs_range"] == "below", "game_key"].tolist(),
        "table": app[["game_key", "game_watts", "source_min_w", "source_max_w", "game_vs_range", "n_sources"]].to_dict("records"),
    }

    # strategy table: Medium, normal day
    med = sim[(sim["level"] == "Medium") & (sim["event"] == "none")]
    out["strategy_medium"] = {
        s: {"energy_kwh": round(g["energy_kwh"].mean(), 2), "cost": round(g["cost"].mean(), 2),
            "comfort": round(g["comfort"].mean(), 2), "score": round(g["score"].mean(), 0),
            "co2_kg": round(g["co2_kg"].mean(), 2), "over_budget_pct": round(100 * g["over_budget"].mean(), 0),
            "peak_share": round(g["peak_share"].mean(), 2), "offpeak_share": round(g["offpeak_share"].mean(), 2)}
        for s, g in med.groupby("strategy")}
    out["rating_by_strategy"] = {s: g["rating"].value_counts().to_dict() for s, g in sim.groupby("strategy")}
    out["over_budget_pct_by_strategy"] = {s: round(100 * g["over_budget"].mean(), 0) for s, g in sim.groupby("strategy")}

    # energy shares for a full-comfort day
    fc = sim[(sim["strategy"] == "full_comfort") & (sim["event"] == "none")]
    kwh = {a.key: fc["hrs_" + a.key].mean() * a.watts / 1000 for a in APPLIANCES}
    tot = sum(kwh.values())
    share = pd.DataFrame({"share": {k: v / tot for k, v in kwh.items()}})
    out["full_comfort_day_kwh"] = round(tot, 2)
    out["energy_share_pct"] = {k: round(100 * v, 1) for k, v in share["share"].items()}

    # events
    full = sim[sim["strategy"] == "full_comfort"].groupby("event")["energy_kwh"].mean()
    out["event_energy_change_pct"] = {e: round((full[e] / full["none"] - 1) * 100, 1) for e in full.index if e != "none"}

    # peak-aware vs full comfort, per level (paired on level, event and seed)
    key = ["level", "event"]
    fcm = sim[sim["strategy"] == "full_comfort"].groupby(key)[["energy_kwh", "co2_kg", "cost"]].mean()
    pa = sim[sim["strategy"] == "peak_aware"].groupby(key)[["energy_kwh", "co2_kg", "cost", "comfort", "score"]].mean()
    j = pa.join(fcm, lsuffix="_pa", rsuffix="_fc")
    j["energy_saved_pct"] = 100 * (1 - j["energy_kwh_pa"] / j["energy_kwh_fc"])
    j["cost_saved_pct"] = 100 * (1 - j["cost_pa"] / j["cost_fc"])
    j["co2_saved_kg"] = j["co2_kg_fc"] - j["co2_kg_pa"]
    sv = j.groupby("level")[["energy_saved_pct", "co2_saved_kg", "cost_saved_pct"]].mean().reindex(["Easy", "Medium", "Hard"])
    out["peak_aware_vs_full"] = {lv: {k: round(float(v), 2) for k, v in r.items()} for lv, r in sv.iterrows()}
    out["peak_aware_vs_full_medium_comfort"] = round(float(pa.xs("Medium", level="level")["comfort"].mean()), 2)
    out["co2_saved_per_year_kg_medium"] = round(float(sv.loc["Medium", "co2_saved_kg"]) * 365, 0)

    # same energy, lower cost: peak-aware vs budget-cutter, paired
    keyed = sim.assign(seed=sim["run_id"].str.rsplit("-", n=1).str[-1])
    a = keyed[keyed["strategy"] == "budget_cutter"].set_index(["level", "event", "seed"])
    b = keyed[keyed["strategy"] == "peak_aware"].set_index(["level", "event", "seed"])
    idx = a.index.intersection(b.index)
    dc = (1 - b.loc[idx, "cost"] / a.loc[idx, "cost"]) * 100
    de = (b.loc[idx, "energy_kwh"] - a.loc[idx, "energy_kwh"])
    lo, hi = ci95(dc)
    out["peak_vs_cutter"] = {"n_pairs": int(len(idx)), "cost_saved_pct_mean": round(float(dc.mean()), 1), "ci95": [round(lo, 1), round(hi, 1)],
                             "energy_diff_kwh_mean": round(float(de.mean()), 3), "score_gain_mean": round(float((b.loc[idx, "score"] - a.loc[idx, "score"]).mean()), 1)}

    # comfort vs energy relationship (optional strategies excluded: essentials_only has no comfort by design)
    core = sim[sim["strategy"].isin(["full_comfort", "casual_random", "budget_cutter", "peak_aware", "optimizer"])]
    r, p = stats.pearsonr(core["energy_kwh"], core["comfort"])
    out["comfort_energy_corr"] = {"r": round(float(r), 2), "p": float(p), "n": int(len(core))}

    # share of energy at peak: full comfort vs peak aware (Medium, normal)
    out["peak_share_medium"] = {s: out["strategy_medium"][s]["peak_share"] for s in ("full_comfort", "budget_cutter", "peak_aware")}

    # human players (empty until real exports are added to data/raw/real_playlogs/)
    if len(human):
        out["human"] = {
            "runs": int(len(human)), "players": out["n_human_players"],
            "by_level": {lv: {"n": int(len(g)), "mean_score": round(g["score"].mean(), 0), "mean_kwh": round(g["energy_kwh"].mean(), 2),
                              "mean_comfort": round(g["comfort"].mean(), 2), "over_budget_pct": round(100 * g["over_budget"].mean(), 0),
                              "mean_peak_share": round(g["peak_share"].mean(), 2)} for lv, g in human.groupby("level")},
            "rating": human["rating"].value_counts().to_dict(),
        }

    hcols = [f"kwh_h{h:02d}" for h in range(24)]
    out["hourly_medium"] = {s: [round(float(v), 3) for v in med[med["strategy"] == s][hcols].mean()] for s in ("full_comfort", "budget_cutter", "peak_aware")}
    out["sensitivity"] = sensitivity(app)
    raw_app = pd.read_csv(ROOT / "data" / "raw" / "appliance_power_sources.csv")
    log_app = pd.read_csv(CLEAN / "appliance_cleaning_log.csv")
    log_play = pd.read_csv(CLEAN / "playlogs_cleaning_log.csv")
    out["dataset"] = {"raw_appliance_rows": int(len(raw_app)), "raw_appliance_sources": int(raw_app["source_id"].nunique()),
                      "appliance_log": log_app.set_index("step")["rows"].to_dict(),
                      "playlog_log": log_play.set_index("step")["rows"].to_dict(), "playlog_columns": int(len(d.columns))}
    out["by_strategy_runs"] = sim["strategy"].value_counts().to_dict()

    # figures
    fig_appliances(app)
    fig_strategies(sim)
    fig_tradeoff(sim, human)
    fig_hourly(sim)
    fig_events(sim, share)
    fig_savings(sv)
    (CLEAN / "summary_stats.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_runs", "n_simulated", "n_human", "peak_aware_vs_full", "peak_vs_cutter", "comfort_energy_corr", "event_energy_change_pct")}, indent=1))


if __name__ == "__main__":
    main()
