"""Weekly DFS backtest: what the builder would have picked, scored on what actually happened.

    python design/dfs_backtest.py                  # the newest week with a complete recap
    python design/dfs_backtest.py --week 1 [--force]

Inputs, all ff-jarvis (design/sources.py): the week's Yahoo pool from history kind `dfs`, and the
recap's pregame `proj` and `actual` (half-PPR). The pool goes through the page's own
`live_dfs_yahoo` and the page's own optimizer (dfs_backtest.js), so the lineups are the page's.

Two limits, stated in every report:
- DST has no actual points anywhere in ff-jarvis, so every total is the 8 skill slots only.
- The recap's `proj` is the model's number at kickoff; a player the model did not project falls
  back to Yahoo's numbers here as on the page, and one with no recap row scored 0. Injury status
  is Sleeper's as ff-jarvis recorded it that Sunday morning, so an OUT player is sat as the page
  sat him.

The hindsight lineup (best 8 skill players under the cap less the cheapest DST) needs scipy; without
it the report says so and carries none. Writes data/dfs_backtest/<season>-w<WW>.json (gitignored;
DFS_BACKTEST_OUT moves it, so the job's detached checkout writes into the working one).
Run by every team-watch rebuild (agent-config scripts/team-watch-rebuild.ps1); a scored week is
skipped, so the first run after Tuesday's ff-waiver-report finalises the recap does the work.
"""
import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build import live_dfs_yahoo, slugify          # noqa: E402
from sources import REPO, load_dfs_history, load_recap, load_status_asof   # noqa: E402

OUT = pathlib.Path(os.environ.get("DFS_BACKTEST_OUT", REPO / "data" / "dfs_backtest"))
CAP = 200
SKILL = {"QB": (1, 1), "RB": (2, 3), "WR": (3, 4), "TE": (1, 2)}   # min, max incl. FLEX


def latest_recap_week(season):
    for week in range(18, 0, -1):
        r = load_recap(season, week)
        if r and r.get("complete"):
            return week
    return None


def week_pool(rows):
    """History rows -> a pool in dfs_pool.json's shape: the newest row per player of the slate
    with the most rows (one main slate a week; a lock-day re-read only adds changed rows)."""
    by_slate = {}
    for r in rows:
        by_slate.setdefault(r["slate"], {})[(r["key"], r["pos"])] = r
    if not by_slate:
        return None
    players = max(by_slate.values(), key=len)
    return {"players": [{**r, "fppg": r.get("fppg") or 0.0} for r in players.values()]}


def slate_sunday(pool):
    """The Sunday on or after the pool's newest read: the morning the page last showed it."""
    day = datetime.date.fromisoformat(max(r["asof"] for r in pool["players"])[:10])
    return (day + datetime.timedelta(days=(6 - day.weekday()) % 7)).isoformat()


def run_optimizer(players):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(players, fh)
    js = pathlib.Path(__file__).with_name("dfs_backtest.js")
    out = subprocess.run(["node", str(js), fh.name], capture_output=True, text=True, check=True)
    pathlib.Path(fh.name).unlink()
    return json.loads(out.stdout)


def hindsight(players, cap):
    try:
        import numpy as np
        from scipy.optimize import LinearConstraint, Bounds, milp
    except ImportError:
        return None
    pool = [p for p in players if p["pos"] in SKILL]
    rows = [[p["sal"] for p in pool], [1] * len(pool)]
    lo, hi = [0, 8], [cap, 8]
    for pos, (mn, mx) in SKILL.items():
        rows.append([1 if p["pos"] == pos else 0 for p in pool])
        lo.append(mn)
        hi.append(mx)
    res = milp(-np.array([p["act"] for p in pool]), constraints=LinearConstraint(np.array(rows), lo, hi),
               integrality=np.ones(len(pool)), bounds=Bounds(0, 1))
    if not res.success:
        return None
    pick = [pool[i] for i in range(len(pool)) if res.x[i] > 0.5]
    return {"cap": cap, "players": pick, "sal": sum(p["sal"] for p in pick),
            "actual": round(sum(p["act"] for p in pick), 1)}


def backtest(season, week):
    recap = load_recap(season, week)
    pool = week_pool(load_dfs_history(season, week))
    if not recap or not pool:
        return None
    mp = {slugify(p["name"]): (p["proj"], "model") for p in recap["players"] if p.get("proj") is not None}
    actual = {p["key"]: p.get("actual") or 0.0 for p in recap["players"]}
    page = live_dfs_yahoo(set(), pool=pool, mp=mp, status=load_status_asof(slate_sunday(pool)))
    key_of = {r["name"]: r["key"] for r in pool["players"]}
    players = [{**p, "act": None if p["pos"] == "DST" else actual.get(key_of[p["n"]], 0.0)}
               for p in page["players"]]
    act_of = {p["n"]: p["act"] for p in players}
    lineups = run_optimizer(players)
    for ls in lineups.values():
        for l in ls:
            for p in l["players"]:
                p["act"] = act_of.get(p["n"])
            l["actual"] = round(sum(p["act"] or 0.0 for p in l["players"]), 1)
            l["dst_sal"] = next(p["sal"] for p in l["players"] if p["slot"] == "DST")
    cheapest_dst = min(p["sal"] for p in players if p["pos"] == "DST")
    best = hindsight(players, CAP - cheapest_dst)
    return {
        "season": season, "week": week, "run": time.strftime("%Y-%m-%d %H:%M"),
        "pool_players": len(players), "recap_players": len(recap["players"]),
        "limits": "Totals are the 8 skill slots; DST has no actual points. Half-PPR actuals.",
        "lineups": lineups, "hindsight": best,
    }


def summary(r):
    lines = [f"DFS backtest {r['season']} week {r['week']} ({r['pool_players']} in pool)"]
    for mode, ls in r["lineups"].items():
        for i, l in enumerate(ls, 1):
            lines.append(f"  {mode} #{i}: proj {l['proj']:.1f}  actual {l['actual']:.1f}  "
                         f"${l['spent']}  DST ${l['dst_sal']}")
    h = r["hindsight"]
    lines.append(f"  hindsight best 8: actual {h['actual']:.1f} (${h['sal']})" if h else "  hindsight: scipy missing")
    lines.append("  " + r["limits"])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--force", action="store_true", help="rewrite a week already backtested")
    a = ap.parse_args()
    week = a.week or latest_recap_week(a.season)
    if not week:
        print("dfs backtest: no complete recap yet")
        return
    out = OUT / f"{a.season}-w{week:02d}.json"
    if out.exists() and not a.force:
        print(f"dfs backtest: week {week} already done -> {out}")
        return
    r = backtest(a.season, week)
    if not r:
        print(f"dfs backtest: week {week} has no saved DFS pool or no recap; nothing to score")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(r, indent=1), encoding="utf-8")
    print(summary(r))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
