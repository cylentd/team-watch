"""Live > TDs' TD clips reel (2026-10-05): Roster's clip rail above the Scored card, of the scorers the
chips keep, newest clip first. Clips come from LIVE_CLIPS (the finished week's) and from our function
(/api/clips?ch=<code>, asked every 5 minutes while the tab is on screen and a game is on).

Live is mounted (tests/component.py) on the game day tests/pages/live.py plants: SF at KC kicked off 20:25Z,
the clock 22:25Z, four scorers, a stubbed window.fetch that answers per channel, and the build's names
(jersey numbers, nicknames) for two of them. Every locator is in LivePage. Who a clip is of, when to ask and
how a reply joins what a channel held are in Node (tests/test_js_tdclips.py)."""
import pytest

from component import mount as base_mount  # noqa: F401  (the fixture, `mount` below)
from pages.live import PHONE, LivePage, ORDER, at, clip
from pages.warm import warm

pytestmark = pytest.mark.render


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with Live's phone context opened once for the module (pages/warm.py)."""
    return warm(base_mount, ("live", PHONE))


@pytest.mark.req("Clips", ac="the TD reel sits above Scored, newest first, with both sources merged")
def test_the_reel_sits_above_scored_newest_first_with_both_sources_merged(mount):
    live, errors = LivePage.open_tds(mount)
    assert live.reel_is_above_scored()
    assert live.reel_heading() == "TD clips"
    cards = live.reel_cards()
    assert [c["id"] for c in cards] == ORDER       # one o1 though LIVE_CLIPS and SF both carry it; o2 (no time) last
    by = {c["id"]: c for c in cards}
    # the second line is the scorer's TD line, never the clip's title; a clip of two scorers is one card naming both
    assert by["h1"]["nm"] == "T. Rusher, T. Catcher" and by["h1"]["cap"] == "2 rush TD"
    assert by["g1"]["nm"] == "T. Catcher" and by["g1"]["cap"] == "1 rec TD"
    assert by["d1"]["nm"] == "D. Grabber" and by["o2"]["cap"] == "1 rec TD"
    # the card is Roster's: a disc where it plays here, the YouTube chip and a link where it does not
    assert by["f1"]["tag"] == "BUTTON" and by["f1"]["disc"] and by["d1"]["tag"] == "A" and not by["d1"]["disc"]
    assert live.thumb_size() == [128, 160]
    # Play n counts what plays here (all but d1), and opens the theater on the first
    assert live.play_all_label() == "Play 8" and live.reel_count_label() == "9 clips"
    live.play_all()
    assert live.opened_in_theater() == {"ids": ORDER, "i": 0, "el": True}
    live.forget_opened()
    live.tap_clip("f3")
    assert live.opened_in_theater()["i"] == ORDER.index("f3")
    # rows are unchanged: Scored still lists the three scorers, and a row opens the profile
    assert live.scored_rows() == 3
    assert live.tap_first_scorer()["n"] == "Test Rusher"
    # the page does not scroll sideways for the rail
    assert not live.page_scrolls_sideways()
    assert errors == []


@pytest.mark.req("Clips", ac="a fresh clip is of a scorer by name, hashtag, nickname or his own jersey")
def test_a_fresh_clip_is_of_a_scorer_by_name_hashtag_nickname_or_his_own_jersey(mount):
    live, errors = LivePage.open_tds(mount)
    ids = set(live.reel_ids())
    assert {"f1", "h1"} <= ids                                      # last name, whole word
    assert "f2" in ids                                              # #TestRusher, no space
    assert "f4" in ids                                              # a nickname
    assert "f3" in ids                                              # No. 22, on SF's own channel
    assert "g2" not in ids and "h2" not in ids                      # 22 on KC's or the NFL's channel is nobody's
    assert "f7" not in ids                                          # 22 inside 22-17, 1:22 and 4th-and-22 is not a jersey
    assert "f5" not in ids and "g3" not in ids                      # a name on a channel that is neither his club's nor the NFL's
    assert "f6" not in ids                                          # posted before his game kicked off
    assert "p1" not in ids                                          # Test Passer scored no anytime TD: no Pass chip, no card
    assert errors == []


