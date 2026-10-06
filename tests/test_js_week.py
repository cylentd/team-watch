"""The page's week (data/schedule.js slateWeek), in Node.

One week for every view that prices a player: the week of the projections. The schedule's own week
(schedWeek, the next game with no final score) stays N until Monday night is final, while from the
last Sunday game on every projection is for N+1. On Monday 2026-10-05 Week and Bets said Week 4 and
Players and Start/Sit said Week 5. The rule, written once in schedule.js and design/DESIGN.md: a view
that prices or ranks reads slateWeek(); a view that lists games reads each game's own week."""
import pytest


def sched(week):
    return {"week": week, "games": [], "alias": {}}


def pages(week=4, ranks=5, teams=5, model=4):
    return {"LIVE_SCHEDULE": sched(week), "LIVE_RANKS": {"week": ranks} if ranks else None,
            "LIVE_TEAMS": {"week": teams} if teams else None,
            "LIVE_MARKET": {"model": {"week": model}} if model else None}


@pytest.fixture
def week(node_js):
    def load(**kw):
        return node_js("data/schedule.js", globals=pages(**kw))
    return load


def test_monday_after_the_sunday_games_the_page_is_week_five(week):
    """2026-10-05: week 4's Monday night game is not final (schedule: week 4), the projections are week 5,
    the props model still says week 4. Every view that prices a player says 5."""
    js = week(week=4, ranks=5, teams=5, model=4)
    assert js("schedWeek()") == 4
    assert js("slateWeek()") == 5


def test_a_week_with_no_overlap_is_the_same_everywhere(week):
    js = week(week=4, ranks=4, teams=4, model=4)
    assert js("[schedWeek(), slateWeek()]") == [4, 4]


def test_ranks_lead_then_teams_then_the_props_model_then_the_schedule(week):
    assert week(week=4, ranks=None, teams=5, model=4)("slateWeek()") == 5
    assert week(week=4, ranks=None, teams=None, model=5)("slateWeek()") == 5
    assert week(week=4, ranks=None, teams=None, model=None)("slateWeek()") == 4


def test_no_data_at_all_is_no_week(node_js):
    js = node_js("data/schedule.js", globals={"LIVE_SCHEDULE": None})
    assert js("slateWeek()") is None
    assert js("schedWeek()") is None
