"""Matchup > Start/Sit, draft A (ledger #94, David 2026-10-09): the reader's lineup leads, our one swap on top, a
tap to compare the two, then our calls a page at a time with the record beside them, and the defenses board last.
The logic is Node-tested (test_js_lineup.py); these check that the view draws it and that its taps work."""
import pathlib
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.matchups import MatchupsPage
from wording import words

# A page of calls on a phone, read from its constants file, never retyped.
LINEUP_JS = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js" / "data" / "lineup.js"
PAGE_ROWS = int(re.search(r"const MU_PAGE_ROWS = (\d+);", LINEUP_JS.read_text(encoding="utf-8"))[1])
REQ = pytest.mark.req("Start/Sit", ac="the lineup leads, with our one swap on top")
CALLS = pytest.mark.req("Start/Sit", ac="the calls page one kind at a time")

# The reader's team, planted as the build draws one (data/teams.js P): Burrow and Brown start, Purdy and a back of
# our own making sit. Brown projects 16.2 and Burrow 1.3 over Purdy in the fixture's Ranks; the test back's points
# decide the swap.
ROSTER = """
  TEAMS[VIEW].roster = [P('Joe Burrow', 'QB', 'CIN', 'joe-burrow', {slot: 'QB', start: true}),
    P('Chase Brown', 'RB', 'CIN', 'chase-brown', {slot: 'RB', start: true}),
    P('Brock Purdy', 'QB', 'SF', 'brock-purdy', {slot: 'BN', start: false}),
    P('Test Back', 'RB', 'CIN', 'test-back', {slot: 'BN', start: false}),
    P('Evan McPherson', 'K', 'CIN', 'evan-mcpherson', {slot: 'K', start: true})];
  LIVE_RANKS.rows.push({slug: 'test-back', n: 'Test Back', pos: 'RB', team: 'CIN', opp: 'NYJ', home: false, pts: %s, rank: 40});
  LIVE_SS3.calls['joe-burrow'] = 'SMASH';
  try { localStorage.removeItem('tw-ss-picks'); } catch (e) {}
"""
NO_TEAM = "try { localStorage.removeItem('tw-team'); } catch (e) {}"


@pytest.fixture
def view(mount):
    def open_(plant=""):
        page, errors = mount("ranks")
        return MatchupsPage(page).open(plant), errors
    return open_


@REQ
def test_the_lineup_leads_with_his_starters_then_his_bench(view):
    mu, errors = view(ROSTER % 17.0)
    assert mu.sections()[0] == "matchups-lineup"
    got = mu.lineup()
    assert [r["slug"] for r in got["starters"]] == ["joe-burrow", "chase-brown"], "a kicker is no lineup call"
    assert [r["slug"] for r in got["bench"]] == ["brock-purdy", "test-back"]
    assert got["starters"][0]["call"] == words("matchups.call.smash"), "a player we called wears the call"
    assert got["starters"][1]["pts"] == "16.2" and got["bench"][1]["pts"] == "17.0"
    assert errors == []


@REQ
def test_a_bench_player_who_out_projects_a_starter_is_our_call_to_start_him(view):
    mu, errors = view(ROSTER % 17.0)
    swap = mu.swap()
    assert swap["kind"] == "swap"
    assert swap["word"] == words("matchups.lineup.swap").format(a="T. Back", b="C. Brown")
    assert swap["gain"] == words("startsit.pick.gap").format(n="0.8")
    marks = {r["slug"]: r["mark"] for g in mu.lineup().values() for r in g}
    assert (marks["test-back"], marks["chase-brown"], marks["joe-burrow"]) == ("in", "out", "")
    assert errors == []


@REQ
def test_inside_half_a_point_the_swap_is_a_coin_flip(view):
    mu, errors = view(ROSTER % 16.0)
    swap = mu.swap()
    assert swap["kind"] == "flip"
    assert swap["word"] == words("matchups.lineup.flip").format(a="T. Back", b="C. Brown")
    assert errors == []


