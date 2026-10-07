"""Bets (2026-09-25): Build as one column of lines; Slips as a research board (2026-10-03: per
kickoff, a card per game, its players by work rising, a tap opens every line he has); the slip as a
tray that counts what lands in it, saves it, and opens into a sheet; one kickoff for both views. A
new view's cards arrive once, and a tap that only adds a leg pops that line without replaying the
arrival of everything else.

The fixture's slate: CIN @ NYJ in the morning (Tee Higgins out, Chase Brown questionable, Burrow),
SEA @ SF on Sunday night (Kittle: TD, receiving yards, Longest reception; no game log), DET @ GB on
Monday night (St. Brown: TD, yards, Longest reception, with a log; Gibbs a depth-2 back whose
rushing line the book moved).

Component tests mount Slips or Build (tests/pages/parlay.py and parlay_build.py hold every locator). The two that need
the full page (the phone's kickoff row lives in the nav chrome; Back closes a sheet) are journeys."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.parlay import ParlayPage
from pages.parlay_build import BuildPage
from test_render import open_page

pytestmark = pytest.mark.render

SECTION = "Parlay and DFS"
NOTE = "Same-game legs move together; the combined chance isn't shown."
# The book moves every line far from the model (build.py `stale`): a moved line never counts as paying more.
MOVE_EVERY_LINE = "() => { PROPS.forEach(p => { p.stale = 1; if (p.books && p.books.Underdog) p.books.Underdog.stale = 1; }); render(); }"


def passes_best_odds(book, facts):
    """The Best odds rule, written out as the oracle (the docstring of its test says it in words).
    `facts` is one listed line's prices from BuildPage.listed_line_facts."""
    if book == "underdog":
        u, d = facts["underdog"], facts["draftkings"]
        lower = u["pick"] == "lower"
        price = u["under"] if lower else u["over"]
        pays_more = price is not None and price > -107
        easier = d is not None and d["line"] is not None and (u["line"] > d["line"] if lower else u["line"] < d["line"])
        return not u["stale"] and (pays_more or easier)
    d, r = facts["draftkings"], facts["ref"]
    return not facts["stale"] and r is not None and (d["line"] < r["line"] or (d["line"] == r["line"] and d["over"] > r["over"]))


@pytest.fixture
def full(browser, page_file):
    """The whole page, for a journey: open(size) -> (ParlayPage, errors). Closed when the test ends."""
    opened = []

    def open_full(size):
        ctx, page, errors = open_page(browser, page_file, size)
        opened.append(ctx)
        return ParlayPage(page), errors
    yield open_full
    for ctx in opened:
        ctx.close()


@pytest.mark.req(SECTION, ac="Build is one column of lines that fits a phone; the line opens the sheet, the call adds the pick")
@pytest.mark.parametrize("book", ["underdog", "dk"])
def test_build_is_one_column_of_lines_that_fits_a_phone(mount, book):
    """Build (2026-09-29): one column under a heading per kickoff, a row per line -- the line, his
    games against it, the call. At 360px the six chips and every row stay on screen; the line and
    its bars open the leg sheet, the call adds the pick."""
    build, errors = BuildPage.open(mount, book, size=(360, 780))
    assert build.player_blocks() > 0
    assert build.right_edge() <= 360
    assert build.bar_controls() <= 6, "STYLE.md: up to ~6 siblings in the row"
    assert len(set(build.call_lefts())) == 1, "every call sits in one column"
    build.tap_first_line_evidence()
    assert build.sheet_open() and build.slip_size() == 0
    build.close_sheet()
    build.tap_first_call()
    assert build.slip_size() == 1
    assert errors == []


@pytest.mark.req(SECTION, ac="a line the book moved shows no chance, sorts last and adds nothing on a tap")
def test_a_moved_line_shows_no_chance_and_sorts_last(mount):
    """A line the book moved far from the model (build.py `stale`) shows "Line moved", no chance,
    and adds nothing on a tap: on 2026-09-29 every Underdog pick at 80%+ was one."""
    build, errors = BuildPage.open(mount, "underdog", size=(360, 780), sort="conf")
    i = build.move_most_confident_line()
    order = build.build_order()
    at = order.index(i)
    assert at > 0 and all(build.is_moved(j) for j in order[at:]), \
        "the top of the confidence sort sinks below every unmoved line"
    build.list_only(i)
    assert build.line_count() == 1
    line = build.only_line()
    assert line["moved"]
    assert "%" not in line["text"] and line["prop"] is None
    build.tap_call_of_only_line()
    assert build.sheet_key() == i and build.slip_size() == 0
    assert errors == []


