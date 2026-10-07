"""The Week plays rail on the Roster (2026-10-05, Clips v2; one card per starter, two to a phone page,
text over the picture since Roster redesign unit C): a row the reader pages or drags, the "This week"
list folded to its one row while it shows. Runs on the ESPN fixture team, the one whose starters have
clips in tests/fixtures/data/clips.json: Purdy 3 (two that YouTube refuses on other sites, then one
tall that plays), Kittle 1 (refused; the same clip as Purdy's second, the touchdown pass, so it is one
item credited to both), C. Brown 2 (both play): three cards, five clips. The Yahoo team has C. Brown's
card and an end card for Burrow, whose club has a game video.

The clip theater and the warm-up belong to clipsheet.js (clipTheaterOpen, clipWarm), so
these tests put stubs on the page and check what the rail asks of them.

Component tests: the roster mounted (`mount`), read through `ClipsPage` (tests/pages/clips.py). The two
tests that leave the roster for another League leaf are `journey` tests on the full page."""
import contextlib
import re

import pytest

from component import mount as base_mount  # noqa: F401  (the fixture, `mount` below)
from pages.clips import ClipsPage
from pages.league_chip import LeagueChip
from pages.roster import RosterPage
from pages.warm import warm
from test_render import drive, go, open_page

PHONE = (360, 800)
DESKTOP = (1100, 800)


@pytest.fixture(scope="module")
def mount(base_mount):
    """`mount`, with the phone's context opened once for the module (pages/warm.py)."""
    return warm(base_mount, ("roster", PHONE))


def on_roster(mount, size=PHONE, clips=True, **show):
    """The roster mounted at a size, the rail's page object on it, and the team shown (`show`'s arguments)."""
    page, errors = mount("roster", size=size)
    rail = ClipsPage(page)
    if not clips:
        rail.drop_clips()
    rail.show(**show)
    return rail, errors


@contextlib.contextmanager
def whole_page(browser, page_file, size):
    """The full page on the roster, for the journeys that leave it: (page, errors)."""
    ctx, page, errors = open_page(browser, page_file, size)
    try:
        drive(page, go("roster"))
        yield page, errors
    finally:
        ctx.close()


@pytest.mark.render
def test_where_nothing_can_embed_every_card_is_a_youtube_link(mount):
    rail, errors = on_roster(mount, served=False)
    kinds = rail.kinds(end=False)
    assert kinds == ["A"] * 3, kinds
    assert rail.play_all_count() == 0, "no Play all when nothing plays here"
    assert errors == []


def test_the_rail_has_a_card_per_starter_best_scorer_first_with_a_count_on_each(mount):
    rail, errors = on_roster(mount, mode="cards", pack_opened=True)
    assert rail.reel_count() == 1
    assert rail.title() == "Week 4 plays"      # LIVE_CLIPS.week, not schedWeek()
    assert rail.count_label() == "5 clips", "every clip once, the shared pass too"
    assert rail.card_count() == 3 and rail.end_count() == 0, "every starter has a clip, so no end card"
    assert rail.names() == ["B. Purdy", "G. Kittle", "C. Brown"], "best scorer first"
    # A card with a clip that plays here is a button wearing the count of his clips; one whose clips
    # YouTube all refuses is a link wearing YouTube's chip where the count goes.
    kinds = rail.card_summaries()
    assert kinds == [["BUTTON", "3", False], ["A", None, True], ["BUTTON", "2", False]], kinds
    assert "YouTube" in rail.first_mark_text()
    # The picture is his first clip's still, in a 16:10 box that has its shape before the image loads.
    src = rail.thumb_sources()
    want = rail.first_clip_thumbs(["brock-purdy", "george-kittle", "chase-brown"])
    assert src == want and src[0] == "https://i.ytimg.com/vi/aaaaaaaaaa1/hqdefault.jpg", src
    thumb = rail.rect("thumb")
    assert thumb["w"] / thumb["h"] == pytest.approx(1.6, abs=.03)
    assert errors == []


