"""Whose team is "mine" on Live (2026-10-04, David: "Make sure that the site registers the roster(s)
that the user picks as the 'yours' or 'mine'. I don't want it to default to my personal rosters.").

The page is public and David's three teams are three of ~36. A reader's team is the one they picked
(tw-team), else one they follow (tw-follow) that plays in the league on screen (live.js gdMine);
with neither, no side is theirs: neutral chips, no "you", and one line that opens My teams. The seed
of every other test picks David's Yahoo team and follows his three, so this file opens a bare browser.
"""
import pathlib
import re

import pytest

from test_render import LIVE_PLANT as plant, PICKED, SEED, go  # noqa: F401

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
    page.goto(page_file.as_uri())
    page.wait_for_function("document.getElementById('view').children.length > 0")
    page.evaluate(PLANT_MATE + setup + plant())
    for kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-tabs")
    return ctx, page, errors


def open_sheet(page, club):
    page.evaluate("""c => { const g = gdWeekGames().find(x => gdSameClub(x.home, c) || gdSameClub(x.away, c));
        gsOpen({event: '1', away: g.away, home: g.home}, null); }""", club)
    page.wait_for_selector("#gamesheet.on")


def test_a_first_visit_has_no_team_of_its_own_on_live(browser, page_file):
    ctx, page, errors = bare(browser, page_file)
    assert page.evaluate("[myTeamLoad(), followLoad()]") == [None, []]
    # no "Your lineup", no UP / DOWN: the game is the league's first, its chip says who leads and nothing else
    assert page.locator(".gd-side.mine, .gd-lead.up, .gd-lead.dn").count() == 0
    assert re.match(r"^(BY \d+\.\d|TIED)$", page.locator(".gd-lead").inner_text())
    assert page.locator(".gd-pick").inner_text() == "Pick your team to see your matchup"
    assert re.match(r"^League median \d+\.\d$", page.locator(".gd-medline").inner_text())   # no "you" gap
    assert not page.evaluate("document.querySelector('.gd-medline').classList.contains('up') || document.querySelector('.gd-medline').classList.contains('dn')")
    # the Games tab counts none as yours; the League tab and the sheet mark none
    page.click("[data-gdtab='games']")
    assert page.locator(".gd-t.mine, .gd-t em").count() == 0
    page.click("[data-gdtab='league']")
    assert page.locator(".gd-g.mine, .gd-l.mine").count() == 0
    page.evaluate("gdSetTab('matchup')")
    open_sheet(page, "DET")
    assert page.locator(".gs-yours .gs-yr").count() == 0 and page.locator(".gs-yours .gs-quiet").count() == 1
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_the_pick_line_opens_my_teams_where_the_reader_picks(browser, page_file):
    ctx, page, errors = bare(browser, page_file)
    page.click(".gd-pick")
    page.wait_for_selector("#view[data-view='pick'] .tp-team")        # nobody has picked: the picker
    key = page.locator(".tp-team").first.get_attribute("data-pick")
    page.click(".tp-team >> nth=0")
    assert page.evaluate("localStorage.getItem('tw-team')") == key
    ctx.close()
    assert errors == []


def test_the_readers_pick_becomes_the_left_side_with_up_or_down(browser, page_file):
    ctx, page, errors = bare(browser, page_file, f"localStorage.setItem('tw-team', '{MATE}');")
    assert page.evaluate("[myTeamLoad(), followLoad()]") == [MATE, [MATE]]    # the pick is followed until they star more
    assert page.locator(".gd-pick").count() == 0
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
    page.evaluate("gdSetTab('matchup')")
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


def test_a_team_in_another_league_is_found_there_only_when_followed(browser, page_file):
    ctx, page, errors = bare(browser, page_file, f"localStorage.setItem('tw-team', '{MATE}');")
    page.click("[data-gdleague='yahoo']")                          # the pick plays in ESPN: no team of theirs here
    assert page.locator(".gd-pick").count() == 1 and page.locator(".gd-side.mine").count() == 0
    page.evaluate("localStorage.setItem('tw-follow', JSON.stringify(['yahoo'])); paintLive()")   # follow another in this league
    assert page.locator(".gd-pick").count() == 0 and page.locator(".gd-side.a.mine").count() == 1
    assert page.evaluate("followLoad()") == ["yahoo"]
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
    # David's Yahoo team is picked, so ESPN has no team of the reader's: its pick line opens the team
    # switch on that league
    page.click(".gd-pick")
    page.wait_for_selector(".ts-menu:not([hidden]) .ts-back")
    assert page.locator(".ts-menu .ts-item[data-k]").count() >= 2      # the league's teams, each pickable
    page.click(".ts-back")
    assert page.locator(".ts-empty").count() == 1                      # nothing followed: the menu says so
    assert page.locator(".ts-league").count() >= 1                     # and every league is one tap away
    page.click(".ts-league[data-tsleague='espn']")
    # The drill-in redraws the menu: wait for the league's own list, then take a team that is on screen
    page.wait_for_selector(".ts-menu:not([hidden]) .ts-back")
    page.locator(".ts-menu .ts-item[data-k^='espn-']:visible").first.click()
    assert page.evaluate("localStorage.getItem('tw-team')") != "yahoo"
    ctx.close()
    assert errors == []


def test_no_live_view_reads_davids_team_as_the_readers():
    """lg.me stays in the data (the build and its tests use it); the Live files go through gdMine."""
    for path in (SRC / "surface" / "live").glob("*.js"):
        assert not re.search(r"\.me\b", path.read_text(encoding="utf-8")), path.name
