"""The clip theater and the ring that opens it (Clips v2, unit U4, 2026-10-05).
Runs on the ESPN fixture: Purdy (two clips YouTube refuses on other sites, then one tall that plays),
Kittle (one refused) and C. Brown (a tall and a wide that play) have the ring; Higgins has none, but his
club's game video is in LIVE_CLIPS. The page is a file here, where the embed cannot load, so a test that
wants it on sets clipEmbedOk; every https request is aborted and `window.YT` is a stub that records what
the page asks of the player and lets a test fire its events, so nothing leaves the machine."""
import pytest

from test_render import drive, go, open_at

RING = ".row .head[data-clips]"
OPEN = "document.getElementById('clipsheet').classList.contains('on')"
STUB = """
window.__yt = {players: [], calls: []};
window.YT = {Player: class {
  constructor(target, opts){ this.opts = opts; this.muted = false; __yt.players.push(this); __yt.calls.push(['new', target]); }
  loadVideoById(id){ __yt.calls.push(['load', id]); }
  cueVideoById(id){ __yt.calls.push(['cue', id]); }
  stopVideo(){ __yt.calls.push(['stop']); }
  playVideo(){ __yt.calls.push(['play']); }
  mute(){ this.muted = true; __yt.calls.push(['mute']); }
  unMute(){ this.muted = false; __yt.calls.push(['unmute']); }
  isMuted(){ return this.muted; }
}};
"""
STUB += "window.__YTSTUB = window.YT;"
RESET = """() => { 'use strict';
  if (CT) clipClose();
  Object.assign(CP, {player: null, ready: false, load: null, muted: false, loud: false});
  CLIP_API = ""; CLIP_WAIT = []; CLIP_BLOCKED = false;
  window.YT = window.__YTSTUB;
  __yt.players.length = 0; __yt.calls.length = 0;
  clipEmbedOk = () => true;
}"""
# The rail's items for Purdy's three, Kittle's one (the touchdown pass is Purdy's second too: one item
# naming both) and Chase Brown's two, plus a Short YouTube refuses.
ITEMS = """() => {
  const r = TEAMS.espn.roster, by = n => r.find(p => p.n === n), p = by('Brock Purdy');
  const cards = ['Brock Purdy', 'George Kittle', 'Chase Brown'].map(n => ({p: by(n), clips: clipItemsOf(by(n))}));
  window.__items = [...reelItems(cards),
    {c: {id: 'tallblock01', title: 'A Short YouTube refuses', shape: 'tall', embed: false}, p, ps: [p]}];
}"""


@pytest.fixture(scope="module")
def theater(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (360, 800), init=[STUB])
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    page.evaluate(ITEMS)
    yield page, errors
    ctx.close()


@pytest.fixture
def pg(theater):
    page, errors = theater
    page.evaluate(RESET)
    page.wait_for_function("LAYER_SKIP.length === 0")
    page.evaluate("LAYERS.length = 0")
    del errors[:]
    yield page
    assert errors == [], errors


def ev(page, name, *args):
    """Fire one of the player's events, the way YouTube's script would."""
    page.evaluate(f"(a) => __yt.players[0].opts.events.{name}(a)", args[0] if args else {})


def state(page, code):
    ev(page, "onStateChange", {"data": code})


def play_all(page, start=2):
    """Items 0-5: Purdy's three (the second also Kittle's), Brown's two, a Short; 2, 3 and 4 play."""
    page.evaluate(f"clipTheaterOpen(__items, {start}, null)")
    ev(page, "onReady")


def loads(page):
    return page.evaluate("__yt.calls.filter(c => c[0] === 'load').map(c => c[1])")


def box(page):
    return page.evaluate("""(() => { const b = document.querySelector('[data-clipbox]').getBoundingClientRect(),
      m = document.querySelector('.clip-main').getBoundingClientRect(), n = document.querySelector('.clip-nav').getBoundingClientRect(),
      c = document.querySelector('.clip-cap').getBoundingClientRect();
      return {w: b.width, h: b.height, top: b.top, bottom: b.bottom, mid: (m.top + m.bottom) / 2, mainMid: (b.top + c.bottom) / 2,
        capTop: c.top, navTop: n.top, navH: n.height, vh: innerHeight, vw: innerWidth};
    })()""")


