"""The run profiler (tests/runlog.py `Profile`, scripts/testlog.py `--profile`): one run split into the
harness (startup, collection, shared fixtures, pytest's own overhead, idle) and the tests (setup, call,
teardown), with the fixtures and workers behind each number. Synthetic reports and clocks, so every
expected number below is arithmetic on the inputs, never read back from the code."""
import json
import os
import subprocess
import sys
import textwrap

import pytest

from runlog import Profile, ProfilePlugin, RunLog, build_profile, testlog


class Report:
    def __init__(self, nodeid, when, duration):
        self.nodeid, self.when, self.duration = nodeid, when, duration


def worker(wid="gw0", start=100.0):
    return Profile(wid, start)


def feed(p, nodeid, setup=0.0, call=0.0, teardown=0.0):
    """One test's three phases, each reported in the order pytest reports them."""
    for when, dur in (("setup", setup), ("call", call), ("teardown", teardown)):
        p.begin(when)
        p.report(Report(nodeid, when, dur))


def test_a_tests_three_phases_are_kept_apart():
    p = worker()
    feed(p, "t.py::a", setup=0.5, call=2.0, teardown=0.25)
    out = p.finish(110.0)
    assert out["tests"] == {"setup": 0.5, "call": 2.0, "teardown": 0.25, "n": 1}
    assert out["top"] == [["t.py::a", 2.75, 0.5, 2.0, 0.25, 0.0]]


def test_a_session_fixture_built_in_a_tests_setup_is_harness_not_that_tests_setup():
    p = worker()
    p.begin("setup")
    p.fixture_setup("built", "session", 4.0)
    p.report(Report("t.py::first", "setup", 5.0))     # 4.0 s of it was the build
    out = p.finish(110.0)
    assert out["shared"]["session_setup"] == 4.0
    assert out["tests"]["setup"] == 1.0


def test_a_module_fixture_torn_down_in_a_tests_teardown_is_harness():
    p = worker()
    p.begin("teardown")
    p.fixture_teardown("page", "module", 1.5)
    p.report(Report("t.py::last", "teardown", 1.75))
    out = p.finish(110.0)
    assert out["shared"]["module_teardown"] == 1.5
    assert out["tests"]["teardown"] == 0.25


def test_a_function_fixture_stays_in_the_tests_setup_and_is_named_on_the_test():
    p = worker()
    p.begin("setup")
    p.fixture_setup("tmp_dir", "function", 0.5)
    p.report(Report("t.py::a", "setup", 0.75))
    out = p.finish(110.0)
    assert out["tests"]["setup"] == 0.75
    assert out["top"][0][5] == 0.5
    assert out["fixtures"]["tmp_dir"] == ["function", 1, 0.5, 0.0]


def test_a_class_or_package_fixture_counts_with_the_module_ones():
    p = worker()
    p.begin("setup")
    p.fixture_setup("cls", "class", 1.0)
    p.fixture_setup("pkg", "package", 2.0)
    p.report(Report("t.py::a", "setup", 3.5))
    assert p.finish(110.0)["shared"]["module_setup"] == 3.0


def test_fixtures_are_totalled_by_name_with_count_setup_and_teardown():
    p = worker()
    for _ in range(3):
        p.begin("setup")
        p.fixture_setup("page", "module", 1.0)
        p.report(Report("t.py::a", "setup", 1.0))
    p.begin("teardown")
    p.fixture_teardown("page", "module", 0.5)
    p.report(Report("t.py::a", "teardown", 0.5))
    assert p.finish(110.0)["fixtures"]["page"] == ["module", 3, 3.0, 0.5]


def test_busy_idle_and_pytest_overhead_come_from_the_protocol_timestamps():
    p = worker(start=100.0)
    p.sessionstart(102.0)                 # 2 s of Python startup and conftest imports
    p.collected(102.5, 104.0)             # 0.5 s of session-start hooks, then 1.5 s collecting
    p.protocol_begin(106.0)               # 2 s idle: the controller had not sent work yet
    feed(p, "t.py::a", setup=0.5, call=2.0, teardown=0.5)
    p.protocol_end(109.5)                 # 3.5 s in the protocol, 3.0 of it in reports: 0.5 overhead
    out = p.finish(112.0)                 # 2.5 s idle at the end, waiting for shutdown
    assert out["startup"] == 2.5 and out["collect"] == 1.5      # startup runs on to the first collection
    assert out["busy"] == 3.5 and out["overhead"] == 0.5
    assert out["idle"] == 4.5 and out["wall"] == 12.0


