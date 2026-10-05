"""The Week plays reel on the Roster (2026-10-05): a card per starter with an official clip, paged
two to a phone screen, the "This week" list folded to its one row while it shows. Runs on the ESPN
fixture team, the one whose starters (Purdy, Kittle, C. Brown) have clips in tests/fixtures/data/clips.json;
the Yahoo team has none."""
import re

import pytest

from test_render import browser, drive, go, open_page  # noqa: F401  (browser is a fixture)


@pytest.fixture(scope="module")
def noclips_file(built, page_file):
    """The same page with LIVE_CLIPS null: the build writes it as one `const LIVE_CLIPS = {...};` line."""
    text, n = re.subn(r"^const LIVE_CLIPS = .*;$", "const LIVE_CLIPS = null;", built.page, count=1, flags=re.M)
    assert n == 1
    p = page_file.parent / "noclips.html"
    p.write_text(text, encoding="utf-8")
    return p


def espn(browser, page_file, viewport, mode="sheet", team="espn"):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    page.evaluate(f"VIEW='{team}'; ROSTER_MODE='{mode}'; render()")
    return ctx, page, errors


def visible_names(page):
    return page.eval_on_selector_all(".reel-card:not([hidden]) .reel-nm", "els => els.map(e => e.textContent)")


def first_row_y(page):
    return page.evaluate("document.querySelector('.row.start').getBoundingClientRect().top + scrollY")


def swipe(page, dx):
    """A one-finger drag along the track, as synthetic touch events (lib/swipe.js listens for those)."""
    page.evaluate("""dx => {
      const el = document.querySelector('.reel-track'), r = el.getBoundingClientRect(), y = r.top + 20;
      const t = x => new Touch({identifier: 1, target: el, clientX: x, clientY: y});
      const x0 = r.left + r.width / 2;
      el.dispatchEvent(new TouchEvent('touchstart', {touches: [t(x0)], changedTouches: [t(x0)], bubbles: true}));
      el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [t(x0 + dx)], bubbles: true}));
    }""", dx)


