"""League > Trade history is its own leaf (David 2026-10-08, ledger #74: "drop All-time and just have Records and
Trade History"). League's row reads Recap, Teams, Records, Trade history; Records is only its records, with no mode row.

The leaf id is `tradehist` (hash `#tradehist`); `#trades` stays the trade finder under Team. The leaf shows only where the
league on screen has graded trades (the Madden Curse's), as Records shows only where it has a record book."""
import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.league_chip import LeagueChip, pick_script  # noqa: E402
from pages.tradehist import TradeHistoryPage  # noqa: E402
from wording import words  # noqa: E402

LEAGUE_ROW = ["recap", "teams", "records", "tradehist"]
# What each league on screen has (chrome/nav.js navFacts): Yahoo's record book and graded trades, ESPN's neither,
# AYO's record book but no graded trades.
YAHOO = {"waivers": True, "teams": True, "recap": True, "records": True, "trades": True, "tradehist": True}
ESPN = {**YAHOO, "records": False, "tradehist": False}
AYO = {**YAHOO, "tradehist": False}


@pytest.fixture(scope="module")
def nav(node_js):
    return node_js("data/navmap.js", "data/navrow.js")


@pytest.mark.req("Trade history", ac="League's row is Recap, Teams, Records, Trade history")
def test_league_holds_recap_teams_records_and_trade_history_in_that_order(nav):
    assert nav("NAV.find(([g]) => g === 'league')[1]") == LEAGUE_ROW
    assert nav("navLeavesFor", "league", YAHOO, False) == LEAGUE_ROW
    assert nav("navGroupOf", "tradehist") == "league" and nav("navLeafOf", "tradehist") == "tradehist"
    assert nav("navLabel", "tradehist") == "Trade history" == words("nav.tab.tradehist")


@pytest.mark.req("Trade history", ac="the leaf shows only where the league has graded trades")
@pytest.mark.parametrize("facts,want", [(ESPN, ["recap", "teams"]), (AYO, ["recap", "teams", "records"])],
                         ids=["espn-has-neither", "ayo-has-no-graded-trades"])
def test_a_league_without_graded_trades_has_no_trade_history_leaf(nav, facts, want):
    assert nav("navLeavesFor", "league", facts, False) == want


@pytest.mark.req("Trade history", ac="a link to the leaf where the league lacks it lands on Recap")
def test_a_tradehist_link_on_a_league_without_it_falls_back_to_recap(nav):
    assert nav("navFallback", "tradehist", ["recap", "teams"]) == "recap"
    assert nav("navFallback", "tradehist", LEAGUE_ROW) == "tradehist"


@pytest.mark.req("Trade history", ac="#trades is still the finder, not the history")
def test_the_trades_hash_is_still_the_finder_under_team(nav):
    assert nav("navLeafOf", "trades") == "trades" and nav("navGroupOf", "trades") == "team"


@pytest.mark.req("Trade history", ac="the leaf draws the old Trades page, with no Records mode row")
@pytest.mark.parametrize("size", [(360, 740), (1280, 900)], ids=["phone", "desktop"])
def test_the_leaf_draws_the_trade_history_with_no_records_tabs(mount, size):
    page, errors = mount("tradehist", size=size)
    h = TradeHistoryPage(page)
    assert h.ranking_count() == 1, "the ranking, the heists and the curses the Records tab drew"
    assert h.all_time_count() == 0
    assert h.old_tab_count() == 0 and h.old_bar_count() == 0
    assert h.fits()
    assert errors == []


@pytest.mark.req("Trade history", ac="Records shows only its records, with no mode row")
@pytest.mark.parametrize("size", [(360, 740), (1280, 900)], ids=["phone", "desktop"])
def test_records_is_only_its_records_with_no_mode_row(mount, size):
    page, errors = mount("records", size=size)
    h = TradeHistoryPage(page)
    assert h.all_time_count() == 1 and h.ranking_count() == 0
    assert h.old_tab_count() == 0 and h.old_bar_count() == 0, "was All-time | Trade history until 2026-10-08"
    assert h.fits()
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_four_pills_fit_the_360_row_and_the_leaf_opens_from_the_sub_row_and_its_hash(browser, page_file):
    from test_render import open_at
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#records")
    chip, h = LeagueChip(page), TradeHistoryPage(page)
    page.wait_for_selector("#view .rc")
    assert chip.subnav_leaves() == LEAGUE_ROW
    assert h.subnav_labels()[-1] == words("nav.tab.tradehist")
    assert h.subnav_overflow() == 0, "four pills in the 332 px row"
    chip.tap_leaf("tradehist")
    page.wait_for_selector("#view .tr-rank")
    assert page.evaluate("location.hash") == "#tradehist"
    assert page.locator("#subnav .mode-sub[aria-pressed='true']").inner_text() == words("nav.tab.tradehist")
    assert h.old_tab_count() == 0
    page.reload()
    page.wait_for_selector("#view .tr-rank")
    chip.open_by_hash("records")
    page.wait_for_selector("#view .rc")
    assert h.fits()
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.journey
def test_a_tradehist_link_on_ayo_lands_on_recap_and_the_row_has_no_such_pill(browser, page_file):
    from test_render import open_at
    ctx, page, errors = open_at(browser, page_file, (360, 800), "#tradehist", init=(pick_script("ayo"),))
    chip = LeagueChip(page)
    page.wait_for_function("SURFACE === 'recap'")
    assert chip.subnav_leaves() == ["recap", "teams", "records"], "AYO has a record book but no graded trades"
    assert errors == []
    ctx.close()
