"""projections.slate: the week the projections speak for is the site's page week (2026-10-05).

The page week comes from ff-jarvis (`page_week` block, read into LIVE_SCHEDULE.week); slate() no longer
infers it from the rows. The `players` file projects each player's NEXT game, so a game that has kicked
off is gone from it. The page week turns when the week's last game is final: on Monday before the Monday
night final it is still N, and week N's only rows are the Monday game's players. Twelve teams, weeks 5
and 6; `rows_at` gives every team the next game it has after a moment, which is what the file holds.
Each case below states the page week the decision gives at that moment; none is computed here."""
import pytest

from projections import slate

TEAMS = "ABCDEFGHIJKL"
GAMES = [  # (week, away, home, kickoff UTC)
    (5, "A", "B", "2026-10-09T00:15:00Z"),   # Thu 8:15 PM ET
    (5, "C", "D", "2026-10-11T17:00:00Z"),   # Sun 1 PM ET
    (5, "E", "F", "2026-10-11T17:00:00Z"),
    (5, "G", "H", "2026-10-11T17:00:00Z"),
    (5, "I", "J", "2026-10-11T20:25:00Z"),   # Sun 4:25 PM ET
    (5, "K", "L", "2026-10-13T00:15:00Z"),   # Mon 8:15 PM ET
    (6, "A", "C", "2026-10-16T00:15:00Z"),   # Thu
    (6, "B", "D", "2026-10-18T17:00:00Z"),   # Sun 1 PM ET
    (6, "E", "G", "2026-10-18T17:00:00Z"),
    (6, "F", "H", "2026-10-18T17:00:00Z"),
    (6, "I", "K", "2026-10-18T20:25:00Z"),   # Sun 4:25 PM ET
    (6, "J", "L", "2026-10-20T00:15:00Z"),   # Mon
]


def schedule(week):
    """LIVE_SCHEDULE as the build makes it, with ff-jarvis's page week."""
    return {"alias": {}, "week": week,
            "games": [{"week": w, "away": a, "home": h, "kickoff": k} for w, a, h, k in GAMES]}


slug = lambda name: name.lower().replace(" ", "-")


def rows_at(now):
    """Each team's next game after `now` (UTC ISO), as the file writes it ("2026-10-11 17:00:00")."""
    out = []
    for team in TEAMS:
        nxt = min((k for _, a, h, k in GAMES if team in (a, h) and k > now), default=None)
        if nxt:
            out.append({"name": f"Player {team}", "team": team, "pos": "WR", "kickoff": nxt.replace("T", " ").rstrip("Z")})
    return out


def kept(rows, off):
    """Teams whose players stay in the week."""
    return sorted(r["team"] for r in rows if slug(r["name"]) not in off)


@pytest.mark.parametrize("now, week", [
    ("2026-10-07T15:00:00Z", 5),   # Wednesday: every row is week 5
    ("2026-10-11T16:00:00Z", 5),   # Sunday 9 AM PT: only Thursday's game has been played
    ("2026-10-11T19:30:00Z", 5),   # Sunday 12:30 PT: 1 PM games gone, the 4 PM game and Monday are to play
    ("2026-10-12T02:00:00Z", 5),   # Sunday 10 PM ET: Monday night is still to play
    ("2026-10-12T15:00:00Z", 5),   # Monday before the final: still week 5
    ("2026-10-13T05:00:00Z", 6),   # Monday night is final (the 9:15 PM PT results run): week 6, all rows
    ("2026-10-13T15:00:00Z", 6),   # Tuesday: week 5 is over
    ("2026-10-16T01:00:00Z", 6),   # Thursday after kickoff: A and C have no next game, the rest are week 6
])
def test_the_week_is_the_page_week_not_what_the_rows_say(now, week):
    """The rows at Monday noon are mostly week 6, and the week still reads 5: the page week decides."""
    assert slate(rows_at(now), slug, schedule(week))[0] == week


def test_monday_before_the_final_keeps_only_the_monday_games_players():
    """Week 5, Monday afternoon: K and L play tonight, so they alone are in the week; the ten teams
    whose game is over are marked played, not given their week-6 number."""
    now = "2026-10-12T20:00:00Z"
    rows = rows_at(now)
    week, off = slate(rows, slug, schedule(5))
    assert week == 5
    assert kept(rows, off) == ["K", "L"]
    assert off == {f"player-{t.lower()}": "played" for t in "ABCDEFGHIJ"}


def test_after_the_final_everyone_is_in_week_six():
    """The page week turned to 6: every team's next game is week 6, so nobody is marked."""
    now = "2026-10-13T05:00:00Z"
    rows = rows_at(now)
    week, off = slate(rows, slug, schedule(6))
    assert week == 6
    assert off == {}
    assert kept(rows, off) == sorted(TEAMS)


def test_a_file_written_before_the_monday_game_marks_its_players_played_after_the_turn():
    """The file is from Monday afternoon (K and L still at their week-5 game), the page week has turned
    to 6: K and L are marked played, so the Monday game's players leave Ranks and Teams."""
    rows = rows_at("2026-10-12T20:00:00Z")
    week, off = slate(rows, slug, schedule(6))
    assert week == 6
    assert off == {"player-k": "played", "player-l": "played"}
    assert kept(rows, off) == list("ABCDEFGHIJ")


def test_sunday_afternoon_the_teams_that_played_are_marked_and_the_rest_keep_their_number():
    rows = rows_at("2026-10-11T19:30:00Z")
    week, off = slate(rows, slug, schedule(5))
    assert week == 5
    assert off == {f"player-{t.lower()}": "played" for t in "ABCDEFGH"}, "the 4 PM and Monday teams have not played"


def test_a_team_with_no_game_in_the_week_is_on_a_bye():
    """M has no week-5 game; its first row is week 6, so it is a bye rather than played."""
    sched = schedule(5)
    sched["games"].append({"week": 6, "away": "M", "home": "N", "kickoff": "2026-10-18T17:00:00Z"})
    rows = rows_at("2026-10-12T20:00:00Z") + [
        {"name": "Player M", "team": "M", "pos": "WR", "kickoff": "2026-10-18 17:00:00"}]
    assert slate(rows, slug, sched)[1]["player-m"] == "bye"


def test_the_week_passed_in_beats_the_schedules():
    assert slate(rows_at("2026-10-07T15:00:00Z"), slug, schedule(6), week=5)[0] == 5


def test_no_page_week_holds_nothing():
    """A missing page_week block: no week, nobody marked; the page already handles a null week."""
    assert slate(rows_at("2026-10-12T20:00:00Z"), slug, schedule(None)) == (None, {})
    assert slate(rows_at("2026-10-12T20:00:00Z"), slug, None) == (None, {})
