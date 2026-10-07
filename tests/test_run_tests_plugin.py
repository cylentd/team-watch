"""scripts/run_tests.py's gating flag, its repeat plugin and the testing skill's time limits (2026-10-05/06),
split out of tests/test_run_tests.py to stay under 500 lines; plus the land queue's loadgate-off path (2026-10-07).

None of these calls loadgate: each builds a command or runs a throwaway pytest in a temp dir.
"""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
# The throwaway pytest needs none of the installed plugins (xdist, the time limits, ...): each one's
# import is start-up time the test is not about. `-p run_tests` is named, so it loads either way.
BARE_PYTEST = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
sys.path.insert(0, str(ROOT / "scripts"))
import run_tests as runner  # noqa: E402


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


# ---- the land queue without loadgate (2026-10-07, SPEC invariant 6) ----

QUEUE_CHECK = (". '{queue}'; $t = Enter-LandQueue -Repo '{repo}' -Label 'probe' -TimeoutMinutes 1; "
               "Write-Output \"TICKET $t\"; Write-Output \"HELD $(Test-Path $t)\"; "
               "Exit-LandQueue $t; Write-Output \"GONE $(-not (Test-Path $t))\"")


@pytest.mark.integration      # a real powershell and git subprocess
@pytest.mark.parametrize("switch", ["off", "absent"])
def test_the_land_queue_falls_back_to_a_git_dir_ticket_when_loadgate_is_off_or_absent(tmp_path, switch):
    """LOADGATE=off, or no ~/.agents/testsched: the old queue, a ticket file in <git dir>/land-queue."""
    ps = shutil.which("powershell")
    if ps is None:
        pytest.skip("the land queue is a PowerShell script and powershell is not on PATH")
    repo, empty_home = tmp_path / "repo", tmp_path / "home"
    repo.mkdir()
    empty_home.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True, timeout=60)
    env = {**os.environ, "LOADGATE_HOME": str(tmp_path / "lg"), "LOADGATE_CODE": ""}
    if switch == "off":
        stub = tmp_path / "code"       # a ts.py is present, so only LOADGATE=off can pick the old queue
        stub.mkdir()
        (stub / "ts.py").write_text("", encoding="utf-8")
        env["LOADGATE_CODE"] = str(stub)
        env["LOADGATE"] = "off"
    else:
        env.pop("LOADGATE", None)
        env["USERPROFILE"] = env["HOME"] = str(empty_home)
    script = QUEUE_CHECK.format(queue=ROOT / "scripts" / "land-queue.ps1", repo=repo)
    done = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-Command", script], env=env,
                          capture_output=True, text=True, timeout=120)
    out = done.stdout.splitlines()
    assert done.returncode == 0, done.stdout + done.stderr
    ticket = next(ln for ln in out if ln.startswith("TICKET ")).removeprefix("TICKET ")
    assert pathlib.Path(ticket).parent == repo / ".git" / "land-queue" and ticket.endswith(".ticket")
    assert "HELD True" in out and "GONE True" in out
