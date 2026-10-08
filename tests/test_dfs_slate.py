"""DFS covers the Sunday main slate only: Yahoo's contest has the early and afternoon games.

Oracles are worked out by hand on the week of Sunday 2026-10-11 (Pacific, PDT = UTC-7): the early
games kick at 10:00 PT, the afternoon at 13:25 PT, Sunday night 17:20 PT, Thursday 17:15 PT the
Thursday before, Monday 17:15 PT the day after.
"""
import pytest

import build
import contract
import dfs_slate

TEAM_FIX = {"JAC": "JAX", "LA": "LAR"}

EARLY, AFTERNOON = "2026-10-11T17:00:00Z", "2026-10-11T20:25:00Z"      # 10:00 PT, 13:25 PT
NIGHT, THURSDAY, MONDAY = "2026-10-12T00:20:00Z", "2026-10-09T00:15:00Z", "2026-10-13T00:15:00Z"
JUST_BEFORE_NIGHT, NIGHT_STARTS = "2026-10-11T23:59:00Z", "2026-10-12T00:00:00Z"   # 16:59 PT, 17:00 PT


def _row(name, game, **extra):
    away, home = game.split("@")
    return {"name": name, "pos": "WR", "team": away, "salary": 20, "fppg": 8.0, "yahoo_proj": None,
            "status": "", "game": game, **extra}


def _schedule(*games, week=5):
    return {"week": week, "games": [{"away": a, "home": h, "kickoff": k, "week": week}
                                    for (a, h, k) in games]}


def _names(pool):
    return [r["name"] for r in pool["players"]]


def _pool(*rows):
    return {"fetched": "2026-10-09 05:56", "players": list(rows)}


@pytest.mark.parametrize("window,kept", [
    ("early", True), ("afternoon", True),
    ("thu", False), ("night", False), ("mnf", False), ("other", False),
])
def test_a_row_stays_only_when_ffjarvis_puts_it_in_the_early_or_afternoon_window(window, kept):
    pool = _pool(_row("A", "CIN@NYJ", slate_window=window))
    assert (_names(dfs_slate.main_slate(pool, None, TEAM_FIX)) == ["A"]) is kept


def test_an_unknown_window_value_fails_the_contract_naming_it():
    pool = _pool(_row("A", "CIN@NYJ", slate_window="brunch"))
    with pytest.raises(contract.ContractError, match="brunch"):
        dfs_slate.main_slate(pool, None, TEAM_FIX)


@pytest.mark.parametrize("kickoff,kept", [
    (EARLY, True), (AFTERNOON, True), (JUST_BEFORE_NIGHT, True),
    (NIGHT_STARTS, False), (NIGHT, False), (THURSDAY, False), (MONDAY, False),
])
def test_a_row_without_the_key_falls_back_to_its_games_kickoff_in_the_schedule(kickoff, kept):
    pool = _pool(_row("A", "CIN@NYJ"))
    sched = _schedule(("CIN", "NYJ", kickoff))
    assert (_names(dfs_slate.main_slate(pool, sched, TEAM_FIX)) == ["A"]) is kept


def test_the_key_wins_over_the_schedule():
    pool = _pool(_row("A", "CIN@NYJ", slate_window="night"))
    sched = _schedule(("CIN", "NYJ", EARLY))
    assert _names(dfs_slate.main_slate(pool, sched, TEAM_FIX)) == []


def test_the_fallback_reads_yahoos_team_codes_through_the_canon_and_espns_dialect():
    pool = _pool(_row("A", "JAC@WAS"), _row("B", "LA@SF"))
    sched = _schedule(("JAX", "WSH", THURSDAY), ("LAR", "SF", AFTERNOON))
    assert _names(dfs_slate.main_slate(pool, sched, TEAM_FIX)) == ["B"]


def test_the_fallback_uses_the_page_weeks_game_when_a_pair_meets_twice():
    pool = _pool(_row("A", "CIN@NYJ"))
    sched = {"week": 5, "games": [
        {"away": "CIN", "home": "NYJ", "kickoff": EARLY, "week": 5},
        {"away": "CIN", "home": "NYJ", "kickoff": NIGHT, "week": 14}]}
    assert _names(dfs_slate.main_slate(pool, sched, TEAM_FIX)) == ["A"]


def test_a_row_whose_window_cannot_be_known_stays_so_the_page_never_blanks():
    pool = _pool(_row("A", "CIN@NYJ"), _row("B", "CIN@NYJ", slate_window=None))
    assert _names(dfs_slate.main_slate(pool, None, TEAM_FIX)) == ["A", "B"]


def test_the_pool_keeps_its_other_fields_and_the_input_is_not_mutated():
    keep, drop = _row("A", "CIN@NYJ", slate_window="early"), _row("B", "DEN@KC", slate_window="mnf")
    pool = _pool(keep, drop)
    out = dfs_slate.main_slate(pool, None, TEAM_FIX)
    assert (out["fetched"], out["players"], len(pool["players"])) == (pool["fetched"], [keep], 2)


def test_the_built_page_pool_holds_only_main_slate_players(monkeypatch):
    rows = [_row("Early Guy", "CIN@NYJ", slate_window="early"),
            _row("Night Guy", "DEN@KC", slate_window="night"),
            _row("Thursday Guy", "LAC@LV", slate_window="thu")]
    monkeypatch.setattr(build, "load_dfs_pool", lambda: _pool(*rows))
    monkeypatch.setattr(build, "load_status", dict)
    monkeypatch.setattr(build, "load_player_proj", lambda: {"players": []})
    block = build.live_dfs_yahoo(set())
    assert [p["n"] for p in block["players"]] == ["Early Guy"]


def test_a_pool_with_no_main_slate_player_builds_no_block(monkeypatch):
    monkeypatch.setattr(build, "load_dfs_pool", lambda: _pool(_row("A", "DEN@KC", slate_window="mnf")))
    monkeypatch.setattr(build, "load_status", dict)
    monkeypatch.setattr(build, "load_player_proj", lambda: {"players": []})
    assert build.live_dfs_yahoo(set()) is None
