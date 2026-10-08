"""League > Records, its two views (design/src/js/surface/league/rctabs.js, 2026-10-06): All-time and Trade history.

Trade history is the old Trades leaf (surface/trades/), now a tab of Records; it is the Madden Curse's alone, so a league with
no graded trades has no tab. A phone draws the tabs as the Records pill's own segments in the tab row, a desktop as a bar
above the page (a view's own tabs never draw a bar of their own on a phone, STYLE.md). Each test mounts Records alone
(tests/component.py) and reads it through tests/pages/records.py."""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.records import RecordsPage  # noqa: E402
from wording import words  # noqa: E402

ALL_TIME, TRADES = words("records.tab.alltime"), words("records.tab.trades")


@pytest.mark.req("Trade history", ac="Records has two tabs, All-time first, and Trade history opens the old Trades page")
@pytest.mark.parametrize("size", [(360, 740), (1280, 900)], ids=["phone", "desktop"])
def test_records_has_all_time_and_trade_history_and_the_second_opens_the_old_trades_page(mount, size):
    page, errors = mount("records", size=size)
    r = RecordsPage(page)
    assert r.tabs() == [{"label": ALL_TIME, "pressed": True}, {"label": TRADES, "pressed": False}]
    assert r.showing() == "alltime"
    r.select(TRADES)
    assert r.showing() == "trades" and r.history_has_ranking(), "the ranking, the heists and the curses the Trades leaf drew"
    assert r.labels() == [ALL_TIME, TRADES] and r.tabs()[1]["pressed"] is True
    assert r.fits()
    r.select(ALL_TIME)
    assert r.showing() == "alltime"
    assert errors == []


@pytest.mark.req("Trade history", ac="the tab is absent where the league has no graded trades")
def test_a_league_with_no_graded_trades_has_no_trade_history_tab(mount):
    page, errors = mount("records")
    page.evaluate("pickTeam('ayo')")                      # AYO has a record book but no graded trades
    page.wait_for_selector("#view[data-view='records'] .lgchip")
    r = RecordsPage(page)
    assert r.tabs() == [] and r.showing() is None, "no tab, and AYO's page is its own empty book"
    assert errors == []


def test_the_chosen_tab_is_kept_for_the_visit(mount):
    page, _ = mount("records", size=(1280, 900))
    r = RecordsPage(page)
    r.select(TRADES)
    page.evaluate("render()")
    assert r.showing() == "trades" and r.tabs()[1]["pressed"] is True
