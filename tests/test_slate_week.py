"""projections.slate: the week the projections speak for, through a Sunday (2026-10-05).

The `players` file projects each player's NEXT game, so a game that has kicked off is gone from it. The week
is the one most rows fall in, which at Sunday 12:30 PT (the noon run, after the 1 PM ET games) was already
N+1 while week N's 4 PM games were still to play. Rule: week N holds while any non-Monday game of week N is
still some team's next game; Monday night alone does not hold it. Twelve teams, weeks 5 and 6; `rows_at`
gives every team the next game it has after a moment, which is what the file holds."""
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
SCHEDULE = {"alias": {}, "games": [{"week": w, "away": a, "home": h, "kickoff": k} for w, a, h, k in GAMES]}
slug = lambda name: name.lower().replace(" ", "-")


def rows_at(now):
    """Each team's next game after `now` (UTC ISO), as the file writes it ("2026-10-11 17:00:00")."""
    out = []
    for team in TEAMS:
        nxt = min((k for _, a, h, k in GAMES if team in (a, h) and k > now), default=None)
        if nxt:
            out.append({"name": f"Player {team}", "team": team, "pos": "WR", "kickoff": nxt.replace("T", " ").rstrip("Z")})
    return out


@pytest.mark.parametrize("now, week", [
    ("2026-10-07T15:00:00Z", 5),   # Wednesday: every row is week 5
    ("2026-10-11T16:00:00Z", 5),   # Sunday 9 AM PT: only Thursday's game has been played
    ("2026-10-11T19:30:00Z", 5),   # Sunday 12:30 PT: 1 PM games gone, 8 of 12 rows are week 6, the 4 PM game is to play
    ("2026-10-12T02:00:00Z", 6),   # Sunday 10 PM ET: only Monday night is left, and it does not hold the week
    ("2026-10-12T15:00:00Z", 6),   # Monday
    ("2026-10-13T15:00:00Z", 6),   # Tuesday: week 5 is over
    ("2026-10-16T01:00:00Z", 6),   # Thursday after kickoff: A and C have no next game, the rest are week 6
])
def test_the_week_through_a_week(now, week):
    assert slate(rows_at(now), slug, SCHEDULE)[0] == week


def test_sunday_afternoon_the_teams_that_played_are_marked_and_the_rest_keep_their_number():
    week, off = slate(rows_at("2026-10-11T19:30:00Z"), slug, SCHEDULE)
    assert week == 5
    assert off == {f"player-{t.lower()}": "played" for t in "ABCDEFGH"}, "the 4 PM and Monday teams have not played"