@pytest.mark.req(SECTION, ac="Best odds keeps only lines that pay more, and each kept row says why")
@pytest.mark.parametrize("book", ["underdog", "dk"])
def test_best_odds_keeps_only_lines_that_pay_more(mount, book):
    """Best odds (2026-09-29): Underdog keeps a pick paying better than its -107 on the model's
    side, or at a line easier than DraftKings'; DraftKings keeps an over easier than the
    BettingPros consensus. Each kept row prints why."""
    build, errors = BuildPage.open(mount, book, size=(360, 780), best=True)
    kept = [passes_best_odds(book, facts) for facts in build.listed_line_facts()]
    assert all(kept)
    assert len(kept) < build.lines_without_best_odds()
    build.reapply_best_odds()
    assert kept, "the fixture keeps lines for both books"
    assert build.line_count() == build.lines_saying_why(), "every kept row says why"
    assert errors == []


@pytest.mark.req(SECTION, ac="Best odds with no line paying more says so, once")
@pytest.mark.parametrize("book", ["underdog", "dk"])
def test_best_odds_with_no_line_paying_more_shows_the_empty_state(mount, book):
    """The empty state of Best odds (the "Better price" chip): when the book moved every line, none pays more,
    so the list is replaced by one empty card. The fixture always keeps lines, so the test moves them all."""
    build, errors = BuildPage.open(mount, book, size=(360, 780), best=True)
    assert build.line_count() > 0 and build.empty_shown() == 0, "the fixture starts with lines that pay more"
    build.page.evaluate(MOVE_EVERY_LINE)
    assert build.line_count() == 0
    assert build.empty_shown() == 1
    assert errors == []


@pytest.mark.req("Motion", ac="a new view enters once and a tap pops only its line")
def test_a_new_view_enters_once_and_a_tap_pops_only_its_line(mount):
    build, errors = BuildPage.open_with_motion(mount)
    assert build.view_enters()
    build.tap_first_call()
    assert not build.view_enters()
    assert build.lines_just_tapped() == 1
    assert build.slip_count_bumped() == 1
    build.wait_for_tray_count(1)
    assert errors == []


@pytest.mark.req(SECTION, ac="the board is games of players with no line and no chance")
def test_the_board_is_games_of_players_with_no_line_and_no_chance(mount):
    """A card per game at the kickoff; a row per player: name, position and club, his work, "N lines"
    -- and no line, no side and no model % (those wait in the player sheet; the row's one pick is a
    label, never a button)."""
    board, errors = ParlayPage.slips(mount, "day-2026-09-13")
    assert board.game_count() == 2, "Sunday: CIN @ NYJ and SEA @ SF"
    assert board.game_titles() == ["CIN @ NYJ", "SEA @ SF"], "kickoff order"
    rows = board.row_summaries()
    assert rows
    assert board.row_controls() == 0
    wrong = [row["slug"] for row in rows
             if not row["go"].startswith(f"{board.line_count_of(row['slug'])} line")]
    assert wrong == []
    assert "model" not in board.board_text()
    assert errors == []


@pytest.mark.req(SECTION, ac="an out player and a moved line leave the board; a questionable starter and a backup stay")
def test_out_and_moved_lines_leave_the_board_and_a_backup_stays(mount):
    """Out (Higgins) and a moved line (Gibbs' rushing yards) leave; a questionable starter (Chase
    Brown) and a depth-2 back (Gibbs, on his touchdown line) stay -- David's wins were role players."""
    board, errors = ParlayPage.slips(mount, "morning")
    board.tap_chip("all")
    assert "T. Higgins" not in board.row_names() and "C. Brown" in board.row_names()
    board.show_window("evening-mon")
    board.tap_chip("all")
    assert "J. Gibbs" in board.row_names()
    assert board.markets_of("jahmyr-gibbs") == ["TD"], "his moved rushing line is not one of his lines"
    assert board.markets_of("amonra-st-brown") == ["TD", "REC"], "a LONG row is no line"
    board.tap_chip("role")
    assert board.row_names() == ["J. Gibbs"], "Role guys: a WR2 or deeper, a backup back"
    board.tap_chip("te")
    assert board.row_count() == 0 and board.none_notes() == 1
    assert board.chip_text("all") == "All 2"
    assert errors == []


