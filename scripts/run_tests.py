"""Run the tests your change can break, in parallel (2026-10-05). land.ps1 runs its tests through here.

    python scripts/run_tests.py               # what the edits on disk can break, uncommitted ones included
    python scripts/run_tests.py --full        # everything
    python scripts/run_tests.py -- -x -k dossier   # anything after -- goes to pytest as is
    python scripts/run_tests.py --repeat-new 10    # every test the branch added or changed, 10 times

A Preview edit runs Preview's tests, Preview's golden slice and the core every view shares (the
build, lint, syntax, budgets), about 15 s; a bare `pytest` runs all of it, one test at a time.
scripts/impact.py picks the files: a path no area claims, shared CSS or shared test setup still
runs everything, minus the browser tests outside impact's files (--e2e-only-in, 2026-10-07: the
after-land run covers them; --full runs all). Exits with pytest's code.

Gating runs (the default and --full, which land.ps1 calls) pass --no-quarantine: a test marked
quarantine drops out of the gate until fixed (--with-quarantine keeps it). --repeat-new N is the
10-run gate for new tests (tests/README.md "Proving a test"); this module doubles as its pytest
plugin (`-p run_tests`), which parametrizes each test N times, so xdist spreads the runs.

The testing skill's time limits (`-p pytest_limits`, `.testing.json` `limits`: a limit per layer and
a shrink-only backlog) load here and nowhere else, so a mutant run or a shuffled flake run is never
timed. An ordinary run lists the tests over their limit; only --repeat-new passes --limits-enforce,
failing a new or changed test whose fastest copy is over. The skill dir is $TESTING_SKILL if set,
else the installed copy (~/.agents/skills/testing/scripts).

Workers and the result cache are loadgate's and testsched's (agent-config/testsched/SPEC.md, 2026-10-07).
The picked files are the cache's units: testsched.runner.run claims workers for the run's class (dev for a
session, land for land.ps1 and --committed, postland for the after-land run; TW_RUN_KIND names it), serves a
file whose inputs have not changed since its last pass, and runs the rest. `--dry-run` prints the claim it
would make and the cache plan. `--results-json PATH` writes {file: passed|failed} for postland's cache check.
LOADGATE=off (TESTSCHED=off, TW_SLOTS=off) runs everything as before. A run that cannot go through a unit
(--update-golden, a path or node id after `--`, --repeat-new) claims its workers from loadgate and runs
pytest itself: --repeat-new exists to run every copy, so it never reads the cache. No library on this machine
($LOADGATE_CODE, ~/.agents/testsched): plain `-n auto`, with a warning.
"""
import argparse
import ast
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import impact  # noqa: E402


def parallel(extra, workers=None, auto=False):
    """xdist flags, or none: --update-golden rewrites one file from every area, so it runs alone.
    `-n` is only for a run this script starts itself: `workers` is what loadgate granted it, `auto` leaves
    the count to xdist when there is no grant. testsched.runner adds its own `-n`, so a unit run has neither."""
    if "--update-golden" in extra:
        return []
    if importlib.util.find_spec("xdist") is None:
        print("  pytest-xdist missing (pip install pytest-xdist) -- running serially", file=sys.stderr)
        return []
    n = ["-n", str(workers) if workers else "auto"] if (workers or auto) else []
    return [*n, "--dist", "loadgroup"]


# --- loadgate and testsched (SPEC 2, 13) ----------------------------------------------------------------

def reach(environ=None, home=None):
    """The folder holding loadgate/ and testsched/: $LOADGATE_CODE, else the install junction
    ~/.agents/testsched; None when there is neither (loadgate is absent, as LOADGATE=off)."""
    environ = os.environ if environ is None else environ
    home = pathlib.Path(home) if home else pathlib.Path.home()
    for cand in (environ.get("LOADGATE_CODE"), home / ".agents" / "testsched"):
        if cand and (pathlib.Path(cand) / "loadgate" / "__init__.py").is_file():
            return pathlib.Path(cand)
    return None


