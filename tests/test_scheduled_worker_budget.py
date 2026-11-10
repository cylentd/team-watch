"""Scheduled and direct suite defaults request two workers; explicit counts remain deliberate."""
import pytest

from test_run_tests import machine, pick_files, record_pytest, runner


@pytest.mark.parametrize("mode", [[], ["--committed"], ["--full"]])
def test_cached_suite_requests_two_workers(machine, monkeypatch, mode):
    pick_files(monkeypatch, ["tests/test_a.py"])
    assert runner.main(mode) == 0
    assert machine.fake.seen.runs[0].kw["cpu"] == 2


def test_direct_suite_requests_two_workers(machine, monkeypatch):
    record_pytest(monkeypatch)
    assert runner.main(["--full", "--", "tests/test_ranks.py"]) == 0
    assert machine.fake.seen.claims[0][1]["cpu"] == 2


@pytest.mark.parametrize("extra,expected", [([], 2), (["-n", "5"], 5)])
def test_repeat_lane_reserves_requested_workers(machine, monkeypatch, extra, expected):
    monkeypatch.setattr(runner, "new_test_ids", lambda *args: ["tests/test_x.py::test_a"])
    record_pytest(monkeypatch)
    assert runner.main(["--repeat-new", "10", "--", *extra]) == 0
    assert machine.fake.seen.claims[0][1]["cpu"] == expected


@pytest.mark.parametrize("extra,expected", [(["-n", "5"], 5), (["-n5"], 5),
    (["--numprocesses=5"], 5), (["--numprocesses", "5"], 5), (["-n", "0"], 1),
    (["-n", "auto"], 2), (["-n", "logical"], 2), (["-n5", "-n", "2"], 2)])
def test_explicit_worker_selection_is_reserved(machine, monkeypatch, extra, expected):
    pick_files(monkeypatch, ["tests/test_a.py"])
    assert runner.main(["--", *extra]) == 0
    assert machine.fake.seen.runs[0].kw["cpu"] == expected