@pytest.mark.req("Clips", ac="the chips decide whose clips the reel holds")
def test_the_chips_decide_whose_clips_the_reel_holds(mount):
    live, errors = LivePage.open_tds(mount)
    live.toggle_chip("rush")
    assert live.reel_ids() == ["h1", "f1", "f4", "f3", "f2", "o1"]
    assert live.reel_cards()[0]["nm"] == "T. Rusher"
    live.toggle_chip("rush")
    live.toggle_chip("rec")
    assert live.reel_ids() == ["h1", "g1", "d1", "o2"]
    live.toggle_chip("rec")
    live.toggle_chip("pass")
    assert live.reel_ids() == ["p1"] and live.reel_cards()[0]["cap"] == "3 pass TD"
    # nobody the chips keep has a clip: no reel, and the Scored card is still there
    live.toggle_chip("pass")
    live.drop_every_clip()
    assert live.reel_count() == 0 and live.row_count() >= 3
    assert errors == []


@pytest.mark.req("Clips", ac="By game has no reel")
def test_by_game_has_no_reel(mount):
    live, errors = LivePage.open_tds(mount)
    live.toggle_by_game()
    assert live.reel_count() == 0 and live.game_card_count() >= 1
    live.toggle_by_game()
    assert live.reel_count() == 1
    assert errors == []


@pytest.mark.req("Clips", ac="one request per channel, four at a time")
def test_it_asks_one_request_per_channel_four_at_a_time(mount):
    live, errors = LivePage.open_tds(mount, wait=False)
    # (the tab was opened before the gate: ask again from a clean slate with every request held)
    live.wait_for_round()
    live.hold_requests()
    live.wait_for_requests_in_flight(4)
    # (a fifth request would have been made in the same tick as the first four: the lanes start together)
    assert [live.call_count(), live.in_flight()] == [4, 4], "a fifth waits for one of the four"
    live.release_requests()
    live.wait_for_round()
    # a page's first round: SF, KC, LA and WAS (under the nflverse spelling of LAR and WSH) are on, DET and MIN ended
    # two hours ago (inside the first round's six), then NFL; MIA and BUF kicked off days ago
    assert sorted(live.calls()) == sorted(["SF", "KC", "DET", "MIN", "LA", "WAS", "NFL"]), live.calls()
    assert live.peak_in_flight() == 4
    assert errors == []


@pytest.mark.req("Clips", ac="it asks again only after five minutes, while a game is on and the tab shows")
def test_it_asks_again_only_after_five_minutes_and_only_while_a_game_is_on_and_the_tab_shows(mount):
    live, errors = LivePage.open_tds(mount)
    n = live.call_count()
    assert n == 7
    later = 5                                                       # every round after the first: the clubs on now, and NFL
    live.advance(299)                                               # a poll repaints; the gap is not up (a request, if any, is made inside that call)
    assert live.call_count() == n
    # a hidden tab asks nothing, even long after
    live.set_tab_visible(False)
    live.advance(600)
    assert live.call_count() == n
    live.set_tab_visible(True)
    live.advance(1)
    live.wait_for_calls(n + later)
    assert sorted(live.calls_since(n)) == ["KC", "LA", "NFL", "SF", "WAS"], "DET and MIN ended over an hour ago"
    # another tab asks nothing either
    live.open_tab("games")
    live.advance(600)
    assert live.call_count() == n + later
    assert errors == []


@pytest.mark.req("Clips", ac="with no game on it asks nothing and the reel shows the page's clips")
def test_with_no_game_on_it_asks_nothing_and_the_reel_still_shows_the_page_clips(mount):
    live, errors = LivePage.open_tds(mount, hours=20, wait=False)
    live.wait_for_reel()
    assert live.call_count() == 0
    assert live.reel_ids() == ["o1", "o2"]                          # LIVE_CLIPS alone, no fetch (a Monday)
    assert errors == []


