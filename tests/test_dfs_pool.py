"""A DST's DFS projection is Yahoo's this-week number, never its season FPPG.

The model projects no defense, so until 2026-09-25 every DST fell back to FPPG unscaled: CIN at
14.5 against Yahoo's own 4.3, and the optimizer paid $20 for it.
"""
import build


def _pool(players):
    return {"fetched": "2026-09-25 05:56", "players": players}


def _row(name, pos, fppg, proj=None):
    return {"name": name, "pos": pos, "team": "CIN", "salary": 20, "fppg": fppg,
            "yahoo_proj": proj, "status": "", "game": "CIN@NYJ"}


def test_a_dst_takes_yahoos_projection_not_its_fppg(monkeypatch):
    monkeypatch.setattr(build, "load_dfs_pool", lambda: _pool([_row("Cincinnati Bengals", "DEF", 14.5, 4.34)]))
    monkeypatch.setattr(build, "load_status", dict)
    monkeypatch.setattr(build, "load_player_proj", lambda: {"players": []})
    [dst] = build.live_dfs_yahoo(set())["players"]
    assert (dst["pos"], dst["proj"], dst["src"]) == ("DST", 4.3, "yahoo")


def test_a_dst_without_a_yahoo_projection_keeps_the_fppg_fallback(monkeypatch):
    monkeypatch.setattr(build, "load_dfs_pool", lambda: _pool([_row("Cincinnati Bengals", "DEF", 6.0)]))
    monkeypatch.setattr(build, "load_status", dict)
    monkeypatch.setattr(build, "load_player_proj", lambda: {"players": []})
    [dst] = build.live_dfs_yahoo(set())["players"]
    assert dst["proj"] == 6.0