def load_sched(environ=None):
    """loadgate.admit and testsched.runner as a namespace, or None when the library is not here."""
    code = reach(environ)
    if code is None:
        return None
    if str(code) not in sys.path:
        sys.path.insert(0, str(code))
    try:
        from loadgate import admit
        from testsched import runner
    except ImportError as e:    # psutil missing, a half-installed copy: a broken budget must never stop a test run
        print(f"  loadgate not usable ({e})", file=sys.stderr)
        return None
    return types.SimpleNamespace(admit=admit, runner=runner)


def kind_of(environ, committed):
    """The loadgate class of this run: TW_RUN_KIND when it names land or postland, else land for a
    --committed run (only land.ps1 and a batch pass it), else dev."""
    tag = (environ.get("TW_RUN_KIND") or "").strip().lower()
    return tag if tag in ("land", "postland") else ("land" if committed else "dev")


def would_claim(sched, kind, lg=None):
    """The claim line of a dry run: what the class could get now, claiming nothing."""
    s = sched.admit.status(kind, **(lg or {}))
    return f"  loadgate {kind}: would claim up to {s['budget']['cpu']} workers ({s['free']['cpu']} free)"


def hold(sched, kind, lg=None, serial=False):
    """(Claim or None, workers or None) for a run this script starts itself. A serial run holds 1 and passes
    no `-n`. No library, or a refused claim: (None, None), which leaves the workers to `-n auto`."""
    if sched is None:
        return None, None
    claim = sched.admit.claim(kind, cpu=1 if serial else None, browser_workers=True,
                              label=f"run_tests {kind}", **(lg or {}))
    if claim is None:
        return None, None
    workers = max(1, int(claim.granted["cpu"]))
    print(f"  loadgate {kind}: claimed {workers} worker{'' if workers == 1 else 's'}", flush=True)
    return claim, (None if serial else workers)


def run_direct(make, ids, limit, env, sched, kind, lg=None, serial=False):
    """Claim workers, run the pytest command `make(workers)` builds, release the claim: pytest's exit code."""
    claim, workers = hold(sched, kind, lg, serial)
    try:
        return run_pytest(make(workers), ids, limit, env=env)
    finally:
        if claim is not None:
            claim.release()


def all_test_files():
    return sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_*.py"))


def sched_split(picked, extra, quarantine=False, skill=None):
    """(units, pytest args) for testsched: the picked files are the cache's units (every test file when the
    pick is everything); the rest of the pick, the gating flags and `extra` go to every unit's pytest."""
    def is_file(p):    # not an option: --e2e-only-in=a.py,b.py ends in .py too
        return p.endswith(".py") and not p.startswith("-")
    units = [p for p in picked if is_file(p)] or all_test_files()
    flags = [*parallel(extra), *gate(extra, quarantine), *limit_args(skill_dir() if skill is None else skill),
             "-p", "run_tests", "--tw-empty-ok"]
    return units, [*flags, *[p for p in picked if not is_file(p)], *extra]


def write_results(path, res):
    """{unit: passed|failed} for every unit that ran: postland feeds it to testsched's cache check."""
    failed = set(res["failed"])
    out = {u: ("failed" if u in failed else "passed") for u in res["ran"]}
    pathlib.Path(path).write_text(json.dumps(out, indent=1), encoding="utf-8")


def selection(pick):
    """pytest arguments for impact.select's answer: the files and the golden areas, or nothing for all."""
    if pick["all"]:
        print(f"  whole suite: {'; '.join(pick['why'])}")
        return []
    args = list(pick["files"])
    if pick["areas"]:
        args += ["--areas", ",".join(pick["areas"])]
    return args


def gate(extra, quarantine=False):
    """--no-quarantine for a gating run, unless asked to keep quarantined tests or already given."""
    return [] if quarantine or "--no-quarantine" in extra else ["--no-quarantine"]


def e2e_args(pick, extra):
    """A gating run of 'everything' (a shared file changed) runs unit + component, and browser tests only
    in impact's files (tests/conftest.py --e2e-only-in); the after-land run covers the rest (2026-10-07).
    A path or node id after `--` (any existing file or directory, `tests` included) is a wish for that
    test, so it keeps every browser test. The golden follows the areas the changed paths own, so
    an all-pick with areas also passes --areas: only test_render.py carries area marks."""
    if not pick["all"] or wants_paths(extra):
        return []
    why = list(pick["why"])
    shown = "; ".join(why[:3]) + (f"; +{len(why) - 3} more" if len(why) > 3 else "")
    args = ["--e2e-only-in=" + ",".join(pick["files"]), f"--e2e-why=shared file: {shown}"]
    return args + (["--areas", ",".join(pick["areas"])] if pick["areas"] else [])


