"""The after-land run: the whole suite on exactly what landed, on Discord only when it fails (2026-10-07).

    python scripts/postland.py                  # fetch, then test origin/main
    python scripts/postland.py --sha <sha>      # test that commit (land.ps1 passes the landed one)
    python scripts/postland.py --dry-run        # print the plan, move nothing, run nothing, post nothing

A land no longer runs every e2e and golden test when its diff touches a shared file (the land runs what
the diff can break, scripts/impact.py). `main` deploys to Vercel within a minute, so this run is the net:
`python scripts/run_tests.py --full` with TW_RUN_KIND=postland (tests/runlog.py records it in the test
history, `python scripts/testlog.py` lists it), claiming workers from the shared budget like any run.

It runs in its own detached checkout, ~/.team-watch-postland: never the landing worktree (the session
removes it right after the land) and never ~/.team-watch-rebuild (the scheduled rebuild owns it). The
checkout is made once with `git worktree add --detach`, then moved to each sha with `checkout --force
--detach` (it is this script's own: a dirty file must not block every later run). The suite runs below
normal priority and claims at most a quarter of the worker budget (worker_slots.py): it is the one that
gives way to the sessions in front of it.

One run at a time. A lock in <git common dir>/postland holds the running pid; a second call while it
lives records its sha as pending and exits 0. The running one, when done, runs again on the pending sha
(the latest only). A dead pid is reaped, like worker_slots.py's claims.

Each failed test is rerun once (same checkout, serially, `-p no:randomly`) before anything is posted: only
a test that fails twice counts, so a flake pings nobody. A run that failed, or one that gave no result,
posts one short message through flake_run's Discord poster: the sha, the commit subject, the first 10
tests that failed twice and a count of the rest, how many failed once and passed on rerun (flaky), the rerun
command. A clean run posts nothing. A crash clears running.json and pending.json; a busy lock is logged. A dead webhook is logged, never raised: this exits 0 unless the script itself breaks.
The log is ~/.team-watch-reports/postland-<sha7>.log.

Pure and tested without git or pytest: decide, next_sha, failed_ids, message, plan_lines.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = pathlib.Path.home() / ".team-watch-postland"
REPORTS = pathlib.Path.home() / ".team-watch-reports"
RUN_TIMEOUT = 3600     # a full run is ~1-2 min, ~10 min on a loaded machine; an hour is a hang
MAX_LINES = 10         # failed ids named in the message; the rest are counted
MAX_CHARS = 1900       # Discord refuses a message over 2000
RERUN = "python scripts/run_tests.py --full"


# --- pure: what to do ---------------------------------------------------------------------------

def decide(running, alive):
    """"run" when no postland run lives (no record, or its process is gone), else "pending"."""
    return "pending" if running and alive(running) else "run"


def next_sha(pending, done):
    """The sha to run after `done`: the pending one, unless there is none or it is the one just run."""
    return pending if pending and pending != done else None


def failed_ids(text):
    """The failed and errored test ids from pytest's short summary, in order, once each."""
    seen = []
    for m in re.finditer(r"^(?:FAILED|ERROR) (\S+\.py(?:::\S+)?)", text, re.MULTILINE):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def still_failing(first, code, out):
    """Of the ids that failed in the full run, those that failed again in their rerun: none when it passed
    (exit 0), else the ids the rerun lists, else all of them (a rerun that broke or timed out proves nothing)."""
    if code == 0:
        return []
    return failed_ids(out) or list(first)


def priority_flags(osname=os.name, sp=subprocess):
    """Popen creationflags that put the suite below normal priority on Windows (workers inherit it), so a
    background check yields to the sessions in front of it; 0 elsewhere."""
    return getattr(sp, "BELOW_NORMAL_PRIORITY_CLASS", 0) if osname == "nt" else 0


def message(sha, subject, failed, code, error=None, flaky=0):
    """The Discord text for a run, or None when it was clean (exit 0 and no error). `flaky` is how many tests
    failed once and passed on rerun: failed holds only those that failed twice."""
    if code == 0 and not failed and not error:
        return None
    s = sha[:7]
    head = f"team-watch after-land run FAILED on {s}: {subject[:100]}"
    lines = [head]
    if error:
        lines.append(f"error: {error[:300]}")
    elif not failed:
        lines.append(f"no result: pytest exit {code}, no failed test listed")
    lines += [i[:160] for i in failed[:MAX_LINES]]
    if len(failed) > MAX_LINES:
        lines.append(f"... and {len(failed) - MAX_LINES} more (log: ~/.team-watch-reports/postland-{s}.log)")
    if flaky:
        lines.append(f"{flaky} more failed once and passed on rerun (flaky)")
    lines.append(f"Rerun at {s}: {RERUN}")
    return "\n".join(lines)[:MAX_CHARS]


