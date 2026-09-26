"""The DFS builder's solver finds the best lineup under the cap, not the best player per slot.

Until 2026-09-25 the builder filled slots one at a time with the top projection that fit, so a
$20 DST projected 1 point better than a $10 one won its slot even when the $10 saved bought a
much better WR. Every case here is checked against brute force over the same small pool.
"""
import itertools
import json
import pathlib
import shutil
import subprocess

import pytest

pytestmark = pytest.mark.skipif(not shutil.which("node"), reason="node not installed")

JS = pathlib.Path(__file__).resolve().parents[1] / "design" / "src" / "js" / "builder"
SHAPES = [{"QB": 1, "RB": 3, "WR": 3, "TE": 1, "DST": 1}, {"QB": 1, "RB": 2, "WR": 4, "TE": 1, "DST": 1},
          {"QB": 1, "RB": 2, "WR": 3, "TE": 2, "DST": 1}]


def solve(pool, cap):
    src = "\n".join((JS / f).read_text(encoding="utf-8") for f in ("solve.js", "lineups.js"))
    script = src + f"\nconst r = solveLineup({json.dumps(pool)}, {cap}, p => p.proj);" \
                   "\nprocess.stdout.write(JSON.stringify(r && r.map(p => [p.slot, p.n])));"
    return json.loads(subprocess.run(["node", "-e", script], capture_output=True, text=True, check=True).stdout)


def brute(pool, cap):
    best = None
    for shape in SHAPES:
        groups = [itertools.combinations([p for p in pool if p["pos"] == pos], k) for pos, k in shape.items()]
        for combo in itertools.product(*groups):
            players = [p for g in combo for p in g]
            if sum(p["sal"] for p in players) <= cap:
                v = sum(p["proj"] for p in players)
                best = v if best is None or v > best else best
    return best


def row(n, pos, sal, proj):
    return {"n": n, "pos": pos, "sal": sal, "proj": proj}


POOL = [row("Qa", "QB", 40, 20), row("Qb", "QB", 20, 14),
        *[row(f"R{i}", "RB", s, p) for i, (s, p) in enumerate([(40, 19), (30, 15), (20, 11), (10, 7), (10, 4)])],
        *[row(f"W{i}", "WR", s, p) for i, (s, p) in enumerate([(40, 18), (30, 14), (20, 10), (10, 8), (10, 5)])],
        row("Ta", "TE", 30, 12), row("Tb", "TE", 10, 6), row("Tc", "TE", 10, 5),
        row("Dear", "DST", 20, 6), row("Dcheap", "DST", 10, 5)]


@pytest.mark.parametrize("cap", [120, 150, 180, 200])
def test_the_solver_matches_brute_force(cap):
    picked = dict(map(tuple, [(n, s) for s, n in solve(POOL, cap)]))
    total = sum(p["proj"] for p in POOL if p["n"] in picked)
    assert total == brute(POOL, cap)
    assert sorted(s for s in picked.values()) == sorted(["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "DST"])


def test_a_cheap_dst_wins_when_the_savings_buy_more_elsewhere():
    names = {n for _, n in solve(POOL, 150)}
    assert "Dcheap" in names and "Dear" not in names


def test_no_lineup_fits_returns_null():
    assert solve(POOL, 50) is None