def names_a_path(arg):
    """True for a pytest argument that is a file or directory in the repo (not a flag, not a -k word)."""
    return not arg.startswith("-") and (ROOT / arg.split("::")[0]).exists()


def wants_paths(extra):
    """True when `extra` names a test file, directory or node id: a wish for exactly that test."""
    return any(a.endswith(".py") or "::" in a or "tests/" in a or names_a_path(a) for a in extra)


def picked_args(full, base, committed, extra=()):
    """The files and --areas the change can break, or for a run of the whole suite the browser-test limit
    that goes with it; none for --full."""
    if full:
        return []
    paths, golden = impact.changed(base, worktree=not committed)
    pick = impact.select(paths, golden=golden)
    return selection(pick) + e2e_args(pick, extra)


def skill_dir(environ=None):
    """The testing skill's scripts dir: $TESTING_SKILL when set (a skill checkout not yet installed), else the installed copy."""
    environ = os.environ if environ is None else environ
    return pathlib.Path(environ.get("TESTING_SKILL") or pathlib.Path.home() / ".agents" / "skills" / "testing" / "scripts")


def limit_args(skill, enforce=False):
    """The skill's per-layer time limits (.testing.json `limits`), loaded here and nowhere else: not in
    conftest or pytest.ini, so a mutant run or a shuffled flake run is never timed. An ordinary run
    only lists the tests over their limit; `enforce` (the 10-run) fails one whose fastest copy is over.
    The suites' wall budgets are the weekly flake job's (flake_run.py). No plugin in the skill dir: no limits."""
    if not (pathlib.Path(skill) / "pytest_limits.py").is_file():
        print(f"  no pytest_limits.py in {skill}: time limits not checked (update the testing skill)", file=sys.stderr)
        return []
    return ["-p", "pytest_limits", *(["--limits-enforce"] if enforce else [])]


def with_path(environ, *dirs):
    """environ with `dirs` in front of its PYTHONPATH."""
    path = os.pathsep.join(filter(None, [*(str(d) for d in dirs), environ.get("PYTHONPATH")]))
    return {**environ, "PYTHONPATH": path}


def command(full, base, committed, extra, quarantine=False, picked=None, skill=None, workers=None, auto=False):
    """The pytest command of a run this script starts itself (the direct path); a unit run is sched_split's."""
    picked = picked_args(full, base, committed, extra) if picked is None else picked
    limits = limit_args(skill_dir() if skill is None else skill)
    return [sys.executable, "-m", "pytest", *parallel(extra, workers, auto), *gate(extra, quarantine), *limits,
            *picked, *extra]


ARGV_LIMIT = 8000   # chars of test ids on a command line; Windows allows 32,767 for the whole line


def fit(cmd, ids, limit=ARGV_LIMIT):
    """(cmd, args file or None): when `ids` (a run of cmd's arguments) would take more than `limit` characters,
    write them one per line to a temp file and put `@<file>` in their place, which pytest reads as the arguments.
    The caller deletes the file."""
    if not ids or sum(len(i) + 1 for i in ids) <= limit:
        return cmd, None
    at = next(i for i in range(len(cmd)) if cmd[i:i + len(ids)] == list(ids))
    fd, name = tempfile.mkstemp(prefix="tw-args-", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(ids) + "\n")
    return cmd[:at] + ["@" + name] + cmd[at + len(ids):], name


def run_pytest(cmd, ids, limit, **kw):
    """Run cmd with `ids` spilled to an args file when long (see fit); the file is gone afterwards."""
    cmd, name = fit(cmd, ids, limit)
    try:
        return subprocess.run(cmd, cwd=ROOT, **kw).returncode
    finally:
        if name:
            os.remove(name)


# --- --repeat-new: which test functions did the branch add or change ---------------------------

