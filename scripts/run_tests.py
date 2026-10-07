"""Run the tests your change can break, in parallel (2026-10-05). land.ps1 runs its tests through here.

    python scripts/run_tests.py               # what the edits on disk can break, uncommitted ones included
    python scripts/run_tests.py --full        # everything
    python scripts/run_tests.py -- -x -k dossier   # anything after -- goes to pytest as is
    python scripts/run_tests.py --repeat-new 10    # every test the branch added or changed, 10 times

A Preview edit runs Preview's tests, Preview's golden slice and the core every view shares (the
build, lint, syntax, budgets), about 15 s; a bare `pytest` runs all of it, one test at a time.
scripts/impact.py picks the files: a path no area claims, shared CSS or shared test setup still
runs everything. Exits with pytest's code.

Gating runs (the default and --full, which land.ps1 calls) pass --no-quarantine: a test marked
quarantine drops out of the gate until fixed (--with-quarantine keeps it). --repeat-new N is the
10-run gate for new tests (tests/README.md "Proving a test"); this module doubles as its pytest
plugin (`-p run_tests`), which parametrizes each test N times, so xdist spreads the runs.

The testing skill's time limits (`-p pytest_limits`, `.testing.json` `limits`: a limit per layer and
a shrink-only backlog) load here and nowhere else, so a mutant run or a shuffled flake run is never
timed. An ordinary run lists the tests over their limit; only --repeat-new passes --limits-enforce,
failing a new or changed test whose fastest copy is over. The skill dir is $TESTING_SKILL if set,
else the installed copy (~/.agents/skills/testing/scripts).

Every run claims its xdist workers from a machine-wide budget first (scripts/worker_slots.py): the
budget is what `-n auto` gives here, a run gets min(wanted, free) and at least 2, and passes
`-n <claimed>`. One line says what it got and who holds the rest. TW_SLOTS=off bypasses it.
"""
import argparse
import ast
import importlib.util
import os
import pathlib
import re
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import impact  # noqa: E402


def parallel(extra, workers=None):
    """xdist flags, or none: --update-golden rewrites one file from every area, so it runs alone.
    `workers` is what claim_workers got from the shared budget; None leaves it to xdist's auto."""
    if "--update-golden" in extra:
        return []
    if importlib.util.find_spec("xdist") is None:
        print("  pytest-xdist missing (pip install pytest-xdist) -- running serially", file=sys.stderr)
        return []
    return ["-n", str(workers) if workers else "auto", "--dist", "loadgroup"]


def slots_module():
    """scripts/worker_slots.py (not test_*.py: the land gate would read that name as a test and freeze it)."""
    import worker_slots
    return worker_slots


def claim_workers(extra, dry_run=False):
    """(workers to pass as -n or None, the Claim or None): the run's share of the machine-wide worker
    budget (scripts/worker_slots.py, one claim file per run in the git common dir). A serial run holds 1,
    a parallel one wants what -n auto would give. TW_SLOTS=off, or no way to claim, leaves it to auto.
    A dry run only looks. The claim is released at exit; callers also release it in a finally."""
    try:
        s = slots_module()
        serial = "--update-golden" in extra or importlib.util.find_spec("xdist") is None
        claim = s.acquire(ROOT, 1 if serial else s.budget(), write=not dry_run)
    except Exception as e:    # a broken budget must never stop a test run
        print(f"  test slots: not used ({type(e).__name__}: {e})", file=sys.stderr)
        return None, None
    if claim is None:
        return None, None
    print(claim.line(), flush=True)
    return (None if serial else claim.got), claim


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


def picked_args(full, base, committed):
    """The files and --areas the change can break; none for --full or a run of the whole suite."""
    if full:
        return []
    paths, golden = impact.changed(base, worktree=not committed)
    return selection(impact.select(paths, golden=golden))


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


def command(full, base, committed, extra, quarantine=False, picked=None, skill=None, workers=None):
    picked = picked_args(full, base, committed) if picked is None else picked
    limits = limit_args(skill_dir() if skill is None else skill)
    return [sys.executable, "-m", "pytest", *parallel(extra, workers), *gate(extra, quarantine), *limits, *picked, *extra]


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
    return [sys.executable, "-m", "pytest", "-p", "run_tests", "--tw-repeat", str(n), *parallel(extra, workers),
            *gate(extra, quarantine), *limits, *ids, *extra]


# --- the pytest plugin: run every collected test N times, tally passes per function ------------

_TALLY = {}


def pytest_addoption(parser):
    parser.addoption("--tw-repeat", type=int, default=0, help="run every collected test this many times")


@pytest.fixture
def _tw_rep(request):
    return request.param


def pytest_generate_tests(metafunc):
    n = metafunc.config.getoption("--tw-repeat")
    if n > 0:
        metafunc.fixturenames.append("_tw_rep")
        metafunc.parametrize("_tw_rep", range(n), indirect=True, ids=[f"rep{i}" for i in range(n)])


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and not report.passed):
        name = report.nodeid.split("[")[0]
        passed, total = _TALLY.get(name, (0, 0))
        _TALLY[name] = (passed + report.passed, total + 1)


def pytest_terminal_summary(terminalreporter):
    for name, (passed, total) in sorted(_TALLY.items()):
        terminalreporter.write_line(f"  {passed}/{total}  {name}")


def repeat_new(a, extra):
    ids = new_test_ids(a.base, a.committed)
    if not ids:
        print("  no new or changed tests -- nothing to repeat")
        return 0
    print(f"  {len(ids)} new or changed test(s), {a.repeat_new} runs each:\n    " + "\n    ".join(ids))
    workers, claim = claim_workers(extra, a.dry_run)
    try:
        cmd = repeat_command(ids, a.repeat_new, extra, a.with_quarantine, workers=workers)
        if a.dry_run:
            print("  python -m pytest " + " ".join(cmd[3:]))
            return 0
        env = with_path(os.environ, ROOT / "scripts", skill_dir())
        code = run_pytest(cmd, ids, getattr(a, "argv_limit", ARGV_LIMIT), env=env)
        return 0 if code == 5 else code    # 5 = every test deselected (all quarantined): nothing to prove, not a failure
    finally:
        slots_module().release(claim)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    extra = argv[argv.index("--") + 1:] if "--" in argv else []
    ours = argv[:argv.index("--")] if "--" in argv else argv
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--full", action="store_true", help="every test, not only what the change can break")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--committed", action="store_true", help="HEAD only, not the files on disk (land.ps1)")
    ap.add_argument("--dry-run", action="store_true", help="print the pytest command, run nothing")
    ap.add_argument("--repeat-new", type=int, metavar="N", help="run each test the branch added or changed N times")
    ap.add_argument("--with-quarantine", action="store_true", help="keep quarantined tests (no --no-quarantine)")
    ap.add_argument("--argv-limit", type=int, default=ARGV_LIMIT, metavar="CHARS",
                    help="more test-id characters than this go to pytest in an @args file")
    a = ap.parse_args(ours)
    if a.repeat_new:
        return repeat_new(a, extra)
    picked = picked_args(a.full, a.base, a.committed)
    workers, claim = claim_workers(extra, a.dry_run)
    try:
        cmd = command(a.full, a.base, a.committed, extra, a.with_quarantine, picked, workers=workers)
        print("  python -m pytest " + " ".join(cmd[3:]), flush=True)
        if a.dry_run:
            return 0
        return run_pytest(cmd, picked, a.argv_limit, env=with_path(os.environ, skill_dir()))
    finally:
        slots_module().release(claim)


if __name__ == "__main__":
    sys.exit(main())
