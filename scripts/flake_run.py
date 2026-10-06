"""The nightly flake run: the full suite N times on one commit, each run recorded in the test history.

    python scripts/flake_run.py              # 3 runs in the main checkout
    python scripts/flake_run.py --runs 5
    python scripts/flake_run.py --dry-run    # print the plan, run nothing, touch nothing

Each run is `python -m pytest -n auto --dist loadgroup` with TW_RUN_KIND=flake, one after another
(never in parallel: contention is what makes a test flaky for the wrong reason). tests/runlog.py
appends every run to <git common dir>/test-history/runs.jsonl; a test that failed in one run and
passed in another of the same commit is flaky, and `python scripts/testlog.py` lists them.
No dashboard and no notification: a flake is data, so this exits 0 unless the script itself breaks.

Runs in the main checkout, not a worktree: that is the tree the scheduled rebuild keeps current.
It fast-forwards to origin only when that checkout is on main and clean; otherwise it runs what is
there and says so. Output goes to stdout and to ~/.team-watch-reports/flake-<date>.txt, whose age is
the job's liveness check in agent-config's jobs.ps1.
"""
import argparse
import datetime as dt
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPORTS = pathlib.Path.home() / ".team-watch-reports"
PYTEST = ["-m", "pytest", "-n", "auto", "--dist", "loadgroup"]
RUN_TIMEOUT = 900    # a full run takes about 60 s; fifteen times that is a hang, not a slow night


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def main_checkout():
    """The main checkout: the parent of the git dir every worktree shares."""
    out = git(HERE, "rev-parse", "--git-common-dir").stdout.strip()
    common = pathlib.Path(out)
    common = common if common.is_absolute() else (HERE / common)
    return common.resolve().parent


class Out:
    """Print every line, and keep it in the dated log unless this is a dry run."""
    def __init__(self, path):
        self.path = path

    def __call__(self, msg):
        line = f"{dt.datetime.now():%H:%M:%S}  {msg}"
        print(line, flush=True)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")


def sync(repo, say, dry):
    """Fast-forward to origin only on a clean main; say what was left alone otherwise."""
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    # Untracked files (a stray screenshot, a log) do not block a fast-forward; tracked edits do.
    dirty = bool(git(repo, "status", "--porcelain", "--untracked-files=no").stdout.strip())
    if branch != "main" or dirty:
        why = f"on {branch}" if branch != "main" else "dirty"
        say(f"not updating: the checkout is {why}; running what is there")
    elif dry:
        say("would fetch, then merge --ff-only @{u} (clean main)")
    else:
        fetched = git(repo, "fetch")
        merged = git(repo, "merge", "--ff-only", "@{u}")
        if fetched.returncode or merged.returncode:
            say(f"update failed ({(fetched.stderr or merged.stderr).strip()[:120]}); running what is there")
        else:
            say("fetched and fast-forwarded: " + (merged.stdout.strip().splitlines() or ["up to date"])[0])
    sha = git(repo, "rev-parse", "--short", "HEAD").stdout.strip()
    say(f"commit {sha}")


def failures_in(text):
    """The failed + error count from pytest's last summary line, or None when there is none."""
    last = next((ln for ln in reversed(text.splitlines()) if re.search(r"\b(passed|failed|error)", ln)), "")
    n = sum(int(m.group(1)) for m in re.finditer(r"(\d+) (?:failed|errors?)\b", last))
    return n if last else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--repo", type=pathlib.Path, default=None, help="default: the main checkout")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    repo = (args.repo or main_checkout()).resolve()
    if not args.dry_run:
        REPORTS.mkdir(parents=True, exist_ok=True)
    say = Out(None if args.dry_run else REPORTS / f"flake-{dt.date.today():%Y-%m-%d}.txt")
    say(f"=== flake run: {args.runs} runs in {repo} ===")
    sync(repo, say, args.dry_run)

    cmd = [sys.executable, *PYTEST]
    env = {**os.environ, "TW_RUN_KIND": "flake"}
    if args.dry_run:
        for i in range(1, args.runs + 1):
            say(f"would run {i}/{args.runs}: TW_RUN_KIND=flake {' '.join(cmd)} (cwd {repo})")
        say(f"dry run: {args.runs} runs planned, nothing run")
        return 0

    fails = []
    for i in range(1, args.runs + 1):
        say(f"run {i}/{args.runs}")
        p = subprocess.Popen(cmd, cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace")
        try:
            out, err = p.communicate(timeout=RUN_TIMEOUT)
        except subprocess.TimeoutExpired:
            # The whole tree: killing python alone would orphan its xdist workers and their Chromiums.
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
            p.communicate()
            fails.append("timeout")
            say(f"run {i} gave no result in {RUN_TIMEOUT} s: stopped (a hung test is itself a finding)")
            continue
        tail = (out or "").strip().splitlines()[-1:] or ["(no output)"]
        n = failures_in(out or "")
        fails.append(n if n is not None else f"exit {p.returncode}")
        say(f"run {i} exit {p.returncode}: {tail[0]}")
        if p.returncode and n is None:
            say("  " + (err or "").strip()[-300:].replace("\n", " "))
    say(f"flake: {args.runs} runs, failures per run: {' '.join(str(f) for f in fails)} "
        f"(python scripts/testlog.py lists the flaky tests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