def test_one_player_plays_every_clip_and_ended_hands_on_to_the_next(pg):
    play_all(pg)
    assert pg.locator("[data-clipcount]").inner_text() == "1 / 3"
    assert loads(pg) == ["aaaaaaaaaa3"]
    state(pg, 0)
    assert loads(pg) == ["aaaaaaaaaa3", "bbbbbbbbbb1"]
    assert pg.locator("[data-clipcount]").inner_text() == "2 / 3"
    assert "Chase Brown" in pg.locator(".clip-who").inner_text()
    state(pg, 0)
    assert loads(pg)[-1] == "bbbbbbbbbb2"
    pg.locator("[data-clipprev]").click()
    pg.locator("[data-clipnext]").click()
    assert loads(pg)[-2:] == ["bbbbbbbbbb1", "bbbbbbbbbb2"]
    assert pg.evaluate("__yt.players.length") == 1 and pg.evaluate("__yt.calls.filter(c => c[0] === 'new').length") == 1
    assert pg.evaluate("document.querySelectorAll('#clipsheet iframe').length") == 0, "no iframe of ours: the one player is YouTube's"
    state(pg, 0)       # the last one ended: the end card
    assert pg.locator("[data-clipend]").is_visible()


def test_the_end_card_lists_the_youtube_only_clips_as_links_with_shorts_and_watch_urls(pg):
    play_all(pg)
    for _ in range(3):
        state(pg, 0)
    assert pg.locator(".clip-done").inner_text() == "That's all 3"
    rows = pg.locator(".clip-ends a")
    assert [rows.nth(i).get_attribute("href") for i in range(rows.count())] == [
        "https://www.youtube.com/watch?v=aaaaaaaaaa1", "https://www.youtube.com/watch?v=aaaaaaaaaa2",
        "https://www.youtube.com/shorts/tallblock01"], "the shared touchdown pass is one row"
    assert rows.nth(1).locator(".clip-rw b").inner_text() == "B. Purdy, G. Kittle"
    row = rows.nth(2)
    assert row.get_attribute("target") == "_blank" and "noopener" in row.get_attribute("rel")
    assert "B. Purdy" in row.inner_text() and "A Short YouTube refuses" in row.inner_text() and "YouTube" in row.locator(".clip-ytchip").inner_text()
    assert row.locator("img").get_attribute("src") == "https://i.ytimg.com/vi/tallblock01/oar2.jpg"
    assert rows.nth(1).locator("img").get_attribute("src") == "https://i.ytimg.com/vi/aaaaaaaaaa2/hqdefault.jpg"
    assert pg.locator("[data-clipnext]").is_disabled() and pg.locator("[data-clipprev]").is_enabled()
    pg.locator("[data-clipprev]").click()      # back to the last clip that played
    assert pg.locator(".clip-end").is_hidden() and loads(pg)[-1] == "bbbbbbbbbb2"


def test_the_end_card_opens_when_nothing_plays_here_or_the_caller_asks_for_it(pg):
    pg.evaluate("clipTheaterOpen(__items, -1, null)")
    assert pg.locator("[data-clipend]").is_visible() and pg.locator(".clip-done").count() == 0
    assert pg.locator(".clip-ends a").count() == 3
    assert pg.evaluate("__yt.calls.filter(c => c[0] === 'load').length") == 0
    pg.evaluate("clipClose()")
    pg.evaluate("() => { CP.player = null; CP.ready = false; __yt.players.length = 0; }")
    pg.evaluate("clipEmbedOk = () => false")      # a file, the Artifact frame: nothing plays
    pg.wait_for_function("LAYER_SKIP.length === 0")
    pg.evaluate("clipTheaterOpen(__items, 3, null)")
    assert pg.locator("[data-clipend]").is_visible() and pg.locator(".clip-ends a").count() == 6
    assert pg.evaluate("__yt.players.length") == 0, "no player is built where it cannot play"


def test_a_tall_clip_is_a_9_16_box_no_wider_than_328_and_a_wide_clip_16_9(pg):
    play_all(pg, 3)      # Brown's Short first
    t = box(pg)
    assert t["w"] <= 328.01 and abs(t["w"] / t["h"] - 9 / 16) < 0.01, t
    assert t["bottom"] <= t["navTop"]
    state(pg, 0)         # his wide one
    w = box(pg)
    assert abs(w["w"] - 328) < 1 and abs(w["w"] / w["h"] - 16 / 9) < 0.01, w
    assert pg.evaluate("document.querySelector('[data-clipbox]').classList.contains('tall')") is False


