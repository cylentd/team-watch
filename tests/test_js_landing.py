"""Which view a group click opens (data/landing.js, 2026-10-09, ledger #91; David: "every tab opens the same
view every time", with one exception for Matchup: "maybe it's live on Sunday or during live games").

Pure over (group, now, schedule, leaves): no DOM, so Node. Kickoffs below are real 2026 slots: Sunday 2026-10-11
is 1:00 pm ET = 17:00Z, 4:25 pm ET = 20:25Z, and Sunday night 8:20 pm ET = 00:20Z on the Monday."""
import datetime

import pytest

UTC = datetime.timezone.utc
HOUR = 3600e3
WEEK_ROW = ["live", "matchups", "preview", "weekrecap", "parlay", "build", "dfs", "weather"]
PLAYERS_ROW = ["news", "ranks", "board", "movers", "usage", "schedule"]


def ms(y, m, d, h, mi=0):
    return datetime.datetime(y, m, d, h, mi, tzinfo=UTC).timestamp() * 1000


def iso(t_ms):
    return datetime.datetime.fromtimestamp(t_ms / 1000, UTC).isoformat().replace("+00:00", "Z")


THU = ms(2026, 10, 9, 0, 15)      # Thursday night, 8:15 pm ET
SUN_1 = ms(2026, 10, 11, 17)      # 1:00 pm ET
SUN_425 = ms(2026, 10, 11, 20, 25)
SUN_NIGHT = ms(2026, 10, 12, 0, 20)   # 8:20 pm ET Sunday
MON = ms(2026, 10, 13, 0, 15)     # Monday night, 8:15 pm ET
GAMES = [{"kickoff": iso(t), "week": 6} for t in (THU, SUN_1, SUN_425, SUN_NIGHT, MON)]


@pytest.fixture(scope="module")
def landing(node_js):
    return node_js("data/landing.js")


@pytest.fixture(scope="module")
def tabs(node_js):
    return node_js("data/tabrow.js")


def test_a_view_forgets_its_tab_when_left_and_a_view_with_nothing_to_forget_is_left_quietly(tabs):
    hits = tabs("(() => { const hits = []; navForget('live', () => hits.push('a')); navForget('live', () => hits.push('b')); "
                "navLeft('live'); navLeft('news'); return hits; })()")
    assert hits == ["a", "b"]


@pytest.mark.parametrize("type_,visit", [("navigate", True), ("reload", False), ("back_forward", False), (None, True)])
def test_a_load_is_a_visit_unless_it_is_a_reload_or_back(tabs, type_, visit):
    assert tabs("navVisitOf", type_) is visit


def matchup(landing, now, games=GAMES):
    return landing("landingLeaf", "week", now, games, WEEK_ROW)


def test_matchup_opens_on_preview_midweek(landing):
    assert matchup(landing, ms(2026, 10, 14, 16)) == "preview"   # Wednesday noon ET


def test_matchup_opens_on_preview_on_sunday_morning_before_the_first_kickoff(landing):
    assert matchup(landing, SUN_1 - 1 * HOUR) == "preview"


def test_matchup_opens_on_live_from_the_first_sunday_kickoff(landing):
    assert matchup(landing, SUN_1) == "live"


def test_matchup_stays_live_between_sunday_windows(landing):
    """Sunday from the first kickoff to the last game's end is one live stretch, gap or not: at 6 pm ET the
    1 pm game is over (window ended 5 pm) and the 8:20 pm game has not kicked off."""
    games = [{"kickoff": iso(SUN_1)}, {"kickoff": iso(SUN_NIGHT)}]
    assert matchup(landing, SUN_1 + 5 * HOUR, games=games) == "live"


def test_matchup_is_live_through_the_sunday_night_game_past_midnight_utc(landing):
    assert matchup(landing, SUN_NIGHT + 2 * HOUR) == "live"


def test_matchup_goes_back_to_preview_when_the_last_sunday_game_has_ended(landing):
    """The game window is four hours (the page's own grace, data/schedule.js SCHED_GRACE_MS)."""
    assert matchup(landing, SUN_NIGHT + 4 * HOUR - 1) == "live"
    assert matchup(landing, SUN_NIGHT + 4 * HOUR) == "preview"


def test_matchup_is_live_while_a_thursday_game_is_in_progress_and_not_the_next_morning(landing):
    assert matchup(landing, THU + 1 * HOUR) == "live"
    assert matchup(landing, THU + 10 * HOUR) == "preview"


def test_a_game_is_on_from_its_kickoff_to_four_hours_after(landing):
    assert landing("landingLive", THU, GAMES) is True
    assert landing("landingLive", THU - 1, GAMES) is False
    assert landing("landingLive", THU + 4 * HOUR - 1, GAMES) is True
    assert landing("landingLive", THU + 4 * HOUR, GAMES) is False


def test_the_last_sunday_game_ends_four_hours_after_its_kickoff_on_the_same_day(landing):
    """8:25 pm ET Sunday is still Sunday in the East: the boundary is the window, not the weekday."""
    games = [{"kickoff": iso(SUN_1)}, {"kickoff": iso(SUN_425)}]
    end = SUN_425 + 4 * HOUR
    assert landing("landingLive", end - 1, games) is True
    assert landing("landingLive", end, games) is False


def test_a_sunday_game_does_not_make_monday_morning_live(landing):
    assert landing("landingLive", ms(2026, 10, 12, 14), GAMES) is False


def test_matchup_is_live_during_monday_night(landing):
    assert matchup(landing, MON + 2 * HOUR) == "live"


def test_a_sunday_with_no_games_is_preview(landing):
    assert matchup(landing, SUN_1 + 1 * HOUR, games=[]) == "preview"


def test_a_game_with_no_readable_kickoff_is_ignored(landing):
    games = [{"kickoff": None}, {"kickoff": "soon"}, {}]
    assert matchup(landing, SUN_1 + 1 * HOUR, games=games) == "preview"


def test_no_schedule_at_all_is_preview(landing):
    assert matchup(landing, SUN_1 + 1 * HOUR, games=None) == "preview"


def test_matchup_falls_back_to_its_first_leaf_when_the_chosen_one_is_not_in_the_row(landing):
    assert landing("landingLeaf", "week", ms(2026, 10, 14, 16), GAMES, ["live", "matchups"]) == "live"


def test_players_opens_on_ranks_whatever_the_day(landing):
    assert landing("landingLeaf", "scouting", SUN_1 + 1 * HOUR, GAMES, PLAYERS_ROW) == "ranks"
    assert landing("landingLeaf", "scouting", ms(2026, 10, 14, 16), GAMES, PLAYERS_ROW) == "ranks"


def test_every_other_group_opens_on_the_first_leaf_of_its_row(landing):
    assert landing("landingLeaf", "team", SUN_1, GAMES, ["roster", "waivers", "trades"]) == "roster"
    assert landing("landingLeaf", "league", SUN_1, GAMES, ["recap", "teams"]) == "recap"
    assert landing("landingLeaf", "home", SUN_1, GAMES, ["digest"]) == "digest"