def test_a_worker_adds_up_to_its_wall_within_a_tenth_of_a_second():
    p = worker(start=100.0)
    p.sessionstart(101.0)
    p.collected(101.0, 103.0)
    p.protocol_begin(103.0)
    p.begin("setup")
    p.fixture_setup("built", "session", 3.0)
    p.report(Report("t.py::a", "setup", 3.5))
    p.begin("call")
    p.report(Report("t.py::a", "call", 1.0))
    p.begin("teardown")
    p.report(Report("t.py::a", "teardown", 0.5))
    p.protocol_end(108.2)
    out = p.finish(109.0)
    got = build_profile([out], controller_wall=9.5)
    parts = sum(got["harness"].values()) + got["tests"]["setup"] + got["tests"]["call"] + got["tests"]["teardown"]
    assert got["worker_s"] == 9.0
    assert abs(parts - got["worker_s"]) <= 0.1 and abs(got["unaccounted"]) <= 0.1


def test_the_run_merges_workers_and_names_the_controllers_share_apart():
    a, b = worker("gw0", 100.0), worker("gw1", 100.0)
    for p, call in ((a, 4.0), (b, 1.0)):
        p.sessionstart(101.0)
        p.collected(101.0, 102.0)
        p.protocol_begin(102.0)
        p.begin("setup")
        p.fixture_setup("page", "module", 0.5)
        p.report(Report("t.py::a", "setup", 0.5))
        p.begin("call")
        p.report(Report("t.py::a", "call", call))
        p.protocol_end(102.5 + call)
    got = build_profile([a.finish(110.0), b.finish(110.0)], controller_wall=11.5)
    assert got["worker_s"] == 20.0
    assert got["tests"]["call"] == 5.0 and got["tests"]["n"] == 2
    assert got["fixtures"]["page"] == ["module", 2, 1.0, 0.0]
    assert got["controller"] == 1.5                       # 11.5 s of controller beside the 10 s workers
    assert got["workers"] == [["gw0", 10.0, 4.5, 3.5, 1], ["gw1", 10.0, 1.5, 6.5, 1]]


def test_the_profile_keeps_the_30_costliest_tests_with_their_split():
    p = worker()
    for i in range(40):
        feed(p, f"t.py::t{i:02d}", setup=0.0, call=float(i))
    got = build_profile([p.finish(110.0)], controller_wall=10.0)
    assert len(got["top"]) == 30
    assert got["top"][0] == ["t.py::t39", 39.0, 0.0, 39.0, 0.0, 0.0]
    assert got["top"][-1][0] == "t.py::t10"


def test_one_fixture_name_with_two_scopes_is_two_rows():
    a, b = worker("gw0"), worker("gw1")
    for p, scope in ((a, "module"), (b, "function")):
        p.begin("setup")
        p.fixture_setup("page", scope, 1.0)
        p.report(Report("t.py::a", "setup", 1.0))
    got = build_profile([a.finish(110.0), b.finish(110.0)], controller_wall=10.0)
    assert got["fixtures"]["page@module"][1:] == [1, 1.0, 0.0]
    assert got["fixtures"]["page@function"][1:] == [1, 1.0, 0.0]


def test_a_fixture_set_up_inside_another_is_charged_to_each_alone():
    p = worker()
    p.enter()                             # outer's function body asks for inner
    p.enter()
    assert p.leave(3.0) == 3.0            # inner took 3 s, all its own
    assert p.leave(5.0) == 2.0            # outer took 5 s in all, 2 s of it its own


@pytest.mark.integration      # record() asks git for the commit and the dirty state
def test_the_run_record_keeps_its_old_fields_and_gains_the_profile():
    config = type("C", (), {"invocation_params": type("I", (), {"args": ()})()})()
    log = RunLog(config)
    p = worker()
    feed(p, "t.py::a", call=1.0)
    log.profiles.append(p.finish(110.0))
    rec = log.record()
    assert {"at", "kind", "sha", "wall", "outcomes", "n_files", "layers", "files", "slow", "failed"} <= set(rec)
    assert rec["profile"]["tests"]["call"] == 1.0


# --- the printout -----------------------------------------------------------------------------------

def a_run(**over):
    prof = {"v": 1, "worker_s": 200.0, "controller": 2.0, "unaccounted": 1.0,
            "harness": {"startup": 20.0, "collect": 10.0, "session_setup": 30.0, "session_teardown": 1.0,
                        "module_setup": 12.0, "module_teardown": 4.0, "overhead": 5.0, "idle": 17.0},
            "tests": {"setup": 20.0, "call": 70.0, "teardown": 10.0, "n": 300},
            "workers": [["gw0", 100.0, 80.0, 10.0, 150], ["gw1", 100.0, 40.0, 20.0, 150]],
            "fixtures": {"built": ["session", 2, 30.0, 1.0], "page": ["module", 9, 12.0, 4.0]},
            "top": [["tests/test_a.py::slow", 9.0, 1.0, 7.0, 1.0, 0.5]]}
    rec = {"at": "2026-10-07T12:00:00+00:00", "kind": "dev", "sha": "abc1234" + "0" * 33, "wall": 120.0,
           "n_files": 200, "layers": {"python": [3, 1.0]}, "files": {}, "failed": [], "profile": prof}
    return rec | over