def plan_lines(sha, checkout, exists):
    """What a run would do, one line each (--dry-run)."""
    first = (f"checkout: {checkout} (exists; git checkout --detach {sha[:7]})" if exists
             else f"checkout: {checkout} (missing; git worktree add --detach {checkout} {sha[:7]})")
    return [f"sha: {sha}", first, f"command: TW_RUN_KIND=postland {RERUN}",
            f"log: {REPORTS / ('postland-' + sha[:7] + '.log')}",
            "on failure: one Discord message; clean: nothing"]


# --- files and git: thin, not unit tested ----------------------------------------------------------

def load(name):
    """A sibling script by path: scripts/ is not on sys.path when a test imports this module."""
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", errors="replace")


def main_checkout():
    """The main checkout: the parent of the git dir every worktree shares."""
    out = git(HERE, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return pathlib.Path(out).parent


def state_dir(repo):
    d = pathlib.Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()) / "postland"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_running(state, sha):
    started = None
    try:
        import psutil
        started = psutil.Process().create_time()
    except Exception:
        pass
    (state / "running.json").write_text(json.dumps({"pid": os.getpid(), "sha": sha, "started": started,
                                                    "since": time.time()}), encoding="utf-8")


def claim(state, sha, slots):
    """True when this process now holds the run; False when one lives and `sha` is recorded as pending."""
    with slots.locked(state):
        if decide(read_json(state / "running.json"), slots.process_alive) == "pending":
            (state / "pending.json").write_text(json.dumps({"sha": sha}), encoding="utf-8")
            return False
        write_running(state, sha)
        return True


def advance(state, done, slots):
    """After a run: the pending sha to run next (and the pending record cleared), or None and the lock freed."""
    with slots.locked(state):
        pending = (read_json(state / "pending.json") or {}).get("sha")
        (state / "pending.json").unlink(missing_ok=True)
        nxt = next_sha(pending, done)
        if nxt:
            write_running(state, nxt)
        else:
            (state / "running.json").unlink(missing_ok=True)
        return nxt


def resolve(repo, sha):
    """A full sha for `sha` (or origin/main after a fetch when None), or None when it is unknown."""
    if not sha:
        git(repo, "fetch", "origin", "main")
        sha = "origin/main"
    elif git(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode:
        git(repo, "fetch", "origin")
    out = git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}")
    return out.stdout.strip() if out.returncode == 0 else None


def move_checkout(repo, sha, checkout=CHECKOUT):
    """Make `checkout` a detached worktree at `sha`; an error string when it cannot (dirty, git failed)."""
    if not (checkout / ".git").exists():
        r = git(repo, "worktree", "add", "--detach", str(checkout), sha)
        return None if r.returncode == 0 else f"worktree add failed: {r.stderr.strip()[:200]}"
    r = git(checkout, "checkout", "--force", "--detach", sha)    # this checkout is ours: a dirty file must not block every later run
    return None if r.returncode == 0 else f"checkout failed: {r.stderr.strip()[:200]}"


def run_logged(cmd, checkout, log, timeout):
    """(exit code or None on a timeout, the output cmd appended to `log`): cmd in `checkout`, tagged postland,
    below normal priority."""
    env = {**os.environ, "TW_RUN_KIND": "postland", "PYTHONIOENCODING": "utf-8"}
    start = log.stat().st_size if log.exists() else 0
    with open(log, "ab") as f:
        p = subprocess.Popen(cmd, cwd=checkout, env=env, stdout=f, stderr=subprocess.STDOUT,
                             creationflags=priority_flags())
        try:
            code = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)    # workers and Chromiums too
            p.wait()
            code = None
    with open(log, "rb") as f:
        f.seek(start)
        return code, f.read().decode("utf-8", errors="replace")


