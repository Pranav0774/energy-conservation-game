from dataclasses import asdict
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from game.appliances import APPLIANCES
from game.engine import evaluate
from game.events import EVENTS, apply_event
from game.levels import LEVELS, par_for
from game.ui_config import build_config, sanitize_schedule

st.set_page_config(
    page_title="Smart Energy Conservation Game",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove Streamlit's own chrome so the game fills the page.
st.markdown(
    """
    <style>
      #MainMenu, footer, [data-testid="stHeader"], [data-testid="stSidebar"],
      [data-testid="collapsedControl"], [data-testid="stToolbar"] { display: none !important; }
      .stApp { background: #070b14; }
      .block-container { padding: 0 !important; max-width: 100% !important; }
      iframe { border: 0; display: block; }
    </style>
    """,
    unsafe_allow_html=True,
)

# The real-time game is a small web app in frontend/. It plays the day live in the browser;
# when the day ends it sends the schedule back here and this file scores it with game/engine.py.
game = components.declare_component("energy_game", path=str(Path(__file__).parent / "frontend"))

st.session_state.setdefault("result", None)
st.session_state.setdefault("nonce", None)

value = game(config=build_config(), result=st.session_state.result, key="game", default=None)

if value and value.get("nonce") != st.session_state.nonce and value.get("level") in LEVELS:
    level = LEVELS[value["level"]]
    event = value.get("event") if value.get("event") in EVENTS else None
    schedule = sanitize_schedule(value.get("schedule", {}))
    res = evaluate(schedule, apply_event(APPLIANCES, event), level.budget_kwh, par_for(level.name, event))
    st.session_state.result = {**asdict(res), "nonce": value["nonce"]}
    st.session_state.nonce = value["nonce"]
    st.rerun()
