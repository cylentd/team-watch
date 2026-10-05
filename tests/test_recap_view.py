"""This week > Recap (leaf `weekrecap`, 2026-10-05, storyboard option C,
https://claude.ai/artifact/HVdkEL4YbiBKUJ3QbLH9gf): the banner, a Players / Scores / Claude bar, one tab's
cards. Browser tests on the week 4 recap fixture (tests/fixtures/data/recap/2026-w04.json): 8 of 16 games
final, Claude 5 of 8 on winners. The data cut is tests/test_recap_data.py's; this proves the page."""
import json
import re

import pytest

from test_render import drive, go, open_page  # noqa: F401

pytestmark = pytest.mark.render

PHONE, DESK = (360, 800), (1100, 900)
SIDEWAYS = "document.scrollingElement.scrollWidth - innerWidth"


def recap(browser, page_file, viewport=PHONE, tab=None, prep=""):
    ctx, page, errors = open_page(browser, page_file, viewport)
    if prep:
        page.evaluate(prep)
    drive(page, go("weekrecap") + ([("click", f"[data-wrtab='{tab}']")] if tab else []))
    return ctx, page, errors


@pytest.fixture(scope="module")
def _phone(browser, page_file):
    """One 360px Recap page for the tests that only pick a tab and read: loaded once per file per
    worker. A test's only change is the tab, and the next test picks its own."""
    ctx, page, errors = recap(browser, page_file)
    assert errors == []                 # whatever the load raised fails here, not lost to a later clear
    yield page, errors
    ctx.close()


@pytest.fixture
def phone(_phone):
    page, errors = _phone
    left, errors[:] = list(errors), []  # each test answers for its own page errors only,
    assert left == []                   # and an error raised or left over since the last one fails this
    return page, errors


def on_tab(phone, tab):
    page, errors = phone
    drive(page, [("click", f"[data-wrtab='{tab}']")])
    assert page.locator(".wr-body").get_attribute("data-wrtabname") == tab
    return page, errors


def page_with(page_file, mutate):
    """A copy of the built page, beside the original (so its heads resolve), whose LIVE_RECAP is
    mutate(block); mutate returns the new value, None for the empty state. LIVE_RECAP is a const, so the
    page is rewritten, not patched at runtime."""
    html = page_file.read_text(encoding="utf-8")
    m = re.search(r"const LIVE_RECAP = (.*?);\n", html)
    new = json.dumps(mutate(json.loads(m.group(1))))
    out = page_file.with_name("recap-variant.html")
    out.write_text(html[:m.start()] + f"const LIVE_RECAP = {new};\n" + html[m.end():], encoding="utf-8")
    return out


def test_three_tabs_open_on_players_and_the_choice_is_kept(browser, page_file):
    ctx, page, errors = recap(browser, page_file)
    names = page.locator(".gd-tabs button").all_inner_texts()
    assert names == ["Players", "Scores", "Claude"]
    assert page.locator(".gd-tabs [aria-pressed='true']").get_attribute("data-wrtab") == "players"
    assert page.locator(".wr-leaders").count() == 1 and page.locator(".wr-games").count() == 0
    page.click("[data-wrtab='scores']")
    assert page.locator(".wr-games").count() == 1 and page.locator(".wr-leaders").count() == 0
    assert page.locator(".gd-tabs [aria-pressed='true']").get_attribute("data-wrtab") == "scores"
    # the banner and the bar hold still: a tab repaints the body, not the view
    assert page.evaluate("document.querySelector('.wr-body').dataset.wrtabname") == "scores"
    assert page.evaluate("localStorage.getItem('tw-recap-tab')") == "scores"
    page.reload()
    page.wait_for_selector(".wr-body")
    assert page.locator(".gd-tabs [aria-pressed='true']").get_attribute("data-wrtab") == "scores"
    page.click("[data-wrtab='claude']")
    assert page.locator(".wr-claude").count() == 1
    ctx.close()
    assert errors == []


def test_the_banner_calls_the_top_scorer_by_yards_and_touchdowns_never_points(browser, page_file):
    ctx, page, errors = recap(browser, page_file)
    head = page.locator(".wr-lead .dg-lead-h").inner_text()
    assert re.search(r"Allen .*285 yards and 4 TDs", head), head
    assert "point" not in head.lower() and "pts" not in head.lower()
    assert page.locator(".wr-when").inner_text().upper() == "WEEK 4 · TOP SCORE SO FAR"     # 8 of 16 final: so far
    pills = page.locator(".wr-lead .dg-lpill")
    assert pills.count() >= 2                                       # the box line under it: passing, rushing
    assert not any("pts" in p for p in pills.all_inner_texts())    # no fantasy points in the pills either
    page.locator(".wr-go").click()
    page.wait_for_selector("#modal.on")
    ctx.close()
    assert errors == []


