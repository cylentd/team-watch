"""The weekly DFS backtest replays the page's own builder on a saved week and scores it.

A tiny slate on disk in ff-jarvis's shapes: history `dfs` and `status` rows and a recap. The
lineups come from the page's lineups.js via node, so this also pins that the file still runs
outside a browser.
"""
import json
import shutil

import pytest

import dfs_backtest
import sources

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="node not installed")

# name, pos, salary, recap proj, actual. The pool is just big enough to fill 9 slots under $200.
SLATE = [
    ("Qb Star", "QB", 40, 20.0, 30.0), ("Qb Cheap", "QB", 20, 12.0, 8.0),
    ("Rb One", "RB", 30, 15.0, 20.0), ("Rb Two", "RB", 20, 10.0, 5.0), ("Rb Three", "RB", 10, 6.0, 12.0),
    ("Rb Hurt", "RB", 10, 14.0, 0.0),
    ("Wr One", "WR", 30, 14.0, 9.0), ("Wr Two", "WR", 20, 10.0, 15.0), ("Wr Three", "WR", 10, 5.0, 6.0),
    ("Wr Four", "WR", 10, 4.0, 1.0), ("Te One", "TE", 15, 8.0, 4.0), ("Te Two", "TE", 10, 5.0, 7.0),
]
DST = [("Aaa Defense", 18, 5.0), ("Bbb Defense", 10, 4.0)]


@pytest.fixture
def week(tmp_path, monkeypatch):
    rows = [{"asof": "2026-09-25T05:56", "slate": "1", "season": 2026, "week": 3, "key": n.lower(),
             "name": n, "pos": pos, "team": "AAA", "salary": sal, "fppg": proj}
            for n, pos, sal, proj, _ in SLATE]
    rows += [{"asof": "2026-09-25T05:56", "slate": "1", "season": 2026, "week": 3, "key": n.lower(),
              "name": n, "pos": "DEF", "team": n[:3].upper(), "salary": sal, "fppg": 13.0, "yahoo_proj": yp}
             for n, sal, yp in DST]
    (tmp_path / "history" / "dfs").mkdir(parents=True)
    (tmp_path / "history" / "dfs" / "2026-09-25.jsonl").write_text("\n".join(map(json.dumps, rows)))
    (tmp_path / "history" / "status").mkdir()
    (tmp_path / "history" / "status" / "2026-09-26.jsonl").write_text(json.dumps(
        {"asof": "2026-09-26T05:55", "key": "rb hurt", "team": "AAA", "pos": "RB", "playing": False}))
    (tmp_path / "recap").mkdir()
    (tmp_path / "recap" / "2026-w03.json").write_text(json.dumps({"complete": True, "players": [
        {"key": n.lower(), "name": n, "pos": pos, "proj": proj, "actual": act} for n, pos, _, proj, act in SLATE]}))
    monkeypatch.setattr(sources, "DWR", tmp_path)
    monkeypatch.setattr(dfs_backtest, "OUT", tmp_path / "out")
    return tmp_path


def test_the_backtest_scores_the_builders_lineups_on_actuals(week):
    r = dfs_backtest.backtest(2026, 3)
    top = r["lineups"]["greedy"][0]
    names = {p["n"] for p in top["players"]}
    assert len(top["players"]) == 9 and top["spent"] <= 200
    assert "Rb Hurt" not in names                         # OUT that Sunday: the page sat him
    assert top["actual"] == round(sum(p["act"] or 0 for p in top["players"]), 1)
    assert next(p for p in top["players"] if p["slot"] == "DST")["act"] is None
    assert r["hindsight"]["actual"] >= top["actual"]


def test_a_dst_is_priced_on_yahoos_projection_in_the_replay(week):
    r = dfs_backtest.backtest(2026, 3)
    dst = next(p for p in r["lineups"]["greedy"][0]["players"] if p["slot"] == "DST")
    assert dst["proj"] in (5.0, 4.0)                      # not the 13.0 FPPG


def test_the_newest_complete_recap_is_the_week_run(week):
    assert dfs_backtest.latest_recap_week(2026) == 3
