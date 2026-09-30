import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from game.appliances import APPLIANCES
from game.engine import CO2_KG_PER_KWH, CURRENCY, PEAK_HOURS, OFFPEAK_HOURS, evaluate, hourly_kwh
from game.levels import LEVELS

HOUR_COLS = [f"{h:02d}" for h in range(24)]
BY_NAME = {f"{a.icon} {a.name}": a for a in APPLIANCES}

st.set_page_config(page_title="Smart Energy Conservation Game", page_icon="⚡", layout="wide")


def fresh_grid() -> pd.DataFrame:
    rows = {}
    for label, a in BY_NAME.items():
        rows[label] = [a.key == "fridge"] * 24  # the fridge starts on; everything else is up to you
    return pd.DataFrame.from_dict(rows, orient="index", columns=HOUR_COLS)


def to_schedule(df: pd.DataFrame) -> dict:
    return {BY_NAME[label].key: [bool(x) for x in row] for label, row in df.iterrows()}


if "grid_version" not in st.session_state:
    st.session_state.grid_version = 0
    st.session_state.finished = False

# ---------- sidebar ----------
with st.sidebar:
    st.header("⚡ Game settings")
    level_name = st.radio("Difficulty", list(LEVELS), index=1)
    level = LEVELS[level_name]
    st.caption(level.description)
    st.metric("Daily budget", f"{level.budget_kwh:.1f} kWh")
    if st.button("Reset day"):
        st.session_state.grid_version += 1
        st.session_state.finished = False
        st.rerun()
    st.markdown(
        f"**Tariff**  \n🟢 Off-peak (22:00–06:00) cheapest  \n🟡 Standard  \n🔴 Peak (17:00–22:00) most expensive"
    )

# ---------- main ----------
st.title("⚡ Smart Energy Conservation Game")
st.write(
    "Plan your household's day. Tick the hours each appliance runs. Stay under the energy budget, "
    "keep the essentials running, and keep everyone comfortable."
)

edited = st.data_editor(
    fresh_grid(),
    key=f"grid_{st.session_state.grid_version}",
    column_config={c: st.column_config.CheckboxColumn(c, width="small") for c in HOUR_COLS},
)
schedule = to_schedule(edited)
appliances = APPLIANCES
res = evaluate(schedule, appliances, level.budget_kwh, level.par_score)

# live metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Energy consumed", f"{res.kwh:.2f} kWh", f"{res.kwh - level.budget_kwh:+.2f} vs budget", delta_color="inverse")
c2.metric("CO₂ equivalent", f"{res.co2:.2f} kg")
c3.metric("Cost", f"{CURRENCY}{res.cost:.2f}")
c4.metric("Comfort", f"{res.comfort * 100:.0f}%")

used = res.kwh / level.budget_kwh
st.progress(min(used, 1.0), text=f"Budget used: {used * 100:.0f}%")
if used > 1:
    st.error(f"Over budget by {res.kwh - level.budget_kwh:.2f} kWh!")
if res.missing:
    st.warning("Essential appliances not running enough: " + ", ".join(res.missing))

if st.button("✅ Finish the day", type="primary"):
    st.session_state.finished = True

# ---------- results ----------
if st.session_state.finished:
    st.divider()
    st.header(f"Result: {res.rating} ({res.score} pts)")
    st.subheader("Score breakdown")
    breakdown = pd.DataFrame(
        {
            "Component": ["Base", "Comfort", "Budget", "Off-peak timing", "Missing essentials"],
            "Points": [res.base_pts, res.comfort_pts, res.budget_pts, res.timing_pts, -res.essential_pen],
        }
    )
    breakdown["Points"] = breakdown["Points"].round(0).astype(int)
    st.table(breakdown.set_index("Component"))

    fig = go.Figure()
    for a in APPLIANCES:
        one = {a.key: schedule[a.key]}
        fig.add_bar(x=HOUR_COLS, y=hourly_kwh(one, [a]), name=f"{a.icon} {a.name}")
    fig.update_layout(barmode="stack", xaxis_title="Hour", yaxis_title="kWh", title="Energy use by hour")
    for h in PEAK_HOURS | OFFPEAK_HOURS:
        fig.add_vrect(
            x0=h - 0.5, x1=h + 0.5, line_width=0,
            fillcolor="red" if h in PEAK_HOURS else "green", opacity=0.07,
        )
    st.plotly_chart(fig)

    per_app = sorted(
        ((a, sum(hourly_kwh({a.key: schedule[a.key]}, [a]))) for a in APPLIANCES), key=lambda t: -t[1]
    )
    top, top_kwh = per_app[0]
    if res.kwh > 0:
        st.info(f"💡 Your biggest consumer was **{top.name}** ({top_kwh / res.kwh * 100:.0f}% of your energy).")
    if res.kwh <= level.budget_kwh:
        st.success(f"You saved {level.budget_kwh - res.kwh:.2f} kWh, about {(level.budget_kwh - res.kwh) * CO2_KG_PER_KWH:.2f} kg of CO₂.")