def test_players_leaders_lists_and_touchdowns(browser, page_file):
    ctx, page, errors = recap(browser, page_file)
    blocks = page.locator(".wr-bp")
    assert blocks.locator("h4").all_inner_texts() == ["QB", "RB", "WR", "TE", "K", "DST"]
    assert all(n == 3 for n in blocks.evaluate_all("bs => bs.map(b => b.querySelectorAll('.wr-r').length)"))
    # a kicker's day is his box line; a defense has no page to open
    assert "FG" in page.locator(".wr-bp:has(h4:text-is('K')) .wr-day").first.inner_text()
    assert page.locator(".wr-bp:has(h4:text-is('DST')) button").count() == 0
    # the three lists, one open on a phone
    assert [re.sub(r"\s+\d+$", "", s) for s in page.locator(".wr-lt").all_inner_texts()] == ["Smashed", "Busts", "Left hurt"]
    assert page.locator(".wr-lp:not([data-off])").count() == 1
    assert page.locator(".wr-lp:not([data-off])").get_attribute("data-wrpanel") == "smashed"
    page.click("[data-wrlist='left']")
    assert page.locator(".wr-lp:not([data-off])").get_attribute("data-wrpanel") == "left"
    assert "Concussion" in page.locator(".wr-lp[data-wrpanel='left']").inner_text()
    # touchdowns: top five, then Show all; a dot per rushing, receiving or return score
    assert page.locator(".wr-tdl .wr-lr").count() == 5
    page.click("[data-wrtds]")
    assert page.locator(".wr-tdl .wr-lr").count() == 19 and page.locator("[data-wrtds]").inner_text() == "Show fewer"
    dots = page.locator(".wr-tdl .wr-lr").evaluate_all("rs => rs.map(r => r.querySelectorAll('.wr-dots i').length)")
    assert dots == sorted(dots, reverse=True) and min(dots) >= 1
    assert page.locator(".wr-foot").inner_text().startswith("Most passing TDs: J. Allen, D. Prescott, A. Rodgers, 3 each")
    assert page.evaluate(SIDEWAYS) <= 0
    page.locator(".wr-tdl .wr-lr").first.click()
    page.wait_for_selector("#modal.on")
    ctx.close()
    assert errors == []


def test_desktop_lays_the_three_lists_open_side_by_side(browser, page_file):
    ctx, page, errors = recap(browser, page_file, DESK)
    assert page.locator(".wr-ltabs").is_hidden()
    panels = page.locator(".wr-lp")
    assert panels.count() == 3 and panels.evaluate_all("ps => ps.every(p => p.offsetParent !== null)")
    tops = panels.evaluate_all("ps => ps.map(p => Math.round(p.getBoundingClientRect().top))")
    assert len(set(tops)) == 1, tops
    xs = panels.evaluate_all("ps => ps.map(p => Math.round(p.getBoundingClientRect().left))")
    assert xs == sorted(xs) and len(set(xs)) == 3
    assert page.locator(".wr-lh").first.is_visible()
    # the leaders sit three across, and nothing's label sits more than 560px from its value
    cols = page.evaluate("getComputedStyle(document.querySelector('.wr-board')).gridTemplateColumns.split(' ').length")
    assert cols == 3
    far = page.evaluate("""[...document.querySelectorAll('.wr-r, .wr-lr, .wr-g')].filter(r => {
      const n = r.querySelector('.wr-n, .wr-ln, .wr-sc'), v = r.querySelector('.wr-pts, .wr-nums, .wr-dots, .wr-pk');
      return n && v && v.getBoundingClientRect().right - n.getBoundingClientRect().left > 560; }).length""")
    assert far == 0
    assert page.evaluate(SIDEWAYS) <= 0
    ctx.close()
    assert errors == []


def test_scores_group_by_window_with_the_pick_and_its_grade(phone):
    page, errors = on_tab(phone, "scores")
    heads = page.locator(".wr-wh span").all_inner_texts()
    assert [h.upper() for h in heads] == ["THURSDAY NIGHT", "SUNDAY MORNING", "SUNDAY EARLY", "SUNDAY LATE", "SUNDAY NIGHT", "MONDAY NIGHT"]
    assert page.locator(".wr-wh em").first.inner_text() == "8:15 PM ET"
    assert page.locator(".wr-g").count() == 16
    assert page.locator(".wr-mk.hit").count() == 5 and page.locator(".wr-mk.miss").count() == 3     # Claude 5 of 8 on winners
    assert re.fullmatch(r"Claude picked 5 of 8 winners · 5–3 vs spread", page.locator(".wr-strip").inner_text())
    # a final's winner is bold; a game still to play shows its kickoff in Eastern time and the pick
    assert page.locator(".wr-g:has-text('PIT 24') .wr-sc b").inner_text() == "CLE 27"
    assert page.locator(".wr-g:has-text('ATL') .wr-pk").inner_text() == "8:15 PM ET · Picked ATL"
    assert page.locator(".wr-g:has-text('ATL') .wr-mk").count() == 0
    assert page.evaluate(SIDEWAYS) <= 0
    assert errors == []


