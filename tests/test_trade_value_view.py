"""Team > Trades > Value, in the browser (2026-11-03): the tab, the chips, the rows and a row's profile.

The rows, the cap and the words are Node's (tests/test_js_tradevalue.py); the cut is test_trade_value.py. These prove what
the screen draws and what a tap does, on the fixture's Yahoo league (the real 2026-10-28 rosters, Rashee Rice's healthy
what-if as of 2026-11-03) for the reader whose team is Chat Take the Wheel. Trades mounts alone (tests/component.py). The
no-file variant mounts a page whose injected LIVE_TRADE_VALUE is null, the way a build without the file injects it."""
import re

import pytest

import component
from component import mount  # noqa: F401  (the fixture)
from pages.finder import reader, serve, FIXTURE
from pages.value import ValuePage

PHONE = (360, 800)
DESKTOP = (1280, 800)


def open_value(mount, size=PHONE, team="yahoo"):
    page, errors = mount("trades", size=size, init=(reader(team), serve(FIXTURE)))
    value = ValuePage(page)
    value.pick_tab("value")
    return page, errors, value


@pytest.mark.render
@pytest.mark.req("Trade value", ac="a second tab on Trades, opened in place in the phone's tab row")
def test_trades_gets_offers_and_value_tabs_in_the_tab_row_and_value_opens_the_list(mount):
    page, errors = mount("trades", size=PHONE, init=(reader("yahoo"), serve(FIXTURE)))
    value = ValuePage(page)
    assert value.tabs() == [("offers", True), ("value", False)]
    value.pick_tab("value")
    assert value.tabs() == [("offers", False), ("value", True)]
    rows = value.rows()
    assert len(rows) == 40 and rows[0]["rank"] == "RB1" and rows[0]["par"] == "+101.3"
    assert value.first_row_top() < 260, "the first row sits under one chip row and a caption"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Trade value", ac="a chip per position, everyone, or the reader's own team")
def test_mine_shows_the_readers_team_in_lime_and_a_position_chip_shows_only_that_position(mount):
    page, errors, value = open_value(mount)
    assert [c for c, _ in value.chips()] == ["all", "mine", "QB", "RB", "WR", "TE"]
    value.pick("mine")
    mine = value.rows()
    assert mine and all(r["mine"] and r["holder"] == "Yours" for r in mine)
    assert [r["name"] for r in mine][:2] == ["D. Henry", "T. McMillan"]
    value.pick("TE")
    te = value.rows()
    assert te and all(r["rank"].startswith("TE") for r in te) and value.more() is None
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Trade value", ac="a healthy what-if beside a player priced for missed games")
def test_a_row_carries_the_rate_and_the_healthy_what_if_under_the_name(mount):
    page, errors, value = open_value(mount)
    value.pick("mine")
    rice = next(r for r in value.rows() if r["slug"] == "rashee-rice")
    assert rice["par"] == "+13.3" and rice["rate"] == "12.0/g × 5.1 g"
    assert rice["healthy"] == "If healthy +8.8"
    assert "Replacement a game: QB 17.1 · RB 9.5 · WR 9.4 · TE 8.2" in value.caption()
    assert re.search(r"Priced Oct 28", value.caption())
    assert errors == []


@pytest.mark.render
def test_show_all_draws_the_rest_of_the_league_and_a_row_opens_the_profile(mount):
    page, errors, value = open_value(mount)
    assert value.more().startswith("Show all (")
    value.show_all()
    assert len(value.rows()) > 40 and value.more() is None
    value.open_row("rashee-rice")
    assert "rashee rice" in page.get_by_test_id("profile-title").inner_text().lower()
    assert errors == []


@pytest.mark.render
def test_a_desktop_draws_the_tab_bar_and_two_columns_without_a_sideways_scroll(mount):
    page, errors, value = open_value(mount, size=DESKTOP)
    assert value.tabs() == [("offers", False), ("value", True)]
    width, inner = value.scroll_width()
    assert width <= inner
    lefts = {round(b["x"]) for b in (r.bounding_box() for r in page.get_by_test_id("value-row").all()[:40])}
    assert len(lefts) == 2, "two columns from 760px"
    assert errors == []


@pytest.fixture(scope="module")
def no_file(browser, built, tmp_path_factory):
    text = re.sub(r"^const LIVE_TRADE_VALUE = .*;$", "const LIVE_TRADE_VALUE = null;", built.fragment, count=1, flags=re.M)
    assert text != built.fragment
    m = component.Mounter(browser, tmp_path_factory.mktemp("tv"), text)
    yield m
    m.pages.close()


@pytest.mark.render
def test_without_the_file_trades_has_no_value_tab(no_file):
    """The fixture's ESPN league, which has offers: the finder draws them under no tab row."""
    page, errors = no_file("trades", size=PHONE, init=(reader("espn"), serve(FIXTURE)))
    assert ValuePage(page).tabs() == []
    page.get_by_test_id("finder-offers").wait_for()
    assert errors == []
