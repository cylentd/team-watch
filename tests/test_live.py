"""The /api/live endpoint's pure functions: how an ESPN payload becomes the board's 5 KB.

Nothing here touches the network. `fetch()` is the only function that would, and it is not
called: every test below drives `shape()` and its helpers off a hand-built payload shaped like
the one the live league returned on 2026-09-20.

The two facts worth pinning are the ones that were wrong first:
  * the live score is `totalPointsLive`; `totalPoints` stays 0.0 until the week settles, so
    reading it shows 0 all Sunday;
  * a player with no statSourceId 0 row has not played, and that must stay None rather than
    becoming 0.0 -- "hasn't kicked off" and "scored nothing" are different things.
"""
import importlib.util
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SWID = "{AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE}"


def _load():
    """api/live.py by path -- it is a Vercel file-based function, not an importable package."""
    spec = importlib.util.spec_from_file_location("live_fn", REPO / "api" / "live.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


live = _load()


def stat(source, total, week=2):
    return {"scoringPeriodId": week, "statSourceId": source, "statSplitTypeId": 1,
            "appliedTotal": total}


def player(name, pro=8, slot=4, actual=None, projected=None, injury="ACTIVE"):
    stats = []
    if actual is not None:
        stats.append(stat(live.ACTUAL, actual))
    if projected is not None:
        stats.append(stat(live.PROJECTED, projected))
    return {"lineupSlotId": slot, "playerPoolEntry": {
        "player": {"fullName": name, "proTeamId": pro, "stats": stats, "injuryStatus": injury}}}


def side(team_id, entries, live_pts, proj, win):
    return {"teamId": team_id, "totalPoints": 0.0, "totalPointsLive": live_pts,
            "totalProjectedPointsLive": proj, "winProbability": win,
            "rosterForCurrentScoringPeriod": {"entries": entries}}


def body(mine=None, theirs=None):
    mine = mine if mine is not None else [player("Amon-Ra St. Brown", actual=31.5, projected=16.0)]
    theirs = theirs if theirs is not None else [player("Jaxon Smith-Njigba", pro=26, projected=15.0)]
    return {
        "scoringPeriodId": 2,
        "status": {"currentMatchupPeriod": 2},
        "teams": [{"id": 12, "name": "Purdy Big in Japan", "primaryOwner": SWID},
                  {"id": 15, "name": "TeamMinh", "primaryOwner": "{OTHER}"}],
        "schedule": [
            {"matchupPeriodId": 1, "home": side(12, [], 0.0, 0.0, 0.5),
             "away": side(15, [], 0.0, 0.0, 0.5)},
            {"matchupPeriodId": 2, "home": side(15, theirs, -2.0, 92.7, 0.24),
             "away": side(12, mine, 31.5, 131.7, 0.76)},
        ],
    }


# --------------------------------------------------------------------------- points

def test_actual_and_projection_are_read_from_their_own_rows():
    p = player("x", actual=31.5, projected=16.0)["playerPoolEntry"]["player"]
    assert live.points(p, 2, live.ACTUAL) == 31.5
    assert live.points(p, 2, live.PROJECTED) == 16.0


def test_a_player_who_has_not_played_returns_none_not_zero():
    """The only game-state signal in the whole payload. Flattening it to 0.0 would claim he
    played and scored nothing, which is the opposite of what it means."""
    p = player("x", projected=9.2)["playerPoolEntry"]["player"]
    assert live.points(p, 2, live.ACTUAL) is None


def test_another_weeks_row_is_not_this_weeks_points():
    p = {"stats": [stat(live.ACTUAL, 40.0, week=1)]}
    assert live.points(p, 2, live.ACTUAL) is None


# --------------------------------------------------------------------------- lineup

def test_starters_sort_ahead_of_bench():
    rows = live.lineup(side(12, [player("Benched", slot=20, projected=1.0),
                               player("Starter", slot=4, projected=2.0)], 0, 0, 0.5), 2)
    assert [r["starter"] for r in rows] == [True, False]


@pytest.mark.parametrize("slot", [20, 21])
def test_bench_and_ir_are_both_bench(slot):
    rows = live.lineup(side(12, [player("x", slot=slot)], 0, 0, 0.5), 2)
    assert rows[0]["starter"] is False


def test_started_tracks_the_actual_row():
    rows = live.lineup(side(12, [player("Played", actual=12.0), player("Waiting", projected=9.0)],
                            0, 0, 0.5), 2)
    assert {r["name"]: r["started"] for r in rows} == {"Played": True, "Waiting": False}


def test_pro_team_id_becomes_a_club_code():
    rows = live.lineup(side(12, [player("x", pro=8)], 0, 0, 0.5), 2)
    assert rows[0]["team"] == "DET"


# --------------------------------------------------------------------------- shape

def test_my_team_is_found_by_swid_and_the_opponent_is_the_other_side():
    out = live.shape(body(), SWID)
    assert out["me"]["team"] == "Purdy Big in Japan"
    assert out["opponent"]["team"] == "TeamMinh"


def test_swid_matches_with_or_without_braces():
    out = live.shape(body(), SWID.strip("{}"))
    assert out["me"]["team"] == "Purdy Big in Japan"


def test_the_live_total_is_used_not_the_settled_one():
    out = live.shape(body(), SWID)
    assert (out["me"]["live"], out["opponent"]["live"]) == (31.5, -2.0)


def test_projection_and_win_probability_come_through():
    out = live.shape(body(), SWID)
    assert out["me"]["projected"] == 131.7
    assert out["me"]["winPct"] + out["opponent"]["winPct"] == pytest.approx(1.0)


def test_only_the_current_matchup_period_is_returned():
    """The schedule carries the whole season; week 1's row must not win the search."""
    out = live.shape(body(), SWID)
    assert out["week"] == 2
    assert len(out["me"]["lineup"]) == 1


def test_an_unknown_swid_is_an_error_not_an_empty_board():
    with pytest.raises(LookupError):
        live.shape(body(), "{NOBODY}")


def test_a_named_team_gets_its_own_board_with_its_side_as_me():
    """A leaguemate's board (?team=, 2026-09-26): the named team is "me", David's is the opponent."""
    out = live.shape(body(), SWID, team="TeamMinh")
    assert (out["me"]["team"], out["opponent"]["team"]) == ("TeamMinh", "Purdy Big in Japan")
    assert (out["me"]["live"], out["opponent"]["live"]) == (-2.0, 31.5)


def test_a_team_name_matches_whatever_its_case_and_spacing():
    """ff-jarvis keys a team by ESPN's own name, double spaces and all ("Lets rock  Mate")."""
    b = body()
    b["teams"][1]["name"] = "Lets rock  Mate"
    assert live.shape(b, SWID, team="lets rock mate")["me"]["team"] == "Lets rock  Mate"


def test_a_team_named_by_location_and_nickname_is_found():
    b = body()
    b["teams"][1] = {"id": 15, "location": "Team", "nickname": "Minh", "primaryOwner": "{OTHER}"}
    assert live.shape(b, SWID, team="Team Minh")["opponent"]["team"] == "Purdy Big in Japan"


def test_an_unknown_team_is_an_error_not_davids_board():
    with pytest.raises(LookupError):
        live.shape(body(), SWID, team="Nobody FC")


def test_one_espn_read_serves_every_teams_board(monkeypatch):
    """The memo holds the league reply, not a shaped board, so twelve teams asking inside the
    window still cost ESPN one read."""
    calls = []
    monkeypatch.setattr(live, "fetch", lambda *a: calls.append(a) or body())
    monkeypatch.setattr(live, "_memo", {"at": 0.0, "raw": None})
    for k, v in {"ESPN_SWID": SWID, "ESPN_S2": "x", "ESPN_LEAGUE_ID": "1"}.items():
        monkeypatch.setenv(k, v)
    mine, theirs = live.live(), live.live("TeamMinh")
    assert len(calls) == 1 and theirs["cached"] is True
    assert mine["me"]["team"] != theirs["me"]["team"]


def test_a_missing_matchup_is_an_error():
    b = body()
    b["schedule"] = [r for r in b["schedule"] if r["matchupPeriodId"] != 2]
    with pytest.raises(LookupError):
        live.shape(b, SWID)


# --------------------------------------------------------------------------- config

@pytest.mark.parametrize("missing", ["ESPN_SWID", "ESPN_S2", "ESPN_LEAGUE_ID"])
def test_configured_needs_every_cookie(monkeypatch, missing):
    for k in ("ESPN_SWID", "ESPN_S2", "ESPN_LEAGUE_ID"):
        monkeypatch.setenv(k, "x")
    monkeypatch.delenv(missing, raising=False)
    assert live.configured() is False


def test_configured_wants_no_passphrase(monkeypatch):
    """The cache is what protects the cookies, not a secret. A passphrase would make the reply
    uncacheable, which is the opposite of what keeps ESPN from being hit once per caller."""
    for k in ("ESPN_SWID", "ESPN_S2", "ESPN_LEAGUE_ID"):
        monkeypatch.setenv(k, "x")
    for k in ("LIVE_PASSPHRASE", "CHAT_PASSPHRASE"):
        monkeypatch.delenv(k, raising=False)
    assert live.configured() is True


def test_season_override_wins(monkeypatch):
    monkeypatch.setenv("ESPN_SEASON", "2024")
    assert live.season() == 2024