def test_the_printout_leads_with_wall_and_worker_seconds_then_the_split_with_the_residual():
    out = testlog.format_profile(a_run())
    assert out.splitlines()[0].startswith("run 2026-10-07 12:00 dev abc1234: 120 s wall, 200 worker wall-s")
    assert "harness" in out and "tests" in out
    assert "unaccounted" in out and "0.5%" in out          # 1.0 of 200


def test_the_printout_ranks_fixtures_tests_and_workers():
    out = testlog.format_profile(a_run())
    assert out.index("built") < out.index("page")          # costliest fixture first
    assert "tests/test_a.py::slow" in out
    assert "gw0" in out and "80%" in out and "40%" in out  # busy share of each worker's wall
    assert "slowest worker gw0" in out


def test_a_run_without_a_profile_says_so():
    rec = a_run()
    del rec["profile"]
    assert "no profile" in testlog.format_profile(rec)


def test_the_default_run_is_the_latest_full_one_with_a_profile_and_last_takes_any_size():
    runs = [a_run(sha="a" * 40), a_run(sha="b" * 40, n_files=5), a_run(sha="c" * 40, n_files=300) | {"profile": None}]
    assert testlog.pick_profile_run(runs, "")["sha"] == "a" * 40
    assert testlog.pick_profile_run(runs, "", last=True)["sha"] == "b" * 40


def test_a_run_is_picked_by_sha_prefix_or_by_index():
    runs = [a_run(sha="a1" * 20), a_run(sha="b2" * 20)]
    assert testlog.pick_profile_run(runs, "b2b2")["sha"] == "b2" * 20
    assert testlog.pick_profile_run(runs, "0")["sha"] == "a1" * 20
    assert testlog.pick_profile_run(runs, "-1")["sha"] == "b2" * 20
    assert testlog.pick_profile_run(runs, "ffff") is None


# --- a real pytest run -------------------------------------------------------------------------------

CONFTEST = """
import pathlib, sys
sys.path.insert(0, {tests!r})
import pytest, runlog

def pytest_configure(config):
    runlog.register(config)

@pytest.fixture(autouse=True)
def _layer(record_property):
    record_property("layer", "python")

def burn(seconds):
    import time
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        pass

@pytest.fixture(scope="session")
def built():
    burn(0.3)
    yield 1
    burn(0.1)

@pytest.fixture(scope="module")
def page(built):
    burn(0.2)
    return built
"""
TESTS = """
def test_a(page): assert page == 1
def test_b(page): assert page == 1
"""


@pytest.mark.integration      # a real pytest in its own process
def test_a_real_run_records_the_fixtures_and_the_harness(tmp_path):
    (tmp_path / "conftest.py").write_text(CONFTEST.format(tests=str(testlog.REPO / "tests")), encoding="utf-8")
    (tmp_path / "test_x.py").write_text(textwrap.dedent(TESTS), encoding="utf-8")
    (tmp_path / "test_y.py").write_text(textwrap.dedent(TESTS), encoding="utf-8")
    hist = tmp_path / "hist"
    done = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                          cwd=tmp_path, capture_output=True, text=True, env={**os.environ, "TW_TEST_HISTORY": str(hist)})
    assert done.returncode == 0, done.stdout + done.stderr
    prof = json.loads((hist / "runs.jsonl").read_text(encoding="utf-8").splitlines()[-1])["profile"]
    built, page = prof["fixtures"]["built"], prof["fixtures"]["page"]
    assert built[0] == "session" and built[1] == 1
    assert built[2] >= 0.3 and built[3] >= 0.1 and page[2] >= 0.2
    assert prof["tests"]["n"] == 4
    assert prof["harness"]["startup"] > 0 and prof["harness"]["collect"] > 0
    assert abs(prof["unaccounted"]) <= 0.05 * prof["worker_s"]
    assert len(prof["workers"]) == 1


# --- the xdist hand-off, without a second process ---------------------------------------------------

class Config:
    """The parts of pytest's config the plugin reads. `workeroutput` makes it an xdist worker's."""
    def __init__(self, worker=False, controller=False):
        self.pluginmanager = type("PM", (), {"hasplugin": lambda self, name: controller})()
        if worker:
            self.workeroutput = {}
            self.workerinput = {"workerid": "gw3"}


