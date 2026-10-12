"""The Streamlit shell must load and register the game component without raising."""
from pathlib import Path

import pytest

streamlit_testing = pytest.importorskip("streamlit.testing.v1")

ROOT = Path(__file__).resolve().parent.parent


def test_app_loads_without_exceptions():
    at = streamlit_testing.AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not at.exception


def test_frontend_files_present():
    for name in ("index.html", "styles.css", "game.js", "scoring.js", "tips.js"):
        assert (ROOT / "frontend" / name).is_file(), name


def test_index_loads_scripts_in_dependency_order():
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    order = [html.index(f'src="{n}.js"') for n in ("scoring", "tips", "game")]
    assert order == sorted(order)  # game.js uses Scoring and Tips, so they must load first