@pytest.mark.req("Clips", ac="a channel that fails keeps its last clips")
def test_a_channel_that_fails_keeps_its_last_clips(mount):
    live, errors = LivePage.open_tds(mount)
    assert "f1" in live.reel_ids() and "h1" in live.reel_ids()
    live.fail_channel("SF", reply_with_none_from=["NFL"])
    live.advance(301)
    live.wait_for_calls(12)
    ids = live.reel_ids()
    assert "f1" in ids and "f3" in ids, "SF failed: its clips stay"
    assert "h1" in ids, "NFL answered with none: what it held before stays (a reply joins, it never replaces)"
    assert errors == []


@pytest.mark.req("Clips", ac="a clip that joins on the left moves nothing the reader is looking at")
def test_a_clip_that_joins_on_the_left_moves_nothing_the_reader_is_looking_at(mount):
    live, errors = LivePage.open_tds(mount)
    # scrolled to the fifth card: the new clip is first, the same cards stay in view
    live.scroll_reel_to("f3")
    live.wait_for_scroll_rest(101)
    before, was = live.card_left("f3"), live.reel_scroll()
    live.reply_with_more("NFL", [clip("n1", "Test Rusher again!", at("22:29"))])
    live.advance(301)
    live.wait_for_calls(12)
    assert live.reel_ids()[0] == "n1"
    assert abs(live.card_left("f3") - before) <= 3
    assert live.reel_scroll() > was + 100
    # at the start of the rail a new clip is simply first, and in view
    live.scroll_reel_to_start()
    live.wait_for_scroll_rest()
    live.reply_with_more("NFL", [clip("n2", "Test Rusher thrice", at("22:31"))])
    live.advance(301)
    live.wait_for_calls(17)
    assert live.reel_ids()[0] == "n2" and live.reel_scroll() <= 1
    assert errors == []


@pytest.mark.req("Clips", ac="a reply joins what the channel held by id")
def test_a_reply_joins_what_the_channel_held_by_id(mount):
    live, errors = LivePage.open_tds(mount)
    # the NFL posts 40 uploads an hour on a Sunday: its next 50 newest no longer reach the early clips
    live.reply_with_only("NFL", [clip("n3", "Test Rusher once more", at("22:40"))])
    live.advance(301)
    live.wait_for_calls(12)
    assert live.channel_clip_ids("NFL") == ["n3", "h1", "h2", "p1"], "newest first, none lost"
    assert live.reel_ids()[:2] == ["n3", "h1"]
    assert errors == []


@pytest.mark.req("Clips", ac="a page opened after the last whistle asks once for the games of the last six hours")
def test_a_page_opened_after_the_last_whistle_asks_once_for_the_games_of_the_last_six_hours(mount):
    live, errors = LivePage.open_tds(mount, hours=4.5, post=True)
    assert sorted(live.calls()) == sorted(["SF", "KC", "LA", "WAS", "DET", "MIN", "NFL"])
    assert live.reel_count() == 1
    live.advance(301)                                               # every game is over an hour ago now: nothing more
    assert live.call_count() == 7
    assert errors == []


@pytest.mark.req("Clips", ac="a page opened the morning after the last whistle asks for nothing")
def test_a_page_opened_the_morning_after_asks_for_nothing(mount):
    live, errors = LivePage.open_tds(mount, hours=12, post=True, wait=False)     # opened the morning after
    live.wait_for_reel()
    assert live.call_count() == 0
    assert errors == []


@pytest.mark.req("Clips", ac="closing the theater after a repaint gives focus back to the card or the reel")
def test_closing_the_theater_after_a_repaint_gives_focus_back_to_the_same_card_or_the_reel(mount):
    live, errors = LivePage.open_tds(mount)
    live.use_the_real_theater()
    live.tap_clip("f3")
    live.wait_for_theater()
    live.repaint()                                                  # Live's 30 s poll: the card that opened the theater is detached
    assert live.theater_return_card_is_detached()
    live.press_escape()
    live.wait_for_theater_closed()
    assert live.focused_clip() == "f3" and live.focus_is_attached()
    live.tap_clip("f3")
    live.wait_for_theater()
    live.drop_fresh_clip("SF", "f3")                                # and now his clip is gone from the reel
    assert "f3" not in live.reel_ids()
    live.press_escape()
    live.wait_for_theater_closed()
    assert live.focus_is_on_first_card()
    assert errors == []