class SinkLog:
    def __init__(self):
        self.profiles = []


def a_plugin(config, log=None):
    p = ProfilePlugin(config, log)
    p.prof = worker("gw3")
    p.restore = lambda: None
    return p


def test_a_worker_leaves_its_profile_in_workeroutput_for_the_controller():
    config, log = Config(worker=True), SinkLog()
    plugin = a_plugin(config, log)
    feed(plugin.prof, "t.py::a", call=1.0)
    plugin.pytest_sessionfinish(session=None)
    assert config.workeroutput["tw_profile"]["id"] == "gw3"
    assert config.workeroutput["tw_profile"]["tests"]["call"] == 1.0
    assert log.profiles == []                  # the controller collects it, the worker keeps none


def test_a_serial_run_hands_its_profile_straight_to_the_run_log():
    config, log = Config(), SinkLog()
    plugin = a_plugin(config, log)
    plugin.pytest_sessionfinish(session=None)
    assert [p["id"] for p in log.profiles] == ["gw3"]


def test_the_controller_takes_a_downed_workers_profile_into_the_run_log():
    log = SinkLog()
    plugin = ProfilePlugin(Config(controller=True), log)
    node = type("Node", (), {"workeroutput": {"tw_profile": {"id": "gw1"}}})()
    plugin.pytest_testnodedown(node, None)
    assert log.profiles == [{"id": "gw1"}]


def test_a_worker_that_sent_no_profile_adds_nothing_to_the_run_log():
    log = SinkLog()
    plugin = ProfilePlugin(Config(controller=True), log)
    plugin.pytest_testnodedown(type("Node", (), {"workeroutput": {}})(), None)
    plugin.pytest_testnodedown(type("Node", (), {})(), None)
    assert log.profiles == []


# --- the FixtureDef.finish patch can never fail a run -----------------------------------------------

class FixtureDefWithFinish:
    argname, scope = "fx", "function"

    def finish(self, request):
        return "torn down"


def started_plugin(monkeypatch, fixture_def):
    monkeypatch.setattr("_pytest.fixtures.FixtureDef", fixture_def)
    plugin = ProfilePlugin(Config(), SinkLog())
    plugin.pytest_sessionstart(session=None)
    return plugin


def test_a_fixturedef_without_finish_leaves_profiling_on_minus_teardown_timing(monkeypatch):
    class NoFinish:
        pass

    plugin = started_plugin(monkeypatch, NoFinish)
    assert plugin.prof is not None
    assert not hasattr(NoFinish, "finish")
    plugin.pytest_sessionfinish(session=None)                  # nothing to restore, and no error
    assert plugin.runlog.profiles[0]["id"] == "main"


def test_a_fixturedef_that_refuses_the_patch_leaves_profiling_on_minus_teardown_timing(monkeypatch):
    class Locked(type):
        def __setattr__(cls, name, value):
            raise TypeError("immutable")

    class Frozen(metaclass=Locked):
        def finish(self, request):
            return "torn down"

    plugin = started_plugin(monkeypatch, Frozen)
    assert plugin.prof is not None
    assert Frozen().finish(None) == "torn down"
    plugin.pytest_sessionfinish(session=None)
    assert len(plugin.runlog.profiles) == 1


def test_the_patched_finish_times_the_teardown_and_returns_what_finish_returns(monkeypatch):
    plugin = started_plugin(monkeypatch, FixtureDefWithFinish)
    assert FixtureDefWithFinish().finish(None) == "torn down"
    count, setup_s, teardown_s = plugin.prof.fixtures["fx", "function"]
    assert (count, setup_s) == (0, 0.0)                           # a teardown only: no setup was seen
    assert teardown_s >= 0.0


def test_the_patched_finish_never_raises_when_the_recording_does(monkeypatch):
    plugin = started_plugin(monkeypatch, FixtureDefWithFinish)

    def boom(*a):
        raise RuntimeError("recording broke")

    plugin.prof.leave = boom
    assert FixtureDefWithFinish().finish(None) == "torn down"


def test_the_patched_finish_still_raises_what_the_fixture_raises(monkeypatch):
    class Failing(FixtureDefWithFinish):
        def finish(self, request):
            raise KeyError("fixture broke")

    started_plugin(monkeypatch, Failing)
    with pytest.raises(KeyError, match="fixture broke"):
        Failing().finish(None)


def test_the_patch_is_taken_off_at_session_finish(monkeypatch):
    original = FixtureDefWithFinish.finish
    plugin = started_plugin(monkeypatch, FixtureDefWithFinish)
    assert FixtureDefWithFinish.finish is not original
    plugin.pytest_sessionfinish(session=None)
    assert FixtureDefWithFinish.finish is original