@pytest.mark.req(SECTION, ac="no Work rising chip, no rising order, no green bar: a game opens on All")
def test_no_work_rising_chip_and_a_game_opens_on_all(mount):
    """12.33: the line already prices a work trend, and calls of rising or falling work hit 46.0% (dev) and 49.8%
    (held out), so the "Work rising" chip, its rising-first order and the green last bar went (2026-10-06). A
    game opens on All, with the chips TE, Role guys and All N, and the bars are all one colour."""
    board, errors = ParlayPage.slips(mount, "evening-mon")
    assert board.chip_kinds() == ["te", "role", "all"]
    assert board.pressed_chip() == "all"
    assert board.row_sentences() == 0, "no sentence under the work (2026-10-05)"
    assert board.spark_bars() >= 3
    assert board.rising_bars() == 0, "the last bar is never green"
    assert "rising" not in board.board_text().lower()
    assert errors == []


@pytest.mark.req(SECTION, ac="the player sheet holds every line with its last four, and two legs come from one sheet")
def test_the_player_sheet_holds_every_line_with_its_last_four(mount):
    """St. Brown's sheet: his touchdown (Yes) and receiving yards (Higher / Lower), each with his
    last four games against today's line; the touchdown "N% to score", the yards the model's tier
    (tests/test_prop_picks.py); then his longest catch in those
    games, history only (plan update 2026-10-03: no Longest reception line, so no sides, no count;
    the fixture's LONG prop rows are ignored, a game with no catch logged is a dash). Two legs from
    one sheet."""
    board, errors = ParlayPage.slips(mount, "evening-mon")
    board.plant_no_catch_in_last_game("amonra-st-brown")
    board.open_player_sheet("amonra-st-brown")
    assert board.sheet_open() and board.sheet_key() == "amonra-st-brown"
    lines = board.sheet_lines()
    assert len(lines) == 2
    assert lines[0]["market"].startswith("Anytime TD") and lines[1]["market"].startswith(board.market_word("REC"))
    assert lines[0]["sides"] == ["Yes"]
    assert [(line["cells"], line["notes"]) for line in lines] == [(4, 0), (4, 0)], "no N of 4 any more"
    assert board.sheet_model_pcts() == ["28% to score"], "only the touchdown keeps a %"
    long = board.sheet_longest()
    assert long["count"] == 1 and long["market"] == "Longest catch"
    assert long["extras"] == 0, "history only"
    assert len(long["cells"]) == 4 and long["cells"][-1] == "–", "no catch logged reads as a dash"
    rec, tdi = board.props_index("Amon-Ra St. Brown", "REC"), board.props_index("Amon-Ra St. Brown", "TD")
    board.pick_in_sheet(rec, "higher")
    board.pick_in_sheet(tdi, "higher")
    assert board.slip() == [[rec, "higher"], [tdi, "higher"]]
    assert board.sheet_open(), "the sheet stays up for the next leg"
    assert board.side_pressed(rec, "higher") == 1
    board.pick_in_sheet(rec, "lower")
    assert board.slip_side(rec) == "lower" and board.slip_size() == 2, "the other side swaps it"
    assert board.tray_count() == "2"
    board.close_sheet()
    assert board.row_on_slip("amonra-st-brown") == 1
    assert errors == []


@pytest.mark.journey
@pytest.mark.req(SECTION, ac="a board row opens its sheet and Back closes it")
def test_a_board_row_opens_its_sheet_and_back_closes_it(full):
    board, errors = full((360, 780))
    board.show_slips("evening-sun")
    before = board.href()
    board.tap_chip("all")
    board.tap_row("george-kittle")
    assert board.sheet_all_line_count() == 2, "Kittle: TD and yards; no log, so no longest-catch row"
    assert board.fits()
    board.go_back()
    assert board.href() == before and board.surface() == "parlay"
    assert errors == []


