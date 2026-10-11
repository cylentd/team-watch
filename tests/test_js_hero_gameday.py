"""The hero's scorer pool (David, 2026-10-11, game day: "the hero hasn't been updated. It's game day but it's still
showing Thursday's game"). On a slate day the hero's top scorer comes from the games kicking off that Pacific day, so
Thursday's final does not hold the banner on Sunday. Any other day keeps the week's scorers: Monday morning is still
Sunday's top score. Data in, data out (data/dayplan.js, DG_LATE_MAX from data/digest.js)."""
import pytest


def ms(iso):
    from datetime import datetime
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


KICKS = {"TB": "2026-10-09T00:15:00Z",        # Thursday 5:15 PM Pacific
         "JAX": "2026-10-11T13:30:00Z",       # Sunday 6:30 AM Pacific
         "CHI": "2026-10-11T17:00:00Z",
         "BAL": "2026-10-12T00:20:00Z",       # Sunday 5:20 PM Pacific, UTC says Monday
         "BUF": "2026-10-13T00:15:00Z"}       # Monday 5:15 PM Pacific
GAMES = [{"away": c, "home": "XXX", "kickoff": k} for c, k in KICKS.items()] + [
    {"away": "GB", "home": "MIN", "kickoff": "2026-10-11T17:00:00Z"},
    {"away": "DEN", "home": "LAC", "kickoff": "2026-10-11T20:05:00Z"}]
ROWS = [{"n": "Bucky Irving", "team": "TB", "pts": 30.5}, {"n": "Parker Washington", "team": "JAX", "pts": 27.4},
        {"n": "D'Andre Swift", "team": "CHI", "pts": 12.0}, {"n": "Lamar Jackson", "team": "BAL", "pts": 3.0},
        {"n": "No Club", "team": "ZZZ", "pts": 40.0}]
POOL = ("([rows, games, now, kicks]) => dgSlateScorers(rows, games, now,"
        " c => kicks[c] && Date.parse(kicks[c])).map(r => r.n)")
EVERYONE = [r["n"] for r in ROWS]


@pytest.fixture(scope="module")
def js(node_js):
    return node_js("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js",
                   globals={"LIVE_SCHEDULE": {"games": [], "alias": {}}})


@pytest.mark.req("Digest", ac="on a slate day the hero's top scorer comes from today's games, not the week's")
def test_thursdays_final_does_not_hold_the_hero_on_sunday(js):
    sunday_morning = ms("2026-10-11T17:02:00Z")      # 10:02 AM Pacific: the 6:30 and 10:00 windows are on
    got = js(POOL, [ROWS, GAMES, sunday_morning, KICKS])
    assert got == ["Parker Washington", "D'Andre Swift", "Lamar Jackson"], "Sunday's clubs, in the order given"


@pytest.mark.req("Digest", ac="on a slate day the hero's top scorer comes from today's games, not the week's")
def test_sunday_before_a_kickoff_has_no_scorer_so_the_kickoff_banner_leads(js):
    early = ms("2026-10-11T12:00:00Z")               # 5 AM Pacific; nobody has scored on Sunday
    thursday_only = [ROWS[0]]
    assert js(POOL, [thursday_only, GAMES, early, KICKS]) == []


@pytest.mark.req("Digest", ac="a standalone slot keeps the week's scorers")
@pytest.mark.parametrize("when", ["2026-10-12T09:00:00Z",   # Monday 2 AM Pacific: Sunday's top score, MNF tonight
                                  "2026-10-09T03:00:00Z"])  # Thursday 8 PM Pacific: one game today
def test_a_day_with_a_standalone_slot_keeps_the_weeks_scorers(js, when):
    assert js(POOL, [ROWS, GAMES, ms(when), KICKS]) == EVERYONE