@pytest.mark.render
def test_the_reel_shows_a_card_per_starter_with_clips(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator(".reel").count() == 1
    assert page.locator(".reel-ti h2").inner_text() == "Week 4 plays"      # LIVE_CLIPS.week, not schedWeek()
    assert page.locator(".reel-ti small").inner_text() == "5 clips"        # Purdy 3 + Kittle 1 + C. Brown 1
    want = page.evaluate("TEAMS.espn.roster.filter(p => p.start && clipsOf(p.slug).length).length")
    assert want == 3 and page.locator(".reel-card:not(.reel-end)").count() == want
    assert page.locator(".reel-end").count() == 0, "every starter has a clip, so no end card"
    badges = page.eval_on_selector_all(".reel-n", "els => els.map(e => [e.textContent, e.classList.contains('td')])")
    assert badges == [["3", True], ["1", True], ["1", False]], badges     # Purdy and Kittle's title says touchdown
    assert visible_names(page) == ["B. Purdy", "G. Kittle"]
    # The badge draws the play triangle, or YouTube's mark when none of his clips plays here.
    marks = page.eval_on_selector_all(".reel-card .reel-n", "els => els.map(e => e.querySelector('.yt-mark') ? 'yt' : 'play')")
    assert marks == ["play", "yt", "play"], "Purdy has one clip that embeds, Kittle only the NFL channel's"
    assert page.locator(".reel-n .yt-mark").first.get_attribute("aria-hidden") == "true"
    # The page names its thumbnails by YouTube's own path, in a box that already has its shape.
    assert page.locator(".reel-thumb img").first.get_attribute("src") == "https://i.ytimg.com/vi/aaaaaaaaaa1/mqdefault.jpg"
    assert page.evaluate("(() => { const r = document.querySelector('.reel-thumb').getBoundingClientRect(); return Math.abs(r.width / r.height - 16 / 9) < .05; })()")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_team_without_clips_has_no_reel(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), team="espn-run-it-back")   # no starter has a clip
    assert page.locator(".reel").count() == 0 and page.locator(".rl-reel").count() == 0
    assert page.locator(".brief-line").count() > 0 and page.locator("[data-briefunfold]").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_yahoo_team_draws_a_card_and_an_end_card(browser, page_file):
    """C. Brown has a clip; J. Burrow has none but his club has a game video; St. Brown and Gibbs
    play for DET, which has neither, so only Burrow is named."""
    ctx, page, errors = espn(browser, page_file, (360, 800), team="yahoo")
    assert page.locator(".reel-card:not(.reel-end)").count() == 1 and page.locator(".reel-end").count() == 1
    assert page.locator(".reel-end .reel-nm").inner_text() == "1 more: game highlights"
    assert page.locator(".reel-end .reel-line").inner_text() == "J. Burrow"
    assert page.locator(".reel-end .reel-n .yt-mark").count() == 1 and page.locator(".reel-end .reel-n svg:not(.yt-mark)").count() == 0, "game highlights are YouTube's: its mark, no play triangle"
    assert page.locator(".reel.one").count() == 1 and page.locator("[data-reelstep='1']").is_hidden(), "two cards are one page: no arrows"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_arrows_and_a_swipe_page_the_cards_and_nothing_scrolls_sideways(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator("[data-reelstep='-1']").is_disabled() and not page.locator("[data-reelstep='1']").is_disabled()
    page.locator("[data-reelstep='1']").click()
    assert visible_names(page) == ["C. Brown"]
    assert page.locator("[data-reelstep='1']").is_disabled() and not page.locator("[data-reelstep='-1']").is_disabled()
    page.locator("[data-reelstep='-1']").click()
    assert visible_names(page) == ["B. Purdy", "G. Kittle"]
    swipe(page, -90)                                  # a swipe left turns to the next page
    assert visible_names(page) == ["C. Brown"]
    swipe(page, 90)
    assert visible_names(page) == ["B. Purdy", "G. Kittle"]
    swipe(page, 20)                                   # too short to be a swipe
    assert visible_names(page) == ["B. Purdy", "G. Kittle"]
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert page.evaluate("(() => { const t = document.querySelector('.reel-track'); return t.scrollWidth - t.clientWidth; })()") <= 0
    assert page.evaluate("[...document.querySelectorAll('#view *')].filter(e => /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4).length") == 0
    page.locator("[data-reelstep='1']").click()
    page.evaluate("render()")                         # a redraw keeps the page the reader turned to
    assert visible_names(page) == ["C. Brown"]
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_list_folds_while_the_reel_shows_and_show_opens_it(browser, page_file, noclips_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    assert page.locator(".brief.done").count() == 1 and page.locator(".brief-line").count() == 0
    assert re.fullmatch(r"\d+ things? to check", page.locator(".brief.done .brief-h small").inner_text())
    page.locator("[data-briefunfold]").click()
    assert page.locator(".brief.done").count() == 0 and page.locator(".brief-line").count() > 0
    assert page.locator(".reel").count() == 1, "Show opens the list; the reel stays"
    unfolded = page.evaluate("document.querySelector('.brief').outerHTML")
    ctx.close()
    # With no clips the page draws no reel and the very same list, unfolded.
    ctx, page, errors = espn(browser, noclips_file, (360, 800))
    assert page.locator(".reel").count() == 0 and page.locator("[data-briefunfold]").count() == 0
    assert page.evaluate("document.querySelector('.brief').outerHTML") == unfolded
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("team", ["espn", "yahoo"])
def test_the_first_starter_does_not_drop_for_the_reel(browser, page_file, noclips_file, team):
    ctx, page, errors = espn(browser, page_file, (360, 800), team=team)
    with_reel = first_row_y(page)
    ctx.close()
    ctx, page, errors = espn(browser, noclips_file, (360, 800), team=team)
    without = first_row_y(page)
    assert with_reel <= without, (with_reel, without)
    ctx.close()


@pytest.mark.render
def test_a_card_opens_only_his_clips_and_play_all_the_whole_queue(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    page.evaluate("() => { window.clipSheetOpen = (q, i, el, all) => { window.__open = {names: q.map(p => p.n), i}; window.__all = !!all; }; }")   # the sheet is clipsheet.js's
    page.locator(".reel-card").nth(1).click()
    assert page.evaluate("__open") == {"names": ["George Kittle"], "i": 0}, "a card does not play on into the next"
    assert page.evaluate("__all") is False, "his own card opens him even when none of his clips plays here"
    page.locator("[data-reelall]").click()
    assert page.evaluate("__open") == {"names": ["Brock Purdy", "George Kittle", "Chase Brown"], "i": 0}
    assert page.evaluate("__all") is True, "Play all asks the sheet to start at a clip that plays and skip the rest"
    assert errors == []
    ctx.close()
    ctx, page, errors = espn(browser, page_file, (360, 800), team="yahoo")
    page.evaluate("() => { window.clipSheetOpen = (q, i, el, all) => { window.__open = {names: q.map(p => p.n), i}; window.__all = !!all; }; }")
    page.locator(".reel-end").click()
    assert page.evaluate("__open") == {"names": ["Joe Burrow"], "i": 0}, "the end card opens the game videos"
    assert page.evaluate("__all") is False
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_best_scorer_leads_and_the_card_carries_his_line(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    page.evaluate("LIVE_GAMELOG.rows.push({slug: 'chase-brown', pos: 'RB', wk: 4, pts: 30.2, car: 20, rush_yds: 100, rush_td: 0,"
                  " rec: 2, rec_yds: 10, rec_td: 0, tgt: 3}); render()")
    assert visible_names(page) == ["C. Brown", "B. Purdy"]
    first = page.locator(".reel-card").first
    assert first.locator(".reel-pts").inner_text() == "30.2"
    assert first.locator(".reel-line").inner_text() == "20-100-0 · 2-10"
    assert not first.locator(".reel-n").evaluate("e => e.classList.contains('td')"), "a box score with no TD beats a title that says one"
    ctx.close()


@pytest.mark.render
def test_the_end_card_names_the_starters_with_no_clip(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800))
    got = page.evaluate("""(() => {
      const bills = [{n: 'Josh Allen', slug: 'josh-allen', pos: 'QB', team: 'BUF', start: true},
                     {n: 'Tyler Bass', slug: 'tyler-bass', pos: 'K', team: 'BUF', start: true},
                     {n: 'Bench Guy', slug: 'bench-guy', pos: 'WR', team: 'BUF', start: false},
                     {n: 'No Game', slug: 'no-game', pos: 'WR', team: 'ZZZ', start: true}];
      const team = {key: 'x', roster: [...TEAMS.espn.roster, ...bills]};
      const m = reelModel(team), box = document.createElement('div');
      box.innerHTML = reelHTML(team);
      return {ends: m.ends.map(p => p.n), queue: m.queue.map(p => p.n), card: box.querySelector('.reel-end').innerText,
              open: +box.querySelector('.reel-end').dataset.reelopen, thumb: box.querySelector('.reel-end img').getAttribute('src')};
    })()""")
    assert got["ends"] == ["Josh Allen", "Tyler Bass"], "a starter with no game video is not named, a bencher never is"
    assert got["queue"] == ["Brock Purdy", "George Kittle", "Chase Brown", "Josh Allen"], "one entry per game video"
    assert "2 more: game highlights" in got["card"] and "J. Allen, T. Bass" in got["card"], got["card"]
    assert got["open"] == 3 and got["thumb"] == "https://i.ytimg.com/vi/cccccccccc2/mqdefault.jpg"
    ctx.close()


@pytest.mark.render
def test_cards_mode_and_a_desktop_draw_the_reel_too(browser, page_file):
    ctx, page, errors = espn(browser, page_file, (360, 800), mode="cards")
    assert page.locator(".reel").count() == 1 and page.locator(".cardgrid").count() > 0
    ctx.close()
    ctx, page, errors = espn(browser, page_file, (1280, 900))
    assert page.locator(".reel").is_visible() and page.locator(".brief-line").first.is_visible(), "the list keeps its column"
    reel, rows, brief = (page.evaluate(f"(() => {{ const r = document.querySelector('{s}').getBoundingClientRect(); return [r.left, r.top, r.width]; }})()")
                         for s in (".reel", ".rl-rows", ".brief"))
    assert reel[0] == rows[0] and rows[1] > reel[1], "the reel sits above the rows, in their column"
    assert brief[0] > reel[0] + reel[2], "and the list beside both"
    assert page.locator(".reel-card:not([hidden])").count() >= 3
    assert page.evaluate("document.scrollingElement.scrollWidth - innerWidth") <= 0
    assert errors == []
    ctx.close()