def test_the_video_and_its_caption_are_centred_together_with_nothing_to_tap_under_them(pg):
    play_all(pg, 4)      # the wide one: the most room above and below
    b = box(pg)
    assert abs(b["mid"] - b["mainMid"]) < 1.5, b
    assert abs(b["capTop"] - b["bottom"]) < 1, "the caption sits right under the video, not at the bottom edge"
    assert b["navH"] == 72 and pg.evaluate("document.querySelector('.clip-top').getBoundingClientRect().height") == 56
    taps = pg.evaluate("""(() => { const bx = document.querySelector('[data-clipbox]').getBoundingClientRect(),
      nav = document.querySelector('.clip-nav');
      return [...document.querySelectorAll('#clipsheet button, #clipsheet a[href], #clipsheet [tabindex]')]
        .filter(e => e.getClientRects().length && !nav.contains(e) && e.getBoundingClientRect().top >= bx.bottom - 1)
        .map(e => e.className); })()""")
    assert taps == [], "only the bottom row sits under the video"
    for sel, size in (("[data-clipprev]", 48), ("[data-clipnext]", 48), (".clip-x", 44)):
        r = pg.locator(sel).bounding_box()
        assert r["width"] == size and r["height"] == size, sel
    assert pg.locator(".clip-up").inner_text() == "Last clip"
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360


def test_the_caption_names_the_player_and_the_bottom_row_who_is_next(pg):
    play_all(pg, 2)
    cap = pg.locator("[data-clipcap]")
    assert cap.locator(".clip-who b").inner_text() == "Brock Purdy" and "QB" in cap.locator(".clip-who").inner_text()
    assert cap.locator(".clip-title").inner_text() == "Purdy scrambles for the first down"
    assert pg.evaluate("getComputedStyle(document.querySelector('.clip-title')).whiteSpace") == "nowrap"
    assert pg.locator(".clip-up").inner_text() == "Next: C. Brown"
    assert pg.locator("[data-clipprev]").is_disabled()
    assert pg.locator(".clip-bars, .clip-list, .clip-next").count() == 0


def test_error_150_shows_the_link_stage_and_play_all_moves_on_after_two_seconds(pg):
    play_all(pg, 3)
    ev(pg, "onError", {"data": 150})
    link = pg.locator("[data-cliplink] a")
    assert link.get_attribute("href") == "https://www.youtube.com/shorts/bbbbbbbbbb1" and "Watch on YouTube" in link.inner_text()
    assert pg.locator("[data-cliplink] img").get_attribute("src") == "https://i.ytimg.com/vi/bbbbbbbbbb1/oar2.jpg"
    pg.wait_for_function("__yt.calls.some(c => c[0] === 'load' && c[1] === 'bbbbbbbbbb2')", timeout=4000)
    assert pg.locator("[data-cliplink]").is_hidden() and pg.locator("[data-clipcount]").inner_text() == "3 / 3"


def test_another_error_code_shows_the_link_stage_and_stays(pg):
    play_all(pg, 3)
    ev(pg, "onError", {"data": 5})
    assert pg.locator("[data-cliplink] a").is_visible()
    pg.wait_for_timeout(2400)
    assert pg.locator("[data-clipcount]").inner_text() == "2 / 3" and loads(pg) == ["bbbbbbbbbb1"]
    pg.locator("[data-clipnext]").click()
    assert pg.locator("[data-cliplink]").is_hidden() and loads(pg)[-1] == "bbbbbbbbbb2"


def test_blocked_autoplay_plays_muted_with_a_pill_and_a_tap_gives_the_sound_back_for_every_clip(pg):
    play_all(pg, 3)
    pill = pg.locator("[data-clipsound]")
    assert pill.is_hidden()
    ev(pg, "onAutoplayBlocked")
    assert pill.is_visible() and pill.inner_text() == "Tap for sound"
    assert pg.evaluate("__yt.calls.filter(c => c[0] === 'mute').length") == 1
    assert pg.evaluate("getComputedStyle(document.querySelector('[data-clipsound]')).backgroundColor") == "rgb(200, 255, 46)"
    state(pg, 0)         # still muted on the next clip: the pill stays
    assert pill.is_visible()
    pill.click()
    assert pill.is_hidden() and pg.evaluate("__yt.calls.filter(c => c[0] === 'unmute').length") == 1
    pg.locator("[data-clipprev]").click()
    assert pill.is_hidden(), "later clips keep the sound"


