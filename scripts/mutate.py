"""Mutation check on the code a branch changed (2026-10-05): does a test fail when the behaviour breaks?

    python scripts/mutate.py                          # design/src/js/data/*.js and design/*.py changed vs origin/main
    python scripts/mutate.py --files design/src/js/data/stock.js --max-mutants 10
    python scripts/mutate.py --threshold 60 --gate    # exit 1 below the threshold (default: warn, exit 0)
    python scripts/mutate.py --json                   # the report as JSON
    python scripts/mutate.py --budget 120             # start no new mutant after 120 s; partial score

One operator at a time, one mutant at a time: the mutated file is written in place, the tests that cover
it run, and the file is put back (a `finally`, SIGINT/SIGTERM and atexit all restore it, and the sha256
is checked). A mutant is killed when those tests exit nonzero or time out, and survives when they pass.
Score = killed / mutants. With --base, only lines the branch added or changed are mutated (the diff
against the fork point, uncommitted edits included); with --files, every line.

Operators (text level; comments, strings and JS regex literals are skipped):
    cmp     < <= > >=  === !==  == !=          arith   + -  * /
    bool    && ||  and or  true false          return  `return X` -> `return null` / `return None`
    const   integer n -> n+1

Tests per file: tests that name the file (data/<x>.js, or `import <x>` for design/<x>.py), plus the
tests impact.py picks for it, minus the shared checks (build, lint, budgets...) and test_render.py.
Node- and Python-layer files are preferred over browser ones, and `-m "not render"` is passed. The
unmutated file must pass them first, else the file is skipped as "baseline red". A file no test covers
counts every mutant as survived: untested changed code is what the score is for.

A mutant that does not parse (`node --check`, `compile`) is dropped, not counted. Mutants an equivalent
rewrite cannot be told from (x * 1 -> x / 1) survive; that is why the gate starts at 60%, not 100%.
"""
import argparse
import atexit
import contextlib
import hashlib
import json
import pathlib
import signal
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from mutate_ops import mask_js, mask_py, line_mutants, mutants_of, sample  # noqa: E402,F401
from mutate_select import (JS_DIR, META, HEAVY, TIMEOUT, git, eligible, changed_files, changed_lines,  # noqa: E402,F401
                           tests_for, run_pytest, parses)

_HELD = {}  # path -> original bytes of a file currently mutated


# ---------------------------------------------------------------- the file is always put back


def digest(b):
    return hashlib.sha256(b).hexdigest()


def put_back(path):
    original = _HELD.get(path)
    if original is None:
        return
    pathlib.Path(path).write_bytes(original)
    if digest(pathlib.Path(path).read_bytes()) != digest(original):
        raise RuntimeError(f"{path} was not restored: restore it with git checkout or from your editor")
    del _HELD[path]
    clear_pyc(path)


def clear_pyc(path):
    """A same-size mutant inside one second would load the last mutant's bytecode."""
    p = pathlib.Path(path)
    for pyc in (p.parent / "__pycache__").glob(p.stem + ".*.pyc"):
        with contextlib.suppress(OSError):
            pyc.unlink()


@contextlib.contextmanager
def in_place(path, text):
    """path holds text inside the block, and its original bytes after it, whatever happens."""
    p = pathlib.Path(path)
    _HELD.setdefault(path, p.read_bytes())
    try:
        p.write_bytes(text.encode("utf-8"))
        clear_pyc(path)
        yield
    finally:
        put_back(path)


def restore_all():
    for path in list(_HELD):
        with contextlib.suppress(Exception):
            put_back(path)


def _die(signum, frame):
    raise KeyboardInterrupt


# ---------------------------------------------------------------- the run


def mutate_file(rel, root, lines, limit, run=run_pytest, valid=parses, tests=None, deadline=None,
                clock=time.monotonic):
    """One file's report. run(files) -> exit code; valid(path) -> bool; tests overrides the selection.
    No mutant starts once clock() passes deadline (a `clock` value, None = no limit): budget_hit is set."""
    path = str(pathlib.Path(root) / rel)
    py = rel.endswith(".py")
    original = pathlib.Path(path).read_bytes()
    text = original.decode("utf-8")
    muts = sample(mutants_of(text, py, lines), limit, rel)
    report = {"path": rel, "status": "ok", "tests": [], "mutants": 0, "killed": 0, "survived": [], "invalid": 0,
              "planned": len(muts), "budget_hit": False}

    def late():
        return deadline is not None and clock() > deadline
    if not muts:
        return {**report, "status": "no mutants"}
    files = tests_for(rel, root) if tests is None else tests
    report["tests"] = files
    if not files:
        report["status"] = "untested"
        report["mutants"] = len(muts)
        report["survived"] = [_shown(m) for m in muts]
        return report
    if late():
        return {**report, "status": "budget", "budget_hit": True}
    if run(files) != 0:
        return {**report, "status": "baseline red"}
    for m in muts:
        if late():
            report["budget_hit"] = True
            break
        with in_place(path, text[:m["start"]] + m["new"] + text[m["end"]:]):
            if not valid(path):
                report["invalid"] += 1
                continue
            code = run(files)
        report["mutants"] += 1
        if code != 0:
            report["killed"] += 1
        else:
            report["survived"].append(_shown(m))
    if digest(pathlib.Path(path).read_bytes()) != digest(original):
        raise RuntimeError(f"{rel} differs from its original after the run")
    return report


