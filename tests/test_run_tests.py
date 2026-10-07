"""scripts/run_tests.py's 10-run gate for new tests and the gating flag (2026-10-05).

The diff -> test function mapping and the nodeids are pure and tested on text. The clone mechanism
runs a real pytest in a temp dir on a three-line test file: no repo suite, about a second.
"""
import os
import pathlib
import subprocess
import sys

import pytest

ROOT =pathlib.Path(__file__).resolve().parents[1]
# The throwaway pytest needs none of the installed plugins (xdist, the time limits, ...): each one's
# import is start-up time the test is not about. `-p run_tests` is named, so it loads either way.
BARE_PYTEST = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
sys.path.insert(0, str(ROOT / "scripts"))
import run_tests as runner  # noqa: E402

SOURCE = '''import pytest

X = 1


def helper():
    return 2


@pytest.mark.parametrize("n", [1, 2])
def test_param(n):
    assert n


def test_plain():
    inner = 1
    assert inner


class TestGroup:
    def test_method(self):
        assert True

    def not_a_test(self):
        pass
'''
# 1-based: helper 6-7, test_param 10-12 (decorator on 10), test_plain 15-17, TestGroup.test_method 21-22


def ids(touched, path="tests/test_x.py"):
    return runner.nodeids_for({path: touched}, {path: SOURCE})


def test_a_function_spans_its_decorators_and_its_body():
    spans = {tail: (a, b) for tail, a, b in runner.functions_in(SOURCE)}
    assert spans == {"test_param": (10, 12), "test_plain": (15, 17), "TestGroup::test_method": (21, 22)}


def test_a_changed_body_line_maps_to_its_function():
    assert ids({16}) == ["tests/test_x.py::test_plain"]
    assert ids({22}) == ["tests/test_x.py::TestGroup::test_method"]


def test_a_changed_decorator_counts_and_a_parametrized_test_is_one_whole_id():
    assert ids({10}) == ["tests/test_x.py::test_param"]  # no [n-1]: pytest runs every variant


def test_a_changed_helper_or_constant_is_no_test():
    assert ids({3, 6, 7, 23}) == []


def test_two_lines_in_one_function_are_one_id_and_ids_sort():
    assert ids({11, 12, 21}) == ["tests/test_x.py::TestGroup::test_method", "tests/test_x.py::test_param"]


def test_a_new_file_is_every_test_in_it():
    assert len(ids(None)) == 3


DIFF = """diff --git a/tests/test_a.py b/tests/test_a.py
--- a/tests/test_a.py
+++ b/tests/test_a.py
@@ -4 +4,2 @@ def f():
-old
+new
+newer
@@ -20,0 +23,3 @@ def g():
+a
+b
+c
@@ -30,2 +33,0 @@ def h():
-gone
-gone
diff --git a/tests/test_b.py b/tests/test_b.py
--- a/tests/test_b.py
+++ b/tests/test_b.py
@@ -1 +1 @@
-x
+y
diff --git a/tests/test_gone.py b/tests/test_gone.py
--- a/tests/test_gone.py
+++ /dev/null
@@ -1,2 +0,0 @@
-x
-y
"""


def test_diff_hunks_become_new_file_line_numbers():
    lines = runner.changed_lines(DIFF)
    assert lines["tests/test_a.py"] == {4, 5, 23, 24, 25, 33, 34}  # a deletion marks the lines around it
    assert lines["tests/test_b.py"] == {1}
    assert "tests/test_gone.py" not in lines and "/dev/null" not in lines


