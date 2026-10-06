"""Whose team is "mine" on Live (2026-10-04, David: "Make sure that the site registers the roster(s)
that the user picks as the 'yours' or 'mine'. I don't want it to default to my personal rosters.").

The page is public and David's three teams are three of ~36. A reader's team is the one they picked
(tw-team), else one they follow (tw-follow) that plays in the league on screen (live.js gdMine), and
since 2026-10-05 that team's league is Live's league; with neither, My league asks whose game it is
and the reader picks right there (mine.js gdWhoHTML). The seed
of every other test picks David's Yahoo team and follows his three, so this file opens a bare browser.
"""
import pathlib
import re

import pytest

from test_render import LOAD_MS, LIVE_PLANT as plant, PICKED, SEED, go  # noqa: F401

pytestmark = pytest.mark.render

SRC = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"
# TeamMinh plays David's ESPN team in the fixture's week 2 (tests/fixtures/gameday.json): key
# "espn-teamminh", Jaxon Smith-Njigba (SEA) in its lineup.
MATE = "espn-teamminh"
PLANT_MATE = f"TEAMS['{MATE}'] = Object.assign({{}}, TEAMS.espn, {{key: '{MATE}', name: 'TeamMinh', mate: true, league: 'espn'}});"


def bare(browser, page_file, setup=""):
    """A first visit: no pick, no follow, the clock pinned; `setup` runs once the page has loaded."""
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    page = ctx.new_page()
    page.set_default_timeout(5000)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED.replace(PICKED, ""))
    page.goto(page_file.as_uri(), timeout=LOAD_MS)
    page.wait_for_function("document.getElementById('view').children.length > 0")
    page.evaluate(PLANT_MATE + setup + plant())
    for kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector("[data-gdboard] .gd-tabs", state="attached")   # a phone hides it: the tab row holds the tabs
    return ctx, page, errors


def open_sheet(page, club):
    page.evaluate("""c => { const g = gdWeekGames().find(x => gdSameClub(x.home, c) || gdSameClub(x.away, c));
        gsOpen({event: '1', away: g.away, home: g.home}, null); }""", club)
    page.wait_for_selector("#gamesheet.on")


def test_a_first_visit_has_no_team_of_its_own_on_live(browser, page_file):
    ctx, page, errors = bare(browser, page_file)
    assert page.evaluate("[myTeamLoad(), followLoad()]") == [None, []]
    # My league asks whose game it is, one card listing every league: no score, no lineups, no "you"
    assert page.locator(".gd-who h3").inner_text() == "Whose game are you watching?"
    assert page.locator(".gd-who [data-gdwho]").count() == page.evaluate("GD.leagues.length")
    assert page.locator(".gd-head, .gd-mirror, .gd-strip, .gd-side.mine").count() == 0
    # the NFL tab counts none as yours; the sheet marks none
    page.click("[data-gdtab='games']")
    assert page.locator(".gd-t.mine, .gd-t em").count() == 0
    page.evaluate("gdSetTab('league')")
    open_sheet(page, "DET")
    assert page.locator(".gs-yours .gs-yr").count() == 0 and page.locator(".gs-yours .gs-quiet").count() == 1
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_the_reader_picks_their_team_inside_live_and_stays_there(browser, page_file):
    ctx, page, errors = bare(browser, page_file)
    # a league lists its teams in the same spot; the back link returns to the leagues
    page.click(".gd-who [data-gdwho='espn']")
    assert page.locator(".gd-who [data-pick]").count() >= 2 and page.locator(".gd-who [data-gdwho]").count() == 0
    page.click("[data-gdwhoback]")
    assert page.locator(".gd-who [data-gdwho]").count() == page.evaluate("GD.leagues.length")
    page.click(".gd-who [data-gdwho='espn']")
    page.click(f".gd-who [data-pick='{MATE}']")
    # saved as the team switch saves it, and the reader's matchup is drawn where they are
    assert page.evaluate("[localStorage.getItem('tw-team'), SURFACE, location.hash]") == [MATE, "live", "#live"]
    assert page.locator(".gd-who").count() == 0 and page.locator(".gd-strip .gd-chip.mine").count() == 1
    assert "TeamMinh" in page.locator(".gd-side.a.mine").inner_text()
    ctx.close()
    assert errors == []


