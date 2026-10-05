"""The ring on a roster head and the clip sheet it opens (roster clips, unit U5, 2026-10-05).
Runs on the ESPN fixture: Purdy (3 clips), Kittle and C. Brown (1 each) have the ring; Higgins has
none, but his club's game video is in LIVE_CLIPS. The page is a file here, where the embed cannot
load, so a test that wants the embed turns it on (clipEmbedOk); every https request is aborted, so
nothing leaves the machine."""
import re

import pytest

from test_render import drive, go, open_page  # noqa: F401

RING = ".row .head[data-clips]"
SHEET_OPEN = "document.getElementById('clipsheet').classList.contains('on')"
PROFILE_OPEN = "document.getElementById('modal').classList.contains('on')"


def roster(browser, page_file, viewport=(360, 780)):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    return ctx, page, errors


def row_of(page, name):
    return page.locator(".row", has=page.locator(".nm-full", has_text=name)).first


def open_ring(page, name="Brock Purdy"):
    row_of(page, name).locator(".head").click()
    page.wait_for_function(SHEET_OPEN)


@pytest.mark.render
def test_a_head_with_clips_has_the_ring_and_the_count(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    purdy, higgins = row_of(page, "Brock Purdy").locator(".head"), row_of(page, "Tee Higgins").locator(".head")
    assert purdy.get_attribute("data-clips") == "3"
    assert purdy.locator(".clipn").inner_text() == "3"
    assert purdy.get_attribute("role") == "button" and purdy.get_attribute("tabindex") == "0"
    assert "3 clips" in purdy.get_attribute("aria-label")
    assert row_of(page, "George Kittle").locator(".head").get_attribute("aria-label").endswith("1 clip")
    assert higgins.get_attribute("data-clips") is None and higgins.locator(".clipn").count() == 0
    assert higgins.get_attribute("role") is None
    assert errors == []
    ctx.close()


@pytest.fixture(scope="module")
def nosched_file(built, page_file):
    """The same page built with no schedule: the build writes it as one `const LIVE_SCHEDULE = {...};` line."""
    text, n = re.subn(r"^const LIVE_SCHEDULE = .*;$", "const LIVE_SCHEDULE = null;", built.page, count=1, flags=re.M)
    assert n == 1
    p = page_file.parent / "nosched.html"
    p.write_text(text, encoding="utf-8")
    return p


@pytest.mark.render
def test_a_club_finds_its_game_video_under_either_spelling_with_or_without_a_schedule(browser, page_file, nosched_file):
    probe = "[clipGameOf('LA'), clipGameOf('LAR'), clipGameOf('WAS'), clipGameOf('SF'), clipGameOf('ZZZ')].map(g => g && g.id)"
    for page_path, schedule in ((page_file, True), (nosched_file, False)):
        ctx, page, errors = roster(browser, page_path)
        assert page.evaluate("schedOk()") is schedule
        page.evaluate("LIVE_CLIPS.games.WSH = {id: 'wwwwwwwwww1', title: 'Game Highlights', secs: 9}")
        assert page.evaluate(probe) == ["cccccccccc1", "cccccccccc1", "wwwwwwwwww1", "cccccccccc1", None]
        assert errors == []
        ctx.close()


@pytest.mark.render
def test_the_sheet_header_carries_the_weeks_points_and_line_when_the_page_has_them(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    open_ring(page, "Chase Brown")
    assert page.locator("#clipsheet .clip-who p").count() == 1, "no box score for the week yet: position and team only"
    page.keyboard.press("Escape")
    page.evaluate("LIVE_GAMELOG.rows.push({slug: 'chase-brown', pos: 'RB', wk: 4, pts: 30.2, car: 20, rush_yds: 100, rush_td: 0,"
                  " rec: 2, rec_yds: 10, rec_td: 0, tgt: 3}); render()")
    open_ring(page, "Chase Brown")
    who = page.locator("#clipsheet .clip-who")
    assert who.locator("p").first.inner_text() == "RB · CIN"
    assert who.locator(".clip-wk").inner_text() == "30.2 · 20-100-0 · 2-10"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_ring_changes_no_row_height(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    with_ring = page.evaluate("[...document.querySelectorAll('.row')].map(r => r.getBoundingClientRect().height)")
    page.evaluate("document.querySelectorAll('.head[data-clips]').forEach(h => { h.removeAttribute('data-clips'); h.querySelector('.clipn').remove(); })")
    without = page.evaluate("[...document.querySelectorAll('.row')].map(r => r.getBoundingClientRect().height)")
    assert with_ring == without
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_ring_opens_the_clip_sheet_and_the_rest_of_the_row_opens_the_profile(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    open_ring(page)
    assert page.evaluate(SHEET_OPEN) and not page.evaluate(PROFILE_OPEN)
    sheet = page.locator("#clipsheet")
    assert sheet.get_attribute("role") == "dialog" and sheet.get_attribute("aria-hidden") == "false"
    assert sheet.is_visible()
    assert page.evaluate("document.getElementById('clipsheet').contains(document.activeElement)")
    assert "Brock Purdy" in sheet.locator(".clip-name").inner_text()
    page.keyboard.press("Escape")
    row_of(page, "Brock Purdy").locator(".nm").click()
    page.wait_for_function(PROFILE_OPEN)
    assert not page.evaluate(SHEET_OPEN)
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_ring_answers_enter_and_space_without_opening_the_profile(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    head = row_of(page, "Brock Purdy").locator(".head")
    for key in ("Enter", " "):
        head.focus()
        page.keyboard.press(key)
        page.wait_for_function(SHEET_OPEN)
        assert not page.evaluate(PROFILE_OPEN)
        page.keyboard.press("Escape")
        page.wait_for_function(f"!({SHEET_OPEN})")
    assert errors == []
    ctx.close()


@pytest.mark.render
@pytest.mark.parametrize("how", ["Escape", "close", "scrim"])
def test_the_sheet_closes_and_focus_goes_back_to_the_head(browser, page_file, how):
    ctx, page, errors = roster(browser, page_file)
    open_ring(page)
    if how == "Escape":
        page.keyboard.press("Escape")
    elif how == "close":
        page.locator("#clipsheet .clip-x").click()
    else:
        page.mouse.click(180, 40)     # the scrim above the sheet
    page.wait_for_function(f"!({SHEET_OPEN})")
    assert page.evaluate("document.activeElement === document.querySelector('.head[data-clips]')")
    assert page.evaluate("document.querySelector('#clipsheet').getAttribute('aria-hidden')") == "true"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_back_closes_the_sheet_before_it_changes_the_view(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    open_ring(page)
    page.go_back()
    page.wait_for_function(f"!({SHEET_OPEN})")
    assert page.locator(".row").count() > 0, "still on the roster"
    assert page.evaluate("location.hash") in ("#roster", "")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_the_stage_is_a_thumbnail_until_play_then_the_nocookie_embed(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    page.evaluate("clipEmbedOk = () => true")
    open_ring(page, "Chase Brown")      # his one clip plays here (embed true)
    stage = page.locator("#clipsheet [data-clipstage]")
    assert stage.locator("img").get_attribute("src") == "https://i.ytimg.com/vi/bbbbbbbbbb1/mqdefault.jpg"
    assert stage.locator("iframe").count() == 0
    ratio = stage.evaluate("e => e.getBoundingClientRect().width / e.getBoundingClientRect().height")
    assert abs(ratio - 16 / 9) < 0.02, ratio
    assert page.locator("#clipsheet script, script[src*='iframe_api']").count() == 0, "the API loads on the first play"
    stage.locator("[data-clipplay]").click()
    frame = stage.locator("iframe")
    src = frame.get_attribute("src")
    assert src.startswith("https://www.youtube-nocookie.com/embed/bbbbbbbbbb1?") and "enablejsapi=1" in src, src
    assert "autoplay" in frame.get_attribute("allow") and frame.get_attribute("title")
    assert page.locator("script[src*='iframe_api']").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_where_the_embed_cannot_load_the_stage_is_a_link_to_youtube(browser, page_file):
    ctx, page, errors = roster(browser, page_file)      # a file: the embed is off
    open_ring(page)
    link = page.locator("#clipsheet [data-clipstage] a")
    assert link.get_attribute("href") == "https://www.youtube.com/watch?v=aaaaaaaaaa1"
    assert "Watch on YouTube" in link.inner_text()
    assert page.locator("#clipsheet iframe").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_players_clips_are_bars_a_caption_and_a_list_and_a_tap_plays_one(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    page.evaluate("clipEmbedOk = () => true")
    open_ring(page)
    sheet = page.locator("#clipsheet")
    assert sheet.locator(".clip-bars i").count() == 3 and sheet.locator(".clip-bars i.now").count() == 1
    assert "Best plays" in sheet.locator(".clip-kick").text_content() and "1 of 3" in sheet.locator(".clip-kick").text_content()
    assert sheet.locator(".clip-list .clip-row").count() == 2, "the rest of his clips"
    assert sheet.locator(".clip-next").count() == 0, "opened from the ring: nothing is next"
    sheet.locator(".clip-row").last.click()          # the clip that plays here (the other two are YouTube's)
    assert "3 of 3" in sheet.locator(".clip-kick").text_content()
    assert "aaaaaaaaaa3" in sheet.locator("iframe").get_attribute("src")
    page.evaluate("clipAdvance()")
    assert "3 of 3" in sheet.locator(".clip-kick").text_content(), "the last clip rests"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_clip_that_cannot_embed_is_the_youtube_link_from_the_start_and_never_an_iframe(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    page.evaluate("clipEmbedOk = () => true")       # the page could embed; YouTube refuses this clip
    open_ring(page)                                 # Purdy's first clip: the NFL channel's best plays
    sheet = page.locator("#clipsheet")
    link = sheet.locator("[data-clipstage] a.clip-poster")
    assert link.get_attribute("href") == "https://www.youtube.com/watch?v=aaaaaaaaaa1"
    assert "Watch on YouTube" in link.inner_text() and link.locator(".yt-mark").count() == 1
    assert sheet.locator(".clip-play, [data-clipplay]").count() == 0, "no play button for a clip that does not play here"
    assert sheet.locator("iframe").count() == 0 and page.locator("script[src*='iframe_api']").count() == 0
    assert "Watch on YouTube" in link.get_attribute("aria-label")
    # The list marks the two he cannot play here and not the one he can; a tap on a marked row shows its link.
    rows = sheet.locator(".clip-row")
    assert [rows.nth(i).locator(".yt-mark").count() for i in range(2)] == [1, 0]
    assert "Watch on YouTube" in rows.first.get_attribute("aria-label")
    assert "aria-hidden" in rows.first.locator(".yt-mark").evaluate("e => e.getAttributeNames().join(' ')")
    rows.first.click()
    assert "2 of 3" in sheet.locator(".clip-kick").text_content()
    assert sheet.locator("[data-clipstage] a.clip-poster").get_attribute("href") == "https://www.youtube.com/watch?v=aaaaaaaaaa2"
    assert sheet.locator("iframe").count() == 0
    # Kittle has only that clip: opened from his own ring it is the link too.
    page.keyboard.press("Escape")
    open_ring(page, "George Kittle")
    assert page.locator("#clipsheet [data-clipstage] a.clip-poster").count() == 1 and page.locator("#clipsheet iframe").count() == 0
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_play_all_starts_at_the_first_clip_that_plays_and_skips_the_ones_that_do_not(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    page.evaluate("clipEmbedOk = () => true;"
                  "const r = TEAMS.espn.roster, by = n => r.find(p => p.n === n);"
                  "window.__q = [by('George Kittle'), by('Brock Purdy'), by('Chase Brown')];"
                  "clipSheetOpen(__q, 0, null, true)")
    sheet = page.locator("#clipsheet")
    assert "Brock Purdy" in sheet.locator(".clip-name").inner_text(), "Kittle has only blocked clips"
    assert "3 of 3" in sheet.locator(".clip-kick").text_content(), "Purdy's first two are blocked"
    nxt = sheet.locator(".clip-next")
    assert "Next: C. Brown" in nxt.inner_text() and "1 play" in nxt.inner_text()
    sheet.locator("[data-clipplay]").click()
    assert "aaaaaaaaaa3" in sheet.locator("iframe").get_attribute("src")
    page.evaluate("clipAdvance()")
    assert "Chase Brown" in sheet.locator(".clip-name").inner_text()
    assert "bbbbbbbbbb1" in sheet.locator("iframe").get_attribute("src")
    # A player of only blocked clips is skipped by the walk, though his own ring still opens him.
    page.evaluate("clipSheetOpen([__q[2], __q[0], __q[1]], 0, null, true)")
    assert "Next: B. Purdy" in sheet.locator(".clip-next").inner_text(), "Kittle is passed over"
    page.evaluate("clipAdvance()")
    assert "Brock Purdy" in sheet.locator(".clip-name").inner_text() and "aaaaaaaaaa3" in sheet.locator("iframe").get_attribute("src")
    # A queue with nothing that plays still opens, on its first entry's link.
    page.evaluate("clipSheetOpen([__q[0]], 0, null, true)")
    assert "George Kittle" in sheet.locator(".clip-name").inner_text() and sheet.locator("a.clip-poster").count() == 1
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_queue_plays_game_highlights_for_a_player_with_no_clips_then_hands_on(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    page.evaluate("clipEmbedOk = () => true;"
                  "const r = TEAMS.espn.roster; clipSheetOpen([r.find(p => p.n === 'Tee Higgins'), r.find(p => p.n === 'Brock Purdy')], 0, null)")
    sheet = page.locator("#clipsheet")
    assert "Game highlights" in sheet.locator(".clip-kick").text_content()
    assert "Bengals vs. Bills" in sheet.locator(".clip-title").inner_text()
    nxt = sheet.locator(".clip-next")
    assert sheet.locator("a.clip-poster").count() == 1 and sheet.locator("iframe").count() == 0, "game highlights are YouTube's own link"
    assert "Next: B. Purdy" in nxt.inner_text() and "1 play" in nxt.inner_text(), "only the clip that plays here counts"
    nxt.click()
    assert "Brock Purdy" in sheet.locator(".clip-name").inner_text()
    assert "aaaaaaaaaa3" in sheet.locator("iframe").get_attribute("src"), "he starts at his first clip that plays"
    assert sheet.locator(".clip-next").count() == 0, "Purdy is last"
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_nothing_scrolls_sideways_with_the_sheet_open(browser, page_file):
    ctx, page, errors = roster(browser, page_file)
    open_ring(page)
    wide = page.evaluate("""[document.documentElement, document.body, document.getElementById('clipsheet'),
      ...document.querySelectorAll('#clipsheet *')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.className || e.tagName)""")
    assert wide == []
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    assert errors == []
    ctx.close()