@pytest.mark.integration      # a real git or pytest subprocess
def test_a_diff_with_curly_quotes_is_read_as_utf8(tmp_path):
    """2026-10-06: a test whose comment held ” (UTF-8 e2 80 9d) crashed the 10-run gate: Windows decoded
    git's output as cp1252, where 0x9d is undefined, and the reader thread returned nothing."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "test_q.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)    # the diff is the file against the index
    (tmp_path / "test_q.py").write_text("x = 1  # “the call”\n", encoding="utf-8")
    assert "+x = 1  # “the call”" in runner.git("diff", "-U0", cwd=tmp_path)


def test_a_branch_with_no_new_tests_says_so(monkeypatch, capsys):
    monkeypatch.setattr(runner, "new_test_ids", lambda base, committed: [])
    args = type("A", (), dict(base="origin/main", committed=False, repeat_new=10, dry_run=False,
                              with_quarantine=False))()
    assert runner.repeat_new(args, []) == 0
    assert "no new or changed tests" in capsys.readouterr().out


def test_dry_run_prints_the_ids_and_the_command_and_runs_nothing(monkeypatch, capsys):
    monkeypatch.setattr(runner, "new_test_ids", lambda base, committed: ["tests/test_x.py::test_a"])
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(AssertionError("ran")))
    args = type("A", (), dict(base="origin/main", committed=False, repeat_new=10, dry_run=True,
                              with_quarantine=False))()
    assert runner.repeat_new(args, []) == 0
    out = capsys.readouterr().out
    assert "tests/test_x.py::test_a" in out and "--tw-repeat 10" in out


def test_the_repeat_command_loads_the_plugin_and_names_the_ids():
    cmd = runner.repeat_command(["tests/test_x.py::test_a"], 10, ["-x"])
    assert cmd[cmd.index("-p") + 1] == "run_tests"
    assert cmd[cmd.index("--tw-repeat") + 1] == "10"
    assert "tests/test_x.py::test_a" in cmd and cmd[-1] == "-x"


def args(**kw):
    return type("A", (), dict(base="origin/main", committed=False, repeat_new=10, dry_run=False,
                              with_quarantine=False, **kw))()


def run_returning(monkeypatch, code):
    monkeypatch.setattr(runner, "new_test_ids", lambda base, committed: ["tests/test_x.py::test_a"])
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, code))


def test_every_test_deselected_is_not_a_failed_gate(monkeypatch):
    """Exit 5: all the changed tests are quarantined, so there is nothing to repeat."""
    run_returning(monkeypatch, 5)
    assert runner.repeat_new(args(), []) == 0


def test_a_failed_repeat_still_fails_the_gate(monkeypatch):
    run_returning(monkeypatch, 1)
    assert runner.repeat_new(args(), []) == 1


def test_a_repeated_test_is_grouped_by_its_repetition_not_its_file():
    import types
    import conftest
    rep3 = types.SimpleNamespace(callspec=types.SimpleNamespace(params={"_tw_rep": 3, "n": 1}))
    rep0 = types.SimpleNamespace(callspec=types.SimpleNamespace(params={"_tw_rep": 0}))
    assert conftest.rep_of(rep3) == 3 and conftest.rep_of(rep0) == 0
    assert conftest.rep_of(types.SimpleNamespace()) is None
    assert conftest.rep_of(types.SimpleNamespace(callspec=types.SimpleNamespace(params={"n": 1}))) is None


def test_a_short_list_of_ids_stays_on_the_command_line():
    cmd = ["python", "-m", "pytest", "-n", "2", "a::t1", "a::t2", "-x"]
    assert runner.fit(cmd, ["a::t1", "a::t2"], limit=8000) == (cmd, None)


def test_a_long_list_of_ids_goes_to_an_args_file_and_the_file_is_deleted(monkeypatch):
    ids = [f"tests/test_x.py::test_{i:04d}" for i in range(500)]
    cmd = ["python", "-m", "pytest", "-n", "2", *ids, "-x"]
    short, name = runner.fit(cmd, ids, limit=8000)
    assert short == ["python", "-m", "pytest", "-n", "2", "@" + name, "-x"]
    assert pathlib.Path(name).read_text(encoding="utf-8").splitlines() == ids
    pathlib.Path(name).unlink()
    seen = {}

    def fake(cmd, **kw):
        arg = next(a for a in cmd if a.startswith("@"))
        seen["file"] = pathlib.Path(arg[1:])
        seen["exists"] = seen["file"].exists()
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(subprocess, "run", fake)
    assert runner.run_pytest(cmd, ids, 8000) == 0
    assert seen["exists"] and not seen["file"].exists()


@pytest.mark.integration      # a real git or pytest subprocess
def test_pytest_reads_an_args_file(tmp_path):
    (tmp_path / "test_a.py").write_text("def test_one():\n    pass\n\ndef test_two():\n    pass\n", encoding="utf-8")
    (tmp_path / "ids.txt").write_text("test_a.py::test_two\n", encoding="utf-8")
    done = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "@ids.txt", "-q"],
                          cwd=tmp_path, env=BARE_PYTEST, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and "1 passed" in done.stdout, done.stdout + done.stderr


# ---- loadgate and testsched: the claim, the cache, the library (2026-10-07) ----

def ns(**kw):
    import types
    return types.SimpleNamespace(**kw)


def fake_machine(cpu=4, exit_code=0, failed=()):
    """Stand-ins for loadgate.admit and testsched.runner that record every call."""
    seen = ns(claims=[], runs=[], held=[])

    def claim(cls, **kw):
        held = ns(granted={"cpu": cpu}, released=False)
        held.release = lambda: setattr(held, "released", True)
        seen.claims.append((cls, kw))
        seen.held.append(held)
        return held

    def run(repo, units, args=(), kind="dev", **kw):
        seen.runs.append(ns(units=list(units), args=list(args), kind=kind, kw=kw))
        return {"kind": kind, "hits": [], "misses": list(units), "never": [], "ran": list(units),
                "failed": [u for u in units if u in failed], "workers": cpu, "exit": exit_code}

    def status(cls=None, **kw):
        return {"budget": {"cpu": 8}, "free": {"cpu": 6.0}}

    def plan(repo, units, args=(), kind="dev", **kw):
        return [], list(units), []
    return ns(seen=seen, admit=ns(claim=claim, status=status), runner=ns(run=run, plan=plan))


@pytest.fixture(autouse=True)
def machine(tmp_path, monkeypatch):
    """Each test gets its own loadgate home and a fake loadgate/testsched; `machine.real()` swaps the real
    library back in (it still keeps its state in the temp home)."""
    monkeypatch.setenv("LOADGATE_HOME", str(tmp_path / "lg"))
    for name in ("LOADGATE", "TESTSCHED", "TW_SLOTS", "TW_RUN_KIND"):
        monkeypatch.delenv(name, raising=False)
    real, fake = runner.load_sched, fake_machine()
    monkeypatch.setattr(runner, "load_sched", lambda environ=None: fake)
    return ns(fake=fake, real=lambda: monkeypatch.setattr(runner, "load_sched", real))


def idle_lg():
    """loadgate's test doubles: the PC from SPEC 3 with nothing else running."""
    import datetime

    class Idle:
        def procs(self):
            return []

        def cpu_busy(self, window):
            return 0.0

        def memory(self):
            return {"ram_free_gb": 30.0, "commit_free_gb": 40.0}

        def gpu(self):
            return None

        def comfy(self):
            return False

        def sessions(self):
            return {}

        sleep = staticmethod(lambda s: None)
    cap = {"cores": 14, "threads": 20, "ram_gb": 32.0, "commit_gb": 48.0, "gpu": None}
    return {"cap": cap, "readers": Idle(), "today": datetime.date(2026, 10, 7)}