def test_a_game_opens_previews_dossier_only_when_preview_holds_the_same_week(browser, page_file):
    ctx, page, errors = recap(browser, page_file, tab="scores")
    assert page.locator("button.wr-g").count() == 0           # the fixture's Preview is week 2
    page.evaluate("LIVE_PREVIEW.week = LIVE_RECAP.week; wrPaint(document.getElementById('view'))")
    buttons = page.locator("button.wr-g")
    assert buttons.count() >= 1
    page.locator("button.wr-g:has-text('PIT 24')").click()
    page.wait_for_function("SURFACE === 'preview'")
    assert page.evaluate("SURFACE") == "preview" and page.evaluate("pvGames()[PV_I].away + pvGames()[PV_I].home") == "PITCLE"
    ctx.close()
    assert errors == []


def test_claude_tab_tiles_calls_and_the_every_week_link(browser, page_file):
    ctx, page, errors = recap(browser, page_file, tab="claude")
    assert page.locator(".wr-tile b").all_inner_texts() == ["5–3", "5–3", "6–2"]
    assert page.locator(".wr-tile span").all_inner_texts() == ["Winners", "Vs spread", "Over/under"]
    # best: a winner picked against the market (CLE at home getting 2.5); worst: the surest miss
    best, worst = page.locator(".wr-call").nth(0), page.locator(".wr-call").nth(1)
    assert "BEST CALL" in best.inner_text().upper() and "CLE over PIT, 27–24" in best.inner_text()
    assert "Picked the underdog to win outright" in best.inner_text()
    assert "WORST CALL" in worst.inner_text().upper() and "JAX at 57% to win" in worst.inner_text() and "CIN won 27–14" in worst.inner_text()
    page.click("[data-wrrec]")
    assert page.evaluate("SURFACE") == "preview" and page.evaluate("PV_REC") is True
    ctx.close()
    assert errors == []


def test_no_recap_file_says_so_in_one_line(browser, page_file):
    variant = page_with(page_file, lambda d: None)
    ctx, page, errors = open_page(browser, variant, PHONE)
    drive(page, go("weekrecap"))
    assert page.locator(".state-empty b").inner_text() == "No recap yet"
    assert page.locator(".gd-tabs").count() == 0 and page.locator(".wr-card").count() == 0
    assert page.evaluate(SIDEWAYS) <= 0
    ctx.close()
    assert errors == []


def test_a_section_without_data_hides_and_one_tab_left_hides_the_bar(browser, page_file):
    def bare(d):       # games only: no players, no record, nothing graded
        d.update(stars=[], k=[], dst=[], smashed=[], busts=[], tds=[], left_hurt=[], preview_record=None, top=None)
        for g in d["games"]:
            g["preview"] = None
        return d
    ctx, page, errors = open_page(browser, page_with(page_file, bare), PHONE)
    drive(page, go("weekrecap"))
    assert page.locator(".gd-tabs").count() == 0                   # Scores is the only tab left
    assert page.locator(".wr-games").count() == 1 and page.locator(".wr-lead").count() == 0
    assert page.locator(".wr-strip").count() == 0 and page.locator(".wr-mk").count() == 0
    ctx.close()

    def sparse(d):     # no touchdowns, one list: the other lists and cards are not drawn, no zeros
        d.update(tds=[], busts=[], left_hurt=[], k=[], dst=[], preview_record=None)
        return d
    ctx, page, errors2 = open_page(browser, page_with(page_file, sparse), PHONE)
    drive(page, go("weekrecap"))
    assert page.locator(".wr-tds").count() == 0 and page.locator(".wr-lt").count() == 1
    assert page.locator(".wr-bp h4").all_inner_texts() == ["QB", "RB", "WR", "TE"]
    assert "0" not in [s.strip() for s in page.locator(".wr-lt em").all_inner_texts()]
    ctx.close()
    assert errors == [] and errors2 == []


def test_weather_is_out_of_the_sub_row_but_the_hash_and_navgo_still_open_it(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, PHONE)
    subs = page.locator("#subnav .mode-sub").all_inner_texts()
    assert [s.strip() for s in subs] == ["Digest", "Recap", "News", "Start/Sit", "Preview", "Live"]
    assert page.evaluate("document.querySelector('#subnav .subnav-in').scrollWidth <= document.querySelector('#subnav .subnav-in').clientWidth")
    page.evaluate("location.hash = '#weather'")
    page.wait_for_function("document.getElementById('view').dataset.view === 'weather'")
    assert page.evaluate("navGroupOf('weather')") == "week"
    assert page.locator("#subnav .mode-sub[aria-pressed='true']").count() == 0
    page.evaluate("navGo('weekrecap')")
    assert page.locator("#subnav .mode-sub[aria-pressed='true']").inner_text().strip() == "Recap"
    ctx.close()
    assert errors == []


@pytest.mark.parametrize("tab", ["players", "scores", "claude"])
def test_nothing_scrolls_sideways_at_360(phone, tab):
    page, errors = on_tab(phone, tab)
    assert page.evaluate(SIDEWAYS) <= 0
    over = page.evaluate("""[...document.querySelectorAll('#view *')].filter(e =>
      /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4).map(e => String(e.className).slice(0, 40))""")
    assert over == []
    assert errors == []
