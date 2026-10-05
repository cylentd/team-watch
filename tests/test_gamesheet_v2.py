"""The game sheet, v2 (2026-10-04, storyboard https://claude.ai/artifact/JrM6hBMrAL2hjFzYPgKitV): full
screen on a phone, the players of mine in the game pinned under the scoreboard, three tabs under them,
and a follow star that outlives the sheet."""
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))

import pytest  # noqa: E402

from test_render import LIVE_PLANT as plant, browser, go, open_page  # noqa: E402,F401  (the suite's one Chromium)

SUMMARY = json.loads((REPO / "tests" / "fixtures" / "data" / "espn_summary.json").read_text(encoding="utf-8"))
BOX = json.loads((REPO / "tests" / "fixtures" / "data" / "sleeper_box.json").read_text(encoding="utf-8"))

FILL = """([s, b]) => { GS_GAME = gsShape(s); GS_BOX = {box: b}; GS_ERR = ""; gsPaint(); }"""
FOLLOWED = "JSON.parse(localStorage.getItem('tw-gs-follow.2') || '{}')"


def open_sheet(page, **extra):
    page.evaluate(plant({"DET": "in_game", "SEA": "in_game"}))
    for _kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-mr")
    page.evaluate("g => gsOpen(g, null)", {"event": "1", "away": "DET", "home": "BUF", **extra})
    page.wait_for_selector("#gamesheet.on")
    page.evaluate(FILL, [SUMMARY, BOX])


def visible(page, sel):
    return page.locator(sel).evaluate_all("els => els.filter(e => e.offsetParent !== null).length")


