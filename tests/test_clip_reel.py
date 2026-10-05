"""The Week plays rail on the Roster (2026-10-05, Clips v2): one card per clip in a row the reader
drags, the "This week" list folded to its one row while it shows. Runs on the ESPN fixture team, the
one whose starters have clips in tests/fixtures/data/clips.json: Purdy 3 (two that YouTube refuses on
other sites, then one tall that plays), Kittle 1 (refused; the same clip as Purdy's second, the touchdown
pass, so one card names both), C. Brown 2 (both play). The Yahoo team has
C. Brown's two and an end card for Burrow, whose club has a game video.

The clip theater and the warm-up belong to clipsheet.js (clipTheaterOpen, clipWarm), so
these tests put stubs on the page and check what the rail asks of them."""
import re

import pytest

from test_render import drive, go, open_page  # noqa: F401

STUBS = """() => {
  window.__opened = null; window.__warm = 0;
  window.clipTheaterOpen = (items, i, el) => { window.__opened = {ids: items.map(it => it.c.id), who: items.map(it => it.p.n), ps: items.map(it => it.ps.map(p => p.n)), i, el: !!el && el.tagName}; };
  window.clipWarm = () => { window.__warm++; };
}"""
NO_NAV = "document.addEventListener('click', e => { if (e.target.closest('a.reel-card')) e.preventDefault(); }, true)"


@pytest.fixture(scope="module")
def noclips_file(built, page_file):
    """The same page with LIVE_CLIPS null: the build writes it as one `const LIVE_CLIPS = {...};` line."""
    text, n = re.subn(r"^const LIVE_CLIPS = .*;$", "const LIVE_CLIPS = null;", built.page, count=1, flags=re.M)
    assert n == 1
    p = page_file.parent / "noclips.html"
    p.write_text(text, encoding="utf-8")
    return p


def espn(browser, page_file, viewport, mode="sheet", team="espn", stubs=False, served=True):
    """`served` stands in for an http(s) page: from file:// clipEmbedOk() is false and every card is a link."""
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    if served:
        page.evaluate("clipEmbedOk = () => true")
    if stubs:
        page.evaluate(STUBS)
        page.evaluate(NO_NAV)
    page.evaluate(f"VIEW='{team}'; ROSTER_MODE='{mode}'; render()")
    return ctx, page, errors


def names(page):
    return page.eval_on_selector_all(".reel-card:not(.reel-end) .reel-nm", "els => els.map(e => e.textContent)")


def first_row_y(page):
    return page.evaluate("document.querySelector('.row.start').getBoundingClientRect().top + scrollY")


def rect(page, sel, n=0):
    return page.evaluate("([s, n]) => { const r = document.querySelectorAll(s)[n].getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, w: r.width, h: r.height}; }", [sel, n])


