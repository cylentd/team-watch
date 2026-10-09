"""Every group opens the same view every time (2026-10-09, ledger #91; David: "currently it takes you to where
you were last at. this is confusing").

Matchup opens on Preview (Live while a game is on), Players on Ranks, and a view's own tab is not remembered
between visits: leaving Live, Recap, Ranks or Slips forgets the tab, so the next visit opens the first one.
The decision itself is data/landing.js, proven in Node (test_js_landing.py); this proves the page uses it, at a
phone and a desktop size, and that a link which sets a tab and then opens the view still lands on that tab.
The page's clock is pinned to a Saturday by the component SEED, so no game is on unless a test says so."""
import pytest

from component import mount  # noqa: F401

pytestmark = pytest.mark.render

SIZES = {"phone bottom bar": (360, 740), "desktop bar": (1280, 800)}
GROUP_BUTTON = "#nav .navitem[data-s='{}']"
IN_A_GAME = "Date.now = () => Date.parse(LIVE_SCHEDULE.games[0].kickoff) + 3600e3"   # an hour after the first kickoff


def leaf(page):
    return page.evaluate("SURFACE")


def tap_group(page, group):
    page.locator(GROUP_BUTTON.format(group)).click()
    page.wait_for_function("g => navGroupOf(SURFACE) === g", arg=group)


@pytest.fixture(params=sorted(SIZES))
def home(request, mount):
    """The Digest at the size under test: (page, errors), asserted free of page errors after the test."""
    page, errors = mount("digest", size=SIZES[request.param])
    yield page
    assert errors == []


@pytest.mark.req("Navigation: one League group, Stats", ac="Matchup opens on Preview")
def test_matchup_opens_on_preview_with_no_game_on(home):
    tap_group(home, "week")
    assert leaf(home) == "preview"


@pytest.mark.req("Navigation: one League group, Stats", ac="Matchup opens on Live while a game is on")
def test_matchup_opens_on_live_during_a_game(home):
    home.evaluate(IN_A_GAME)
    tap_group(home, "week")
    assert leaf(home) == "live"


@pytest.mark.req("Navigation: one League group, Stats", ac="Players opens on Ranks")
def test_players_opens_on_ranks_after_the_reader_left_it_on_usage(home):
    home.evaluate("navGo('usage')")
    tap_group(home, "home")
    tap_group(home, "scouting")
    assert leaf(home) == "ranks"


@pytest.mark.req("Navigation: one League group, Stats", ac="a view opens its first tab on a fresh visit")
def test_live_opens_on_my_league_after_the_reader_left_it_on_tds(home):
    home.evaluate("navGo('live'); gdSetTab('tds')")
    home.evaluate("navGo('digest')")
    home.evaluate("navGo('live')")
    assert home.evaluate("gdTab()") == "league"


@pytest.mark.req("Navigation: one League group, Stats", ac="a view opens its first tab on a fresh visit")
def test_the_tds_tab_opens_on_the_feed_after_the_reader_left_it_on_by_game(home):
    home.evaluate("navGo('live'); tdSetMode('game')")
    home.evaluate("navGo('digest')")
    home.evaluate("navGo('live')")
    assert home.evaluate("tdMode()") == "feed"


@pytest.mark.req("Navigation: one League group, Stats", ac="a view opens its first tab on a fresh visit")
def test_recap_opens_on_its_first_tab_after_the_reader_left_it_on_scores(home):
    home.evaluate("navGo('weekrecap'); wrSetTab('scores')")
    home.evaluate("navGo('digest')")
    home.evaluate("navGo('weekrecap')")
    assert home.evaluate("wrTab(wrD()) === wrAvail(wrD())[0]") is True


@pytest.mark.req("Navigation: one League group, Stats", ac="a view opens its first tab on a fresh visit")
def test_ranks_opens_on_this_week_after_the_reader_left_it_on_rest_of_season(home):
    home.evaluate("navGo('ranks'); RK_VIEW = 'ros'")
    home.evaluate("navGo('digest')")
    home.evaluate("navGo('ranks')")
    assert home.evaluate("RK_VIEW") == "week"


@pytest.mark.req("Navigation: one League group, Stats", ac="a view opens its first tab on a fresh visit")
def test_slips_opens_on_its_default_kickoff_after_the_reader_left_it_on_another(home):
    home.evaluate("navGo('parlay'); GAL_WIN = 'zzz'")
    home.evaluate("navGo('digest')")
    home.evaluate("navGo('parlay')")
    assert home.evaluate("GAL_WIN") == "ALL"


@pytest.mark.req("Navigation: one League group, Stats", ac="a link that names a tab still opens it")
def test_a_link_that_sets_a_tab_then_opens_the_view_lands_on_that_tab(home):
    """The Digest's TDs card sets Live's tab, then opens Live; leaving the Digest forgets only the Digest's."""
    home.evaluate("gdSetTab('tds'); navGo('live')")
    assert home.evaluate("gdTab()") == "tds"


@pytest.mark.req("Navigation: one League group, Stats", ac="a hash still restores a view")
def test_a_hash_still_opens_the_view_it_names(home):
    home.evaluate("location.hash = '#usage'")
    home.wait_for_function("SURFACE === 'usage'")
    assert leaf(home) == "usage"
