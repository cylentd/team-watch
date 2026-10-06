"""The Week plays rail on the Roster (2026-10-05, Clips v2; one card per starter, two to a phone page,
text over the picture since Roster redesign unit C): a row the reader pages or drags, the "This week"
list folded to its one row while it shows. Runs on the ESPN fixture team, the one whose starters have
clips in tests/fixtures/data/clips.json: Purdy 3 (two that YouTube refuses on other sites, then one
tall that plays), Kittle 1 (refused; the same clip as Purdy's second, the touchdown pass, so it is one
item credited to both), C. Brown 2 (both play): three cards, five clips. The Yahoo team has C. Brown's
card and an end card for Burrow, whose club has a game video.

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


@pytest.fixture(scope="module")
def phone(browser, page_file):
    """One 360x800 page for the tests that only read it: ESPN's roster, Cards mode, this week's pack
    already opened so no stage covers the page."""
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    drive(page, go("roster"))
    page.evaluate("() => { window.__clipWeekRow = clipWeekRow; }")
    assert errors == [], "the page raised an error while loading"
    yield page, errors
    ctx.close()


@pytest.fixture
def ph(phone):
    page, errors = phone
    page.evaluate("""() => { 'use strict';
      clipEmbedOk = () => true; window.clipWeekRow = window.__clipWeekRow;
      packMark(TEAMS.espn, schedWeek());
      navGo('roster'); VIEW = 'espn'; ROSTER_MODE = 'cards'; render(); }""")
    return page, errors


def first_row_y(page):
    return page.evaluate("document.querySelector('.row.start').getBoundingClientRect().top + scrollY")


def rect(page, sel, n=0):
    return page.evaluate("([s, n]) => { const r = document.querySelectorAll(s)[n].getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, w: r.width, h: r.height}; }", [sel, n])


@pytest.mark.render
def test_where_nothing_can_embed_every_card_is_a_youtube_link(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), served=False)
    kinds = page.eval_on_selector_all(".reel-card:not(.reel-end)", "els => els.map(e => e.tagName)")
    assert kinds == ["A"] * 3, kinds
    assert page.locator("[data-reelall]").count() == 0, "no Play all when nothing plays here"
    assert errors == []
    ctx.close()


def test_the_rail_has_a_card_per_starter_best_scorer_first_with_a_count_on_each(ph):
    page, errors = ph
    assert page.locator(".reel").count() == 1
    assert page.locator(".reel-ti h2").inner_text() == "Week 4 plays"      # LIVE_CLIPS.week, not schedWeek()
    assert page.locator(".reel-ti small").inner_text() == "5 clips", "every clip once, the shared pass too"
    assert page.locator(".reel-card").count() == 3 and page.locator(".reel-end").count() == 0, "every starter has a clip, so no end card"
    assert names(page) == ["B. Purdy", "G. Kittle", "C. Brown"], "best scorer first"
    # A card with a clip that plays here is a button wearing the count of his clips; one whose clips
    # YouTube all refuses is a link wearing YouTube's chip where the count goes.
    kinds = page.eval_on_selector_all(".reel-card", "els => els.map(e => [e.tagName, (e.querySelector('.reel-n') || {}).textContent || null, !!e.querySelector('.reel-mark')])")
    assert kinds == [["BUTTON", "3", False], ["A", None, True], ["BUTTON", "2", False]], kinds
    assert "YouTube" in page.locator(".reel-mark").first.inner_text()
    # The picture is his first clip's still, in a 16:10 box that has its shape before the image loads.
    src = page.eval_on_selector_all(".reel-thumb img", "els => els.map(e => e.getAttribute('src'))")
    want = page.evaluate("['brock-purdy', 'george-kittle', 'chase-brown'].map(s => clipThumbOf(clipsOf(s)[0]))")
    assert src == want and src[0] == "https://i.ytimg.com/vi/aaaaaaaaaa1/hqdefault.jpg", src
    thumb = rect(page, ".reel-thumb")
    assert thumb["w"] / thumb["h"] == pytest.approx(1.6, abs=.03)
    assert errors == []


def test_two_cards_fill_a_phone_page_and_the_third_waits_for_the_next(ph):
    page, errors = ph
    track, a, b, c = (rect(page, ".reel-track" if i is None else ".reel-card", i or 0) for i in (None, 0, 1, 2))
    assert abs(b["r"] - a["l"] - 2 * a["w"] - 8) < 1.5 and a["w"] == b["w"] == c["w"], "two cards and a gap fill the page"
    assert b["r"] <= track["r"] and c["l"] >= track["r"] - 1, "the third card does not show past the edge"
    assert rect(page, ".reel-card")["h"] == pytest.approx(rect(page, ".reel-thumb")["h"], abs=.5), "no text block under the picture"
    assert errors == []


def test_a_cards_name_points_and_stat_line_sit_inside_its_picture(ph):
    page, errors = ph
    page.evaluate("""() => { window.clipWeekRow = p => p.n === 'Brock Purdy' ? {row: {}, pts: 17.6, line: '6-86-1 · 11 tgt'} : {row: null, pts: null, line: null}; render(); }""")
    thumb = rect(page, ".reel-thumb")
    for sel in (".reel-ov", ".reel-nm", ".reel-pt", ".reel-l2", ".reel-n"):
        r = rect(page, sel)
        assert thumb["l"] <= r["l"] and r["r"] <= thumb["r"] + .5 and thumb["t"] <= r["t"] and r["t"] + r["h"] <= thumb["t"] + thumb["h"] + .5, (sel, r, thumb)
    assert page.locator(".reel-nm").first.inner_text() == "B. Purdy" and page.locator(".reel-pt").first.inner_text() == "17.6"
    assert page.locator(".reel-l2").first.inner_text() == "6-86-1 · 11 tgt"
    nm, pt, l2, n = (rect(page, s) for s in (".reel-nm", ".reel-pt", ".reel-l2", ".reel-n"))
    assert nm["r"] <= pt["l"] and l2["t"] >= nm["t"] + nm["h"] - 1, "name left, points right, the stat line under"
    assert n["r"] > thumb["r"] - 12 and n["t"] < thumb["t"] + 12, "the count chip sits top right"
    assert page.locator(".reel-pt").count() == 1, "a starter with no week row shows no points"
    assert errors == []


def test_the_hero_is_one_row_with_the_switch_at_its_right_end(ph):
    page, errors = ph
    row, sw, sub, hero = (rect(page, s) for s in (".hero-eyebrow", ".rmode", ".hero-sub", ".hero"))
    assert row["t"] - 1 <= sw["t"] <= row["t"] + row["h"], "the switch's top is inside the name row's box"
    assert sw["r"] >= 360 - 20 and sw["l"] > row["l"] + 100, "at the row's right end"
    assert sub["t"] + sub["h"] <= hero["t"] + hero["h"] and hero["h"] < 80, hero
    assert sub["l"] == row["l"] and sub["r"] < sw["l"], "the league line is under the name, one line, beside the switch"
    assert page.evaluate("document.querySelector('.hero-sub').scrollHeight") <= 18
    btns = page.eval_on_selector_all(".rmode [data-rmode]", "els => els.map(e => [e.dataset.rmode, e.getAttribute('aria-label'), e.getAttribute('aria-pressed'), e.textContent.trim(), !!e.querySelector('svg')])")
    assert btns == [["sheet", "Sheet", "false", "", True], ["cards", "Cards", "true", "", True]], btns
    assert page.locator(".rmode [data-rerip]").count() == 0, "Rip again stays on the Starters rule"
    page.locator("[data-rmode=sheet]").click()
    assert page.locator(".row.start").count() > 0 and page.locator("[data-rmode=sheet]").get_attribute("aria-pressed") == "true"
    assert errors == []


def test_recap_has_the_league_chip_and_no_hero_or_roster_switch(ph):
    """My recap (2026-09-27) kept the roster's one-row hero without its Sheet / Cards switch; since the League
    merge (2026-10-05) Recap draws the one chip instead of a hero."""
    page, errors = ph
    page.evaluate("VIEW = 'yahoo'; navGo('myrecap')")
    assert page.evaluate("SURFACE") == "recap", "the old hash lands on Recap"
    assert page.locator(".hero").count() == 0 and page.locator(".rmode").count() == 0
    assert page.locator(".lgchip #switch").count() == 1
    assert errors == []


@pytest.mark.render
def test_the_header_says_play_all_when_something_plays_and_nothing_when_none_does(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator("[data-reelall]").inner_text() == "Play all"
    h2, small, all_, prev, nxt = (rect(page, s) for s in (".reel-ti h2", ".reel-ti small", "[data-reelall]", "[data-reelstep='-1']", "[data-reelstep='1']"))
    assert h2["r"] <= small["l"] and small["r"] <= all_["l"] <= all_["r"] <= prev["l"] and prev["r"] <= nxt["l"], "title, count, Play all, then the arrows"
    centres = [r["t"] + r["h"] / 2 for r in (h2, small, all_, prev, nxt)]
    assert max(centres) - min(centres) < 10 and rect(page, ".reel-h")["h"] < 44, "one line"
    page.evaluate("for (const l of Object.values(LIVE_CLIPS.players)) l.forEach(c => { c.embed = false; }); render()")
    assert page.locator("[data-reelall]").count() == 0, "nothing plays here: no pill"
    assert page.locator(".reel-n").count() == 0 and page.locator("a.reel-card").count() == 3
    assert page.locator(".reel-ti small").inner_text() == "5 clips"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_youtube_only_card_is_a_link_and_opens_no_theater(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    a = page.locator("a.reel-card").first                              # Kittle's: his one clip is the shared one YouTube refuses
    assert a.get_attribute("target") == "_blank" and a.get_attribute("rel") == "noopener"
    assert "youtube.com/" in a.get_attribute("href") and "aaaaaaaaaa2" in a.get_attribute("href"), a.get_attribute("href")
    want = page.evaluate("typeof clipYtUrl === 'function' ? clipYtUrl(clipsOf('george-kittle')[0]) : null")
    assert want is None or a.get_attribute("href") == want, "the link is the sheet's own YouTube address"
    assert a.get_attribute("aria-label") == "Purdy finds Kittle for the touchdown, opens YouTube"
    a.click()
    assert page.evaluate("__opened") is None, "no sheet for a card that opens YouTube"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_card_opens_the_theater_on_his_clips_only_and_play_all_on_every_clip(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    page.locator("button.reel-card").first.click()                    # Purdy's three, from his tall clip, the one that plays
    got = page.evaluate("__opened")
    assert got["i"] == 2 and got["el"] == "BUTTON"
    assert got["ids"] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3"], "his clips only: the YouTube-only ones ride along"
    assert got["ps"][1] == ["Brock Purdy", "George Kittle"], "the shared pass is still credited to both"
    page.evaluate("__opened = null")
    page.locator("[data-reelall]").click()
    got = page.evaluate("__opened")
    assert got["i"] == 2 and got["el"] == "BUTTON", "Play all starts at the first clip that plays"
    assert got["ids"] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3", "bbbbbbbbbb1", "bbbbbbbbbb2"], "every clip once, the shared one once"
    page.evaluate("__opened = null")
    page.locator("button.reel-card").nth(1).evaluate("e => e.scrollIntoView({inline: 'start'})")
    page.locator("button.reel-card").nth(1).click()                   # Brown's two
    got = page.evaluate("__opened")
    assert got["ids"] == ["bbbbbbbbbb1", "bbbbbbbbbb2"] and got["i"] == 0, got
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
    assert page.locator(".reel-card").count() == 2 and page.locator(".reel-end").count() == 1, "Brown's card, then the end card"
    end = page.locator(".reel-end")
    assert end.evaluate("e => e.tagName") == "A" and end.get_attribute("target") == "_blank"
    assert "cccccccccc2" in end.get_attribute("href"), "the first such game's video"
    assert end.locator(".reel-no").inner_text() == "No clip"
    assert end.locator(".reel-endline").inner_text() == "J. Burrow: their game's highlights on YouTube"
    assert "YouTube" in end.locator(".reel-mark").inner_text()
    last, first = rect(page, ".reel-end .reel-thumb"), rect(page, ".reel-thumb")
    assert (last["w"], last["h"]) == (first["w"], first["h"]), "the same size as a clip card"
    inside = page.evaluate("""(() => { const t = document.querySelector('.reel-end .reel-thumb').getBoundingClientRect();
      return [...document.querySelectorAll('.reel-end .reel-thumb > *')].every(e => { const r = e.getBoundingClientRect();
        return r.left >= t.left - .5 && r.right <= t.right + .5 && r.top >= t.top - .5 && r.bottom <= t.bottom + .5; }); })()""")
    assert inside, "the end card's words fit its box"
    assert page.locator("[data-reelall]").inner_text() == "Play all"
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
def test_the_rail_scrolls_sideways_a_page_at_a_time_and_nothing_else_does(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    track = page.locator(".reel-track")
    css = track.evaluate("e => { const s = getComputedStyle(e); return [s.overflowX, s.scrollSnapType, s.touchAction, s.overscrollBehaviorX, s.scrollbarWidth]; }")
    assert css == ["auto", "x", "auto", "contain", "none"], "native touch scroll, x snapping (proximity is the default and prints as x), no bar, no paging"
    assert page.evaluate("[...document.querySelectorAll('.reel-card')].every(e => getComputedStyle(e).scrollSnapAlign.startsWith('start'))")
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth - t.clientWidth; })()") > 100
    prev, nxt = page.locator("[data-reelstep='-1']"), page.locator("[data-reelstep='1']")
    assert prev.is_visible() and prev.is_disabled() and nxt.is_enabled(), "three cards are more than the one page of two: the arrows turn it"
    # An arrow scrolls by the measured page: the cards that fit whole, each a width and a gap (two here).
    page.evaluate("document.querySelector('.reel-track').scrollBy = o => { window.__by = o; }")
    nxt.click()
    card = rect(page, ".reel-card")
    assert page.evaluate("__by")["left"] == pytest.approx(2 * (card["w"] + 8), abs=1)
    track.evaluate("e => { e.scrollLeft = 1000; }")                  # to the end: the page is out of cards
    page.wait_for_function("document.querySelector('[data-reelstep=\"1\"]').disabled")
    assert prev.is_enabled()
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert page.evaluate("[...document.querySelectorAll('#view *')].filter(e => /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4 && !e.matches('.reel-track')).length") == 0
    track.evaluate("e => { e.scrollLeft = 200; }")                   # touch scroll is the browser's; the same property it moves
    assert track.evaluate("e => e.scrollLeft") > 100
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_mouse_drags_the_rail_and_a_drag_opens_no_card(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), stubs=True)
    second = rect(page, ".reel-card", 1)                             # a card on the page, a link here
    x, y = second["l"] + 30, second["t"] + 40
    page.mouse.move(x, y)
    page.mouse.down()
    for dx in (-10, -40, -90, -150):
        page.mouse.move(x + dx, y)
    page.mouse.up()
    assert page.evaluate("document.querySelector('.reel-track').scrollLeft") > 100, "the rail followed the mouse"
    assert page.evaluate("__opened") is None, "the click that ends a drag opens nothing"
    # A press that moves less than the threshold is still a click.
    # (the rail's scroll has come to rest: the same scrollLeft on two frames running, so a snap is done)
    page.evaluate("window.__sl = null")
    page.wait_for_function("() => { const t = document.querySelector('.reel-track').scrollLeft; const same = window.__sl === t; window.__sl = t; return same; }")
    page.evaluate("document.querySelector('.reel-track').scrollLeft = 0")
    first = rect(page, "button.reel-card")
    page.mouse.move(first["l"] + 30, first["t"] + 40)
    page.mouse.down()
    page.mouse.move(first["l"] + 32, first["t"] + 40)
    page.mouse.up()
    assert page.evaluate("__opened")["i"] == 2, "a plain click opens its card after a drag"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_on_a_desktop_four_cards_make_a_page_and_the_arrows_hide_when_the_rail_fits(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (1100, 800))
    a, d = rect(page, ".reel-card"), rect(page, ".reel-track")
    assert d["w"] / a["w"] > 3.8, "four cards to a page from 760px"
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth <= t.clientWidth + 1; })()"), "three cards fit the column"
    assert page.locator(".reel-arr").first.is_hidden() and page.locator(".reel.fits").count() == 1
    assert errors == []
    ctx.close()
    ctx, page, errors = espn(browser, page_file, (1100, 800), team="yahoo")     # a card and the end card: they fit
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth <= t.clientWidth + 1; })()")
    assert page.locator(".reel-arr").first.is_hidden() and page.locator(".reel.fits").count() == 1
    assert errors == []
    ctx.close()
    # More cards than a page: the page turns by four cards, and the end of the rail disables ›.
    ctx, page, errors = espn(browser, page_file, (1100, 800))
    page.evaluate("""() => { const tr = document.querySelector('.reel-track'), c = tr.querySelector('.reel-card');
      for (let i = 0; i < 3; i++) tr.appendChild(c.cloneNode(true));
      reelFit(document.querySelector('.reel')); }""")
    nxt = page.locator("[data-reelstep='1']")
    assert nxt.is_visible() and nxt.is_enabled() and page.locator("[data-reelstep='-1']").is_disabled()
    page.evaluate("document.querySelector('.reel-track').scrollBy = o => { window.__by = o; }")
    nxt.click()
    card = rect(page, ".reel-card")
    assert page.evaluate("__by")["left"] == pytest.approx(4 * (card["w"] + 8), abs=1), "a page, measured"
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
    """The folded list pays for the rail. 2026-10-05, 360x800, Sheet: 573 with the 160px-tall cards of Clips v2,
    392 with the 16:10 two-up cards and the one-row hero of Roster redesign unit C."""
    ctx, page, errors = espn(browser, page_file, (360, 800), team=team)
    with_reel = first_row_y(page)
    ctx.close()
    ctx, page, errors = espn(browser, noclips_file, (360, 800), team=team)
    without = first_row_y(page)
    assert with_reel < 430 and with_reel - without < 60, (with_reel, without)
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
