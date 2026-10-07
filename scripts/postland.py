"""The after-land run: the whole suite on exactly what landed, on Discord only when it fails (2026-10-07).

    python scripts/postland.py                  # fetch, then test origin/main
    python scripts/postland.py --sha <sha>      # test that commit (land.ps1 and testsched's after_land pass the landed one)
    python scripts/postland.py --dry-run        # print the plan, move nothing, run nothing, post nothing

A land no longer runs every e2e and golden test when its diff touches a shared file (the land runs what
the diff can break, scripts/impact.py). `main` deploys to Vercel within a minute, so this run is the net:
`python scripts/run_tests.py --full` with TW_RUN_KIND=postland (tests/runlog.py records it in the test
history, `python scripts/testlog.py` lists it). run_tests.py runs it through loadgate's `postland` class:
idle priority, a quarter of the worker budget, waits until 2 workers are free, never reads the result cache.

It runs in its own detached checkout, ~/.team-watch-postland: never the landing worktree (the session
removes it right after the land) and never ~/.team-watch-rebuild (the scheduled rebuild owns it). The
checkout is made once with `git worktree add --detach`, then moved to each sha with `checkout --force
--detach` (it is this script's own: a dirty file must not block every later run).

One run at a time: testsched's coalesce job `postland`. A second call while one lives records its sha as
pending and exits 0; the running one, when done, runs again on the pending sha (the latest only). A dead
runner's job is reaped by the next call. No loadgate library on this machine: one run, no lock, no check.

Each failed test is rerun once (same checkout, serially, `-p no:randomly`) before anything is posted: only
a test that fails twice counts, so a flake pings nobody. A run that failed, or one that gave no result,
posts one short message through flake_run's Discord poster: the sha, the commit subject, the first 10
tests that failed twice and a count of the rest, how many failed once and passed on rerun (flaky), the rerun
command. A clean run posts nothing. A busy lock is logged. A dead webhook is logged, never raised: this exits
0 unless the script itself breaks. The log is ~/.team-watch-reports/postland-<sha7>.log.

The result cache's check (testsched `cache.verify`): run_tests.py writes {file: passed|failed} next to the log
(postland-<sha7>.json); a file whose test failed twice while the cache holds a pass for the same inputs is a
lie. The cache goes off, an event is written, and the message names the file.

Pure and tested without git or pytest: message, failed_ids, still_failing, outcomes, plan_lines.
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
import types

HERE = pathlib.Path(__file__).resolve().parent
CHECKOUT = pathlib.Path.home() / ".team-watch-postland"
REPORTS = pathlib.Path.home() / ".team-watch-reports"
JOB = "postland"       # the coalesce job: one run at a time, the latest sha pending
RUN_TIMEOUT = 3600     # a full run is ~1-2 min, ~10 min on a loaded machine; an hour is a hang
MAX_LINES = 10         # failed ids named in the message; the rest are counted
MAX_CHARS = 1900       # Discord refuses a message over 2000
RERUN = "python scripts/run_tests.py --full"


# --- pure: what to say --------------------------------------------------------------------------

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


def message(sha, subject, failed, code, error=None, flaky=0, lies=()):
    """The Discord text for a run, or None when it was clean (exit 0 and no error). `flaky` is how many tests
    failed once and passed on rerun: failed holds only those that failed twice. `lies` are the files whose
    failure the result cache had a pass for."""
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
    if lies:
        lines.append(f"cache lie: {', '.join(lies)} failed with a cached pass; the result cache is off")
    lines.append(f"Rerun at {s}: {RERUN}")
    return "\n".join(lines)[:MAX_CHARS]


def outcomes(units, failed):
    """{file: passed|failed} for the files that ran (`units`, a file -> outcome map or None) given the test ids
    that failed twice: a file is failed only when one of its own tests failed both times. None: nothing ran."""
    if not units:
        return None
    bad = {i.split("::")[0] for i in failed}
    return {u: ("failed" if u in bad else "passed") for u in units}


def results_path(log):
    """Where run_tests.py writes the units it ran, beside the log."""
    return pathlib.Path(log).with_suffix(".json")


def plan_lines(sha, checkout, exists):
    """What a run would do, one line each (--dry-run)."""
    first = (f"checkout: {checkout} (exists; git checkout --detach {sha[:7]})" if exists
             else f"checkout: {checkout} (missing; git worktree add --detach {checkout} {sha[:7]})")
    return [f"sha: {sha}", first, f"command: TW_RUN_KIND=postland {RERUN}",
            f"log: {REPORTS / ('postland-' + sha[:7] + '.log')}",
            f"job: testsched coalesce '{JOB}' (one run at a time; a sha that lands during a run waits, the latest only)",
            "workers: loadgate class postland (idle priority, a quarter of the budget, waits until 2 are free)",
            "then: cache verify on the run's results (a cached pass that fails twice is a lie: the cache goes off)",
            "on failure: one Discord message; clean: nothing"]


# --- files and git: thin, not unit tested ----------------------------------------------------------

def load(name):
    """A sibling script by path: scripts/ is not on sys.path when a test imports this module."""
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_sched():
    """testsched's coalesce and cache modules, or None when the library is not on this machine (run_tests.py
    knows where to look)."""
    code = load("run_tests").reach()
    if code is None:
        return None
    if str(code) not in sys.path:
        sys.path.insert(0, str(code))
    try:
        from testsched import cache, coalesce
    except ImportError as e:
        print(f"loadgate not usable ({e}): one run, no lock, no cache check", file=sys.stderr)
        return None
    return types.SimpleNamespace(coalesce=coalesce, cache=cache)


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8", errors="replace")


def main_checkout():
    """The main checkout: the parent of the git dir every worktree shares."""
    out = git(HERE, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return pathlib.Path(out).parent


def read_json(path):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


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
    """(exit code or None on a timeout, the output cmd appended to `log`): cmd in `checkout`, tagged postland.
    The priority is the class's: run_tests.py claims `postland` from loadgate, whose runner sets it."""
    env = {**os.environ, "TW_RUN_KIND": "postland", "PYTHONIOENCODING": "utf-8"}
    start = log.stat().st_size if log.exists() else 0
    with open(log, "ab") as f:
        p = subprocess.Popen(cmd, cwd=checkout, env=env, stdout=f, stderr=subprocess.STDOUT)
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
    """(exit code or None on a timeout, pytest's output): run_tests.py --full in `checkout`, which writes the
    files it ran to results_path(log)."""
    results_path(log).unlink(missing_ok=True)
    return run_logged([sys.executable, "scripts/run_tests.py", "--full", "--results-json", str(results_path(log))],
                      checkout, log, timeout)


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