@pytest.mark.render
def test_a_phone_gets_the_sheet_full_screen_with_three_tabs(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    open_sheet(page)
    box = page.evaluate("(() => { const r = document.getElementById('gamesheet').getBoundingClientRect(); return [r.top, r.height, innerHeight]; })()")
    assert box[0] == 0 and box[1] == box[2] == 780
    tabs = page.locator(".gs-tab")
    assert tabs.all_inner_texts() == ["Plays", "Box score", "Top scorers"]
    # Box score is the default; each tab shows its own card and no other
    for tab, card in (("box", ".gs-box"), ("plays", ".gs-plays"), ("top", ".gs-top")):
        page.click(f"[data-gstab='{tab}']")
        assert page.locator(f"[data-gstab='{tab}']").get_attribute("aria-selected") == "true"
        assert visible(page, ".gs-panes > .gs-card") == 1 and visible(page, card) == 1
    assert visible(page, ".gs-top .gs-star") == 5            # any scorer can be followed from here
    # the last tab is remembered through a close and a reopen, and the pinned block never scrolls away
    page.keyboard.press("Escape")
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    page.evaluate("gsOpen({event: '1', away: 'DET', home: 'BUF'}, null)")
    page.wait_for_selector("#gamesheet.on")
    assert page.locator("[data-gstab='top']").get_attribute("aria-selected") == "true"
    assert visible(page, ".gs-yours") == 1 and visible(page, ".gs-tabs") == 1
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_phone_sheet_scrolls_as_one_body_with_the_tabs_stuck_to_its_top(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    open_sheet(page)
    # a dozen followed players make the pinned block taller than a third of the screen
    page.evaluate("""() => { GS_FOLLOW = Object.fromEntries(Array.from({length: 12}, (_, i) =>
        ['f' + i, {id: 'f' + i, sid: 'f' + i, slug: 'f' + i, n: 'Fake Player' + i, pos: 'WR', team: 'DET'}])); gsPaint(); }""")
    page.click("[data-gstab='plays']")
    m = page.evaluate("""() => {
      const d = document.getElementById('gamesheet'), main = d.querySelector('.gs-main'), yl = d.querySelector('.gs-yl');
      const scrollers = [...d.querySelectorAll('*')].filter(e => /auto|scroll/.test(getComputedStyle(e).overflowY)).map(e => e.className);
      const before = d.querySelector('.gs-tabs').getBoundingClientRect().top;
      main.scrollTop = main.scrollHeight;
      return {scrollers, rows: yl.querySelectorAll('.gs-yr').length, ylScroll: yl.scrollHeight, ylClient: yl.clientHeight,
              mainScrolls: main.scrollHeight > main.clientHeight, scrolled: main.scrollTop > 0,
              tabsTop: Math.round(d.querySelector('.gs-tabs').getBoundingClientRect().top), mainTop: Math.round(main.getBoundingClientRect().top), before: Math.round(before)};
    }""")
    ctx.close()
    assert m["scrollers"] == ["gs-main"], m                  # one scroller, not the pinned block and the pane as well
    assert m["rows"] >= 12 and m["ylScroll"] == m["ylClient"], m   # every pinned row shows, none behind a scrollbar
    assert m["mainScrolls"] and m["scrolled"], m
    assert m["tabsTop"] == m["mainTop"] < m["before"], m     # the tab bar rode up and stuck to the top of the scroll
    assert errors == []


@pytest.mark.render
def test_opening_the_sheet_drops_the_follow_keys_of_other_weeks(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate("""() => { localStorage.setItem('tw-gs-follow.1', '{"x":{}}'); localStorage.setItem('tw-gs-follow.2', '{}');
        localStorage.setItem('tw-follow', 'keep'); }""")
    open_sheet(page)
    keys = page.evaluate("Object.keys(localStorage).filter(k => k.startsWith('tw-gs-follow.') || k === 'tw-follow').sort()")
    ctx.close()
    assert keys == ["tw-follow", "tw-gs-follow.2"]
    assert errors == []


@pytest.mark.render
def test_yours_in_this_game_lists_my_players_and_leads_with_the_one_i_came_from(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    open_sheet(page, slug="amonra-st-brown")
    rows = page.locator(".gs-yours .gs-yr")
    assert rows.count() >= 2                                   # St. Brown and Goff (DET) in the fixture's espn league
    assert "St. Brown" in rows.first.inner_text() and "focus" in rows.first.get_attribute("class")
    assert page.locator(".gs-yr.focus").count() == 1
    assert "Goff" in page.locator(".gs-yours").inner_text()
    assert page.locator(".gs-yours svg").count() >= 2          # the star is a drawn shape, not a glyph
    # no player of mine is in this game: a sentence says so
    page.evaluate("GS = {event: '', away: 'AAA', home: 'BBB'}; gsPaint()")
    assert page.locator(".gs-yours .gs-quiet").count() == 1
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_star_follows_a_player_and_survives_closing_the_sheet(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    open_sheet(page, slug="amonra-st-brown")
    assert page.evaluate(FOLLOWED) == {}
    star = page.locator(".gs-yr.focus .gs-star")
    assert star.get_attribute("aria-pressed") == "false"
    star.click()
    assert list(page.evaluate(FOLLOWED)) == ["7547"]          # tw-gs-follow.<week>, never tw-follow
    assert page.evaluate("localStorage.getItem('tw-follow')") is None
    page.keyboard.press("Escape")
    page.wait_for_selector("#gamesheet:not(.on)", state="attached")
    page.evaluate("gsOpen({event: '1', away: 'DET', home: 'BUF'}, null)")     # no slug now
    page.wait_for_selector("#gamesheet.on")
    page.evaluate(FILL, [SUMMARY, BOX])
    assert page.locator(".gs-yours [data-gsfollow='7547']").get_attribute("aria-pressed") == "true"
    # a player in the top scorers follows from there and joins the pinned block
    before = page.locator(".gs-yours .gs-yr").count()
    page.click("[data-gstab='top']")
    scorer = page.locator(".gs-top .gs-star[aria-pressed='false']").first
    sid = scorer.get_attribute("data-gsfollow")
    scorer.click()
    assert sid in page.evaluate(FOLLOWED)
    assert page.locator(f".gs-yours [data-gsfollow='{sid}']").count() == 1
    assert page.locator(".gs-yours .gs-yr").count() >= before
    # tapping it again lets him go
    page.locator(f".gs-top [data-gsfollow='{sid}']").click()
    assert sid not in page.evaluate(FOLLOWED)
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_scoreboard_clock_stands_in_until_espns_summary_loads(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate(plant({"DET": "in_game", "BUF": "in_game"}))
    page.evaluate("""() => { const g = {state: 'in', q: 3, clock: '4:12', half: false, detail: '', clubs: ['DET', 'BUF']};
        GD_CLOCK = {DET: g, BUF: g}; }""")
    for _kind, sel in go("live"):
        page.click(sel)
    page.wait_for_selector(".gd-mr")
    page.evaluate("gsOpen({event: '1', away: 'DET', home: 'BUF'}, null)")
    page.wait_for_selector("#gamesheet.on")
    page.evaluate("GS_GAME = null; GS_ERR = ''; gsPaint()")
    assert "Q3 4:12" in page.locator(".gs-mid").inner_text()
    ctx.close()
    assert errors == []