def test_two_cards_fill_a_phone_page_and_the_third_waits_for_the_next(mount):
    rail, errors = on_roster(mount, mode="cards", pack_opened=True)
    track, a, b, c = rail.rect("track"), rail.rect("card", 0), rail.rect("card", 1), rail.rect("card", 2)
    assert abs(b["r"] - a["l"] - 2 * a["w"] - 8) < 1.5 and a["w"] == b["w"] == c["w"], "two cards and a gap fill the page"
    assert b["r"] <= track["r"] and c["l"] >= track["r"] - 1, "the third card does not show past the edge"
    assert rail.rect("card")["h"] == pytest.approx(rail.rect("thumb")["h"], abs=.5), "no text block under the picture"
    assert errors == []


def test_a_cards_name_points_and_stat_line_sit_inside_its_picture(mount):
    rail, errors = on_roster(mount, mode="cards", pack_opened=True)
    rail.plant_week_row("Brock Purdy", 17.6, "6-86-1 · 11 tgt")
    thumb = rail.rect("thumb")
    placed = rail.inside_its_picture()
    assert placed
    assert [(part, got["rect"], thumb) for part, got in placed.items() if not got["inside"]] == []
    assert rail.text("nm") == "B. Purdy" and rail.text("pt") == "17.6"
    assert rail.text("l2") == "6-86-1 · 11 tgt"
    nm, pt, l2, n = (rail.rect(p) for p in ("nm", "pt", "l2", "n"))
    assert nm["r"] <= pt["l"] and l2["t"] >= nm["t"] + nm["h"] - 1, "name left, points right, the stat line under"
    assert n["r"] > thumb["r"] - 12 and n["t"] < thumb["t"] + 12, "the count chip sits top right"
    assert rail.point_count() == 1, "a starter with no week row shows no points"
    assert errors == []


def test_the_team_line_is_one_row_with_the_switch_at_its_right_end(mount):
    """Since 2026-10-05 a phone names the team in the header bar (its team switch), so Roster's team line
    (surface/league/switch.js, the same on every League leaf) is the league line, with Sheet / Cards at its right end."""
    rail, errors = on_roster(mount, mode="cards", pack_opened=True)
    chip, roster = LeagueChip(rail.page), RosterPage(rail.page)
    got, switch = chip.line(), roster.mode_switch()
    sw, sub, line = switch["rect"], got["sub"], got["line"]
    assert got["chip_switch_hidden"] and got["header_switch_visible"]
    assert sw["t"] <= sub["t"] + sub["h"] and sub["t"] <= sw["t"] + sw["h"], "the switch shares the league line's row"
    assert sw["r"] >= 360 - 20 and sw["l"] > line["l"] + 100, "at the row's right end"
    assert line["h"] < 50, line
    assert sub["l"] == line["l"] and sub["r"] < sw["l"], "the league line, one line, beside the switch"
    assert got["sub_scroll_height"] <= 24, "one line (the ⓘ's tap height)"
    assert switch["buttons"] == [["sheet", "Sheet", "false", "", True], ["cards", "Cards", "true", "", True]], switch["buttons"]
    assert roster.mode_switch_rerips() == 0, "Rip again stays on the Starters rule"
    roster.mode("sheet")
    assert roster.start_rows() > 0 and roster.sheet_pressed() == "true"
    assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_every_league_leaf_draws_the_same_team_line(browser, page_file):
    """The six League leaves drew three shapes of team switch until 2026-10-05 (Roster's hero title, Waivers'
    full hero plus a boxed chip, the chip elsewhere), so the switch moved as the reader changed tab. Now one
    line, at the same height on each."""
    with whole_page(browser, page_file, PHONE) as (page, errors):
        ClipsPage(page).show("espn", "cards", pack_opened=True)
        chip = LeagueChip(page)
        chip.pick_on_screen_team()
        tops, names, drawn = {}, {}, {}
        for leaf in chip.league_leaves():
            got = chip.visit(leaf)
            drawn[leaf] = (got["chips"], got["heroes"])
            names[leaf] = got["name"]
            tops[leaf] = got["top"]
        assert drawn == {leaf: (1, 0) for leaf in drawn}
        assert len(tops) >= 4 and len(set(tops.values())) == 1, tops
        assert len(set(names.values())) == 1, names
        chip.back_to_roster()
        assert errors == []