def test_the_readers_pick_becomes_the_left_side_with_up_or_down(browser, page_file):
    ctx, page, errors = bare(browser, page_file, f"localStorage.setItem('tw-team', '{MATE}');")
    assert page.evaluate("[myTeamLoad(), followLoad()]") == [MATE, [MATE]]    # the pick is followed until they star more
    assert page.locator(".gd-who").count() == 0
    left = page.locator(".gd-side.a")
    assert "TeamMinh" in left.inner_text() and "mine" in left.get_attribute("class")      # not David's team, who is its opponent
    assert page.locator(".gd-side.b").inner_text().startswith("Purdy Big in Japan")
    assert re.match(r"^(UP|DOWN) \d+\.\d$", page.locator(".gd-lead").inner_text())
    assert re.match(r"^League median \d+\.\d · you [+−]\d+\.\d$", page.locator(".gd-medline").inner_text())
    # his lineup is the one mirrored on the left, benches included
    assert page.locator(".gd-mirror:not(.bn) .gd-h.l", has_text="Smith-Njigba").count() == 1
    assert page.locator(".gd-mirror:not(.bn) .gd-h.r", has_text="St. Brown").count() == 1
    # the Games tab and the sheet count the picked team's players: Smith-Njigba (SEA) is his, St. Brown (DET) David's
    page.click("[data-gdtab='games']")
    assert page.locator(".gd-t.mine em").count() >= 1
    page.evaluate("gdSetTab('league')")
    open_sheet(page, "SEA")
    assert "Smith-Njigba" in page.locator(".gs-yours").inner_text()
    page.keyboard.press("Escape")
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    open_sheet(page, "DET")
    yours = page.locator(".gs-yours").inner_text()                 # TeamMinh's Lions D/ST, not David's St. Brown
    assert "Lions" in yours and "St. Brown" not in yours
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_the_picked_team_decides_the_league_and_a_followed_one_only_without_a_pick(browser, page_file):
    ctx, page, errors = bare(browser, page_file, f"localStorage.setItem('tw-team', '{MATE}');")
    # the pick plays in ESPN; following a Yahoo team does not move Live off it
    page.evaluate("localStorage.setItem('tw-follow', JSON.stringify(['yahoo'])); paintLive()")
    assert page.evaluate("gdLeague().key") == "espn" and "TeamMinh" in page.locator(".gd-side.a.mine").inner_text()
    # with no pick, the first followed team that plays here decides
    page.evaluate("localStorage.removeItem('tw-team'); paintLive()")
    assert page.evaluate("[myTeamLoad(), followLoad(), gdLeague().key]") == [None, ["yahoo"], "yahoo"]
    assert page.locator(".gd-who").count() == 0 and page.locator(".gd-side.a.mine").count() == 1
    ctx.close()
    assert errors == []


def test_nothing_followed_is_nothing_not_davids_teams(browser, page_file):
    ctx, page, errors = bare(browser, page_file)
    assert page.evaluate("followLoad()") == []
    page.evaluate("localStorage.setItem('tw-team', 'yahoo')")
    assert page.evaluate("followLoad()") == ["yahoo"]                # the picked team, and only it
    page.evaluate("followToggle('espn')")
    assert page.evaluate("followLoad()") == ["yahoo", "espn"]
    ctx.close()
    assert errors == []


def test_the_switch_still_lets_a_reader_with_nothing_followed_pick(browser, page_file):
    ctx, page, errors = bare(browser, page_file, "localStorage.setItem('tw-team', 'yahoo'); localStorage.setItem('tw-follow', '[]');")
    # David's Yahoo team is picked and nothing is followed: the header bar's team switch (a phone's; the
    # score head shows the plain name there) opens on that team's league
    page.click("#hdrswitch [data-tsbtn]")
    page.wait_for_selector("#hdrswitch .ts-menu:not([hidden]) .ts-back")
    assert page.locator("#hdrswitch .ts-menu .ts-item[data-k='yahoo']").count() == 1   # the league's teams, each pickable
    page.click("#hdrswitch .ts-back")
    assert page.locator("#hdrswitch .ts-empty").count() == 1                      # nothing followed: the menu says so
    assert page.locator("#hdrswitch .ts-league").count() >= 1                     # and every league is one tap away
    page.click("#hdrswitch .ts-league[data-tsleague='espn']")
    # The drill-in redraws the menu: wait for the league's own list, then take a team that is on screen
    page.wait_for_selector("#hdrswitch .ts-menu:not([hidden]) .ts-back")
    page.locator("#hdrswitch .ts-menu .ts-item[data-k^='espn-']:visible").first.click()
    assert page.evaluate("localStorage.getItem('tw-team')") != "yahoo"
    assert page.evaluate("[SURFACE, gdLeague().key]") == ["live", "espn"]     # the reader stays on Live
    ctx.close()
    assert errors == []


def test_no_live_view_reads_davids_team_as_the_readers():
    """lg.me stays in the data (the build and its tests use it); the Live files go through gdMine."""
    for path in (SRC / "surface" / "live").glob("*.js"):
        assert not re.search(r"\.me\b", path.read_text(encoding="utf-8")), path.name