def test_a_start_the_browser_muted_shows_the_pill_too(pg):
    play_all(pg, 3)
    pg.evaluate("__yt.players[0].muted = true")
    state(pg, 1)
    assert pg.locator("[data-clipsound]").is_visible()


def test_a_tap_that_comes_before_the_player_is_ready_plays_when_it_is(pg):
    pg.evaluate("clipTheaterOpen(__items, 3, null)")
    assert pg.evaluate("__yt.players.length") == 1 and loads(pg) == []
    ev(pg, "onReady")
    assert loads(pg) == ["bbbbbbbbbb1"]


def test_warm_is_idempotent_and_builds_the_player_without_loading_or_cueing_a_clip(pg):
    pg.evaluate("clipWarm(); clipWarm(); clipWarm()")
    assert pg.evaluate("__yt.players.length") == 1
    assert pg.evaluate("[...document.head.querySelectorAll('link[rel=preconnect]')].map(l => l.href)").count("https://i.ytimg.com/") == 1
    hosts = pg.evaluate("[...document.head.querySelectorAll('link[rel=preconnect]')].map(l => l.href)")
    assert "https://www.youtube-nocookie.com/" in hosts and "https://i.ytimg.com/" in hosts
    ev(pg, "onReady")
    assert pg.evaluate("__yt.calls.filter(c => c[0] === 'cue' || c[0] === 'load')") == []


def test_a_tap_on_a_playable_rail_card_after_the_player_is_warm_sends_one_load_and_no_cue(pg):
    """Real YouTube drops a loadVideoById that follows a cueVideoById, so a press must cue nothing."""
    pg.evaluate("clipWarm()")
    ev(pg, "onReady")
    pg.evaluate("render()")
    card = pg.locator("button.reel-card").first
    card.scroll_into_view_if_needed()
    box_ = card.bounding_box()
    pg.mouse.move(box_["x"] + 20, box_["y"] + 20)
    pg.mouse.down()
    assert pg.evaluate("__yt.calls.filter(c => c[0] === 'cue').length") == 0, "the press cues nothing"
    pg.mouse.up()
    pg.wait_for_function(OPEN)
    assert pg.evaluate("__yt.calls.filter(c => c[0] === 'cue' || c[0] === 'load')") == [["load", "aaaaaaaaaa3"]]


def test_one_clip_credited_to_two_starters_is_one_item_naming_both(pg):
    items = pg.evaluate("__items.map(it => [it.c.id, it.ps.map(p => p.n)])")
    assert [i[0] for i in items] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3", "bbbbbbbbbb1", "bbbbbbbbbb2", "tallblock01"]
    assert items[1][1] == ["Brock Purdy", "George Kittle"]
    pg.evaluate("""() => { const x = __items[1]; x.c = {...x.c, embed: true}; clipTheaterOpen(__items, 1, null); }""")
    ev(pg, "onReady")
    assert pg.locator(".clip-who b").inner_text() == "B. Purdy, G. Kittle"
    assert "QB/TE" in pg.locator(".clip-who").inner_text()
    assert loads(pg) == ["aaaaaaaaaa2"] and pg.locator("[data-clipcount]").inner_text() == "1 / 4"
    assert pg.locator(".clip-up").inner_text() == "Next: B. Purdy"
    pg.evaluate("__items[1].c = {...__items[1].c, embed: false}")


def test_a_failed_api_load_while_the_theater_waits_shows_the_youtube_links(pg):
    pg.evaluate("delete window.YT")      # the page's iframe_api request is aborted: the script's onerror fires
    pg.evaluate("clipTheaterOpen(__items, 3, null)")
    pg.wait_for_selector("[data-cliplink] a", state="visible")
    link = pg.locator("[data-cliplink] a")
    assert link.get_attribute("href") == "https://www.youtube.com/shorts/bbbbbbbbbb1" and "Watch on YouTube" in link.inner_text()
    assert pg.evaluate("CLIP_BLOCKED") is True and pg.evaluate("CP.load") is None
    assert pg.evaluate("__yt.players.length") == 0 and loads(pg) == []


