"""The test history (scripts/testlog.py, tests/runlog.py): what counts as a full run, what counts as
flaky, and that a land's phases are recorded as numbers."""
import importlib.util
import json
import subprocess
import sys

import pytest

from runlog import RunLog, testlog


def run(sha, files, failed=(), n_files=None):
    return {"at": "2026-10-05T00:00:00+00:00", "kind": "dev", "sha": sha, "wall": 1.0,
            "n_files": n_files or len(files), "layers": {"python": [1, 1.0]},
            "files": {f: [1, 1.0, "python"] for f in files}, "failed": list(failed)}


@pytest.fixture
def history(tmp_path, monkeypatch):
    monkeypatch.setenv("TW_TEST_HISTORY", str(tmp_path))
    return tmp_path


def test_a_run_of_one_area_is_not_full():
    runs = [run("a", [f"test_{i}.py" for i in range(80)]), run("a", ["test_1.py"]),
            run("b", [f"test_{i}.py" for i in range(75)])]
    assert [r["n_files"] for r in testlog.full_runs(runs)] == [80, 75]


def test_flaky_is_a_fail_and_a_pass_on_one_commit():
    t = "tests/test_x.py::test_y"
    runs = [run("a", ["test_x.py"], [t]), run("a", ["test_x.py"]),        # failed, then passed: flaky
            run("b", ["test_x.py"], [t]), run("c", ["test_x.py"]),        # failed and passed on different commits
            run("d", ["test_x.py"], ["tests/test_x.py::test_z"]), run("d", ["test_other.py"]),  # the file never ran again
            run("e", ["test_x.py"], [t]) | {"dirty": True}, run("e", ["test_x.py"])]  # an edit between: a fix, not a flake
    assert testlog.flaky(runs) == {t: (1, 1)}


def test_a_land_records_numbers(history):
    testlog.land(["branch=wt", "outcome=landed", "test=12.34", "full=False"])
    rec = json.loads((history / "lands.jsonl").read_text(encoding="utf-8"))
    assert rec["test"] == 12.3 and rec["outcome"] == "landed" and rec["full"] == "False"


def test_off_records_nothing(monkeypatch, tmp_path):
    monkeypatch.setenv("TW_TEST_HISTORY", "off")
    assert testlog.append("runs.jsonl", {"x": 1}) is None


@pytest.mark.integration
def test_the_summary_reads_what_was_recorded(history):
    testlog.append("runs.jsonl", run("a", ["test_x.py"], ["tests/test_x.py::t"]) | {"slow": []})
    testlog.append("runs.jsonl", run("a", ["test_x.py"]) | {"slow": []})
    out = subprocess.run([sys.executable, str(testlog.REPO / "scripts" / "testlog.py"), "--days", "36500"],
                         capture_output=True, text=True, check=True).stdout
    assert "2 runs, 2 full" in out and "flaky tests (failed, passed on the same commit): 1" in out


def test_a_land_with_one_area_is_no_pass_for_a_test_it_did_not_run():
    t = "tests/test_x.py::test_y"
    whole = run("a", ["test_x.py"], [t])
    whole["files"]["test_x.py"][0] = 30
    part = run("a", ["test_x.py"])                       # -k or --areas ran 1 of the file's 30 tests
    assert testlog.flaky([whole, part]) == {}


def test_the_flake_runner_reads_failures_from_pytests_summary():
    spec = importlib.util.spec_from_file_location("flake_run", testlog.REPO / "scripts" / "flake_run.py")
    fr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fr)
    assert fr.failures_in("....\n3150 passed, 1 skipped in 61.6s") == 0
    assert fr.failures_in("F.\n2 failed, 3148 passed, 1 error in 60s") == 3
    assert fr.failures_in("Traceback ... ImportError") is None


class Report:
    def __init__(self, nodeid, when, outcome, duration, layer):
        self.nodeid, self.when, self.duration = nodeid, when, duration
        self.user_properties = [("layer", layer)]
        self.failed, self.skipped = outcome == "failed", outcome == "skipped"


@pytest.mark.integration      # record() asks git for the commit and the dirty state
def test_the_recorder_sums_phases_per_layer_and_file():
    log = RunLog(type("C", (), {"invocation_params": type("I", (), {"args": ()})()})())
    for r in (Report("tests/test_a.py::t1", "setup", "passed", 1.0, "browser"),
              Report("tests/test_a.py::t1", "call", "failed", 0.5, "browser"),
              Report("tests/test_b.py::t2", "call", "passed", 0.01, "node"),
              Report("tests/test_a.py::t3", "setup", "passed", 0.0, "python")):    # a cheap test after: still a browser file
        log.pytest_runtest_logreport(r)
    rec = log.record()
    assert rec["layers"] == {"python": [0, 0.0], "node": [1, 0.0], "browser": [1, 1.5]}
    assert rec["files"]["test_a.py"] == [1, 1.5, "browser"]
    assert rec["failed"] == ["tests/test_a.py::t1"] and rec["n_files"] == 2
    assert rec["outcomes"] == {"passed": 1, "failed": 1, "skipped": 0, "error": 0}
