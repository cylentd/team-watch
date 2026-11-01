"""League > Trade history for a reader on the ESPN league (2026-11-01, David: the history for the 10-team league
too, managers as first names, players as `M. Nabers`).

ff-jarvis's espn_trade_verdicts.json is not on its main yet, so the fixture build has no ESPN block (a null
block, tests/test_espn_trades.py). These tests plant one after the page loads: the Yahoo fixture's verdicts
read as ESPN's, with ESPN-style player names and a made-up first-name map. The Yahoo league's block stays in
the page beside it, so a Yahoo reader proves the two do not mix.
"""
import copy
import json

import pytest

import league_trades as T
from component import mount  # noqa: E402,F401  (the fixture)
from conftest import FIXTURES
from pages.league_chip import LeagueChip, pick_script  # noqa: E402
from pages.tradehist import TradeHistoryPage  # noqa: E402
from pages.tradehist_text import TradeHistoryText  # noqa: E402
from wording import words  # noqa: E402

PHONE, DESKTOP = (360, 740), (1280, 900)
FIRST_NAMES = ["Will", "Anthony", "Thomas", "Eric", "Brandon", "Brian", "David", "Gordon", "John", "Minh", "Phillip",
               "Nate", "Max"]
# A long side, to prove a long list wraps at 360px; ESPN names players "A.J. Brown" and a defense "Raiders D/ST".
LONG_SIDE = ["Marvin Harrison Jr.", "A.J. Brown", "Amon-Ra St. Brown", "Raiders D/ST", "Malik Nabers", "J.K. Dobbins",
             "Tetairoa McMillan", "Zed Plantwell"]    # the last is invented: it can only come from this plant


@pytest.fixture(scope="module")
def planted():
    """The block ff-jarvis's two files would give (design/league_trades.py), as the page receives it."""
    verdicts = json.loads((FIXTURES / "data" / "yahoo_trade_verdicts.json").read_text(encoding="utf-8"))
    verdicts = copy.deepcopy(verdicts)
    verdicts["trades"][0]["sides"][0]["players"] = [{"name": n} for n in LONG_SIDE]
    verdicts["trades"][0]["margin"] = 999.0     # the biggest heist, so its card is drawn without a tap
    names = dict(zip([*verdicts["managers"], "former-1"], FIRST_NAMES))
    return T.live_trades(verdicts, {"managers": names}, key="espn")


def open_as(mount, planted, team, size=PHONE):
    """The page as a reader of `team` sees Trade history once ESPN's block is in: (page, errors, text)."""
    page, errors = mount("tradehist", size=size, init=(pick_script(team),))
    text = TradeHistoryText(page)
    text.plant_and_open(planted)
    return page, errors, text


@pytest.mark.req("Trade history", ac="an ESPN reader sees the tab and the page, managers as first names")
def test_an_espn_reader_gets_the_leaf_and_the_page_with_first_names(mount, planted):
    page, errors, text = open_as(mount, planted, "espn")
    assert LeagueChip(page).subnav_leaves() == ["recap", "teams", "tradehist"], "ESPN has no record book"
    assert TradeHistoryPage(page).ranking_count() == 1
    assert set(text.managers()) <= set(FIRST_NAMES) | {words("trades.former")}
    steps = {name for row in text.trade_names() for name in row.split(" → ")}     # a curse's rows read "A → B"
    assert steps <= set(FIRST_NAMES) | {words("trades.former")}
    assert text.league_title() == "We're Big in Japan"
    assert errors == []


@pytest.mark.req("Trade history", ac="players read first initial plus last name; initials and a defense stay")
def test_players_read_as_a_first_initial_and_a_last_name(mount, planted):
    _, errors, text = open_as(mount, planted, "espn")
    want = {"M. Harrison Jr.", "A.J. Brown", "A. St. Brown", "Raiders D/ST", "M. Nabers", "J.K. Dobbins", "Z. Plantwell"}
    assert want <= set(text.players())
    assert errors == []


@pytest.mark.req("Trade history", ac="long ESPN lists do not overflow at 360px")
@pytest.mark.parametrize("size", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_a_long_espn_trade_fits_the_width(mount, planted, size):
    page, errors, _ = open_as(mount, planted, "espn", size)
    assert TradeHistoryPage(page).fits()
    assert errors == []


@pytest.mark.req("Trade history", ac="the ESPN page says how it grades")
def test_the_espn_page_carries_its_grading_caption(mount, planted):
    _, errors, text = open_as(mount, planted, "espn")
    assert text.caption() == words("trades.espn.note")
    assert errors == []


@pytest.mark.req("Trade history", ac="a Yahoo reader's page is unchanged by ESPN's block")
def test_a_yahoo_reader_sees_no_espn_caption_names_or_trades(mount, planted):
    page, errors, text = open_as(mount, planted, "yahoo")
    assert text.caption() is None
    assert text.players() and "Z. Plantwell" not in text.players(), "the Yahoo league's own trades, not ESPN's"
    assert LeagueChip(page).subnav_leaves() == ["recap", "teams", "records", "tradehist"]
    assert errors == []


@pytest.mark.req("Trade history", ac="AYO, with no graded trades, is unchanged by ESPN's block")
def test_an_ayo_reader_still_has_no_trade_history_leaf(mount, planted):
    page, errors, text = open_as(mount, planted, "ayo")
    assert LeagueChip(page).subnav_leaves() == ["recap", "teams", "records"]
    assert text.caption() is None and text.players() == []
    assert errors == []


@pytest.mark.req("Trade history", ac="no ESPN block: the leaf is absent and the page is as before")
def test_without_an_espn_block_the_espn_reader_has_no_leaf(mount):
    page, errors = mount("recap", size=PHONE, init=(pick_script("espn"),))
    assert LeagueChip(page).subnav_leaves() == ["recap", "teams"]
    assert errors == []
