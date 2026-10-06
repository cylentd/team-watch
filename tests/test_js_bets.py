"""Bets lists only games still to come, and says the page's week (surface/parlay/parlay.js, in Node).

Monday 2026-10-05: Build listed "Thursday night PIT @ CLE" and "883 lines priced · week 4" with the
week's Thursday and Sunday games long played. A game past kickoff is no longer a line to pick, and the
count under Build is the lines still open, not the book's whole pull. Kickoff labels are cut from each
row's own UTC time in the reader's clock, never from the Pacific label Python wrote."""
import pytest

# 2026-10-05 13:00 UTC, Monday: Thursday and Sunday have kicked off, Monday night (00:15 UTC Tuesday) has not.
MONDAY_NOON = 1791205200000


def prop(n, game, commence, kick, win):
    return {"n": n, "slug": n.lower().replace(" ", "-"), "pos": "WR", "mkt": "REC", "line": 40.5, "game": game,
            "commence": commence, "kick": kick, "win": win, "book": "DraftKings", "model": 55, "edge": 3.0}


PROPS = [
    prop("Thursday Guy", "PIT @ CLE", "2026-10-02 00:15:00", "Thu 5:15p", "evening-thu"),
    prop("Sunday Guy", "DET @ CAR", "2026-10-04 17:00:00", "Sun 10:00a", "morning"),
    prop("Monday Guy", "ATL @ NO", "2026-10-06 00:15:00", "Mon 5:15p", "evening-mon"),
    prop("Undated Guy", "SF @ NYJ", None, "", "afternoon"),
]
WINDOWS = [
    {"k": "evening-thu", "label": "Thursday Night", "short": "THURSDAY NIGHT", "date": "2026-10-01", "kick": "Thu 5:15p", "at": "2026-10-02T00:15:00Z"},
    {"k": "morning", "label": "Morning", "short": "MORNING", "date": "2026-10-04", "kick": "Sun 10:00a", "at": "2026-10-04T17:00:00Z"},
    {"k": "evening-mon", "label": "Monday Night", "short": "MONDAY NIGHT", "date": "2026-10-05", "kick": "Mon 5:15p", "at": "2026-10-06T00:15:00Z"},
]
GLOBALS = {"KICK_TZ": "America/Los_Angeles", "BETS_NOW": MONDAY_NOON,
           "LIVE_PROPS": {"props": PROPS, "windows": WINDOWS, "days": [], "books": ["DraftKings"],
                          "model": {"week": 4}},
           "LIVE_SCHEDULE": {"week": 4, "games": [], "alias": {}},
           "LIVE_RANKS": {"week": 5},
           # What Build's controls hold on a fresh load.
           "MKT_POS": "ALL", "MKT_KIND": "ALL", "MKT_MINE": False, "MKT_BEST": False, "GAL_WIN": "ALL",
           "PARLAY_BOOK": "draftkings"}
FILES = ("lib/kick.js", "data/schedule.js", "data/market.js", "builder/slips.js", "surface/parlay/parlay.js")


@pytest.fixture(scope="module")
def bets(node_js):
    js = node_js(*FILES, globals=GLOBALS)
    # The sort and the shared helpers builder/ and lib/odds.js own: not what is under test.
    js("(() => { globalThis.SORTS = {edge: () => 0}; globalThis.MKT_SORT = 'edge'; globalThis.lineMoved = () => 0; "
       "globalThis.udPick = () => ({});globalThis.bestOdds = () => true; return 1; })()")
    return js


def names(js, src):
    return [p["n"] for p in js(src)]


def test_build_lists_only_games_that_have_not_kicked_off(bets):
    got = names(bets, "buildLines().map(p => ({n: p.n}))")
    assert "Thursday Guy" not in got and "Sunday Guy" not in got
    assert sorted(got) == ["Monday Guy", "Undated Guy"]


def test_the_count_under_build_is_the_lines_still_open(bets):
    assert bets("buildCount()") == 2


def test_the_week_label_is_the_schedules_week_whatever_the_projections_say(bets):
    assert bets("schedWeek()") == 4


def test_kickoff_labels_come_from_each_rows_own_utc_time(bets):
    assert bets("PROPS.map(p => p.kick)") == ["Thu 5:15 PM", "Sun 10:00 AM", "Mon 5:15 PM", ""]
    assert bets("WINDOWS.map(w => w.kick)") == ["Thu 5:15 PM", "Sun 10:00 AM", "Mon 5:15 PM"]