def check_cache(sched, repo, sha, log, failed, code, say):
    """The files whose failure the result cache had a pass for. Only a run that said what failed (or passed) is
    checked: a crash marks nothing. A check that breaks is logged and changes nothing."""
    units = read_json(results_path(log))
    results = outcomes(units, failed)
    if sched is None or results is None or not (failed or code == 0):
        return []
    try:
        lies = sched.cache.verify(repo, results, root=CHECKOUT, sha=sha)["lies"]
    except Exception as exc:    # the check is a net under the cache; it must not hide the result
        say(f"cache check not made: {type(exc).__name__}: {exc}")
        return []
    if lies:
        say(f"cache lie: {', '.join(lies)}")
    return lies


def one_run(repo, sha, say, log, poster=None, sched=None):
    """Test `sha` once and post when it failed; the exit code, or None when it gave no result."""
    subject = git(repo, "log", "-1", "--format=%s", sha).stdout.strip()
    say(f"=== after-land run on {sha[:7]} {subject} ===")
    bad = move_checkout(repo, sha)
    flaky, lies = 0, []
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
    if not error:
        lies = check_cache(sched, repo, sha, log, failed, code, say)
    text = message(sha, subject, failed, code, error, flaky, lies)
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
    sched = load_sched()

    def work(s):
        one_run(repo, s, logger(s), REPORTS / f"postland-{s[:7]}.log", sched=sched)
    if sched is None:    # no lock to share: the one run, as before there was a library
        work(sha)
        return 0
    try:
        got = sched.coalesce.submit(repo, JOB, sha, work=work)
    except TimeoutError as e:    # the lock stayed busy: nothing was recorded, so say so and leave cleanly
        logger(sha)(f"postland not run: {e}")
        return 0
    if got == "pending":
        print(f"a postland run is going; {sha[:7]} is pending and runs after it")
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


if __name__ == "__main__":
    sys.exit(main())