@REQ
def test_when_every_starter_projects_higher_we_keep_the_lineup_and_name_the_closest_call(view):
    mu, errors = view(ROSTER % 10.0)
    swap = mu.swap()
    assert swap["kind"] == "keep"
    assert swap["word"] == words("matchups.lineup.keep")
    assert swap["sub"] == words("matchups.lineup.keepSub").format(a="J. Burrow", b="B. Purdy")
    assert {r["mark"] for g in mu.lineup().values() for r in g} == {""}, "no row is marked when nothing changes"
    assert errors == []


BOOKS = """
  LIVE_RANKS.rows.find(r => r.slug === 'chase-brown').rank_pts = 20;
  LIVE_RANKS.rows.find(r => r.slug === 'test-back').rank_pts = 10;
"""


@REQ
def test_our_points_decide_two_backs_whatever_the_books_say(view):
    """VISION 2026-10-08, David: the rank is our own. Test Back out-projects Brown, and the books pricing Brown higher
    changes nothing: we'd start Test Back, and the card says no word about whose number it is."""
    mu, errors = view(ROSTER % 17.0 + BOOKS)
    swap = mu.swap()
    assert swap["kind"] == "swap"
    assert swap["word"] == words("matchups.lineup.swap").format(a="T. Back", b="C. Brown")
    assert swap["why"] == []
    assert errors == []


@REQ
def test_compare_the_two_opens_the_picker_on_that_pair(view):
    mu, errors = view(ROSTER % 17.0)
    assert mu.swap()["compare"] == words("matchups.lineup.compare")
    mu.compare_the_two()
    assert mu.picked() == ["test-back", "chase-brown"]
    assert errors == []


@pytest.mark.req("Start/Sit", ac="a reader with no team picked")
def test_with_no_team_picked_the_first_card_asks_for_one_and_offers_the_compare(view):
    mu, errors = view(NO_TEAM)
    assert mu.sections()[0] == "matchups-noteam"
    assert mu.noteam() == {"line": words("matchups.lineup.none"), "pick": words("matchups.lineup.pick"),
                           "compare": words("matchups.compare.link")}
    assert mu.swap() is None
    mu.compare_two()
    assert mu.picked() == [], "nobody is picked for him: the search is open"
    assert errors == []


@pytest.mark.req("Start/Sit", ac="a reader with no team picked")
def test_pick_your_team_opens_the_team_switch(view):
    mu, errors = view(NO_TEAM)
    mu.pick_team()
    assert mu.team_menu_open()
    assert errors == []


@CALLS
def test_the_calls_page_six_at_a_time_one_kind_at_a_time(view):
    mu, errors = view(ROSTER % 17.0)
    first = mu.calls()
    assert (first["kind"], first["counts"]) == ("smash", {"smash": "10", "start": "4", "sit": "5"})
    assert first["labels"] == {k: words(f"matchups.call.{k}") for k in ("smash", "start", "sit")}
    assert len(first["rows"]) == PAGE_ROWS and (first["prev"], first["next"]) == (False, True)
    assert first["page"] == words("matchups.calls.page").format(n=1, of=2)
    mu.next_page()
    second = mu.calls()
    assert len(second["rows"]) == 10 - PAGE_ROWS and (second["prev"], second["next"]) == (True, False)
    assert set(first["rows"]).isdisjoint(second["rows"])
    mu.kind("sit")
    sit = mu.calls()
    assert len(sit["rows"]) == 5 and sit["page"] == words("matchups.calls.page").format(n=1, of=1)
    assert errors == []


@CALLS
def test_the_record_sits_in_the_calls_card(view):
    mu, errors = view(ROSTER % 17.0)
    assert mu.record_in_calls()
    assert mu.record().startswith(words("matchups.record.label"))
    assert errors == []


@CALLS
def test_with_no_calls_posted_the_record_still_stands(view):
    mu, errors = view(ROSTER % 17.0 + "LIVE_SS3.smash.length = 0; LIVE_SS3.takes.length = 0;")
    assert "matchups-calls" not in mu.sections()
    assert mu.record().startswith(words("matchups.record.label"))
    assert errors == []


@REQ
def test_the_calls_then_last_week_then_the_board_follow_the_lineup(view):
    mu, errors = view(ROSTER % 17.0)
    assert mu.sections() == ["matchups-lineup", "matchups-calls", "matchups-last", "matchups-board"]
    assert errors == []
