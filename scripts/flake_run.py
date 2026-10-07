"""The weekly flake run: the suite N times in shuffled order on one commit, flaky tests posted to Discord.

    python scripts/flake_run.py              # the runs .testing.json `flake` sets (5), in the main checkout
    python scripts/flake_run.py --runs 3
    python scripts/flake_run.py --dry-run    # print the plan and an example message, run and post nothing

The runs are the testing skill's flake.py (`$TESTING_SKILL`, else ~/.agents/skills/testing/scripts):
the suite N times, each in a different seeded order, one after another (never in parallel: contention
is what makes a test flaky for the wrong reason). TW_RUN_KIND=flake tags each pytest run, so
tests/runlog.py still appends it to <git common dir>/test-history/runs.jsonl and `python
scripts/testlog.py` still lists the flaky tests.

A test that failed in some runs and passed in others is FLAKY; one that failed in every run is BROKEN.
Either, or a run that gave no result, posts one short message to the Discord webhook in
~/.config/ff-jarvis/discord.json. A clean run posts nothing.

Then each suite in .testing.json limits.suites (fast: unit + integration, 10 s; component, 35 s) runs 3
times through the testing skill's pytest_limits plugin, and its fastest wall time is held to its budget:
a suite over it adds a line to the same message, one under it adds nothing. Wall time swings 15-49 s with
the machine's load, so this quiet-machine job is the one place it is enforced, never the land. Every
suite's fastest time goes in the dated log. A failed post is logged, never raised:
this exits 0 unless the script itself breaks.

Runs in the main checkout, not a worktree: that is the tree the scheduled rebuild keeps current.
It fast-forwards to origin only when that checkout is on main and clean; otherwise it runs what is
there and says so. Output goes to stdout and to ~/.team-watch-reports/flake-<date>.txt, whose age is
the job's liveness check in agent-config's jobs.ps1.
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
REPORTS = pathlib.Path.home() / ".team-watch-reports"
WEBHOOK_FILE = pathlib.Path.home() / ".config" / "ff-jarvis" / "discord.json"
RUN_TIMEOUT = 900    # per run, flake.py's own limit; this script allows every run its share and a margin
DEFAULT_RUNS = 5
MAX_LINES = 10       # failing tests named in the message; the rest are counted
MAX_CHARS = 1900     # Discord refuses a message over 2000


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def main_checkout():
    """The main checkout: the parent of the git dir every worktree shares."""
    out = git(HERE, "rev-parse", "--git-common-dir").stdout.strip()
    common = pathlib.Path(out)
    common = common if common.is_absolute() else (HERE / common)
    return common.resolve().parent


def skill_dir(environ=None):
    """The testing skill's scripts dir: $TESTING_SKILL when set, else the installed copy (same as run_tests.py)."""
    environ = os.environ if environ is None else environ
    return pathlib.Path(environ.get("TESTING_SKILL") or pathlib.Path.home() / ".agents" / "skills" / "testing" / "scripts")


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


# --- the runs: the skill's flake.py --------------------------------------------------------------

def flake_command(skill, repo, runs=None):
    cmd = [sys.executable, str(pathlib.Path(skill) / "flake.py"), "--repo", str(repo), "--json"]
    return cmd + (["--runs", str(runs)] if runs else [])


def run_flake(cmd, timeout, env, cwd=None):
    """(exit code, stdout, stderr) of flake.py; on a timeout the whole process tree is stopped."""
    p = subprocess.Popen(cmd, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, encoding="utf-8", errors="replace")
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # The whole tree: killing python alone would orphan its xdist workers and their Chromiums.
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        p.communicate()
        return None, "", f"flake.py gave no result in {timeout} s"
    return p.returncode, out, err


def parse_report(code, out, err):
    """flake.py's JSON report, or an error report when it printed none."""
    try:
        report = json.loads(out)
        if isinstance(report, dict) and "flaky" in report and "broken" in report:
            report.setdefault("runs", [])
            report.setdefault("error", None)
            return report
    except ValueError:
        pass
    why = (err or out or "").strip()[-300:].replace("\n", " ")
    return error_report(f"flake.py exit {code}: {why}")


def error_report(text):
    return {"runs": [], "flaky": [], "broken": [], "error": text}


# --- suite wall-time budgets ----------------------------------------------------------------------
# `.testing.json` limits.suites names suites ({"fast": {"layers": [...], "wall_s": 10}}). Wall time
# swings with the machine's load, so no land enforces it; this job runs on a quiet machine (Wednesday
# 3:30 am) and takes the fastest of SUITE_RUNS runs per suite.