def _shown(m):
    return {"line": m["line"], "op": m["op"], "old": m["old"], "new": m["new"]}


def score(killed, total):
    return None if not total else round(100.0 * killed / total, 1)


def summarize(reports, threshold):
    killed, total = sum(r["killed"] for r in reports), sum(r["mutants"] for r in reports)
    s = score(killed, total)
    run = sum(r["mutants"] + r.get("invalid", 0) for r in reports)
    planned = sum(r["planned"] if r.get("budget_hit") else r["mutants"] + r.get("invalid", 0) for r in reports)
    return {"threshold": threshold, "killed": killed, "mutants": total, "score": s,
            "pass": s is None or s >= threshold, "files": reports,
            "budget_hit": any(r.get("budget_hit") for r in reports), "run": run, "planned": planned}


def render(summary):
    lines = []
    for r in summary["files"]:
        head = f"{r['path']}  [{r['status']}]"
        if r["tests"]:
            head += "  tests: " + " ".join(r["tests"])
        lines.append(head)
        if r["mutants"]:
            lines.append(f"  mutants {r['mutants']}  killed {r['killed']}  survived {len(r['survived'])}"
                         f"  score {score(r['killed'], r['mutants'])}%")
        for s in r["survived"]:
            lines.append(f"  survived: line {s['line']} {s['op']} `{s['old']}` -> `{s['new']}`")
    if summary["score"] is None:
        lines.append("overall: no mutants")
    else:
        lines.append(f"overall: {summary['killed']}/{summary['mutants']} killed = {summary['score']}% "
                     f"(threshold {summary['threshold']}%)")
    if summary.get("budget_hit"):
        lines.append(f"(budget hit: {summary['run']} of {summary['planned']} mutants run)")
    return "\n".join(lines)


def main(argv=None, run=run_pytest, valid=parses, root=ROOT):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--files", nargs="+", help="mutate these (repo-relative) files, every line")
    ap.add_argument("--threshold", type=float, default=60.0)
    ap.add_argument("--gate", action="store_true", help="exit 1 below the threshold")
    ap.add_argument("--max-mutants", type=int, default=30, help="per file, sampled with a fixed seed")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--budget", type=float, metavar="SECONDS",
                    help="start no new mutant after this many seconds; the partial score is reported")
    a = ap.parse_args(argv)
    atexit.register(restore_all)
    old = {s: signal.signal(s, _die) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        return _run(a, run, valid, root)
    finally:
        for s, handler in old.items():
            signal.signal(s, handler)
        restore_all()


def _run(a, run, valid, root):
    try:
        if a.files:
            targets = [(f.replace("\\", "/"), None) for f in a.files]
        else:
            targets = [(f, changed_lines(a.base, f, root)) for f in changed_files(a.base, root)]
    except subprocess.CalledProcessError as e:
        print(f"mutate: git failed ({e.stderr.strip() or e}); is {a.base} fetched?", file=sys.stderr)
        return 2
    reports = []
    deadline = None if a.budget is None else time.monotonic() + a.budget
    for rel, lines in targets:
        if not eligible(rel):
            print(f"mutate: {rel} is not design/src/js/data/*.js or design/*.py", file=sys.stderr)
            return 2
        reports.append(mutate_file(rel, root, lines, a.max_mutants, run=run, valid=valid, deadline=deadline))
    summary = summarize(reports, a.threshold)
    print(json.dumps(summary, indent=1) if a.json else render(summary))
    if not summary["pass"]:
        print(f"WARNING: mutation score {summary['score']}% is below {a.threshold:g}%: a test the branch "
              "added or kept does not fail when the code it covers breaks", file=sys.stderr)
        return 1 if a.gate else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