def functions_in(source):
    """[(nodeid tail, first line, last line)] for each test function; decorators count, a class prefixes."""
    out = []

    def walk(body, prefix):
        for n in body:
            if isinstance(n, ast.ClassDef) and n.name.startswith("Test"):
                walk(n.body, prefix + [n.name])
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test"):
                first = min([n.lineno] + [d.lineno for d in n.decorator_list])
                out.append(("::".join(prefix + [n.name]), first, n.end_lineno))
    walk(ast.parse(source).body, [])
    return out


def changed_lines(diff):
    """{path: set of new-file line numbers} from `git diff -U0`; a pure deletion marks the two lines around it."""
    lines, path = {}, None
    for row in diff.splitlines():
        if row.startswith("+++ "):
            path = row[4:].removeprefix("b/") if row != "+++ /dev/null" else None
        m = re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", row)
        if m and path:
            start, count = int(m[1]), 1 if m[2] is None else int(m[2])
            lines.setdefault(path, set()).update(range(start, start + count) if count else (start, start + 1))
    return lines


def nodeids_for(lines, sources):
    """Sorted nodeids of the test functions holding a changed line; lines None = the whole file is new.
    A parametrized test is its function's id, so pytest runs every variant."""
    ids = set()
    for path, touched in lines.items():
        for tail, first, last in functions_in(sources[path]):
            if touched is None or any(first <= n <= last for n in touched):
                ids.add(f"{path}::{tail}")
    return sorted(ids)


def git(*args, cwd=ROOT):
    """A git command's output as text. git writes UTF-8; Windows' default (cp1252) cannot read every byte."""
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8", check=True).stdout


def new_test_ids(base, committed):
    """Nodeids of the test functions added or changed vs `base` (files on disk too, unless committed)."""
    spec = ["--", "tests/test_*.py"]
    fork = git("merge-base", base, "HEAD").strip()  # what main had when the branch left it
    lines = changed_lines(git("diff", "-U0", f"{fork}..HEAD" if committed else fork, *spec))
    if not committed:
        lines.update({p: None for p in git("ls-files", "--others", "--exclude-standard", *spec).split()})
    lines = {p: v for p, v in lines.items() if (ROOT / p).is_file()}
    return nodeids_for(lines, {p: (ROOT / p).read_text(encoding="utf-8") for p in lines})


def repeat_command(ids, n, extra, quarantine=False, skill=None, workers=None):
    limits = limit_args(skill_dir() if skill is None else skill, enforce=True)
    return [sys.executable, "-m", "pytest", "-p", "run_tests", "--tw-repeat", str(n),
            *parallel(extra, workers, auto=True), *gate(extra, quarantine), *limits, *ids, *extra]


# --- the pytest plugin: run every collected test N times, tally passes per function ------------

_TALLY = {}
_REPEATING = []


def pytest_addoption(parser):
    parser.addoption("--tw-repeat", type=int, default=0, help="run every collected test this many times")
    parser.addoption("--tw-empty-ok", action="store_true", default=False,
                     help="exit 0 when every test of the run was deselected (pytest's exit 5)")


def pytest_configure(config):
    _REPEATING[:] = [config.getoption("--tw-repeat") > 0]


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """A unit whose tests are all deselected (browser tests outside --e2e-only-in, another area's golden
    slice) is not a failure: testsched reads any nonzero exit as one."""
    if exitstatus == 5 and session.config.getoption("--tw-empty-ok"):
        session.exitstatus = 0


@pytest.fixture
def _tw_rep(request):
    return request.param


def pytest_generate_tests(metafunc):
    n = metafunc.config.getoption("--tw-repeat")
    if n > 0:
        metafunc.fixturenames.append("_tw_rep")
        metafunc.parametrize("_tw_rep", range(n), indirect=True, ids=[f"rep{i}" for i in range(n)])


def pytest_runtest_logreport(report):
    if _REPEATING and _REPEATING[0] and (report.when == "call" or (report.when == "setup" and not report.passed)):
        name = report.nodeid.split("[")[0]
        passed, total = _TALLY.get(name, (0, 0))
        _TALLY[name] = (passed + report.passed, total + 1)


def pytest_terminal_summary(terminalreporter):
    for name, (passed, total) in sorted(_TALLY.items()):
        terminalreporter.write_line(f"  {passed}/{total}  {name}")


