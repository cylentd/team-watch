"""The test history: every pytest run and every land, one JSON line each, and what they add up to.

    python scripts/testlog.py            # the summary: layers, trend, slowest files, flaky tests, lands
    python scripts/testlog.py --days 7   # the same over the last week

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
    summary(ap.parse_args().days)


if __name__ == "__main__":
    main()