def test_escape_back_and_the_close_button_shut_the_theater(pg):
    play_all(pg)
    pg.keyboard.press("Escape")
    assert not pg.evaluate(OPEN) and pg.evaluate("__yt.calls.slice(-1)[0]") == ["stop"]
    pg.wait_for_function("LAYER_SKIP.length === 0")
    play_all(pg)
    pg.go_back()
    pg.wait_for_function(f"!({OPEN})")
    assert pg.locator("#clipsheet").get_attribute("aria-hidden") == "true"
    play_all(pg)
    pg.locator(".clip-x").click()
    assert not pg.evaluate(OPEN)
    pg.wait_for_function("LAYER_SKIP.length === 0")


def test_the_arrow_keys_step_and_the_counter_is_in_the_mono_face(pg):
    play_all(pg)
    pg.keyboard.press("ArrowRight")
    assert pg.locator("[data-clipcount]").inner_text() == "2 / 3"
    pg.keyboard.press("ArrowLeft")
    assert pg.locator("[data-clipcount]").inner_text() == "1 / 3"
    mono = pg.evaluate("""(() => { const s = document.createElement('span'); s.style.fontFamily = 'var(--mono)';
      document.body.appendChild(s); const f = getComputedStyle(s).fontFamily; s.remove(); return f; })()""")
    assert pg.evaluate("getComputedStyle(document.querySelector('[data-clipcount]')).fontFamily") == mono


def test_the_theater_is_full_screen_and_opaque(pg):
    play_all(pg)
    r = pg.locator("#clipsheet").bounding_box()
    assert r["x"] == 0 and r["y"] == 0 and r["width"] == 360 and r["height"] == 800
    assert pg.evaluate("getComputedStyle(document.getElementById('clipsheet')).backgroundColor") == "rgb(0, 0, 0)"
    assert pg.evaluate("document.elementFromPoint(180, 400).closest('#clipsheet') !== null")


def test_the_ring_warms_the_player_on_pointerdown_and_opens_his_own_clips(pg):
    pg.evaluate("render()")
    head = pg.locator(".row", has=pg.locator(".nm-full", has_text="Chase Brown")).first.locator(".head")
    head.dispatch_event("pointerdown")
    assert pg.evaluate("__yt.players.length") == 1
    head.click()
    pg.wait_for_function(OPEN)
    ev(pg, "onReady")
    assert loads(pg) == ["bbbbbbbbbb1"] and pg.locator("[data-clipcount]").inner_text() == "1 / 2", "his own two clips, not the others"
    assert pg.evaluate("document.getElementById('clipsheet').contains(document.activeElement)")
    pg.keyboard.press("Escape")
    pg.wait_for_function(f"!({OPEN})")
    assert pg.evaluate("document.activeElement.matches('.head[data-clips]')"), "focus goes back to the ring"


def test_a_ring_whose_clips_none_play_here_opens_the_end_card(pg):
    pg.evaluate("render()")
    pg.locator(".row", has=pg.locator(".nm-full", has_text="George Kittle")).first.locator(".head").click()
    pg.wait_for_function(OPEN)
    assert pg.locator("[data-clipend]").is_visible()
    assert pg.locator(".clip-ends a").get_attribute("href") == "https://www.youtube.com/watch?v=aaaaaaaaaa2"
    assert pg.evaluate("__yt.calls.filter(c => c[0] === 'load').length") == 0


def test_a_player_with_no_clips_of_his_own_plays_his_games_highlight_link(pg):
    pg.evaluate("""() => { const p = TEAMS.espn.roster.find(p => p.n === 'Tee Higgins');
      const items = clipItemsOf(p).map(c => ({c, p})); clipTheaterOpen(items, -1, null); }""")
    assert pg.locator(".clip-ends a").get_attribute("href") == "https://www.youtube.com/watch?v=cccccccccc2"
    assert "Bengals vs. Bills" in pg.locator(".clip-ends").inner_text()


def test_the_theater_fits_a_desktop_screen_by_height(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, (1280, 600), init=[STUB])
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    page.evaluate(ITEMS)
    page.evaluate("clipEmbedOk = () => true")
    page.evaluate("clipTheaterOpen(__items, 4, null)")
    b = box(page)
    assert b["bottom"] <= b["navTop"] and abs(b["w"] / b["h"] - 16 / 9) < 0.01 and abs(b["mid"] - b["mainMid"]) < 1.5, b
    assert b["w"] < 1280 - 32, "cut to the height it has"
    page.evaluate("clipTheaterOpen(__items, 3, null)")
    b = box(page)
    assert b["w"] <= 328.01 and b["bottom"] <= b["navTop"]
    assert errors == []
    ctx.close()
