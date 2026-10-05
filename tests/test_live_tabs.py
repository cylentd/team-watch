"""This week > Live, the tabs and the mirrored lineups (2026-10-04, storyboard
https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV, option A): Matchup, Games, TDs, League in one
segmented control; the Matchup tab draws one row per starter slot, my starter against theirs.
Browser tests on the week 2 fixture (tests/fixtures/gameday.json): SF's game is on, DET's has not
started, every other game is final."""
import re

import pytest

from test_render import LIVE_PLANT as plant, browser, go, open_page  # noqa: F401  (the suite's one Chromium)

pytestmark = pytest.mark.render

PHONE = (360, 780)


def live(browser, page_file, viewport=PHONE, states=None):
    ctx, page, errors = open_page(browser, page_file, viewport)
    page.evaluate(plant(states))
    for kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-tabs")
    return ctx, page, errors


def test_four_tabs_and_the_matchup_is_a_mirrored_row_per_starter_slot(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    assert page.locator(".gd-tabs button").all_inner_texts()[:1] == ["Matchup"]
    names = [re.sub(r"\d+$", "", s).strip() for s in page.locator(".gd-tabs button").all_inner_texts()]
    assert names == ["Matchup", "Games", "TDs", "League"]
    assert page.locator(".gd-tabs [aria-pressed='true']").get_attribute("data-gdtab") == "matchup"
    # nine starters in my ESPN lineup: nine rows, each a slot pill between two halves
    starters = page.evaluate("gdLeague().teams[gdLeague().me].lineup.filter(gdStarter).length")
    rows = page.locator(".gd-mirror:not(.bn) .gd-mr")
    assert starters == 9 and rows.count() == 9
    assert rows.evaluate_all("rs => rs.every(r => r.querySelectorAll('.gd-h').length === 2 && r.querySelectorAll('.gd-sl').length === 1)")
    # every half with a game carries a clock button that opens the game sheet on his game
    clocks = page.locator(".gd-mirror .gd-ck[data-gdnfl]")
    assert clocks.count() >= 1      # the fixture schedule holds only some of week 2's clubs
    assert clocks.evaluate_all("bs => bs.every(b => b.tagName === 'BUTTON' && /^[^,]*,[A-Z]+,[A-Z]+$/.test(b.dataset.gdnfl) && b.dataset.gdfocus)")
    assert page.locator(".gd-mirror button button").count() == 0            # never a button in a button
    # the slot pill wears the position's colour; FLEX stays neutral
    col = lambda slot: page.locator(f".gd-mr .gd-sl:text-is('{slot}')").first.evaluate("e => getComputedStyle(e).color")
    assert len({col("QB"), col("RB"), col("TE"), col("WR")}) == 4
    assert page.locator(".gd-sl.qb").count() >= 1 and page.locator(".gd-sl.def").count() >= 1
    assert page.locator(".gd-mr .gd-sl:text-is('FLEX')").first.get_attribute("class").strip() == "gd-sl"
    # the median line sits under the score in a league that pays the top half
    assert re.match(r"^League median \d+\.\d · you [+−]\d+\.\d$", page.locator(".gd-medline").inner_text())
    # benches are shut until the Benches row opens them, mirrored the same way
    assert page.locator(".gd-mirror.bn").count() == 0
    page.click("[data-gdbench]")
    assert page.locator(".gd-mirror.bn .gd-mr").count() >= 1
    # a row's name opens his profile; a row's clock opens that game's sheet
    page.locator(".gd-mirror .gd-nb").first.click()
    page.wait_for_selector("#modal.on")
    page.keyboard.press("Escape")
    page.locator(".gd-mirror .gd-ck[data-gdnfl]").first.click()
    page.wait_for_selector("#gamesheet.on")
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_a_phone_fits_the_score_and_nine_starters_in_780px(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    page.wait_for_selector(".gd-mirror .gd-mr")
    m = page.evaluate("""() => {
      const rows = [...document.querySelectorAll('.gd-mirror:not(.bn) .gd-mr')];
      const box = e => e.getBoundingClientRect();
      const at = s => { const e = document.querySelector(s); return e ? [Math.round(box(e).top + scrollY), Math.round(box(e).height)] : null; };
      return {last: Math.round(box(rows[8]).bottom + scrollY), tallest: Math.round(Math.max(...rows.map(r => box(r).height))),
              head: Math.round(box(document.querySelector('.gd-head')).top + scrollY),
              parts: {tabs: at('.gd-tabs'), leagues: at('.gd-leagues'), head: at('.gd-head'), median: at('.gd-medline'), rows: at('.gd-mirror')}};
    }""")
    ctx.close()
    print("9th starter row bottom:", m["last"], "tallest row:", m["tallest"], "parts [top, height]:", m["parts"])
    assert m["last"] <= 780, m
    assert m["tallest"] <= 52, m
    assert errors == []


def test_games_tab_lists_every_game_live_first_and_a_tile_opens_the_sheet(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    n_games = page.evaluate("gdWeekGames().length")
    assert n_games >= 3
    # the first game of the week is on, the second has not kicked off, the rest are final
    page.evaluate("""() => {
      const gs = gdWeekGames(), st = GD_STATS.games;
      gs.forEach((g, i) => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = i === 0 ? "in_game" : i === 1 ? "pre_game" : "complete"; });
      paintLive();
    }""")
    # Games carries the lime count of games on now
    assert page.locator("[data-gdtab='games'] .gd-n").inner_text() == "1"
    assert page.locator("[data-gdtab='games'] .gd-n").get_attribute("aria-label") == "1 game live now"
    page.evaluate("""() => { const st = GD_STATS.games; gdWeekGames().slice(0, 2).forEach(g => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = "in_game"; }); paintLive(); }""")
    assert page.locator("[data-gdtab='games'] .gd-n").get_attribute("aria-label") == "2 games live now"
    page.evaluate("""() => { const st = GD_STATS.games; gdWeekGames().forEach((g, i) => { for (const c of gdCodes(g.home).concat(gdCodes(g.away))) st[c] = i === 0 ? "in_game" : i === 1 ? "pre_game" : "complete"; }); paintLive(); }""")
    page.click("[data-gdtab='games']")
    assert page.evaluate("localStorage.getItem('tw-live-tab')") == "games"
    assert page.locator(".gd-mirror").count() == 0 and page.locator(".gd-nfl, .gd-now").count() == 0
    tiles = page.locator(".gd-tiles .gd-t")
    assert tiles.count() == n_games
    kinds = tiles.evaluate_all("ts => ts.map(t => t.classList.contains('in') ? 'in' : t.classList.contains('pre') ? 'pre' : 'post')")
    assert kinds[0] == "in" and kinds[1] == "pre" and set(kinds[2:]) == {"post"}
    # a tile with my starters has a lime edge and says how many; two tiles side by side on a phone
    mine = page.locator(".gd-t.mine")
    assert mine.count() >= 1 and re.match(r"^\d+ yours$", mine.first.locator(".gd-ts em").inner_text())
    lime = page.evaluate("(() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.body).getPropertyValue('--lime'); document.body.append(d); const c = getComputedStyle(d).color; d.remove(); return c; })()")
    assert mine.first.evaluate("e => getComputedStyle(e).borderTopColor") == lime
    xs = tiles.evaluate_all("ts => ts.slice(0, 2).map(t => Math.round(t.getBoundingClientRect().left))")
    assert xs[0] != xs[1]
    tiles.first.click()
    page.wait_for_selector("#gamesheet.on")
    page.keyboard.press("Escape")
    ctx.close()
    assert errors == []


def test_league_tab_lists_every_matchup_and_a_tap_opens_it_in_the_matchup_tab(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    n = page.evaluate("gdLeague().games.length")
    page.click("[data-gdtab='league']")
    rows = page.locator(".gd-games .gd-g")
    assert rows.count() == n and n >= 2
    # a compact row: both names, both scores, the leader bright
    assert rows.evaluate_all("rs => rs.every(r => r.querySelectorAll('.gd-gn').length === 2 && r.querySelectorAll('.gd-gp').length === 2)")
    assert rows.evaluate_all("rs => rs.every(r => r.getBoundingClientRect().height < 64)")
    assert page.locator(".gd-ladder .gd-median:not(.quiet)").count() == 1
    assert page.locator(".gd-mirror").count() == 0
    other = page.locator(".gd-g:not(.mine)").first
    other.click()
    assert page.evaluate("localStorage.getItem('tw-live-tab')") == "matchup"
    assert page.locator(".gd-mirror .gd-mr").count() >= 1
    assert re.match(r"^BY \d+\.\d$|^TIED$", page.locator(".gd-lead").inner_text())
    ctx.close()
    assert errors == []


def test_the_league_chips_show_only_on_the_tabs_that_belong_to_a_league(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    assert page.evaluate("GD.leagues.length") >= 2, "the fixture needs two leagues for chips to draw"
    chips = lambda: page.locator(".gd-leagues button").count()
    shown = {}
    for tab in ("matchup", "games", "tds", "league"):
        page.click(f"[data-gdtab='{tab}']")
        shown[tab] = chips()
    ctx.close()
    n = shown["matchup"]
    # Games and TDs are NFL-wide: no league to pick. Matchup and League are one league's.
    assert n >= 2 and shown == {"matchup": n, "games": 0, "tds": 0, "league": n}
    assert errors == []


def test_the_tab_survives_a_reload_of_the_view_and_a_blocked_store_still_switches(browser, page_file):
    ctx, page, errors = live(browser, page_file)
    page.click("[data-gdtab='tds']")
    assert page.locator("[data-gdtab='tds']").get_attribute("aria-pressed") == "true"
    # the TDs tab hosts surface/live/tds.js, or an empty state while that file is absent
    assert page.locator(".gd-card").count() >= 1 or page.locator(".state-empty").count() == 1
    assert page.evaluate("location.hash") in ("", "#live")                  # the tab is never in the hash
    page.click("[data-gdtab='matchup']")
    # another view sends the reader to a tab by setting it, then opening #live
    page.evaluate("localStorage.setItem('tw-live-tab', 'league'); render()")
    assert page.locator(".gd-games").count() == 1
    page.evaluate("localStorage.setItem('tw-live-tab', 'nonsense'); render()")
    assert page.locator(".gd-mirror").count() >= 1                           # anything else is the default
    page.evaluate("Object.defineProperty(window, 'localStorage', {get(){ throw new Error('blocked'); }})")
    page.click("[data-gdtab='games']")
    assert page.locator(".gd-tiles").count() == 1
    ctx.close()
    assert errors == []


def test_desktop_keeps_the_rows_one_reading_width(browser, page_file):
    ctx, page, errors = live(browser, page_file, (1400, 900))
    w = page.evaluate("Math.round(document.querySelector('.gd-mirror').getBoundingClientRect().width)")
    ctx.close()
    assert 400 < w <= 760
    assert errors == []
