"""The Digest after kickoff (2026-10-04, storyboard JrM6hBMrAL2hjFzYPgKitV; DESIGN.md "Digest", "After kickoff").

Component tests on `mount("digest")` with Live's poll planted (`DigestPage.plant_live`); the two taps that
leave the Digest for Live's TDs tab are journeys on the full page.
"""
import re

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_live import LEAD, DigestLivePage
from test_render import open_at
from wording import words

PHONE = (390, 844)


@pytest.mark.render
@pytest.mark.req("Digest", ac="during a game the headline is the top score and Right now lists the top five")
def test_during_a_game_the_headline_is_the_top_score_and_right_now_lists_five(mount):
    """David, 2026-10-04: "Sometimes something big happens like injury or top scores. The headline should
    change accordingly. Need to know and Highlights become old news on kickoff." With a game on, the banner
    names the top scorer in GD_STATS.lead and says where his game is; Highlights becomes Right now, the top
    five and a touchdown count that opens Live's TDs tab; Need to know, with nothing left in it, is gone."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_live(noHurt=True, clock={"DET": {"state": "in", "q": 3, "clock": "4:12", "half": False, "detail": "", "clubs": ["DET"]}})
    assert dg.headline() == "St. Brown ERUPTS: 10 catches, 180 yards, 2 TDs"
    assert dg.lead_fact() == "12 tgt · Q3 4:12"                      # what the head (10 catches, 180 yards, 2 TDs) leaves out
    assert dg.now_title() == words("digest.live.title")
    assert dg.facts_panels() == 1                                    # Right now is the one .dg-facts panel
    assert dg.now_rows() == 3                                        # three rows, then More (2026-10-05)
    first = dg.now_first_row_text()
    assert "A. St. Brown" in first and "WR" in first and "DET" in first and "Q3 4:12" in first and "31.4" in first
    assert dg.now_points() == ["31.4", "27.1", "24.0"]
    assert dg.now_more() == {"text": "More", "expanded": "false"}
    dg.tap_now_more()                                                # the rest opens in place: no navigation, no rebuild
    assert dg.now_rows() == 5 and dg.hash() != "#live"
    assert dg.now_points() == ["31.4", "27.1", "24.0", "19.2", "17.8"]
    assert dg.now_more_text() == "Less"
    dg.tap_now_more()
    assert dg.now_rows() == 3
    dg.tap_now_more()
    tds = sum(int(v["s"].get("rush_td", 0)) + int(v["s"].get("rec_td", 0)) for v in LEAD.values())
    assert dg.now_td_text() == f"{tds} touchdowns so far"
    assert dg.need_count() == 0 and "no-need" in dg.ticker_classes()
    dg.tap_now_row()                                                 # a scorer opens his profile
    assert dg.profile_open()
    dg.close_profile()
    assert errors == []


@pytest.mark.journey
@pytest.mark.render
@pytest.mark.req("Digest", ac="the touchdown count opens Live's TDs tab")
def test_the_touchdown_count_opens_lives_tds_tab(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#digest")
    try:
        dg = DigestLivePage(page)
        dg.plant_live(noHurt=True)
        dg.tap_now_td()
        assert dg.stored_live_tab() == "tds"
        assert dg.hash() == "#live"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.journey
@pytest.mark.render
@pytest.mark.req("Digest", ac="the TDs link opens Live's TDs tab even when storage throws")
def test_the_tds_link_opens_lives_tds_tab_even_when_storage_throws(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#digest")
    try:
        dg = DigestLivePage(page)
        dg.plant_live(noHurt=True)
        dg.block_storage()
        dg.tap_now_td()
        assert dg.hash() == "#live"
        assert dg.live_tab() == "tds"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
@pytest.mark.req("Digest", ac="a poll repaints the headline in place, and does nothing off the Digest")
def test_a_poll_repaints_the_headline_in_place(mount):
    """paintDigestLive swaps the banner and Right now when their words change and never rebuilds the page
    under a thumb; off the Digest it does nothing."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_live()
    dg.mark_root()
    dg.plant_scorer_pts("9226", 40.2)
    dg.paint_poll()
    kept, head, rows = dg.root_is_marked(), dg.headline_text(), dg.now_points()
    dg.paint_poll_off_the_digest(1.0)
    assert errors == []
    assert kept and head == "Achane ERUPTS: 170 yards, 1 TD"
    assert rows[0] == "40.2" and dg.headline_text() == head


@pytest.mark.render
@pytest.mark.req("Digest", ac="before the first kickoff the Digest is unchanged by the week's live data")
def test_before_the_first_kickoff_the_digest_is_unchanged(mount):
    """Nothing about the week's live data may change the Digest until a game starts."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_live(at="2026-10-04T08:00:00Z", sunState="pre_game")
    drawn = dg.html()
    assert dg.live_parts() == 0
    head = dg.headline()
    assert "going into" not in head and "points" not in head
    dg.clear_scorers()
    assert dg.html() == drawn
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="the banner opens its player after swapping between the packet's lead and a live one")
def test_the_banner_opens_its_player_after_swapping_between_the_packets_lead_and_a_live_one(mount):
    """The band is a data-dgslug button (wired once, when the page renders) or a data-dglv one (the page's
    one listener). Between windows the packet's hurt lead stands; once a game is on the top scorer takes
    it. The swap must render again, or the button swapped in is dead."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_live(at="2026-10-05T09:00:00Z", sunState="complete", mon=["NYG", "DAL"])
    dg.plant_extra_late_games()
    assert dg.lead_buttons()["slug"] == 1 and dg.mnf_cards() == 0
    dg.tap_lead_and_close()
    dg.plant_banner_state("2026-10-05T15:30:00Z", "in_game")
    assert dg.lead_buttons()["live"] == 1 and "yards" in dg.headline()
    dg.tap_lead_and_close()
    dg.plant_banner_state("2026-10-05T09:00:00Z", "pre_game")
    assert dg.lead_buttons()["slug"] == 1 and "points" not in dg.headline()
    dg.tap_lead_and_close()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="Monday night is one card")
def test_monday_night_is_one_card(mount):
    """Monday 6 AM Pacific, PHI @ CHI tonight and all the week has left: the card says who is out and
    who steps in, with no word of what the books moved (12.46 failed its backtest; the "Moved" list and the
    "books moved CHI's pass catchers" line went 2026-10-06). The ticker it once stood above went 2026-10-06."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.set_clock("2026-09-28T13:00:00Z")
    story = dg.tn_story()
    assert story == "Caleb Williams is out (hamstring). Case Keenum is CHI's projected QB."
    assert "books" not in story and "combined" not in story and "flat" not in story
    assert dg.tn_list_heads() == ["Out", words("digest.tn.calls.h"), words("digest.tn.proj.h")], "no Moved list"
    assert "move" not in dg.tn_foot()
    assert dg.retired_rows() == 0
    # After kickoff the card is the game's one block (mnf.js), a tap away from its sheet.
    dg.start_monday_game()
    assert dg.tn_block_count() == 1
    assert re.fullmatch(r"[A-Z]{3} · .+", dg.tn_when())
    assert errors == []
