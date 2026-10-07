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


# ---- gating ----

def test_a_land_run_passes_no_quarantine(monkeypatch):
    monkeypatch.setattr(runner.impact, "changed", lambda base, worktree: ([], []))
    monkeypatch.setattr(runner.impact, "select", lambda paths, golden: {"all": True, "why": [], "files": [], "areas": []})
    assert "--no-quarantine" in runner.command(False, "origin/main", True, [])
    assert "--no-quarantine" in runner.command(True, "origin/main", True, [])


def test_the_gate_flag_is_not_doubled_and_can_be_kept_off():
    assert runner.gate(["--no-quarantine"]) == []
    assert runner.gate([], quarantine=True) == []
    assert runner.gate([]) == ["--no-quarantine"]
    assert "--no-quarantine" in runner.repeat_command(["tests/test_x.py::test_a"], 3, [])


# ---- the clone mechanism, in a real pytest ----

def run_plugin(tmp_path, body, n):
    (tmp_path / "test_sample.py").write_text(body, encoding="utf-8")
    env = {**BARE_PYTEST, "PYTHONPATH": str(ROOT / "scripts")}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "run_tests", "-p", "no:cacheprovider", "--tw-repeat", str(n),
         "test_sample.py::test_a", "-q"], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120)


@pytest.mark.integration      # a real git or pytest subprocess
def test_the_plugin_runs_a_test_n_times_and_tallies_passes(tmp_path):
    done = run_plugin(tmp_path, "def test_a():\n    assert True\n\ndef test_b():\n    assert False\n", 4)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "4 passed" in done.stdout and "4/4  test_sample.py::test_a" in done.stdout


@pytest.mark.integration      # a real git or pytest subprocess
def test_one_failure_among_the_runs_fails_the_gate(tmp_path):
    counter = "import pathlib\n\ndef test_a():\n    p = pathlib.Path('n'); n = int(p.read_text() or 0) if p.exists() else 0\n" \
              "    p.write_text(str(n + 1))\n    assert n != 2\n"
    done = run_plugin(tmp_path, counter, 5)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "4/5  test_sample.py::test_a" in done.stdout


@pytest.mark.integration      # a real git or pytest subprocess
def test_a_parametrized_test_runs_every_variant_n_times(tmp_path):
    body = "import pytest\n\n@pytest.mark.parametrize('v', [1, 2, 3])\ndef test_a(v):\n    assert v\n"
    done = run_plugin(tmp_path, body, 2)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "6/6  test_sample.py::test_a" in done.stdout


# ---- the testing skill's time limits (2026-10-06) ----

def skill_with_plugin(tmp_path):
    (tmp_path / "pytest_limits.py").write_text("", encoding="utf-8")
    return tmp_path


def picked_everything(monkeypatch):
    monkeypatch.setattr(runner.impact, "changed", lambda base, worktree: ([], []))
    monkeypatch.setattr(runner.impact, "select", lambda paths, golden: {"all": True, "why": [], "files": [], "areas": []})


def test_the_skill_dir_is_testing_skill_else_the_installed_copy(tmp_path):
    assert runner.skill_dir({"TESTING_SKILL": str(tmp_path)}) == tmp_path
    assert runner.skill_dir({}) == pathlib.Path.home() / ".agents" / "skills" / "testing" / "scripts"


def test_the_limits_plugin_loads_only_when_the_skill_has_it(tmp_path):
    assert runner.limit_args(tmp_path) == []
    assert runner.limit_args(skill_with_plugin(tmp_path)) == ["-p", "pytest_limits"]
    assert runner.limit_args(skill_with_plugin(tmp_path), enforce=True) == ["-p", "pytest_limits", "--limits-enforce"]


def test_no_run_passes_the_retired_suite_flag(monkeypatch, tmp_path):
    """The suite budgets are wall times the weekly flake job measures (flake_run.py), not a land flag."""
    skill = skill_with_plugin(tmp_path)
    picked_everything(monkeypatch)
    runs = [runner.command(True, "origin/main", True, [], skill=skill),
            runner.command(False, "origin/main", True, [], picked=["tests/test_ranks.py"], skill=skill),
            runner.repeat_command(["tests/test_x.py::test_a"], 10, [], skill=skill)]
    assert [r for r in runs if "--limits-no-suite" in r] == []


def test_the_repeat_run_enforces_the_limits(tmp_path):
    """Only the land's 10-run of new and changed tests fails on time: on the fastest of its copies."""
    cmd = runner.repeat_command(["tests/test_x.py::test_a"], 10, [], skill=skill_with_plugin(tmp_path))
    assert "pytest_limits" in cmd and "--limits-enforce" in cmd


def test_an_ordinary_run_only_reports_the_limits(monkeypatch, tmp_path):
    picked_everything(monkeypatch)
    whole = runner.command(True, "origin/main", True, [], skill=skill_with_plugin(tmp_path))
    assert "pytest_limits" in whole and "--limits-enforce" not in whole


def test_the_skill_dir_goes_on_pythonpath_ahead_of_the_existing_path(tmp_path):
    env = runner.with_path({"PYTHONPATH": "elsewhere", "X": "1"}, tmp_path, "scripts")
    assert env["PYTHONPATH"].split(os.pathsep) == [str(tmp_path), "scripts", "elsewhere"]
    assert env["X"] == "1"
    assert runner.with_path({}, tmp_path)["PYTHONPATH"] == str(tmp_path)


def test_the_limits_plugin_is_in_no_pytest_config_so_mutation_and_flake_runs_never_fail_on_time():
    """Only scripts/run_tests.py loads it (-p pytest_limits): a mutant or a shuffled run is not timed."""
    assert "pytest_limits" not in (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "pytest_limits" not in (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