SUITE_RUNS = 3
FLAKE_ARGS = ["-n", "auto", "--dist", "loadgroup"]


def testing_json(repo):
    try:
        return json.loads((pathlib.Path(repo) / ".testing.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def suites_from(repo):
    """{suite name: wall_s budget} from the repo's .testing.json limits.suites; {} when it names none."""
    suites = (testing_json(repo).get("limits") or {}).get("suites") or {}
    return {name: s["wall_s"] for name, s in suites.items()}


def suite_command(name, json_path, args=None):
    """pytest for one suite: the plugin deselects the other layers and writes its wall time to json_path."""
    return [sys.executable, "-m", "pytest", *(args or FLAKE_ARGS), "-q", "-p", "pytest_limits",
            "--limits-suite", name, "--limits-suite-json", str(json_path)]


def suite_env(skill, environ=None):
    """The environment of a suite run: the skill dir first on PYTHONPATH (the plugin), the run tagged flake."""
    environ = dict(os.environ if environ is None else environ)
    old = environ.get("PYTHONPATH")
    environ["PYTHONPATH"] = str(skill) + (os.pathsep + old if old else "")
    environ["TW_RUN_KIND"] = "flake"
    return environ


def read_wall(path):
    """The wall seconds the plugin wrote, or None when it wrote nothing readable (the run gave no result)."""
    try:
        return float(json.loads(pathlib.Path(path).read_text(encoding="utf-8"))["wall_s"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def measure_suites(budgets, run, tries=SUITE_RUNS):
    """{name: {"fastest_s", "budget_s", "runs_s"}}: `run(name)` -> wall seconds or None, `tries` times each."""
    out = {}
    for name, budget in budgets.items():
        walls = [w for w in (run(name) for _ in range(tries)) if w is not None]
        out[name] = {"fastest_s": min(walls) if walls else None, "budget_s": budget, "runs_s": walls}
    return out


def suite_runner(skill, repo, args=None):
    """`run(name)` for measure_suites: one pytest run of the suite in `repo`, its wall seconds or None."""
    def run(name):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "suite.json"
            run_flake(suite_command(name, path, args), RUN_TIMEOUT, suite_env(skill), cwd=str(repo))
            return read_wall(path)
    return run


def over_budget(result):
    return result["fastest_s"] is None or result["fastest_s"] > result["budget_s"]


def suite_lines(suites):
    """One message line per suite over its budget (or with no timing); a suite on budget adds nothing."""
    lines = []
    for name, r in (suites or {}).items():
        if r["fastest_s"] is None:
            lines.append(f"suite {name}: no timing in {SUITE_RUNS} runs, budget {r['budget_s']:g} s")
        elif over_budget(r):
            lines.append(f"suite {name}: {r['fastest_s']:.1f} s, budget {r['budget_s']:g} s "
                         f"(fastest of {SUITE_RUNS})")
    return lines


# --- the message ----------------------------------------------------------------------------------

def message(report, planned=DEFAULT_RUNS, skill=None):
    """The Discord text for a report, or None when the run was clean."""
    flaky, broken, error = report["flaky"], report["broken"], report.get("error")
    slow = suite_lines(report.get("suites"))
    if not (flaky or broken or error or slow):
        return None
    runs = len(report["runs"]) or planned
    lines = [f"team-watch flake run: {len(flaky)} flaky, {len(broken)} broken ({runs} shuffled runs)"]
    if error:
        lines.append(f"error: {error[:300]}")
    named = flaky + broken
    for item in named[:MAX_LINES]:
        seeds = ", ".join(str(s) for s in item["failed_seeds"])
        lines.append(f"{item['nodeid'][:160]} — failed on seed {seeds}")
    if len(named) > MAX_LINES:
        lines.append(f"... and {len(named) - MAX_LINES} more (python scripts/testlog.py)")
    lines += slow
    if named:
        where = f" (PYTHONPATH={skill})" if skill else ""
        lines.append(f"Reproduce: python -m pytest -p pytest_shuffle --shuffle {named[0]['failed_seeds'][0]}{where}")
    return "\n".join(lines)[:MAX_CHARS]


def webhook_url(path=WEBHOOK_FILE):
    with open(path, encoding="utf-8") as f:
        url = json.load(f).get("webhook")
    if not url:
        raise RuntimeError(f"no webhook in {path}")
    return url


def post_discord(content, url=None, opener=urllib.request.urlopen):
    """POST {"content": content} to the webhook. Raises on any failure; notify() logs it."""
    req = urllib.request.Request(
        url or webhook_url(), data=json.dumps({"content": content}).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (team-watch flake)"})
    with opener(req, timeout=20) as resp:
        return getattr(resp, "status", None)


def notify(report, say, planned=DEFAULT_RUNS, skill=None, dry=False, poster=post_discord):
    """Post the message when there is one; True when it was posted. Never raises: a failed post is logged."""
    text = message(report, planned, skill)
    if text is None:
        say("clean: nothing to post")
        return False
    if dry:
        say("would post to Discord:\n" + text)
        return False
    try:
        poster(text)
    except Exception as exc:    # a dead webhook must not turn a finished run into a failed job
        say(f"discord post failed: {type(exc).__name__}: {exc}")
        return False
    say("posted to Discord")
    return True


def log_report(report, say):
    for r in report["runs"]:
        say(f"seed {r['seed']}: {r['passed']} passed, {r['failed']} failed, {r['seconds']} s")
    for label, items in (("FLAKY", report["flaky"]), ("BROKEN", report["broken"])):
        for item in items:
            say(f"{label}  {item['nodeid']}  failed on seed {', '.join(str(s) for s in item['failed_seeds'])}")
    if report.get("error"):
        say(f"ERROR  {report['error']}")
    for name, r in (report.get("suites") or {}).items():
        mark = ", OVER" if over_budget(r) else ""
        if r["fastest_s"] is None:
            say(f"suite {name}: no timing in {SUITE_RUNS} runs, budget {r['budget_s']:g} s{mark}")
        else:
            say(f"suite {name}: fastest {r['fastest_s']:.1f} s, budget {r['budget_s']:g} s{mark} "
                f"(runs {', '.join(f'{w:.1f}' for w in r['runs_s'])})")
    say(f"flake: {len(report['runs'])} runs, {len(report['flaky'])} flaky, {len(report['broken'])} broken "
        f"(python scripts/testlog.py lists the flaky tests)")


SAMPLE = {"runs": [], "error": None, "broken": [],
          "flaky": [{"nodeid": "tests.test_example::test_a", "failed_seeds": [101], "passed_seeds": [102, 103]}]}
SAMPLE_SUITES = {"fast": {"fastest_s": 12.4, "budget_s": 10, "runs_s": [13.0, 12.4, 12.9]},
                 "component": {"fastest_s": 29.0, "budget_s": 35, "runs_s": [29.0, 30.1, 29.5]}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", type=int, default=None, help="default: .testing.json flake.runs (5)")
    ap.add_argument("--repo", type=pathlib.Path, default=None, help="default: the main checkout")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")    # the message holds an em dash; a cp1252 console would raise

    repo = (args.repo or main_checkout()).resolve()
    skill = skill_dir()
    runs = args.runs or DEFAULT_RUNS
    if not args.dry_run:
        REPORTS.mkdir(parents=True, exist_ok=True)
    say = Out(None if args.dry_run else REPORTS / f"flake-{dt.date.today():%Y-%m-%d}.txt")
    say(f"=== flake run: {runs} shuffled runs in {repo} ===")
    sync(repo, say, args.dry_run)

    cmd = flake_command(skill, repo, args.runs)
    budgets = suites_from(repo)
    flake_args = (testing_json(repo).get("flake") or {}).get("args")
    if args.dry_run:
        say(f"would run: TW_RUN_KIND=flake {' '.join(cmd)}")
        for name, budget in budgets.items():
            say(f"would run {SUITE_RUNS}x, fastest wins (budget {budget:g} s): "
                f"{' '.join(suite_command(name, '<tmp>/suite.json', flake_args))}")
        notify({**SAMPLE, "suites": SAMPLE_SUITES}, say, runs, skill, dry=True)
        say("dry run: nothing run, nothing posted")
        return 0

    if (skill / "flake.py").is_file():
        env = {**os.environ, "TW_RUN_KIND": "flake"}
        report = parse_report(*run_flake(cmd, runs * RUN_TIMEOUT + 300, env))
    else:
        report = error_report(f"no flake.py in {skill}: update the testing skill")
    if budgets and (skill / "pytest_limits.py").is_file():
        report["suites"] = measure_suites(budgets, suite_runner(skill, repo, flake_args))
    elif budgets:
        report["error"] = report.get("error") or f"no pytest_limits.py in {skill}: suites not timed"
    log_report(report, say)
    notify(report, say, runs, skill)
    return 0


if __name__ == "__main__":
    sys.exit(main())