@pytest.mark.req(SECTION, ac="a saved slip survives a reload, marks its players, loads back with its sides and the x deletes it")
def test_a_saved_slip_survives_a_reload_and_marks_its_players(mount):
    """Save keeps the tray's slip on the device for the slate week; the same legs twice is one slip;
    a reload keeps it and its players carry "on slip"; a saved slip loads back with its sides; the
    x deletes it."""
    board, errors = ParlayPage.slips(mount, "evening-mon")
    rec = board.props_index("Amon-Ra St. Brown", "REC")
    board.open_player_sheet("amonra-st-brown")
    board.pick_in_sheet(rec, "lower")
    board.close_sheet()
    board.save_slip()
    assert board.save_disabled(), "saved: nothing new to save"
    key = board.saved_key()
    assert key.startswith("tw.slips.saved.")
    assert board.saved_on_device(key) == 1
    board.reload()
    board.show_slips("evening-mon")
    assert board.slip_size() == 0 and board.saved_count() == 1
    assert board.row_on_slip("amonra-st-brown") == 1
    board.open_tray()
    assert board.saved_rows() == 1
    board.load_saved()
    assert board.slip() == [[rec, "lower"]]
    assert board.slip_legs_in_open_sheet() == 1, "the sheet stays up, the slip in it"
    board.drop_saved()
    assert board.saved_count() == 0 and board.saved_rows() == 0
    assert errors == []


@pytest.mark.req(SECTION, ac="a slip with Longest reception has no chance and copies its side and Underdog's line")
def test_a_slip_with_longest_reception_has_no_chance_and_copies(mount):
    """A LONG prop row is tolerated though never offered (Build can still add one from the fixture):
    with no model chance, a slip holding it prints none rather than a wrong one, and its copied text
    names the side and Underdog's line."""
    board, errors = ParlayPage.slips(mount, "evening-mon")
    long, rec = board.props_index("Amon-Ra St. Brown", "LONG"), board.props_index("Amon-Ra St. Brown", "REC")
    board.put_on_slip([(rec, "higher"), (long, "higher")])
    assert board.slip_chance() is None
    board.open_tray()
    assert board.sheet_odds_rows() == 0
    assert board.sheet_slip_legs() == 2
    text = board.slip_text()
    assert "Amon-Ra St. Brown Higher 28.5 Longest rec" in text and "Amon-Ra St. Brown Higher 75.5" in text
    assert errors == []


@pytest.mark.req(SECTION, ac="the board fits a phone and spreads on a desktop")
def test_the_board_fits_a_phone_and_spreads_on_a_desktop(mount):
    """360px: nothing scrolls sideways and the first player sits on the first screen. 1280px: the
    day's two games side by side, sharing a top edge."""
    phone, errors = ParlayPage.slips(mount, "day-2026-09-13", size=(360, 800))
    assert phone.scroll_width() <= 360
    y = phone.first_row_top()
    assert y < 800, f"first row at {y}px"
    assert errors == []
    desk, errors = ParlayPage.slips(mount, "day-2026-09-13", size=(1280, 900))
    a, b = desk.game_box(0), desk.game_box(1)
    assert abs(a["y"] - b["y"]) < 1 and b["x"] > a["x"] + a["width"]
    assert desk.board_columns() >= 2
    assert errors == []


@pytest.mark.journey
@pytest.mark.req(SECTION, ac="the kickoff tabs pick what the board shows, and Build opens with the same kickoff")
def test_the_kickoff_tabs_pick_what_the_board_shows(full):
    """Slips' kickoff is its row of tabs (a whole day by its weekday, then its parts); a tab shows
    that kickoff's games, and Build opens with it. On a phone (2026-10-05) the tabs are the Slips pill's
    segments in the tab row, and the view's own row keeps only the book chip."""
    board, errors = full((360, 800))
    board.go_to_slips()
    assert board.desktop_tabs_hidden()
    labels = board.phone_tab_labels()
    assert labels, "the fixture has no kickoff windows"
    assert labels == board.kick_chip_labels()
    k = board.tap_phone_tab(1)
    assert board.kickoff() == {"chosen": k, "board": k}
    assert board.game_titles() == board.board_games()
    assert board.phone_tab_pressed(k) == 1
    assert board.desktop_tab_selected(k) == 1   # a desktop's row follows
    assert board.scroll_width() <= 360
    build = BuildPage(board.page)
    build.build_with_settings_panel()
    assert build.kickoff_setting() == k
    assert errors == []


@pytest.mark.req(SECTION, ac="the typed payout decides the verdict and belongs to its slip")
def test_the_typed_payout_decides_the_verdict(mount):
    """The sheet takes the multiplier the Underdog app quotes (2026-09-25): it starts at the
    standard board, the verdict follows what is typed without the field losing focus, and the
    number belongs to that slip only."""
    board, errors = ParlayPage.slips(mount, "morning")
    board.put_first_picks_on_slip(3)
    n = board.slip_size()
    assert n == 3
    board.open_tray()
    assert board.payout_shown() == str({2: 3, 3: 6, 4: 10, 5: 20}[n])
    board.type_payout("1.5")
    assert board.payout_verdict().startswith("Short of the 1.5× payout")
    assert board.payout_box_focused()
    board.type_payout("500")
    assert board.payout_verdict().startswith("Beats the 500× payout")
    board.drop_last_leg()
    assert board.payout_for_slip() == {1: None, 2: 3, 3: 6, 4: 10}[n - 1], "a changed slip goes back to the board"
    assert errors == []


