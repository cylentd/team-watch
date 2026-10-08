"""This week > Live, the tabs, the strip and the mirrored lineups (2026-10-05, storyboard
https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP, option 2A): My league, NFL, TDs in one segmented
control (Matchup and League merged into My league that day); My league leads with a strip of the
league's matchups, then one row per starter slot, my starter against theirs, then the ranking.
Component tests (Live mounted, tests/component.py; every locator in tests/pages/live_tabs.py) on the week 2
fixture (tests/fixtures/gameday.json): SF's game is on, DET's has not started, every other game is final.
The reader's team is David's ESPN one unless a test says not."""
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.live_tabs import DESK, LiveTabsPage
from wording import words

pytestmark = pytest.mark.render


def test_three_tabs_and_my_league_is_a_mirrored_row_per_starter_slot(mount):
    live, errors = LiveTabsPage.open_league(mount)
    # A phone (2026-10-05): the Live pill opens in place into the three tabs, and the board draws no bar of its own.
    assert live.tab_names() == [words("live.tab.myleague"), "NFL", "TDs"]
    assert live.open_pill() == "Live"
    assert live.row_pressed_tab() == "league"
    assert live.bar_is_hidden()
    # nine starters in the reader's ESPN lineup: nine rows, each a slot pill between two halves
    starters = live.starter_count()
    assert starters == 9 and live.starter_rows() == 9
    assert live.rows_have_two_halves_and_a_slot()
    # every half with a game carries a clock button that opens the game sheet on his game
    clocks = live.clocks()
    assert len(clocks) >= 1      # the fixture schedule holds only some of week 2's clubs
    assert all(c["tag"] == "BUTTON" and re.match(r"^[^,]*,[A-Z]+,[A-Z]+$", c["nfl"]) and c["focus"] for c in clocks)
    assert live.nested_buttons() == 0            # never a button in a button
    # the slot pill wears the position's colour; FLEX wears the RB-WR-TE blend
    assert len({live.slot_colour("QB"), live.slot_colour("RB"), live.slot_colour("TE"), live.slot_colour("WR")}) == 4
    assert live.slot_class_count("qb") >= 1 and live.slot_class_count("def") >= 1
    assert live.slot_classes("FLEX") == ["gd-sl", "mix", "flex"]
    assert "linear-gradient" in live.slot_background("FLEX")
    # the median line sits under the score in a league that pays the top half
    assert re.match(r"^League median \d+\.\d · you [+−]\d+\.\d$", live.median_line())
    # benches are shut until the Benches row opens them, mirrored the same way
    assert live.bench_count() == 0
    live.open_benches()
    assert live.bench_rows() >= 1
    # a row's name opens his profile; a row's clock opens that game's sheet
    live.tap_first_name()
    live.wait_for_profile()
    live.press_escape()
    live.tap_first_clock()
    live.wait_for_game_sheet()
    live.press_escape()
    assert errors == []


def test_a_phone_fits_the_score_and_nine_starters_in_780px(mount):
    live, errors = LiveTabsPage.open_league(mount)
    live.wait_for_rows()
    m = live.layout()
    bar = live.tab_bar_top()
    # the header bar is the phone's team switch: the score head shows the reader's name, never a second switch
    assert live.switch_on_head_is_hidden() and live.my_name_is_visible()
    assert live.header_switch_is_visible()
    print("9th starter row bottom:", m["last"], "tallest row:", m["tallest"], "parts [top, height]:", m["parts"], "bottom bar top:", bar)
    # Since 2026-10-05 the phone's bottom tab bar covers the screen's last 64px: the rows end above it.
    assert m["last"] <= bar, m
    assert m["tallest"] <= 52, m
    assert errors == []