def files_on_disk():
    return sorted("tests/" + n for n in os.listdir(ROOT / "tests") if n.startswith("test_") and n.endswith(".py"))


def pick_files(monkeypatch, files, areas=()):
    monkeypatch.setattr(runner.impact, "changed", lambda base, worktree: ([], []))
    monkeypatch.setattr(runner.impact, "select", lambda paths, golden: {
        "all": False, "why": [], "files": list(files), "areas": list(areas)})


def record_pytest(monkeypatch, code=0):
    seen = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: seen.append(cmd) or subprocess.CompletedProcess(cmd, code))
    return seen


def test_the_library_is_found_by_env_then_the_junction_and_never_a_checkout_path(tmp_path):
    def lib(*parts):
        d = tmp_path.joinpath(*parts)
        (d / "loadgate").mkdir(parents=True)
        (d / "loadgate" / "__init__.py").write_text("", encoding="utf-8")
        return d
    from_env = lib("env")
    assert runner.reach({"LOADGATE_CODE": str(from_env)}, home=tmp_path) == from_env
    assert runner.reach({}, home=tmp_path) is None
    lib("Github", "agent-config", ".claude", "worktrees", "testsched", "testsched")
    assert runner.reach({}, home=tmp_path) is None
    junction = lib(".agents", "testsched")
    assert runner.reach({}, home=tmp_path) == junction
    assert runner.reach({"LOADGATE_CODE": str(tmp_path / "nope")}, home=tmp_path) == junction