@pytest.mark.req(SECTION, ac="a leg counts at the graded rate of its side")
def test_a_leg_counts_at_the_graded_rate_of_its_side(mount):
    """A higher pick counts at most 42.3% (ff-jarvis 12.51), a lower at most 56.3% (57.3% at the
    model's own lower at 65%+); a pick against the model's call at what the model leaves for it."""
    board, errors = ParlayPage.slips(mount, "morning")
    got = board.graded_rates()
    conf_hi = got["conf"] if got["pick"] == "higher" else 100 - got["conf"]
    assert got["hi"] == min(conf_hi, 42.3) and got["lo"] == min(100 - conf_hi, 56.3)
    assert board.longest_leg_rate() is None
    assert errors == []


@pytest.mark.req(SECTION, ac="a stack counts at its graded joint rate and gets no standard payout")
def test_a_stack_counts_at_its_graded_joint_rate(mount):
    """A QB and his top two receivers, all lower, hit together 23.1% (ff-jarvis 12.32), not the
    product of three legs, and a stack gets no standard payout."""
    board, errors = ParlayPage.slips(mount, "morning", size=(390, 844))
    got = board.planted_stack()
    assert got is not None, "no all-lower stack, even with one planted"
    assert abs(got["chance"] - 0.231) < 1e-9
    assert got["pay"] is None and got["inside"]
    assert errors == []


@pytest.mark.req("Motion", ac="reduced motion never marks an entrance")
def test_reduced_motion_never_marks_an_entrance(mount):
    build, errors = BuildPage.open(mount, size=(390, 844))
    assert not build.view_enters()
    build.tap_first_call()
    assert build.lines_just_tapped() == 0
    assert errors == []


@pytest.mark.req(SECTION, ac="a saved slip loads into the sheet: one bar per leg, then the slip")
def test_a_saved_slip_loads_into_the_sheet(mount):
    """A saved slip fills the tray with every leg at its side, and the tray opens the sheet: one bar
    per leg, then the slip itself, then the saved list. Every morning leg is one game (CIN @ NYJ), so there
    is no all-hit bar (tests below)."""
    board, errors = ParlayPage.slips(mount, "morning")
    board.put_every_pick_on_slip("higher")
    legs = board.slip_size()
    board.save_slip()
    board.clear_slip()
    board.open_tray()
    board.load_saved()
    assert board.slip_size() == legs and board.slip_all_on("higher")
    assert board.slip_sheet_open() == 1
    assert board.sheet_odds_rows() == legs
    assert board.sheet_slip_legs() == legs
    board.close_slip_sheet()
    assert errors == []


@pytest.mark.req(SECTION, ac="legs of different games keep the all-hit bar; a second leg of one game takes it away")
def test_legs_of_different_games_keep_the_all_hit_bar_and_a_second_leg_of_one_game_takes_it_away(mount):
    """2026-10-05 (plan "Bets UX" change 5): two legs of one game are not independent, so the slip shows each
    leg's own chance, no combined chance, no verdict against the payout, and says why."""
    board, errors = ParlayPage.slips(mount, "morning")
    brown = board.props_index("Chase Brown", "RUSH")
    purdy = board.props_index("Brock Purdy", "PASS")
    burrow = board.props_index("Joe Burrow", "PASS")
    board.put_on_slip([(brown, "higher"), (purdy, "lower")])
    board.open_tray()
    assert board.sheet_odds_rows() == 3 and board.sheet_all_hit_rows() == 1
    assert board.joint_notes() == 0
    assert board.all_hit_chance() != "—"
    board.close_slip_sheet()
    board.put_on_slip([(burrow, "lower")])   # Burrow plays Brown's game
    board.open_tray()
    assert board.sheet_odds_rows() == 3 and board.sheet_all_hit_rows() == 0
    assert board.joint_note().endswith(NOTE)
    assert board.all_hit_chance() == "—" and board.payout_verdict() == ""
    board.close_slip_sheet()
    assert errors == []
