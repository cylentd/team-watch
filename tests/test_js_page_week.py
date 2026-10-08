"""One page week (2026-10-05, David's decision; plan one-page-week), in Node.

The whole site turns week at one build: the first rebuild after the week's last game is final. Until
then every forward view says the schedule's week (LIVE_SCHEDULE.week, schedWeek), whatever the
projections, the Teams board or the props model carry; a backward view whose week is behind the page
says "Week W · final tomorrow" until its stats land. The reader's clock never picks a week."""
import json
import pathlib
import re

import pytest

from wording import words

JS = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js"


def pages(week=4, ranks=5, teams=5, model=5):
    return {"LIVE_SCHEDULE": {"week": week, "games": [], "alias": {}},
            "LIVE_RANKS": {"week": ranks} if ranks else None,
            "LIVE_TEAMS": {"week": teams} if teams else None,
            "LIVE_MARKET": {"model": {"week": model}} if model else None}


@pytest.fixture
def page(node_js):
    return lambda **kw: node_js("data/schedule.js", globals=pages(**kw))


def test_the_page_week_is_the_schedules_whatever_the_projections_say(page):
    js = page(week=4, ranks=5, teams=5, model=5)
    assert js("schedWeek()") == 4


def test_no_schedule_is_no_week(node_js):
    js = node_js("data/schedule.js", globals={"LIVE_SCHEDULE": None})
    assert js("schedWeek()") is None


def test_no_second_week_function_is_left(page):
    """slateWeek and slateWeekOf are gone: a label that asks them fails loudly, not with another week."""
    js = page()
    assert js("[typeof slateWeek, typeof slateWeekOf]") == ["undefined", "undefined"]


def test_no_source_file_reads_a_projection_weeks_for_a_label():
    """Greppable: the old rule's names and the three blocks' own weeks appear nowhere in the page's JS."""
    bad = re.compile(r"slateWeek|SLATE_WEEK|LIVE_RANKS\.week|LIVE_TEAMS\.week|LIVE_MARKET\.model\.week")
    hits = [f"{p.relative_to(JS)}:{n}" for p in JS.rglob("*.js") for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if bad.search(line)]
    assert hits == []


@pytest.mark.parametrize("sched, block, ok", [
    (4, 4, True),        # written for the page week
    (5, 4, False),       # the site turned, the producer has not: show the not-posted state
    (4, 5, False),       # a block ahead of the page is no more this week's
    (4, None, True),     # a block that names no week is not judged
    (None, 4, True),     # a page with no week judges nothing
])
def test_a_forward_block_is_for_the_page_week_or_it_is_not_shown(node_js, sched, block, ok):
    js = node_js("data/schedule.js", globals={"LIVE_SCHEDULE": {"week": sched, "games": [], "alias": {}}})
    assert js("schedIsPageWeek", block) is ok


# --- Ranks' "left off" line ------------------------------------------------------------------------