@pytest.mark.render
@pytest.mark.journey
def test_recap_has_the_league_chip_and_no_hero_or_roster_switch(browser, page_file):
    """My recap (2026-09-27) kept the roster's one-row hero without its Sheet / Cards switch; since the League
    merge (2026-10-05) Recap draws the one chip instead of a hero."""
    with whole_page(browser, page_file, PHONE) as (page, errors):
        ClipsPage(page).show("espn", "cards", pack_opened=True)
        chip = LeagueChip(page)
        chip.open_old_recap()
        assert chip.surface() == "recap", "the old hash lands on Recap"
        got = chip.chrome()
        assert got["heroes"] == 0 and RosterPage(page).mode_switch_count() == 0
        assert got["chip_switch"] == 1
        assert errors == []


@pytest.mark.render
def test_the_header_says_play_all_when_something_plays_and_nothing_when_none_does(mount):
    rail, errors = on_roster(mount)
    assert rail.play_all_text() == "Play all"
    h2, small, all_, prev, nxt = (rail.rect(p) for p in ("title", "count", "all", "prev", "next"))
    assert h2["r"] <= small["l"] and small["r"] <= all_["l"] <= all_["r"] <= prev["l"] and prev["r"] <= nxt["l"], "title, count, Play all, then the arrows"
    centres = [r["t"] + r["h"] / 2 for r in (h2, small, all_, prev, nxt)]
    assert max(centres) - min(centres) < 10 and rail.rect("head")["h"] < 44, "one line"
    rail.disable_embedding()
    assert rail.play_all_count() == 0, "nothing plays here: no pill"
    assert rail.chip_count() == 0 and rail.link_count() == 3
    assert rail.count_label() == "5 clips"
    assert errors == []


@pytest.mark.render
def test_a_youtube_only_card_is_a_link_and_opens_no_theater(mount):
    rail, errors = on_roster(mount, stubs=True)
    link = rail.link()                                  # Kittle's: his one clip is the shared one YouTube refuses
    assert link["target"] == "_blank" and link["rel"] == "noopener"
    assert "youtube.com/" in link["href"] and "aaaaaaaaaa2" in link["href"], link["href"]
    want = rail.sheet_address("george-kittle")
    assert want is None or link["href"] == want, "the link is the sheet's own YouTube address"
    assert link["label"] == "Purdy finds Kittle for the touchdown, opens YouTube"
    rail.click_card("link_card")
    assert rail.opened() is None, "no sheet for a card that opens YouTube"
    assert errors == []


@pytest.mark.render
def test_a_card_opens_the_theater_on_his_clips_only_and_play_all_on_every_clip(mount):
    rail, errors = on_roster(mount, stubs=True)
    rail.click_card()                                   # Purdy's three, from his tall clip, the one that plays
    got = rail.opened()
    assert got["i"] == 2 and got["el"] == "BUTTON"
    assert got["ids"] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3"], "his clips only: the YouTube-only ones ride along"
    assert got["ps"][1] == ["Brock Purdy", "George Kittle"], "the shared pass is still credited to both"
    rail.clear_opened()
    rail.play_all()
    got = rail.opened()
    assert got["i"] == 2 and got["el"] == "BUTTON", "Play all starts at the first clip that plays"
    assert got["ids"] == ["aaaaaaaaaa1", "aaaaaaaaaa2", "aaaaaaaaaa3", "bbbbbbbbbb1", "bbbbbbbbbb2"], "every clip once, the shared one once"
    rail.clear_opened()
    rail.scroll_card_into_view(1)
    rail.click_card("button_card", 1)                   # Brown's two
    got = rail.opened()
    assert got["ids"] == ["bbbbbbbbbb1", "bbbbbbbbbb2"] and got["i"] == 0, got
    assert errors == []