def repeat_new(a, extra, lg=None):
    """The 10-run: every copy must run, so it claims its workers (class land) and never reads the cache."""
    ids = new_test_ids(a.base, a.committed)
    if not ids:
        print("  no new or changed tests -- nothing to repeat")
        return 0
    print(f"  {len(ids)} new or changed test(s), {a.repeat_new} runs each:\n    " + "\n    ".join(ids))
    sched, kind = load_sched(), kind_of(os.environ, a.committed)

    def make(workers):
        return repeat_command(ids, a.repeat_new, extra, a.with_quarantine, workers=workers)
    if a.dry_run:
        print(would_claim(sched, kind, lg) if sched else "  loadgate not found: no claim")
        print("  python -m pytest " + " ".join(make(None)[3:]))
        return 0
    env = with_path(os.environ, ROOT / "scripts", skill_dir())
    code = run_direct(make, ids, getattr(a, "argv_limit", ARGV_LIMIT), env, sched, kind, lg)
    return 0 if code == 5 else code    # 5 = every test deselected (all quarantined): nothing to prove, not a failure


def parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--full", action="store_true", help="every test, not only what the change can break")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--committed", action="store_true", help="HEAD only, not the files on disk (land.ps1)")
    ap.add_argument("--dry-run", action="store_true", help="print the claim, the cache plan and the command; run nothing")
    ap.add_argument("--repeat-new", type=int, metavar="N", help="run each test the branch added or changed N times")
    ap.add_argument("--with-quarantine", action="store_true", help="keep quarantined tests (no --no-quarantine)")
    ap.add_argument("--argv-limit", type=int, default=ARGV_LIMIT, metavar="CHARS",
                    help="more test-id characters than this go to pytest in an @args file")
    ap.add_argument("--results-json", metavar="PATH", help="write {file: passed|failed} for the units that ran")
    return ap


def run_units(a, extra, picked, kind, sched, lg):
    """The cached path: the picked files are units of testsched.runner.run, which claims the workers."""
    units, args = sched_split(picked, extra, a.with_quarantine)
    env = with_path(os.environ, ROOT / "scripts", skill_dir())
    if a.dry_run:
        hits, misses, never = sched.runner.plan(ROOT, units, args, kind, environ=env)
        print(would_claim(sched, kind, lg))
        print(f"  testsched {kind} plan: {len(hits)} hit, {len(misses)} miss, {len(never)} never of {len(units)} units")
        return 0
    res = sched.runner.run(ROOT, units, args, kind, environ=env, browser=True, lg=lg)
    print(f"  testsched {kind}: {len(res['ran'])} ran, {len(res['hits'])} cached, {len(res['failed'])} failed")
    if a.results_json:
        write_results(a.results_json, res)
    return res["exit"]


def run_alone(a, extra, picked, kind, sched, lg):
    """The path with no unit: claim the workers, run pytest on the picked files (or none: all)."""
    serial = "--update-golden" in extra
    env = with_path(os.environ, skill_dir())

    def make(workers):
        cmd = command(a.full, a.base, a.committed, extra, a.with_quarantine, picked, workers=workers, auto=True)
        print("  python -m pytest " + " ".join(cmd[3:]), flush=True)
        return cmd
    if a.dry_run:
        print(would_claim(sched, kind, lg) if sched else "  loadgate not found: no claim")
        make(None)
        return 0
    return run_direct(make, picked, a.argv_limit, env, sched, kind, lg, serial)


def main(argv=None, lg=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    ours = argv[:argv.index("--")] if "--" in argv else argv
    a = parser().parse_args(ours)
    if a.repeat_new:
        return repeat_new(a, extra, lg)
    picked = picked_args(a.full, a.base, a.committed, extra)
    sched, kind = load_sched(), kind_of(os.environ, a.committed)
    if sched is None:
        print("  loadgate not found ($LOADGATE_CODE, ~/.agents/testsched): running without a claim or the cache",
              file=sys.stderr)
    if sched is None or "--update-golden" in extra or wants_paths(extra):
        return run_alone(a, extra, picked, kind, sched, lg)
    return run_units(a, extra, picked, kind, sched, lg)


if __name__ == "__main__":
    sys.exit(main())