def test_games_tab_lists_every_game_live_first_and_a_tile_opens_the_sheet(mount):
    live, errors = LiveTabsPage.open_league(mount)
    n_games = live.week_game_count()
    assert n_games >= 3
    # the first game of the week is on, the second has not kicked off, the rest are final
    live.plant_week_states()
    # NFL carries the lime count of games on now, in the tab row on a phone (repainted with each poll)
    assert live.row_live_text() == "1"
    assert live.row_live_label() == words("live.tab.liveNow1")
    live.make_first_two_games_live()
    assert live.row_live_label() == "2 games live now"
    assert live.bar_live_label() == "2 games live now"   # and in the desktop's bar
    live.plant_week_states()
    live.open_tab("games")
    assert live.stored_tab() == "games"
    assert live.mirror_count() == 0 and live.now_card_count() == 0
    assert live.tile_count() == n_games
    kinds = live.tile_kinds()
    assert kinds[0] == "in" and kinds[1] == "pre" and set(kinds[2:]) == {"post"}
    # a tile with my starters has a lime edge and says how many; two tiles side by side on a phone
    assert live.mine_tile_count() >= 1 and re.match(r"^\d+ yours$", live.first_mine_tile_says())
    [lime] = live.colours("--lime")
    assert live.first_mine_tile_border() == lime
    xs = live.tile_lefts(2)
    assert xs[0] != xs[1]
    live.tap_first_tile()
    live.wait_for_game_sheet()
    live.press_escape()
    assert errors == []


def test_games_tiles_read_by_state_and_the_leader_wears_its_club_colour(mount):
    live, errors = LiveTabsPage.open_league(mount)
    live.plant_week_states()
    live.open_tab("games")
    # three states, three looks: a live tile has a lime stripe and wash, a final one is dimmer, an
    # upcoming one is the plain panel
    live_t, pre_t, post_t = (live.tile_style(k, "backgroundColor") for k in ("in", "pre", "post"))
    assert len({live_t, pre_t, post_t}) == 3
    assert "200, 255, 46" in live.tile_style("in", "boxShadow") and live.tile_style("pre", "boxShadow") == "none"
    # mine stays a ring: a lime border on every side, never the live stripe alone
    assert live.resting_mine_tile_count() >= 1 and live.resting_mine_tile_shadow() == "none"
    # who leads is read off the score: the trailer is grey, the leader is not, a tie is plain
    rows = live.tile_scores()
    assert rows
    wrong = [(a, h, ca, ch) for a, h, ca, ch in rows
             if (ca, ch) != (("lead", "behind") if a > h else ("behind", "lead") if h > a else ("plain", "plain"))]
    assert wrong == []
    # the leader's club code and score share one colour; it is the club's own when readable on the
    # panel (set as --tc), else the page's ink; the trailer is --ink-3
    ink, ink3 = live.colours("--ink", "--ink-3")
    cols = live.leader_colours()
    assert cols and all(c == b for c, b, _ in cols)
    assert all((tc != "") == (c != ink) for c, _, tc in cols)
    assert set(live.trailer_colours()) <= {ink3}
    # every club colour the tab can pick holds 3:1 against the panel; a near-black one falls back
    assert live.low_contrast_clubs() == []
    assert live.club_tint("KC") == "#e31837"
    # a navy primary is lifted in its own hue, not dropped to ink: blue stays the strongest channel
    nyg = live.club_tint("NYG")
    assert nyg and int(nyg[5:7], 16) > int(nyg[1:3], 16)
    uncoloured = live.clubs_without_tint()
    assert len(uncoloured) <= 2, uncoloured
    assert live.club_tint("WSH") == live.club_tint("WAS")
    assert errors == []


def test_the_strip_leads_my_league_and_a_chip_shows_its_game_without_leaving_the_tab(mount):
    live, errors = LiveTabsPage.open_league(mount)
    n = live.league_game_count()
    assert live.chip_count() == n and n >= 2
    # the strip sits on top, above the score head; the reader's game is first, ringed in lime, and on screen
    assert live.strip_order()[:2] == ["gd-strip", "gd-head"]
    assert "mine" in live.chip_classes(0) and "on" in live.chip_classes(0)
    assert live.my_chip_count() == 1
    [lime] = live.colours("--lime")
    assert live.chip_border_colour(0) == lime
    # each chip: a state word, then two short names with two scores
    assert all(c["state"] >= 1 and c["rows"] == 2 and c["scores"] == 2 for c in live.chip_shapes())
    assert all(re.match(r"^(LIVE|\d+ LEFT|FINAL)$", s.strip()) for s in live.chip_state_words())
    # a tap on another game shows it in the score head and the lineups, on the same tab
    live.tap_chip(1)
    assert live.picked_chip_count() == 1 and "mine" not in live.picked_chip_classes()
    assert live.bar_pressed_tab() == "league"
    assert re.match(r"^BY \d+\.\d$|^TIED$", live.lead_text())
    assert live.row_count() >= 1 and live.my_side_count() == 0
    # the reader's own chip brings their game back
    live.tap_my_chip()
    assert re.match(r"^(UP|DOWN) \d+\.\d$|^TIED$", live.lead_text())
    assert live.my_picked_chip_count() == 1
    # the ranking sits below the lineups: the median line in a league that pays the top half
    assert live.ladder_is_below_mirror()
    assert live.ladder_median_lines() == 1
    assert errors == []