NOW = "2026-10-05T19:00:00Z"        # Monday 3 PM ET, before the 8:15 PM kickoff
TEAMS = ["ARI", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET"]


def off_page(node_js, games, week=4):
    js = node_js("data/schedule.js", globals={"LIVE_SCHEDULE": {"week": week, "alias": {}, "games": games}})
    js(f"(() => {{ Date.now = () => Date.parse('{NOW}'); return 1; }})()")
    return js


def game(away, home, kickoff, final=False, week=4):
    return {"week": week, "away": away, "home": home, "kickoff": kickoff, "final": final}


MONDAY = game("ATL", "NO", "2026-10-06T00:15:00Z")
SUNDAY = game("KC", "SF", "2026-10-04T20:25:00Z", final=True)


def test_a_few_teams_off_are_named(node_js):
    js = off_page(node_js, [MONDAY, SUNDAY])
    assert js("schedOffLine", TEAMS[:8]) == "ARI, BAL, BUF, CAR, CHI, CIN, CLE, DAL left off: already played or on a bye."


def test_past_eight_teams_the_line_names_what_is_left(node_js):
    js = off_page(node_js, [MONDAY, SUNDAY])
    assert js("schedOffLine", TEAMS[:9]) == "Only ATL @ NO left in week 4."


def test_a_few_games_left_are_each_named_and_many_are_counted(node_js):
    three = [MONDAY, game("MIA", "NYJ", "2026-10-06T02:00:00Z"), game("LV", "LAC", "2026-10-06T03:00:00Z"), SUNDAY]
    assert off_page(node_js, three)("schedOffLine", TEAMS) == "Only ATL @ NO, MIA @ NYJ, LV @ LAC left in week 4."
    six = [game("A", "B", "2026-10-06T00:15:00Z")] * 5 + [MONDAY]
    assert off_page(node_js, six)("schedOffLine", TEAMS) == "Only 6 games left in week 4."


def test_a_game_that_kicked_off_or_is_final_is_not_left(node_js):
    started = game("MIA", "NYJ", "2026-10-05T18:00:00Z")          # an hour before NOW, no final score yet
    js = off_page(node_js, [MONDAY, started, SUNDAY, game("GB", "MIN", "2026-10-12T17:00:00Z", week=5)])
    assert js("schedOffLine", TEAMS) == "Only ATL @ NO left in week 4."


def test_nothing_left_or_no_schedule_falls_back_to_the_teams(node_js):
    assert off_page(node_js, [SUNDAY])("schedOffLine", TEAMS).startswith("ARI, BAL, BUF")
    js = node_js("data/schedule.js", globals={"LIVE_SCHEDULE": None})
    assert js("schedOffLine", TEAMS).endswith("left off: already played or on a bye.")
    assert js("schedOffLine", []) == ""


# --- Preview: a game is over when the schedule says final ------------------------------------------

def preview_page(node_js, week, sched_week, final):
    games = [{"week": week, "home": "NO", "away": "ATL", "kickoff": "2026-10-06T00:15:00Z", "final": final}]
    return node_js("data/schedule.js", "data/preview.js", globals={
        "LIVE_SCHEDULE": {"week": sched_week, "games": games, "alias": {}},
        "LIVE_PREVIEW": {"week": week, "games": [{"away": "ATL", "home": "NO", "kickoff": "2026-10-06T00:15:00Z"}]}})


def test_a_final_game_is_over_before_its_four_hours_are_up(node_js):
    """Clock one hour after kickoff, so only the schedule's `final` can say over."""
    js = preview_page(node_js, 4, 4, True)
    js("(() => { Date.now = () => Date.parse('2026-10-06T01:15:00Z'); return 1; })()")
    assert js("pvOver", {"away": "ATL", "home": "NO", "kickoff": "2026-10-06T00:15:00Z"}) is True


def test_a_game_with_no_final_score_is_not_over_one_hour_in(node_js):
    js = preview_page(node_js, 4, 4, False)
    js("(() => { Date.now = () => Date.parse('2026-10-06T01:15:00Z'); return 1; })()")
    assert js("pvOver", {"away": "ATL", "home": "NO", "kickoff": "2026-10-06T00:15:00Z"}) is False


def test_preview_has_no_games_when_its_week_is_not_the_page_week(node_js):
    assert len(preview_page(node_js, 4, 4, False)("pvGames")) == 1
    assert preview_page(node_js, 4, 5, False)("pvGames") == []


# --- the Digest -----------------------------------------------------------------------------------

@pytest.fixture
def digest(node_js):
    return lambda **kw: node_js("data/schedule.js", "data/digest.js", globals=pages(**kw))


GAMES = [{"week": 4, "kickoff": "2026-10-06T00:15:00Z"}, {"week": 4, "kickoff": "2026-10-04T17:00:00Z"}]


def with_clock(js, now, games=GAMES):
    js(f"(() => {{ Date.now = () => Date.parse('{now}'); LIVE_SCHEDULE.games = {json.dumps(games)}; return 1; }})()")
    return js


def test_between_the_last_kickoff_and_the_turn_the_digest_names_the_next_week(digest):
    """Every game of week 4 has kicked off, the page week is still 4 (the Monday final is not in): the
    hurt row waits for week 5's report, not "Week 4's injury report is still in the trainer's room"."""
    js = with_clock(digest(week=4), "2026-10-06T02:00:00Z")
    assert js("dgWeekDone({week: 4})") is True
    assert js("dgRowWeek({week: 4})") == 5


def test_before_the_last_kickoff_the_digest_names_the_page_week(digest):
    js = with_clock(digest(week=4), "2026-10-05T12:00:00Z")
    assert js("dgWeekDone({week: 4})") is False
    assert js("dgRowWeek({week: 4})") == 4


def test_after_the_turn_the_digest_names_the_page_week_not_the_packets_plus_one(digest):
    """The clock is past every kickoff of the packet's week 4, but the page turned to 5 and the packet
    is week 5's own: its row says 5, and a packet still on week 4 is not "done" twice."""
    js = with_clock(digest(week=5), "2026-10-07T12:00:00Z")
    assert js("dgRowWeek({week: 5})") == 5
    assert js("dgRowWeek({week: 4})") == 5


def test_digest_row_week_falls_back_to_the_packets_without_a_schedule(node_js):
    js = node_js("data/schedule.js", "data/digest.js", globals={"LIVE_SCHEDULE": None})
    assert js("dgRowWeek({week: 4})") == 4


# --- backward views -------------------------------------------------------------------------------

@pytest.mark.parametrize("sched, recap, complete, turned", [
    (5, 4, False, True),     # the site has turned, week 4's stats have not landed
    (5, 4, True, False),     # stats landed: the usual label
    (4, 4, False, False),    # not turned: "so far" stays "so far"
    (5, 5, False, False),    # the recap is this week's own
])
def test_final_tomorrow_only_when_turned_and_incomplete(page, sched, recap, complete, turned):
    js = page(week=sched)
    assert js("schedFinalSoon", {"week": recap, "complete": complete}) is turned


def test_the_recap_kicker_words(page):
    js = page(week=5)
    assert js("recapKicker", {"week": 4, "complete": False}) == "Week 4 · final tomorrow"
    assert js("recapKicker", {"week": 4, "complete": True}) == "Week 4 · top score"
    js = page(week=4)
    assert js("recapKicker", {"week": 4, "complete": False}) == "Week 4 · top score so far"


def test_the_digests_recap_chip_stays_short_and_the_note_carries_final_tomorrow(page):
    """At 360px a chip of "Wk 4 · final tomorrow" left the row's text 31px; the chip is always "Wk 4"."""
    js = page(week=5)
    assert js("recapChip", {"week": 4, "complete": False}) == "Wk 4"
    assert js("recapChip", {"week": 4, "complete": True}) == "Wk 4"
    assert js("recapNote", {"week": 4, "complete": False}) == words("digest.recapRow.final")
    assert js("recapNote", {"week": 4, "complete": True}) == ""
    assert page(week=4)("recapNote", {"week": 4, "complete": False}) == ""