@pytest.mark.render
def test_the_first_touch_warms_the_player_once_and_a_press_on_a_card_primes_nothing(mount):
    """A cue before the click's load is lost on real YouTube, so the rail only warms (test_clip_sheet pins the load)."""
    rail, errors = on_roster(mount, stubs=True)
    rail.tap_at("track")
    rail.tap_at("track")
    assert rail.warm_count() == 1, "once per render"
    assert not rail.has_prime_step(), "no prime step exists"
    rail.tap_at("button_card")
    assert rail.warm_count() == 1 and rail.opened()["i"] == 2
    rail.redraw()
    rail.tap_at("track")
    assert rail.warm_count() == 2, "a new render is a new rail"
    assert errors == []


@pytest.mark.render
def test_the_end_card_names_the_starters_with_no_clip_and_opens_their_game(mount):
    """C. Brown has clips; J. Burrow has none but his club has a game video; St. Brown and Gibbs
    play for DET, which has neither, so only Burrow is named."""
    rail, errors = on_roster(mount, team="yahoo", stubs=True)
    assert rail.card_count() == 2 and rail.end_count() == 1, "Brown's card, then the end card"
    end = rail.end_card()
    assert end["tag"] == "A" and end["target"] == "_blank"
    assert "cccccccccc2" in end["href"], "the first such game's video"
    assert end["no"] == "No clip"
    assert end["line"] == "J. Burrow: their game's highlights on YouTube"
    assert "YouTube" in end["mark"]
    thumbs = rail.thumb_rects()
    last, first = thumbs["end"], thumbs["first"]
    assert (last["w"], last["h"]) == (first["w"], first["h"]), "the same size as a clip card"
    assert rail.parts_inside_thumb("end"), "the end card's words fit its box"
    assert rail.play_all_text() == "Play all"
    rail.click_end()
    assert rail.opened() is None
    assert errors == []


@pytest.mark.render
def test_a_starter_with_no_game_video_is_not_named_and_a_bencher_never_is(mount):
    rail, errors = on_roster(mount)
    got = rail.plant_starters([("Josh Allen", "BUF", True), ("Tyler Bass", "BUF", True),
                               ("Bench Guy", "BUF", False), ("No Game", "ZZZ", True)])
    assert got == {"ends": ["Josh Allen", "Tyler Bass"], "line": "J. Allen, T. Bass: their game's highlights on YouTube", "items": 5}, got
    assert errors == []


@pytest.mark.render
def test_a_team_without_clips_has_no_rail(mount):
    rail, errors = on_roster(mount, team="espn-run-it-back")   # no starter has a clip
    assert rail.reel_count() == 0 and rail.rail_count_in_layout() == 0
    assert rail.list_lines() > 0 and rail.unfold_buttons() == 0
    assert errors == []


@pytest.mark.render
def test_the_rail_scrolls_sideways_a_page_at_a_time_and_nothing_else_does(mount):
    rail, errors = on_roster(mount)
    css = rail.track_css()
    assert css == ["auto", "x", "auto", "contain", "none"], "native touch scroll, x snapping (proximity is the default and prints as x), no bar, no paging"
    assert rail.every_card_snaps_to_start()
    assert rail.track_room() > 100
    prev, nxt = rail.arrow("prev"), rail.arrow("next")
    assert prev["visible"] and prev["disabled"] and nxt["enabled"], "three cards are more than the one page of two: the arrows turn it"
    # An arrow scrolls by the measured page: the cards that fit whole, each a width and a gap (two here).
    rail.catch_scroll_by()
    rail.step("next")
    card = rail.rect("card")
    assert rail.scrolled_by()["left"] == pytest.approx(2 * (card["w"] + 8), abs=1)
    rail.scroll_to(1000)                                # to the end: the page is out of cards
    rail.wait_until_next_disabled()
    assert rail.arrow("prev")["enabled"]
    assert rail.page_overflow() <= 0
    assert rail.stray_scrollers() == 0
    rail.scroll_to(200)                                 # touch scroll is the browser's; the same property it moves
    assert rail.scroll_left() > 100
    assert errors == []


@pytest.mark.render
def test_a_mouse_drags_the_rail_and_a_drag_opens_no_card(mount):
    rail, errors = on_roster(mount, stubs=True)
    rail.drag("card", 1, (-10, -40, -90, -150))         # a card on the page, a link here
    assert rail.scroll_left() > 100, "the rail followed the mouse"
    assert rail.opened() is None, "the click that ends a drag opens nothing"
    # A press that moves less than the threshold is still a click.
    rail.wait_until_at_rest()
    rail.scroll_to(0)
    rail.drag("button_card", 0, (2,))
    assert rail.opened()["i"] == 2, "a plain click opens its card after a drag"
    assert errors == []