def test_live_draws_no_league_chips_and_the_picked_team_decides_the_league(mount):
    live, errors = LiveTabsPage.open_league(mount, team="yahoo")
    assert live.league_count() >= 2, "the fixture needs two leagues"
    chips = {}
    for tab in ("league", "games", "tds"):
        live.open_tab(tab)
        chips[tab] = live.league_chip_count()
    assert chips == {"league": 0, "games": 0, "tds": 0}
    live.open_tab("league")
    assert live.league_key() == "yahoo"
    assert "Chat Take the Wheel" in live.my_side_text()
    # Live keeps no league setting of its own
    assert live.stored_league() is None
    live.pick_team("espn")
    assert live.league_key() == "espn"
    assert "Purdy Big in Japan" in live.my_side_text()
    assert errors == []


def test_the_readers_name_on_the_score_head_switches_team_and_stays_on_live(mount):
    # A desktop: a phone's header bar holds the switch, so its score head shows the plain name (test above).
    live, errors = LiveTabsPage.open_league(mount, DESK, team="yahoo")
    assert live.my_name_is_hidden()
    live.open_team_menu()
    # a poll does not shut the open menu
    live.repaint()
    assert live.team_menu_count() == 1
    live.choose_team("espn")
    assert live.state() == ["espn", "live", "espn"]
    assert "Purdy Big in Japan" in live.my_side_text()
    assert errors == []


def test_a_team_with_no_game_this_week_says_so_and_the_strip_leads_with_the_closest_game(mount):
    live, errors = LiveTabsPage.open_league(mount)
    # a bye: the reader's game leaves the week (out of the fantasy playoffs and week 18 look the same)
    live.remove_my_game()
    assert live.bye_text().endswith(words("live.bye"))
    assert live.bye_switch_count() == 1                      # the name still switches team
    assert live.mirror_count() == 0 and live.my_chip_count() == 0
    # the order itself is tested in Node (test_js_gdstrip.py); here, the first chip's two scores are the closest
    gaps = live.chip_gaps()
    assert len(gaps) >= 1 and gaps[0] == min(gaps)
    live.tap_chip(0)
    assert live.bye_count() == 0 and live.row_count() >= 1
    assert errors == []


def test_the_tab_survives_a_reload_of_the_view_and_a_blocked_store_still_switches(mount):
    live, errors = LiveTabsPage.open_league(mount)
    live.open_tab("tds")
    assert live.row_tab_pressed("tds") == "true"
    # the TDs tab hosts surface/live/tds.js, or an empty state while that file is absent
    assert live.tds_card_count() >= 1 or live.empty_state_count() == 1
    assert live.hash() in ("", "#live")                  # the tab is never in the hash
    live.open_tab("league")
    # another view sends the reader to a tab by setting it, then opening #live; the four tabs' old
    # values land on My league (matchup, league) and NFL (games)
    landed = []
    for old in ("matchup", "league", "games"):
        live.store_tab_and_render(old)
        landed.append(live.bar_pressed_tab())
    assert landed == ["league", "league", "games"]
    live.store_tab_and_render("nonsense")
    assert live.mirror_count() >= 1                           # anything else is the default
    live.block_storage()
    live.open_tab("games")
    assert live.tile_grid_count() == 1
    assert errors == []


def test_desktop_keeps_the_rows_one_reading_width(mount):
    live, errors = LiveTabsPage.open_league(mount, DESK)
    w = live.mirror_width()
    assert 400 < w <= 760
    assert errors == []