@pytest.mark.parametrize("env,committed,kind", [
    ({}, False, "dev"), ({}, True, "land"), ({"TW_RUN_KIND": "land"}, False, "land"),
    ({"TW_RUN_KIND": "postland"}, True, "postland"), ({"TW_RUN_KIND": "mutate"}, False, "dev")])
def test_the_class_comes_from_the_run_kind_else_the_committed_flag(env, committed, kind):
    assert runner.kind_of(env, committed) == kind


def test_a_pick_becomes_units_and_pytest_args(tmp_path):
    picked = ["tests/test_a.py", "tests/test_b.py", "--areas", "ranks"]
    units, args = runner.sched_split(picked, ["-x"], quarantine=False, skill=tmp_path)
    assert units == ["tests/test_a.py", "tests/test_b.py"]
    assert args[-3:] == ["--areas", "ranks", "-x"]
    assert "--no-quarantine" in args and "--tw-empty-ok" in args
    assert args[args.index("-p") + 1] == "run_tests"
    assert "-n" not in args, "the workers are loadgate's to grant"
    assert [a for a in args if a.endswith(".py")] == []


def test_a_run_of_everything_with_the_browser_list_keeps_the_list_as_an_arg_not_a_unit(tmp_path):
    """--e2e-only-in=a.py,b.py ends in .py but is one pytest option, not a test file (found by land.ps1 -DryRun)."""
    picked = ["--e2e-only-in=tests/test_a.py,tests/test_b.py", "--e2e-why=shared file: design/build.py", "--areas", "ranks"]
    units, args = runner.sched_split(picked, [], quarantine=False, skill=tmp_path)
    assert units == files_on_disk()
    assert args[-4:] == picked


def test_a_run_of_everything_has_every_test_file_as_a_unit(tmp_path):
    units, _ = runner.sched_split([], [], quarantine=False, skill=tmp_path)
    assert units == files_on_disk() and len(units) > 100