def run_suite(checkout, log, timeout=RUN_TIMEOUT):
    """(exit code or None on a timeout, pytest's output): run_tests.py --full in `checkout`."""
    return run_logged([sys.executable, "scripts/run_tests.py", "--full"], checkout, log, timeout)


def rerun_failed(checkout, failed, log, timeout=RUN_TIMEOUT):
    """(exit code or None, output): only the `failed` ids, once more, in the same checkout, serially and in file
    order. The ids go through an @args file: 170 of them would pass the Windows command line limit."""
    fd, name = tempfile.mkstemp(prefix="tw-rerun-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(failed) + "\n")
        return run_logged([sys.executable, "-m", "pytest", "@" + name, "-p", "no:randomly"], checkout, log, timeout)
    finally:
        os.remove(name)


def post(text, say, poster=None):
    """Post `text`; True when sent. A failed post is logged, never raised."""
    try:
        (poster or load("flake_run").post_discord)(text)
    except Exception as exc:    # a dead webhook must not turn a finished run into a failed job
        say(f"discord post failed: {type(exc).__name__}: {exc}")
        return False
    say("posted to Discord")
    return True


def one_run(repo, sha, say, log, poster=None):
    """Test `sha` once and post when it failed; the exit code, or None when it gave no result."""
    subject = git(repo, "log", "-1", "--format=%s", sha).stdout.strip()
    say(f"=== after-land run on {sha[:7]} {subject} ===")
    bad = move_checkout(repo, sha)
    flaky = 0
    if bad:
        code, failed, error = None, [], bad
    else:
        code, out = run_suite(CHECKOUT, log)
        failed = failed_ids(out)
        error = "no result in %d s" % RUN_TIMEOUT if code is None else None
    say(f"exit {code}, {len(failed)} failed" + (f", {error}" if error else ""))
    if failed and not error:    # a first failure may be a flake: only a test that fails twice is posted
        again = still_failing(failed, *rerun_failed(CHECKOUT, failed, log))
        flaky = len(failed) - len(again)
        say(f"rerun: {len(again)} failed again" + (f", {flaky} failed once and passed on rerun (flaky)" if flaky else ""))
        failed, code = again, (code if again else 0)    # nothing left failing is a clean run
    text = message(sha, subject, failed, code, error, flaky)
    if text is None:
        say("clean: nothing to post")
    else:
        post(text, say, poster)
    return code


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sha", help="the commit to test; default origin/main after a fetch")
    ap.add_argument("--dry-run", action="store_true", help="print the plan; move, run and post nothing")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    repo = main_checkout()
    sha = resolve(repo, a.sha)
    if not sha:
        print(f"unknown commit: {a.sha}", file=sys.stderr)
        return 1
    if a.dry_run:
        print("\n".join(plan_lines(sha, CHECKOUT, (CHECKOUT / ".git").exists())))
        print("dry run: nothing moved, nothing run, nothing posted")
        return 0
    REPORTS.mkdir(parents=True, exist_ok=True)
    slots, state = load("worker_slots"), state_dir(repo)
    try:
        mine = claim(state, sha, slots)
    except TimeoutError as e:    # the lock stayed busy: nothing was recorded, so say so and leave cleanly
        logger(sha)(f"postland not run: {e}")
        return 0
    if not mine:
        print(f"a postland run is going; {sha[:7]} is pending and runs after it")
        return 0
    try:
        while sha:
            say = logger(sha)
            one_run(repo, sha, say, REPORTS / f"postland-{sha[:7]}.log")
            sha = advance(state, sha, slots)
    finally:
        if sha:    # an error mid-run: free the lock and drop the pending sha, which would run after the next land's
            clear_state(state, slots)
    return 0


def logger(sha):
    """say(msg): one timestamped line to stdout and to the sha's log."""
    log = REPORTS / f"postland-{sha[:7]}.log"

    def say(msg):
        line = f"{dt.datetime.now():%H:%M:%S}  {msg}"
        print(line, flush=True)
        with open(log, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    return say


def clear_state(state, slots):
    """Delete running.json and pending.json, under the lock when it can be had and without it when it stays busy."""
    try:
        with slots.locked(state):
            for name in ("running.json", "pending.json"):
                (state / name).unlink(missing_ok=True)
    except TimeoutError:
        for name in ("running.json", "pending.json"):
            (state / name).unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