@pytest.mark.render
def test_where_nothing_can_embed_every_card_is_a_youtube_link(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), served=False)
    kinds = page.eval_on_selector_all(".reel-card:not(.reel-end)", "els => els.map(e => e.tagName)")
    assert kinds == ["A"] * 5, kinds
    assert page.locator("[data-reelall]").count() == 0, "no Play n when nothing plays here"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_rail_has_a_card_per_clip_in_order_with_a_mark_on_each(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator(".reel").count() == 1
    assert page.locator(".reel-ti h2").inner_text() == "Week 4 plays"      # LIVE_CLIPS.week, not schedWeek()
    assert page.locator(".reel-ti small").inner_text() == "5 clips"
    assert page.locator(".reel-card").count() == 5 and page.locator(".reel-end").count() == 0, "every starter has a clip, so no end card"
    assert names(page) == ["B. Purdy", "B. Purdy, G. Kittle", "B. Purdy"] + ["C. Brown"] * 2, "best scorer first, his clips in data order, the shared pass once naming both"
    assert page.eval_on_selector_all(".reel-cap", "els => els.map(e => e.textContent)")[:3] == [
        "Brock Purdy's best plays from Week 4", "Purdy finds Kittle for the touchdown", "Purdy scrambles for the first down"]
    # A clip that plays here wears the disc and a button; one YouTube refuses wears the chip and is a link.
    kinds = page.eval_on_selector_all(".reel-card", "els => els.map(e => [e.tagName, !!e.querySelector('.reel-disc'), !!e.querySelector('.reel-mark')])")
    assert kinds == [["A", False, True], ["A", False, True], ["BUTTON", True, False], ["BUTTON", True, False], ["BUTTON", True, False]], kinds
    assert "YouTube" in page.locator(".reel-mark").first.inner_text()
    assert page.eval_on_selector_all(".reel-dur", "els => els.map(e => e.textContent)") == ["3:32", "0:34", "0:28", "0:41", "1:36"]
    # A tall clip's thumbnail is the vertical frame, a wide one's the 16:9 still, in a box with its shape already.
    src = page.eval_on_selector_all(".reel-thumb img", "els => els.map(e => e.getAttribute('src'))")
    assert src[0] == "https://i.ytimg.com/vi/aaaaaaaaaa1/hqdefault.jpg", src
    assert src[2] == "https://i.ytimg.com/vi/aaaaaaaaaa3/oar2.jpg" and src[4] == "https://i.ytimg.com/vi/bbbbbbbbbb2/hqdefault.jpg", src
    thumb = rect(page, ".reel-thumb")
    assert (thumb["w"], thumb["h"]) == (128, 160) and rect(page, ".reel-card")["w"] == 128
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_header_counts_the_clips_that_play_and_hides_the_pill_when_none_does(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator("[data-reelall]").inner_text() == "Play 3" and page.locator("[data-reelall] svg").count() == 1
    page.evaluate("for (const l of Object.values(LIVE_CLIPS.players)) l.forEach(c => { c.embed = false; }); render()")
    assert page.locator("[data-reelall]").count() == 0, "nothing plays here: no pill"
    assert page.locator(".reel-disc").count() == 0 and page.locator("a.reel-card").count() == 5
    assert page.locator(".reel-ti small").inner_text() == "5 clips"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_youtube_only_card_is_a_link_and_opens_no_theater(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    a = page.locator("a.reel-card").first
    assert a.get_attribute("target") == "_blank" and a.get_attribute("rel") == "noopener"
    assert "youtube.com/" in a.get_attribute("href") and "aaaaaaaaaa1" in a.get_attribute("href"), a.get_attribute("href")
    want = page.evaluate("typeof clipYtUrl === 'function' ? clipYtUrl(clipsOf('brock-purdy')[0]) : null")
    assert want is None or a.get_attribute("href") == want, "the link is the sheet's own YouTube address"
    assert a.get_attribute("aria-label") == "Brock Purdy's best plays from Week 4, opens YouTube"
    a.click()
    assert page.evaluate("__opened") is None, "no sheet for a card that opens YouTube"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_playable_card_and_play_n_open_the_theater_on_every_clip_in_rail_order(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    page.locator("button.reel-card").first.scroll_into_view_if_needed()
    page.locator("button.reel-card").first.click()                    # Purdy's tall clip, the third card
    got = page.evaluate("__opened")
    assert got["i"] == 2 and got["el"] == "BUTTON"
    assert got["ids"] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3", "bbbbbbbbbb1", "bbbbbbbbbb2"], "YouTube-only ones ride along, the shared clip once"
    assert got["who"][1] == "Brock Purdy" and got["ps"][1] == ["Brock Purdy", "George Kittle"]
    page.evaluate("__opened = null")
    page.locator("[data-reelall]").click()
    got = page.evaluate("__opened")
    assert got["i"] == 2 and got["el"] == "BUTTON", "Play n starts at the first clip that plays"
    page.evaluate("__opened = null")
    page.locator("button.reel-card").nth(2).click()
    assert page.evaluate("__opened")["i"] == 4, "a card's index is its place in the rail"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_first_touch_warms_the_player_once_and_a_press_on_a_card_primes_nothing(browser, page_file):
    """A cue before the click's load is lost on real YouTube, so the rail only warms (test_clip_sheet pins the load)."""
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    track = rect(page, ".reel-track")
    page.mouse.move(track["l"] + 20, track["t"] + 20)
    page.mouse.down()
    page.mouse.up()
    page.mouse.down()
    page.mouse.up()
    assert page.evaluate("__warm") == 1, "once per render"
    assert page.evaluate("typeof clipPrime") == "undefined", "no prime step exists"
    card = rect(page, "button.reel-card")
    page.mouse.move(card["l"] + 20, card["t"] + 20)
    page.mouse.down()
    page.mouse.up()
    assert page.evaluate("__warm") == 1 and page.evaluate("__opened")["i"] == 2
    page.evaluate("render()")
    page.mouse.move(track["l"] + 20, track["t"] + 20)
    page.mouse.down()
    page.mouse.up()
    assert page.evaluate("__warm") == 2, "a new render is a new rail"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_end_card_names_the_starters_with_no_clip_and_opens_their_game(browser, page_file):
    """C. Brown has clips; J. Burrow has none but his club has a game video; St. Brown and Gibbs
    play for DET, which has neither, so only Burrow is named."""
    ctx, page, errors = espn(browser, page_file, (360, 800), team="yahoo", stubs=True)
    assert page.locator(".reel-card").count() == 3 and page.locator(".reel-end").count() == 1
    end = page.locator(".reel-end")
    assert end.evaluate("e => e.tagName") == "A" and end.get_attribute("target") == "_blank"
    assert "cccccccccc2" in end.get_attribute("href"), "the first such game's video"
    assert end.locator(".reel-no").inner_text() == "No clip"
    assert end.locator(".reel-endline").inner_text() == "J. Burrow: their game's highlights on YouTube"
    assert "YouTube" in end.locator(".reel-mark").inner_text()
    last, first = rect(page, ".reel-end .reel-thumb"), rect(page, ".reel-thumb")
    assert (last["w"], last["h"]) == (first["w"], first["h"]) == (128, 160), "the same size as a clip card"
    assert page.locator("[data-reelall]").inner_text() == "Play 2"
    end.click()
    assert page.evaluate("__opened") is None
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_starter_with_no_game_video_is_not_named_and_a_bencher_never_is(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    got = page.evaluate("""(() => {
      const mk = (n, team, start) => ({n, slug: n.toLowerCase().replace(' ', '-'), pos: 'WR', team, start});
      const team = {key: 'x', roster: [...TEAMS.espn.roster, mk('Josh Allen', 'BUF', true), mk('Tyler Bass', 'BUF', true),
                                       mk('Bench Guy', 'BUF', false), mk('No Game', 'ZZZ', true)]};
      const m = reelModel(team), box = document.createElement('div');
      box.innerHTML = reelHTML(team);
      return {ends: m.ends.map(p => p.n), line: box.querySelector('.reel-endline').textContent, items: m.items.length};
    })()""")
    assert got == {"ends": ["Josh Allen", "Tyler Bass"], "line": "J. Allen, T. Bass: their game's highlights on YouTube", "items": 5}, got
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_team_without_clips_has_no_rail(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), team="espn-run-it-back")   # no starter has a clip
    assert page.locator(".reel").count() == 0 and page.locator(".rl-reel").count() == 0
    assert page.locator(".brief-line").count() > 0 and page.locator("[data-briefunfold]").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_rail_scrolls_sideways_with_the_next_card_showing_and_nothing_else_does(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    track = page.locator(".reel-track")
    css = track.evaluate("e => { const s = getComputedStyle(e); return [s.overflowX, s.scrollSnapType, s.touchAction, s.overscrollBehaviorX, s.scrollbarWidth]; }")
    assert css == ["auto", "x", "auto", "contain", "none"], "native touch scroll, x snapping (proximity is the default and prints as x), no bar, no paging"
    assert page.evaluate("[...document.querySelectorAll('.reel-card')].every(e => getComputedStyle(e).scrollSnapAlign.startsWith('start'))")
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth - t.clientWidth; })()") > 100
    t, third = rect(page, ".reel-track"), rect(page, ".reel-card", 2)
    assert third["l"] < t["r"] < third["r"], "the third card shows past the edge"
    assert page.locator(".reel-arr").first.is_hidden(), "buttons are for a desktop"
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert page.evaluate("[...document.querySelectorAll('#view *')].filter(e => /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4 && !e.matches('.reel-track')).length") == 0
    track.evaluate("e => { e.scrollLeft = 200; }")                   # touch scroll is the browser's; the same property it moves
    assert track.evaluate("e => e.scrollLeft") > 100
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_mouse_drags_the_rail_and_a_drag_opens_no_card(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    third = rect(page, ".reel-card", 2)                              # a playable card
    x, y = third["l"] + 30, third["t"] + 40
    page.mouse.move(x, y)
    page.mouse.down()
    for dx in (-10, -40, -90, -150):
        page.mouse.move(x + dx, y)
    page.mouse.up()
    assert page.evaluate("document.querySelector('.reel-track').scrollLeft") > 100, "the rail followed the mouse"
    assert page.evaluate("__opened") is None, "the click that ends a drag opens nothing"
    # A press that moves less than the threshold is still a click.
    third = rect(page, ".reel-card", 3)
    page.mouse.move(third["l"] + 30, third["t"] + 40)
    page.mouse.down()
    page.mouse.move(third["l"] + 32, third["t"] + 40)
    page.mouse.up()
    page.wait_for_timeout(450)
    page.evaluate("document.querySelector('.reel-track').scrollLeft = 0")
    page.locator("button.reel-card").first.click()
    assert page.evaluate("__opened")["i"] == 2, "a plain click opens its card after a drag"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_on_a_desktop_the_arrows_scroll_one_card_and_hide_when_the_rail_fits(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (1100, 800))
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth > t.clientWidth; })()"), "five cards overflow the column"
    prev, nxt = page.locator("[data-reelstep='-1']"), page.locator("[data-reelstep='1']")
    assert prev.is_visible() and prev.is_disabled() and nxt.is_enabled()
    room = page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth - t.clientWidth; })()")
    nxt.click()
    page.wait_for_function("document.querySelector('.reel-track').scrollLeft > 20")
    page.wait_for_timeout(500)
    assert page.evaluate("document.querySelector('.reel-track').scrollLeft") == pytest.approx(min(138, room), abs=2), "one card width and a gap, or what is left"
    assert prev.is_enabled()
    assert errors == []
    ctx.close()
    ctx, page, errors = espn(browser, page_file, (1100, 800), team="yahoo")     # three cards: they fit
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth <= t.clientWidth + 1; })()")
    assert page.locator(".reel-arr").first.is_hidden() and page.locator(".reel.fits").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_list_folds_while_the_rail_shows_and_show_opens_it(browser, page_file, noclips_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator(".brief.done").count() == 1 and page.locator(".brief-line").count() == 0
    assert re.fullmatch(r"\d+ things? to check", page.locator(".brief.done .brief-h small").inner_text())
    page.locator("[data-briefunfold]").click()
    assert page.locator(".brief.done").count() == 0 and page.locator(".brief-line").count() > 0
    assert page.locator(".reel").count() == 1, "Show opens the list; the rail stays"
    unfolded = page.evaluate("document.querySelector('.brief').outerHTML")
    ctx.close()
    # With no clips the page draws no rail and the very same list, unfolded.
    ctx, page, errors = espn(browser, noclips_file, (360, 800))
    assert page.locator(".reel").count() == 0 and page.locator("[data-briefunfold]").count() == 0
    assert page.evaluate("document.querySelector('.brief').outerHTML") == unfolded
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("team", ["espn", "yahoo"])
def test_the_first_starter_stays_on_the_first_screen_under_the_rail(browser, page_file, noclips_file, team):
    """The folded list pays for the rail, but a 160px thumbnail is taller than the old 2-up cards (2026-10-05:
    573 and 573 against 550 and 530 with no rail at 360x800), so the bar is the first screen, not the old row."""
    ctx, page, errors = espn(browser, page_file, (360, 800), team=team)
    with_reel = first_row_y(page)
    ctx.close()
    ctx, page, errors = espn(browser, noclips_file, (360, 800), team=team)
    without = first_row_y(page)
    assert with_reel < 650 and with_reel - without < 60, (with_reel, without)
    ctx.close()


@pytest.mark.render
def test_cards_mode_and_a_desktop_draw_the_rail_too(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), mode="cards")
    assert page.locator(".reel").count() == 1 and page.locator(".cardgrid").count() > 0
    ctx.close()
    ctx, page, errors = espn(browser, page_file, (1280, 900))
    assert page.locator(".reel").is_visible() and page.locator(".brief-line").first.is_visible(), "the list keeps its column"
    reel, rows, brief = (page.evaluate(f"(() => {{ const r = document.querySelector('{s}').getBoundingClientRect(); return [r.left, r.top, r.width]; }})()")
                         for s in (".reel", ".rl-rows", ".brief"))
    assert reel[0] == rows[0] and rows[1] > reel[1], "the rail sits above the rows, in their column"
    assert brief[0] > reel[0] + reel[2], "and the list beside both"
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert errors == []
    ctx.close()