@pytest.mark.render
def test_on_a_desktop_four_cards_make_a_page_and_the_arrows_hide_when_the_rail_fits(mount):
    rail, errors = on_roster(mount, size=DESKTOP)
    a, d = rail.rect("card"), rail.rect("track")
    assert d["w"] / a["w"] > 3.8, "four cards to a page from 760px"
    assert rail.track_fits(), "three cards fit the column"
    assert rail.first_arrow_hidden() and rail.fits_count() == 1
    assert errors == []


@pytest.mark.render
def test_on_a_desktop_a_card_and_the_end_card_fit_the_rail_and_hide_the_arrows(mount):
    rail, errors = on_roster(mount, size=DESKTOP, team="yahoo")     # a card and the end card: they fit
    assert rail.track_fits()
    assert rail.first_arrow_hidden() and rail.fits_count() == 1
    assert errors == []


@pytest.mark.render
def test_on_a_desktop_more_cards_than_a_page_turn_by_four_and_the_end_disables_next(mount):
    # More cards than a page: the page turns by four cards, and the end of the rail disables ›.
    rail, errors = on_roster(mount, size=DESKTOP)
    rail.add_cards(3)
    nxt = rail.arrow("next")
    assert nxt["visible"] and nxt["enabled"] and rail.arrow("prev")["disabled"]
    rail.catch_scroll_by()
    rail.step("next")
    card = rail.rect("card")
    assert rail.scrolled_by()["left"] == pytest.approx(4 * (card["w"] + 8), abs=1), "a page, measured"
    assert errors == []


@pytest.mark.render
def test_the_list_folds_while_the_rail_shows_and_show_opens_it(mount):
    rail, errors = on_roster(mount)
    assert rail.folded() == 1 and rail.list_lines() == 0
    assert re.fullmatch(r"\d+ things? to check", rail.fold_count_text())
    rail.unfold_list()
    assert rail.folded() == 0 and rail.list_lines() > 0
    assert rail.reel_count() == 1, "Show opens the list; the rail stays"
    unfolded = rail.list_html()
    # With no clips the page draws no rail and the very same list, unfolded.
    rail, errors = on_roster(mount, clips=False)
    assert rail.reel_count() == 0 and rail.unfold_buttons() == 0
    assert rail.list_html() == unfolded
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("team", ["espn", "yahoo"])
def test_the_first_starter_stays_on_the_first_screen_under_the_rail(mount, team):
    """The folded list pays for the rail. 2026-10-05, 360x800, Sheet: 573 with the 160px-tall cards of Clips v2,
    392 with the 16:10 two-up cards and the one-row hero of Roster redesign unit C."""
    rail, errors = on_roster(mount, team=team)
    with_reel = RosterPage(rail.page).first_starter_y()
    rail, errors = on_roster(mount, clips=False, team=team)
    without = RosterPage(rail.page).first_starter_y()
    assert with_reel < 430 and with_reel - without < 60, (with_reel, without)


@pytest.mark.render
def test_cards_mode_draws_the_rail_too(mount):
    rail, errors = on_roster(mount, mode="cards")
    assert rail.reel_count() == 1 and RosterPage(rail.page).card_grid_count() > 0
    assert errors == []


@pytest.mark.render
def test_a_desktop_draws_the_rail_above_the_rows_with_the_list_beside_both(mount):
    rail, errors = on_roster(mount, size=(1280, 900))
    assert rail.reel_visible() and rail.first_list_line_visible(), "the list keeps its column"
    cols = rail.columns()
    reel, rows, brief = cols["reel"], cols["rows"], cols["brief"]
    assert reel[0] == rows[0] and rows[1] > reel[1], "the rail sits above the rows, in their column"
    assert brief[0] > reel[0] + reel[2], "and the list beside both"
    assert rail.page_overflow() <= 0
    assert errors == []
