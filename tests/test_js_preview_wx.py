"""Preview's Weather row says "Dome" for a game under a roof (surface/preview/research.js pvWxRow), in Node.

Monday 2026-10-05: ATL @ NO showed no weather line and never said why. A roof is an answer, not a gap:
the game has no weather, and the reader should be told so rather than left to wonder whether the
forecast failed. An open-air game with no forecast yet still draws nothing."""
import re

import pytest

FILES = ("surface/preview/dossier.js", "surface/preview/research.js")


@pytest.fixture(scope="module")
def pv(node_js):
    return node_js(*FILES)


def text(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]*>", " ", html)).strip()


def game(**wx):
    return {"home": "NO", "away": "ATL", "site": {"stadium": "Caesars Superdome", "neutral": False},
            "wx": {"roof": "dome", "temp": None, "wind": None, "precip": None, "sky": None, **wx}}


def test_a_dome_says_dome_and_names_the_stadium(pv):
    out = text(pv("pvWxRow", game()))
    assert "Weather" in out and "Caesars Superdome" in out
    assert re.search(r"\bDome\b", out), out


def test_a_dome_never_draws_a_forecast_even_when_a_forecast_arrived(pv):
    out = text(pv("pvWxRow", game(temp=71, wind=4, precip=10, sky="Clear")))
    assert re.search(r"\bDome\b", out) and "71" not in out and "mph" not in out


def test_a_closed_roof_says_so(pv):
    assert "Roof closed" in text(pv("pvWxRow", game(roof="closed")))


def test_open_air_without_a_forecast_still_draws_nothing(pv):
    assert pv("pvWxRow", game(roof="open")) == ""


def test_no_weather_block_draws_nothing(pv):
    assert pv("pvWxRow", {"home": "NO", "away": "ATL", "wx": None}) == ""
