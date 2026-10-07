"""The test history: every pytest run and every land, one JSON line each, and what they add up to.

    python scripts/testlog.py            # the summary: layers, trend, slowest files, flaky tests, lands
    python scripts/testlog.py --days 7   # the same over the last week
    python scripts/testlog.py --profile  # the latest full run split into harness and tests (--last: any size;
                                         # --profile abc1234 or --profile -2: that commit or history index)

Written for an agent to read, not a person: David decided (2026-10-05) he would never look at a
dashboard, so there is none. The files live in the git dir every worktree shares, so a worktree's
runs outlive the worktree and every session reads the same history:

    <git common dir>/test-history/runs.jsonl    tests/runlog.py appends one line per pytest run
    <git common dir>/test-history/lands.jsonl   scripts/land.ps1 appends one line per land (`land` below)

TW_TEST_HISTORY overrides the directory; "off" records nothing. A run is "full" when it ran at least
90% of the test files the fullest recent run did; trends and the slowest files read full runs only,
because a land that ran one area is not slower or faster, only smaller. A test is flaky when it failed
in one run and passed in another of the same commit on a clean tree, in any kind of run (dev, land,
flake, scheduled); a run with uncommitted edits is recorded but never counted toward flakiness.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import statistics
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
FULL_SHARE = 0.9


def history_dir():
    """The shared directory, or None when recording is off."""
    env = os.environ.get("TW_TEST_HISTORY", "")
    if env.lower() == "off":
        return None
    if env:
        return pathlib.Path(env)
    out = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--git-common-dir"],
                         capture_output=True, text=True, check=True).stdout.strip()
    common = pathlib.Path(out)
    return (common if common.is_absolute() else REPO / common) / "test-history"


def append(name, record):
    d = history_dir()
    if d is None:
        return None
    d.mkdir(parents=True, exist_ok=True)
    with open(d / name, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, separators=(",", ":")) + "\n")
    return d / name


def read(name, days=None):
    d = history_dir()
    p = d / name if d else None
    if not p or not p.is_file():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:      # a run killed mid-write leaves half a line; the rest still count
            continue
    if days:
        cut = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
        rows = [r for r in rows if r.get("at", "") >= cut]
    return rows


def full_runs(runs):
    most = max((r.get("n_files", 0) for r in runs[-50:]), default=0)
    return [r for r in runs if most and r.get("n_files", 0) >= FULL_SHARE * most]


def flaky(runs):
    """{nodeid: (failed, passed)} counts per test that both failed and passed on one commit. Only
    runs of a clean tree count: two runs of one commit with different uncommitted edits tested two
    different things, and a fix in between is not a flake."""
    by_sha = {}
    for r in runs:
        if not r.get("dirty"):
            by_sha.setdefault(r.get("sha"), []).append(r)
    out = {}
    for same in by_sha.values():
        if len(same) < 2:
            continue
        # A run counts as a pass for a test only if it ran the whole file: a land with --areas or a
        # dev run with -k that deselected the test says nothing about it.
        whole = {}
        for r in same:
            for f, v in r.get("files", {}).items():
                whole[f] = max(whole.get(f, 0), v[0])
        ran_all = lambda o, f: f in o.get("files", {}) and o["files"][f][0] >= whole[f]
        for r in same:
            for nodeid in r.get("failed", []):
                f = nodeid.split("::")[0].split("/")[-1]
                passed = sum(1 for o in same if o is not r and ran_all(o, f) and nodeid not in o.get("failed", []))
                if passed:
                    fails = sum(1 for o in same if nodeid in o.get("failed", []))
                    out[nodeid] = (fails, passed)
    return out


def median_file_seconds(fulls, k=5):
    recent = fulls[-k:]
    files = {f for r in recent for f in r.get("files", {})}
    rows = []
    for f in files:
        secs = [r["files"][f][1] for r in recent if f in r.get("files", {})]
        last = next(r["files"][f] for r in reversed(recent) if f in r.get("files", {}))
        rows.append((statistics.median(secs), f, last[0], last[2] if len(last) > 2 else "?"))
    return sorted(rows, reverse=True)


def summary(days):
    runs, lands = read("runs.jsonl", days), read("lands.jsonl", days)
    if not runs:
        print(f"no runs recorded in {history_dir()}")
        return
    fulls = full_runs(runs)
    print(f"{len(runs)} runs, {len(fulls)} full, {len(lands)} lands since {runs[0]['at'][:10]} "
          f"(times UTC; {history_dir()})")
    if fulls:
        last = fulls[-1]
        total = sum(s for _, s in last["layers"].values()) or 1
        shares = " | ".join(f"{k} {n} tests {s:.0f} s ({100 * s / total:.0f}%)" for k, (n, s) in last["layers"].items())
        print(f"\nlast full run {last['at'][:16]} {last['kind']} {last['sha'][:7]}: {last['wall']:.0f} s wall\n  {shares}")
        print("\nfull runs, newest last (wall s, worker s, browser s, failed):")
        for r in fulls[-10:]:
            work = sum(s for _, s in r["layers"].values())
            print(f"  {r['at'][:16]} {r['kind']:<9} {r['sha'][:7]} {r['wall']:6.0f} {work:7.0f} "
                  f"{r['layers'].get('browser', [0, 0])[1]:7.0f} {len(r.get('failed', []))}")
        print("\nslowest files, median worker s over the last 5 full runs (s, tests, layer):")
        for s, f, n, layer in median_file_seconds(fulls)[:10]:
            print(f"  {s:6.1f}  {n:4d}  {layer:<8} {f}")
    flakes = flaky(runs)
    print(f"\nflaky tests (failed, passed on the same commit): {len(flakes) or 'none'}")
    for nodeid, (fails, passed) in sorted(flakes.items(), key=lambda x: -x[1][0])[:10]:
        print(f"  {fails} fail / {passed} pass  {nodeid}")
    if lands:
        keys = [k for k in ("test", "repeat", "mutate", "queue", "retest", "build", "push", "total") if any(k in x for x in lands)]
        med = {k: statistics.median([x[k] for x in lands if k in x]) for k in keys}
        print(f"\nlands, median s over {len(lands)}: " + " | ".join(f"{k} {v:.0f}" for k, v in med.items()))


FULL_FILES = 120     # --profile's "full run": more test files than this


def pick_profile_run(runs, which="", last=False):
    """The run --profile prints. `which` is a commit prefix, or an index into the history (0 is the
    oldest, -1 the newest; up to 3 digits or a minus sign, so a short all-digit sha still reads as one).
    With none: the latest full run that has a profile, or with `last` the latest of any size."""
    has = lambda r: bool(r.get("profile"))
    if which:
        if which.lstrip("-").isdigit() and (which.startswith("-") or len(which) < 4):
            try:
                return runs[int(which)]
            except IndexError:
                return None
        hits = [r for r in runs if r.get("sha", "").startswith(which)]
        return next((r for r in reversed(hits) if has(r)), hits[-1] if hits else None)
    pool = [r for r in runs if has(r)]
    if not last:
        pool = [r for r in pool if r.get("n_files", 0) > FULL_FILES]
    return pool[-1] if pool else None


def format_profile(rec):
    """One run's profile for an agent: the answer first, then harness against tests, the costliest
    fixtures and tests, and how busy each worker was."""
    head = f"run {rec['at'][:16].replace('T', ' ')} {rec['kind']} {rec['sha'][:7]}"
    p = rec.get("profile")
    if not p:
        return f"{head}: no profile recorded (the run predates it, or ran no layered test)"
    h, t, total = p["harness"], p["tests"], p["worker_s"] or 1.0
    harness, tests = sum(h.values()), t["setup"] + t["call"] + t["teardown"]
    pct = lambda x: f"{100 * x / total:.0f}%".replace("-0%", "0%")        # no "-0%" for a rounding crumb
    gap = 100 * p["unaccounted"] / total
    p = p | {"unaccounted": round(p["unaccounted"], 1) + 0.0}
    out = [f"{head}: {rec['wall']:.0f} s wall, {p['worker_s']:.0f} worker wall-s,{len(p['workers'])} worker(s), "
           f"{t['n']} tests" + (", dirty tree" if rec.get("dirty") else ""),
           f"harness {harness:.0f} s ({pct(harness)}) | tests {tests:.0f} s ({pct(tests)}) | "
           f"unaccounted {p['unaccounted']:.1f} s ({abs(gap):.1f}%, {'inside' if abs(gap) <= 5 else 'OUTSIDE'} 5%)", "",
           f"{'worker wall-s':<42}{'s':>8}{'%':>6}"]
    rows = [("tests: call", t["call"]), ("tests: setup (function fixtures in)", t["setup"]),
            ("tests: teardown", t["teardown"]),
            ("harness: startup (python, conftest imports)", h["startup"]), ("harness: collection", h["collect"]),
            ("harness: session fixtures, setup", h["session_setup"]),
            ("harness: session fixtures, teardown", h["session_teardown"]),
            ("harness: module fixtures, setup", h["module_setup"]),
            ("harness: module fixtures, teardown", h["module_teardown"]),
            ("harness: pytest overhead between phases", h["overhead"]),
            ("harness: idle (worker waiting for work)", h["idle"]), ("unaccounted", p["unaccounted"])]
    out += [f"{label:<42}{s:>8.1f}{pct(s):>6}" for label, s in rows]
    out.append(f"controller, beside the workers: {p['controller']:.1f} s")
    fx = sorted(p["fixtures"].items(), key=lambda kv: -(kv[1][2] + kv[1][3]))[:10]
    out += ["", "costliest fixtures (setup + teardown):", f"  {'name':<28}{'scope':<9}{'n':>5}{'setup':>8}{'teardown':>9}{'total':>8}"]
    out += [f"  {n:<28}{sc:<9}{c:>5}{su:>8.1f}{td:>9.1f}{su + td:>8.1f}" for n, (sc, c, su, td) in fx]
    out += ["", "costliest tests (s: total = setup + call + teardown; fixtures = function-scoped, in setup):"]
    out += [f"  {tot:>6.1f} = {su:.1f} + {ca:.1f} + {td:.1f}   fixtures {fxs:.1f}   {nid}"
            for nid, tot, su, ca, td, fxs in p["top"][:10]]
    out += ["", "workers (busy = in the test loop; the rest is startup, collection and idle):"]
    out += [f"  {wid:<8} wall {wall:>6.1f}  busy {100 * busy / (wall or 1):>3.0f}%  idle {idle:>6.1f}  {n:>4} tests"
            for wid, wall, busy, idle, n in p["workers"]]
    slow = max(p["workers"], key=lambda w: w[1])
    out.append(f"slowest worker {slow[0]}: wall {slow[1]:.1f} s, busy {100 * slow[2] / (slow[1] or 1):.0f}%")
    return "\n".join(out)


def land(argv):
    """land key=value ...: one land's phase seconds and outcome, from scripts/land.ps1."""
    rec = {"at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    for kv in argv:
        k, _, v = kv.partition("=")
        try:
            rec[k] = round(float(v), 1)
        except ValueError:
            rec[k] = v
    append("lands.jsonl", rec)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "land":
        return land(sys.argv[2:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--profile", nargs="?", const="", default=None, metavar="SHA|INDEX",
                    help="one run's harness-vs-tests profile: the latest full run, or this commit prefix or index")
    ap.add_argument("--last", action="store_true", help="with --profile: the latest run of any size")
    a = ap.parse_args()
    if a.profile is None and not a.last:
        return summary(a.days)
    runs = read("runs.jsonl", a.days)
    rec = pick_profile_run(runs, a.profile or "", a.last)
    print(format_profile(rec) if rec else
          f"no {'matching ' if a.profile else 'full ' if not a.last else ''}run with a profile in {history_dir()} "
          "(python scripts/run_tests.py --full records one; --last takes a run of any size)")


if __name__ == "__main__":
    main()
