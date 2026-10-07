"""The clip theater and the ring that opens it (Clips v2, unit U4, 2026-10-05).
Runs on the ESPN fixture: Purdy (two clips YouTube refuses on other sites, then one tall that plays),
Kittle (one refused) and C. Brown (a tall and a wide that play) have the ring; Higgins has none, but his
club's game video is in LIVE_CLIPS. The page is a file here, where the embed cannot load, so `ClipSheet` stands
in for an http(s) page; every https request is aborted and `window.YT` is a stub that records what the page asks
of the player and lets a test fire its events, so nothing leaves the machine.

Component tests (2026-10-06): the roster mounted (`mount`), read through `ClipSheet` (tests/pages/clip_sheet.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.clip_sheet import YT_STUB, ClipSheet

PHONE = (360, 800)


def theater(mount, size=PHONE):
    """The ESPN roster mounted with the stub player: (ClipSheet, errors)."""
    page, errors = mount("roster", size=size, init=(YT_STUB,))
    return ClipSheet(page), errors


def test_one_player_plays_every_clip_and_ended_hands_on_to_the_next(mount):
    sheet, errors = theater(mount)
    sheet.play_all()
    assert sheet.counter() == "1 / 3"
    assert sheet.loads() == ["aaaaaaaaaa3"]
    sheet.state(0)
    assert sheet.loads() == ["aaaaaaaaaa3", "bbbbbbbbbb1"]
    assert sheet.counter() == "2 / 3"
    assert "Chase Brown" in sheet.who()["text"]
    sheet.state(0)
    assert sheet.loads()[-1] == "bbbbbbbbbb2"
    sheet.step("prev")
    sheet.step("next")
    assert sheet.loads()[-2:] == ["bbbbbbbbbb1", "bbbbbbbbbb2"]
    assert sheet.player_count() == 1 and sheet.calls("new") == 1
    assert sheet.own_iframes() == 0, "no iframe of ours: the one player is YouTube's"
    sheet.state(0)       # the last one ended: the end card
    assert sheet.end_visible()
    assert errors == []


def test_the_end_card_lists_the_youtube_only_clips_as_links_with_shorts_and_watch_urls(mount):
    sheet, errors = theater(mount)
    sheet.play_all()
    for _ in range(3):
        sheet.state(0)
    assert sheet.done_text() == "That's all 3"
    assert sheet.end_hrefs() == [
        "https://www.youtube.com/watch?v=aaaaaaaaaa1", "https://www.youtube.com/watch?v=aaaaaaaaaa2",
        "https://www.youtube.com/shorts/tallblock01"], "the shared touchdown pass is one row"
    assert sheet.end_row(1)["names"] == "B. Purdy, G. Kittle"
    row = sheet.end_row(2)
    assert row["target"] == "_blank" and "noopener" in row["rel"]
    assert "B. Purdy" in row["text"] and "A Short YouTube refuses" in row["text"] and "YouTube" in row["chip"]
    assert row["img"] == "https://i.ytimg.com/vi/tallblock01/oar2.jpg"
    assert sheet.end_row(1)["img"] == "https://i.ytimg.com/vi/aaaaaaaaaa2/hqdefault.jpg"
    assert sheet.is_disabled("next") and sheet.is_enabled("prev")
    sheet.step("prev")      # back to the last clip that played
    assert sheet.end_hidden() and sheet.loads()[-1] == "bbbbbbbbbb2"
    assert errors == []


def test_the_end_card_opens_when_nothing_plays_here_or_the_caller_asks_for_it(mount):
    sheet, errors = theater(mount)
    sheet.open(-1)
    assert sheet.end_visible() and sheet.done_count() == 0
    assert sheet.end_row_count() == 3
    assert sheet.calls("load") == 0
    sheet.close()
    sheet.forget_player()
    sheet.embed_ok(False)      # a file, the Artifact frame: nothing plays
    sheet.settle_layers()
    sheet.open(3)
    assert sheet.end_visible() and sheet.end_row_count() == 6
    assert sheet.player_count() == 0, "no player is built where it cannot play"
    assert errors == []


def test_a_tall_clip_is_a_9_16_box_no_wider_than_328_and_a_wide_clip_16_9(mount):
    sheet, errors = theater(mount)
    sheet.play_all(3)      # Brown's Short first
    t = sheet.box()
    assert t["w"] <= 328.01 and abs(t["w"] / t["h"] - 9 / 16) < 0.01, t
    assert t["bottom"] <= t["navTop"]
    sheet.state(0)         # his wide one
    w = sheet.box()
    assert abs(w["w"] - 328) < 1 and abs(w["w"] / w["h"] - 16 / 9) < 0.01, w
    assert sheet.box_is_tall() is False
    assert errors == []


def test_the_video_and_its_caption_are_centred_together_with_nothing_to_tap_under_them(mount):
    sheet, errors = theater(mount)
    sheet.play_all(4)      # the wide one: the most room above and below
    b = sheet.box()
    assert abs(b["mid"] - b["mainMid"]) < 1.5, b
    assert abs(b["capTop"] - b["bottom"]) < 1, "the caption sits right under the video, not at the bottom edge"
    assert b["navH"] == 72 and sheet.top_height() == 56
    assert sheet.taps_under_video() == [], "only the bottom row sits under the video"
    for which, size in (("prev", 48), ("next", 48), ("close", 44)):
        r = sheet.control_size(which)
        assert r["width"] == size and r["height"] == size, which
    assert sheet.up_next() == "Last clip"
    assert sheet.page_width() <= 360
    assert errors == []


def test_the_caption_names_the_player_and_the_bottom_row_who_is_next(mount):
    sheet, errors = theater(mount)
    sheet.play_all(2)
    who = sheet.who()
    assert who["names"] == "Brock Purdy" and "QB" in who["text"]
    assert sheet.title() == "Purdy scrambles for the first down"
    assert sheet.title_white_space() == "nowrap"
    assert sheet.up_next() == "Next: C. Brown"
    assert sheet.is_disabled("prev")
    assert sheet.old_parts_drawn() == 0
    assert errors == []


def test_error_150_shows_the_link_stage_and_play_all_moves_on_after_two_seconds(mount):
    sheet, errors = theater(mount)
    sheet.play_all(3)
    sheet.error(150)
    link = sheet.link_stage()
    assert link["href"] == "https://www.youtube.com/shorts/bbbbbbbbbb1" and "Watch on YouTube" in link["text"]
    assert link["img"] == "https://i.ytimg.com/vi/bbbbbbbbbb1/oar2.jpg"
    sheet.wait_for_load("bbbbbbbbbb2")
    assert sheet.link_stage_hidden() and sheet.counter() == "3 / 3"
    assert errors == []


def test_another_error_code_shows_the_link_stage_and_stays(mount):
    sheet, errors = theater(mount)
    sheet.play_all(3)
    # The 2 s the other code would take runs on the page's clock (VCLOCK), put back as it was after, so the
    # page keeps its real timers for the taps that follow.
    with sheet.virtual_clock():
        sheet.error(5)
        assert sheet.link_stage_visible()
        sheet.run_virtual(2400)
        assert sheet.counter() == "2 / 3" and sheet.loads() == ["bbbbbbbbbb1"]
    sheet.step("next")
    assert sheet.link_stage_hidden() and sheet.loads()[-1] == "bbbbbbbbbb2"
    assert errors == []


def test_blocked_autoplay_plays_muted_with_a_pill_and_a_tap_gives_the_sound_back_for_every_clip(mount):
    sheet, errors = theater(mount)
    sheet.play_all(3)
    assert sheet.sound_hidden()
    sheet.fire("onAutoplayBlocked")
    assert sheet.sound_visible() and sheet.sound_text() == "Tap for sound"
    assert sheet.calls("mute") == 1
    assert sheet.sound_background() == "rgb(200, 255, 46)"
    sheet.state(0)         # still muted on the next clip: the pill stays
    assert sheet.sound_visible()
    sheet.tap_sound()
    assert sheet.sound_hidden() and sheet.calls("unmute") == 1
    sheet.step("prev")
    assert sheet.sound_hidden(), "later clips keep the sound"
    assert errors == []


def test_a_start_the_browser_muted_shows_the_pill_too(mount):
    sheet, errors = theater(mount)
    sheet.play_all(3)
    sheet.player_muted_by_browser()
    sheet.state(1)
    assert sheet.sound_visible()
    assert errors == []


def test_a_tap_that_comes_before_the_player_is_ready_plays_when_it_is(mount):
    sheet, errors = theater(mount)
    sheet.open(3)
    assert sheet.player_count() == 1 and sheet.loads() == []
    sheet.fire("onReady")
    assert sheet.loads() == ["bbbbbbbbbb1"]
    assert errors == []


def test_warm_is_idempotent_and_builds_the_player_without_loading_or_cueing_a_clip(mount):
    sheet, errors = theater(mount)
    sheet.warm(3)
    assert sheet.player_count() == 1
    assert sheet.preconnects().count("https://i.ytimg.com/") == 1
    hosts = sheet.preconnects()
    assert "https://www.youtube-nocookie.com/" in hosts and "https://i.ytimg.com/" in hosts
    sheet.fire("onReady")
    assert sheet.cues_and_loads() == []
    assert errors == []


def test_a_tap_on_a_playable_rail_card_after_the_player_is_warm_sends_one_load_and_no_cue(mount):
    """Real YouTube drops a loadVideoById that follows a cueVideoById, so a press must cue nothing."""
    sheet, errors = theater(mount)
    sheet.warm()
    sheet.fire("onReady")
    sheet.rail.redraw()
    sheet.press_rail_card()
    assert sheet.calls("cue") == 0, "the press cues nothing"
    sheet.release()
    sheet.wait_open()
    assert sheet.cues_and_loads() == [["load", "aaaaaaaaaa3"]]
    assert errors == []


def test_one_clip_credited_to_two_starters_is_one_item_naming_both(mount):
    sheet, errors = theater(mount)
    items = sheet.items()
    assert [i[0] for i in items] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3", "bbbbbbbbbb1", "bbbbbbbbbb2", "tallblock01"]
    assert items[1][1] == ["Brock Purdy", "George Kittle"]
    sheet.open_second_item_embeddable()
    sheet.fire("onReady")
    who = sheet.who()
    assert who["names"] == "B. Purdy, G. Kittle"
    assert "QB/TE" in who["text"]
    assert sheet.loads() == ["aaaaaaaaaa2"] and sheet.counter() == "1 / 4"
    assert sheet.up_next() == "Next: B. Purdy"
    assert errors == []


def test_a_failed_api_load_while_the_theater_waits_shows_the_youtube_links(mount):
    sheet, errors = theater(mount)
    sheet.api_fails()      # the page's iframe_api request is aborted: the script's onerror fires
    sheet.open(3)
    sheet.wait_for_link_stage()
    link = sheet.link_stage()
    assert link["href"] == "https://www.youtube.com/shorts/bbbbbbbbbb1" and "Watch on YouTube" in link["text"]
    assert sheet.blocked() is True and sheet.waiting_clip() is None
    assert sheet.player_count() == 0 and sheet.loads() == []
    assert errors == []


def test_escape_back_and_the_close_button_shut_the_theater(mount):
    sheet, errors = theater(mount)
    sheet.play_all()
    sheet.press("Escape")
    assert not sheet.is_open() and sheet.last_call() == ["stop"]
    sheet.settle_layers()
    sheet.play_all()
    sheet.go_back()
    sheet.wait_closed()
    assert sheet.aria_hidden() == "true"
    sheet.play_all()
    sheet.close_button()
    assert not sheet.is_open()
    sheet.settle_layers()
    assert errors == []


def test_the_arrow_keys_step_and_the_counter_is_in_the_mono_face(mount):
    sheet, errors = theater(mount)
    sheet.play_all()
    sheet.press("ArrowRight")
    assert sheet.counter() == "2 / 3"
    sheet.press("ArrowLeft")
    assert sheet.counter() == "1 / 3"
    assert sheet.counter_font() == sheet.mono_font()
    assert errors == []


def test_the_theater_is_full_screen_and_opaque(mount):
    sheet, errors = theater(mount)
    sheet.play_all()
    r = sheet.sheet_rect()
    assert r["x"] == 0 and r["y"] == 0 and r["width"] == 360 and r["height"] == 800
    assert sheet.sheet_background() == "rgb(0, 0, 0)"
    assert sheet.covers_the_screen_at(180, 400)
    assert errors == []


def test_the_ring_warms_the_player_on_pointerdown_and_opens_his_own_clips(mount):
    sheet, errors = theater(mount)
    sheet.rail.redraw()
    sheet.ring_pointerdown("Chase Brown")
    assert sheet.player_count() == 1
    sheet.ring_click("Chase Brown")
    sheet.wait_open()
    sheet.fire("onReady")
    assert sheet.loads() == ["bbbbbbbbbb1"] and sheet.counter() == "1 / 2", "his own two clips, not the others"
    assert sheet.focus_inside_theater()
    sheet.press("Escape")
    sheet.wait_closed()
    assert sheet.focus_on_ring(), "focus goes back to the ring"
    assert errors == []


def test_a_ring_whose_clips_none_play_here_opens_the_end_card(mount):
    sheet, errors = theater(mount)
    sheet.rail.redraw()
    sheet.ring_click("George Kittle")
    sheet.wait_open()
    assert sheet.end_visible()
    assert sheet.end_hrefs() == ["https://www.youtube.com/watch?v=aaaaaaaaaa2"]
    assert sheet.calls("load") == 0
    assert errors == []


def test_a_player_with_no_clips_of_his_own_plays_his_games_highlight_link(mount):
    sheet, errors = theater(mount)
    sheet.open_items("Tee Higgins")
    assert sheet.end_hrefs() == ["https://www.youtube.com/watch?v=cccccccccc2"]
    assert "Bengals vs. Bills" in sheet.ends_text()
    assert errors == []


def test_the_theater_fits_a_desktop_screen_by_height(mount):
    sheet, errors = theater(mount, (1280, 600))
    sheet.open(4)
    b = sheet.box()
    assert b["bottom"] <= b["navTop"] and abs(b["w"] / b["h"] - 16 / 9) < 0.01 and abs(b["mid"] - b["mainMid"]) < 1.5, b
    assert b["w"] < 1280 - 32, "cut to the height it has"
    sheet.open(3)
    b = sheet.box()
    assert b["w"] <= 328.01 and b["bottom"] <= b["navTop"]
    assert errors == []