@pytest.mark.integration      # a real pytest subprocess
def test_a_run_that_deselects_every_test_exits_zero_with_the_flag_and_five_without(tmp_path):
    (tmp_path / "test_s.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    env = {**BARE_PYTEST, "PYTHONPATH": str(ROOT / "scripts")}

    def code(*flags):
        return subprocess.run([sys.executable, "-m", "pytest", "-p", "run_tests", "-p", "no:cacheprovider",
                               "-k", "nomatch", "-q", *flags], cwd=tmp_path, env=env, capture_output=True,
                              text=True, timeout=120).returncode
    assert code() == 5
    assert code("--tw-empty-ok") == 0


@pytest.mark.integration      # a real pytest subprocess
def test_without_repeat_the_plugin_prints_no_tally(tmp_path):
    (tmp_path / "test_s.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    env = {**BARE_PYTEST, "PYTHONPATH": str(ROOT / "scripts")}
    done = subprocess.run([sys.executable, "-m", "pytest", "-p", "run_tests", "-p", "no:cacheprovider", "-q"],
                          cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)
    assert done.returncode == 0 and "1 passed" in done.stdout
    assert "1/1" not in done.stdout


def _library():
    """$LOADGATE_CODE if set, else the install junction ~/.agents/testsched if it exists, else None."""
    env = os.environ.get("LOADGATE_CODE")
    if env:
        return pathlib.Path(env)
    junction = pathlib.Path.home() / ".agents" / "testsched"
    return junction if junction.exists() else None


LIBRARY = _library()


@pytest.fixture
def real_library(monkeypatch):
    """Points LOADGATE_CODE at the installed testsched, or skips the one test that needs the real library."""
    if LIBRARY is None or not (LIBRARY / "loadgate" / "__init__.py").is_file():
        pytest.skip(f"the loadgate library is not at $LOADGATE_CODE or ~/.agents/testsched ({LIBRARY})")
    monkeypatch.setenv("LOADGATE_CODE", str(LIBRARY))


def test_dry_run_prints_a_claim_line_and_a_cache_plan_line(machine, real_library, capsys):
    machine.real()
    assert runner.main(["--full", "--dry-run"], lg=idle_lg()) == 0
    out = capsys.readouterr().out.splitlines()
    n = len(files_on_disk())
    claim = [ln for ln in out if ln.startswith("  loadgate dev:")]
    plan = [ln for ln in out if ln.startswith("  testsched dev plan:")]
    assert len(claim) == 1 and "would claim" in claim[0] and "workers" in claim[0]
    assert plan == [f"  testsched dev plan: 0 hit, {n} miss, 0 never of {n} units"]


def test_a_land_run_goes_to_testsched_with_the_land_class_the_files_and_the_args(machine, monkeypatch):
    pick_files(monkeypatch, ["tests/test_a.py"], ["ranks"])
    assert runner.main(["--committed", "--base", "origin/main"]) == 0
    (run,) = machine.fake.seen.runs
    assert run.kind == "land" and run.units == ["tests/test_a.py"]
    assert run.args[-2:] == ["--areas", "ranks"] and "--no-quarantine" in run.args
    assert run.kw["browser"] is True
    assert str(ROOT / "scripts") in run.kw["environ"]["PYTHONPATH"]


def test_a_failed_unit_makes_the_run_exit_one_and_the_summary_counts_it(monkeypatch, capsys):
    fake = fake_machine(exit_code=1, failed=["tests/test_a.py"])
    monkeypatch.setattr(runner, "load_sched", lambda environ=None: fake)
    pick_files(monkeypatch, ["tests/test_a.py", "tests/test_b.py"])
    assert runner.main([]) == 1
    assert "  testsched dev: 2 ran, 0 cached, 1 failed" in capsys.readouterr().out.splitlines()


def test_results_json_maps_each_unit_that_ran_to_its_outcome(monkeypatch, tmp_path):
    import json
    fake = fake_machine(exit_code=1, failed=["tests/test_b.py"])
    monkeypatch.setattr(runner, "load_sched", lambda environ=None: fake)
    pick_files(monkeypatch, ["tests/test_a.py", "tests/test_b.py"])
    runner.main(["--results-json", str(tmp_path / "r.json")])
    assert json.loads((tmp_path / "r.json").read_text(encoding="utf-8")) == {
        "tests/test_a.py": "passed", "tests/test_b.py": "failed"}


def test_without_the_library_it_runs_plain_pytest_on_auto_workers_and_says_so(monkeypatch, capsys):
    monkeypatch.setattr(runner, "load_sched", lambda environ=None: None)
    seen = record_pytest(monkeypatch)
    assert runner.main(["--full"]) == 0
    assert seen[0][seen[0].index("-n") + 1] == "auto"
    assert "loadgate not found" in capsys.readouterr().err


def test_update_golden_runs_alone_on_one_claimed_worker(machine, monkeypatch):
    seen = record_pytest(monkeypatch)
    assert runner.main(["--full", "--", "--update-golden"]) == 0
    ((cls, kw),) = machine.fake.seen.claims
    assert cls == "dev" and kw["cpu"] == 1
    assert "-n" not in seen[0] and "--update-golden" in seen[0]
    assert machine.fake.seen.held[0].released and machine.fake.seen.runs == []


def test_a_test_path_after_the_double_dash_runs_directly_on_the_claimed_workers(machine, monkeypatch):
    seen = record_pytest(monkeypatch)
    assert runner.main(["--full", "--", "tests/test_ranks.py"]) == 0
    assert seen[0][seen[0].index("-n") + 1] == "4"
    assert machine.fake.seen.held[0].released and machine.fake.seen.runs == []


def test_the_ten_run_claims_land_workers_and_passes_them_as_n(machine, monkeypatch):
    monkeypatch.setattr(runner, "new_test_ids", lambda base, committed: ["tests/test_x.py::test_a"])
    seen = record_pytest(monkeypatch)
    a = type("A", (), dict(base="origin/main", committed=True, repeat_new=10, dry_run=False, with_quarantine=False))()
    assert runner.repeat_new(a, []) == 0
    ((cls, kw),) = machine.fake.seen.claims
    assert cls == "land"
    assert seen[0][seen[0].index("-n") + 1] == "4"
    assert machine.fake.seen.held[0].released
