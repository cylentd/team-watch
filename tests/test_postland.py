"""scripts/postland.py: the after-land full run posts to Discord only when it fails (2026-10-07).

The message, the failed ids and the plan are pure and tested with fakes. The one-run-at-a-time job and its
pending sha are testsched's coalesce (real, in a temp loadgate home); git, the checkout, the suite and the
cache check are replaced. No git, no pytest, no network, no real webhook file, no real checkout.
"""
import contextlib
import importlib.util
import json
import pathlib
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("postland", ROOT / "scripts" / "postland.py")
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)

SHA = "92f3ed776f26234c3dd8b4efa327e04f15e8c84b"
NEWER = "aaaaaaa1111111111111111111111111111111aa"
SUMMARY = ("FAILED tests/test_a.py::test_one - assert 1 == 2\n"
           "ERROR tests/test_b.py::test_two - fixture error\n"
           "FAILED tests/test_a.py::test_one - assert 1 == 2\n"
           "1 failed, 1 error, 40 passed in 9.0s\n")


def ids(n):
    return [f"tests/test_x.py::test_{i}" for i in range(n)]


# --- the message ------------------------------------------------------------------------------------

def test_a_clean_run_has_no_message():
    assert pl.message(SHA, "Digest days hold more", [], 0) is None


def test_failures_name_the_sha_the_subject_the_ids_and_the_rerun_command():
    text = pl.message(SHA, "Digest days hold more", ids(2), 1)
    assert text.splitlines() == ["team-watch after-land run FAILED on 92f3ed7: Digest days hold more",
                                 "tests/test_x.py::test_0", "tests/test_x.py::test_1",
                                 "Rerun at 92f3ed7: python scripts/run_tests.py --full"]


def test_only_ten_ids_are_named_and_the_rest_are_counted_with_the_log_path():
    lines = pl.message(SHA, "s", ids(13), 1).splitlines()
    assert lines[1:11] == ids(10)
    assert lines[11] == "... and 3 more (log: ~/.team-watch-reports/postland-92f3ed7.log)"


def test_exactly_ten_failures_add_no_count_line():
    lines = pl.message(SHA, "s", ids(10), 1).splitlines()
    assert [ln.startswith("...") for ln in lines] == [False] * 12


def test_a_run_with_no_failed_test_and_a_bad_exit_says_it_gave_no_result():
    lines = pl.message(SHA, "s", [], 2).splitlines()
    assert lines[1] == "no result: pytest exit 2, no failed test listed"


def test_an_error_replaces_the_no_result_line_and_is_cut_to_300_chars():
    lines = pl.message(SHA, "s", [], None, "x" * 400).splitlines()
    assert lines[1] == "error: " + "x" * 300
    assert len(lines) == 3


def test_a_clean_exit_with_an_error_still_posts():
    assert pl.message(SHA, "s", [], 0, "checkout failed").splitlines()[1] == "error: checkout failed"


def test_the_message_stays_under_discords_limit_whatever_the_ids_and_subject():
    long_ids = [f"tests/test_x.py::{'t' * 400}{i}" for i in range(50)]
    text = pl.message(SHA, "s" * 500, long_ids, 1, "e" * 900)
    assert len(text) <= 1900


def test_an_id_is_cut_to_160_chars_and_the_subject_to_100():
    lines = pl.message(SHA, "s" * 150, ["i" * 200], 1).splitlines()
    assert lines[0] == "team-watch after-land run FAILED on 92f3ed7: " + "s" * 100
    assert lines[1] == "i" * 160


# --- reading pytest's summary -----------------------------------------------------------------------

def test_failed_ids_come_from_the_short_summary_once_each_in_order():
    assert pl.failed_ids(SUMMARY) == ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]


def test_a_file_that_failed_to_collect_is_named_by_its_path():
    assert pl.failed_ids("ERROR tests/test_c.py - ImportError: no module\n") == ["tests/test_c.py"]


def test_a_summary_with_no_failures_has_no_ids():
    assert pl.failed_ids("40 passed in 9.0s\nFAILED is only a word here\n") == []


# --- the plan ---------------------------------------------------------------------------------------

def test_the_plan_names_the_sha_checkout_command_and_log(tmp_path):
    lines = pl.plan_lines(SHA, tmp_path / "co", exists=True)
    assert lines[0] == f"sha: {SHA}"
    assert lines[1] == f"checkout: {tmp_path / 'co'} (exists; git checkout --detach 92f3ed7)"
    assert lines[2] == "command: TW_RUN_KIND=postland python scripts/run_tests.py --full"
    assert lines[3].endswith("postland-92f3ed7.log")


def test_a_missing_checkout_is_planned_as_a_worktree_add(tmp_path):
    line = pl.plan_lines(SHA, tmp_path / "co", exists=False)[1]
    assert f"missing; git worktree add --detach {tmp_path / 'co'} 92f3ed7" in line


def test_the_plan_says_who_holds_the_lock_the_workers_and_the_cache_check(tmp_path):
    assert pl.plan_lines(SHA, tmp_path / "co", exists=True)[4:] == [
        "job: testsched coalesce 'postland' (one run at a time; a sha that lands during a run waits, the latest only)",
        "workers: loadgate class postland (idle priority, a quarter of the budget, waits until 2 are free)",
        "then: cache verify on the run's results (a cached pass that fails twice is a lie: the cache goes off)",
        "on failure: one Discord message; clean: nothing"]


# --- posting and the whole loop, with fakes ------------------------------------------------------------

class Poster:
    def __init__(self, fail=None):
        self.sent, self.fail = [], fail

    def __call__(self, text):
        if self.fail:
            raise self.fail
        self.sent.append(text)


def test_a_dead_webhook_is_logged_and_does_not_raise():
    said = []
    assert pl.post("x", said.append, Poster(fail=OSError("no route"))) is False
    assert said == ["discord post failed: OSError: no route"]


def test_a_live_webhook_gets_the_text_once():
    poster, said = Poster(), []
    assert pl.post("hello", said.append, poster) is True
    assert poster.sent == ["hello"] and said == ["posted to Discord"]


UNITS = ["tests/test_a.py", "tests/test_b.py", "tests/test_c.py"]


@pytest.fixture
def world(tmp_path, monkeypatch):
    """The module with git, the checkout, the suite and the cache check replaced: `results` is the queue of
    (exit code, output); a run writes the results file run_tests.py would, `UNITS` with the files of its
    failed tests marked. The job lock is testsched's real coalesce, in a temp loadgate home."""
    monkeypatch.setenv("LOADGATE_HOME", str(tmp_path / "lg"))
    w = types.SimpleNamespace(poster=Poster(), results=[], ran=[], moved=[], bad=None, during=None, reruns=[],
                              rerun_ids=[], verified=[], lies=[], job=None)
    flake = types.SimpleNamespace(post_discord=lambda text: w.poster(text))
    real = pl.load_sched()
    w.coalesce = real.coalesce
    w.job = real.coalesce.job_dir(tmp_path, "postland")
    cache = types.SimpleNamespace(verify=lambda repo, results, root=None, sha=None:
                                  w.verified.append((dict(results), sha)) or {"lies": list(w.lies), "verified": []})
    sched = types.SimpleNamespace(coalesce=real.coalesce, cache=cache)

    def fake_git(repo, *args):
        return types.SimpleNamespace(returncode=0, stdout="Digest days hold more\n", stderr="")

    def fake_move(repo, sha, checkout=None):
        w.moved.append(sha)
        return w.bad

    def fake_run(checkout, log, timeout=None):
        w.ran.append(log.name)
        w.during and w.during.pop(0)()    # what another land does while this run is going
        code, out = w.results.pop(0)
        bad = {i.split("::")[0] for i in pl.failed_ids(out)}
        pl.results_path(log).write_text(json.dumps({u: "failed" if u in bad else "passed" for u in UNITS}))
        return code, out

    def fake_rerun(checkout, failed, log, timeout=None):
        """The second run of the failed ids: queued in `reruns`, else they fail again."""
        w.rerun_ids.append(list(failed))
        return w.reruns.pop(0) if w.reruns else (1, "".join(f"FAILED {i} - again\n" for i in failed))

    monkeypatch.setattr(pl, "rerun_failed", fake_rerun)
    monkeypatch.setattr(pl, "git", fake_git)
    monkeypatch.setattr(pl, "move_checkout", fake_move)
    monkeypatch.setattr(pl, "run_suite", fake_run)
    monkeypatch.setattr(pl, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(pl, "resolve", lambda repo, sha: sha or SHA)
    monkeypatch.setattr(pl, "main_checkout", lambda: tmp_path)
    monkeypatch.setattr(pl, "load", lambda name: flake)
    monkeypatch.setattr(pl, "load_sched", lambda: sched)
    return w


def test_a_clean_run_posts_nothing_and_exits_zero(world):
    world.results = [(0, "40 passed in 9.0s\n")]
    assert pl.main(["--sha", SHA]) == 0
    assert world.poster.sent == [] and world.moved == [SHA]


def test_a_failing_run_posts_one_message_with_the_failed_ids(world):
    world.results = [(1, SUMMARY)]
    assert pl.main(["--sha", SHA]) == 0
    assert len(world.poster.sent) == 1
    assert world.poster.sent[0].splitlines()[1:3] == ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]


def test_a_dead_webhook_on_a_failing_run_is_logged_in_the_run_log_and_the_exit_is_zero(world):
    world.results = [(1, SUMMARY)]
    world.poster.fail = OSError("webhook gone")
    assert pl.main(["--sha", SHA]) == 0
    assert "discord post failed: OSError: webhook gone" in (pl.REPORTS / "postland-92f3ed7.log").read_text()


def test_a_timeout_posts_a_no_result_message(world):
    world.results = [(None, "")]
    pl.main(["--sha", SHA])
    assert world.poster.sent[0].splitlines()[1] == "error: no result in 3600 s"


def test_a_checkout_that_cannot_be_moved_runs_nothing_and_posts_the_reason(world):
    world.bad = "checkout failed: bad object"
    pl.main(["--sha", SHA])
    assert world.ran == []
    assert world.poster.sent[0].splitlines()[1] == "error: checkout failed: bad object"


def test_a_run_that_is_going_records_the_new_sha_and_runs_nothing(world, tmp_path):
    assert world.coalesce.submit(tmp_path, "postland", SHA) == "run"    # a live run: this process holds the job
    assert pl.main(["--sha", NEWER]) == 0
    assert world.ran == [] and json.loads((world.job / "pending.json").read_text()) == {"sha": NEWER}


@pytest.mark.integration      # the real testsched coalesce: lock and record files, psutil checks (~300 ms on Windows)
def test_a_sha_that_lands_during_a_run_is_tested_after_it_and_then_the_job_is_freed(world, tmp_path):
    world.results = [(0, "ok"), (1, SUMMARY)]
    world.during = [lambda: world.coalesce.submit(tmp_path, "postland", NEWER)]
    assert pl.main(["--sha", SHA]) == 0
    assert world.moved == [SHA, NEWER]
    assert world.ran == ["postland-92f3ed7.log", "postland-aaaaaaa.log"]
    assert len(world.poster.sent) == 1 and "FAILED on aaaaaaa" in world.poster.sent[0]
    assert not (world.job / "running.json").exists() and not (world.job / "pending.json").exists()


def test_the_dry_run_prints_the_plan_and_touches_nothing(world, capsys):
    assert pl.main(["--sha", SHA, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert f"sha: {SHA}" in out and "TW_RUN_KIND=postland python scripts/run_tests.py --full" in out
    assert "loadgate class postland" in out and "testsched coalesce 'postland'" in out
    assert world.moved == [] and world.ran == [] and not (world.job / "running.json").exists()


def test_an_unknown_sha_exits_one(world, monkeypatch):
    monkeypatch.setattr(pl, "resolve", lambda repo, sha: None)
    assert pl.main(["--sha", "nope"]) == 1


# --- a failure is rerun once, and only what fails twice is posted --------------------------------------

def test_a_test_that_failed_once_and_passes_on_rerun_posts_nothing_and_the_log_says_flaky(world):
    world.results = [(1, SUMMARY)]
    world.reruns = [(0, "2 passed in 3.0s\n")]
    assert pl.main(["--sha", SHA]) == 0
    assert world.rerun_ids == [["tests/test_a.py::test_one", "tests/test_b.py::test_two"]]
    assert world.poster.sent == []
    assert "2 failed once and passed on rerun (flaky)" in (pl.REPORTS / "postland-92f3ed7.log").read_text()


def test_only_the_tests_that_failed_twice_are_posted_and_the_message_counts_the_flaky_ones(world):
    world.results = [(1, SUMMARY)]
    world.reruns = [(1, "FAILED tests/test_b.py::test_two - still\n")]
    pl.main(["--sha", SHA])
    assert world.poster.sent[0].splitlines() == [
        "team-watch after-land run FAILED on 92f3ed7: Digest days hold more",
        "tests/test_b.py::test_two",
        "1 more failed once and passed on rerun (flaky)",
        "Rerun at 92f3ed7: python scripts/run_tests.py --full"]


def test_a_rerun_that_lists_nothing_but_exits_badly_keeps_every_first_failure(world):
    world.results = [(1, SUMMARY)]
    world.reruns = [(2, "ERROR: not found: tests/test_a.py::test_one\n")]
    pl.main(["--sha", SHA])
    assert world.poster.sent[0].splitlines()[1:3] == ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]


def test_a_rerun_that_timed_out_keeps_every_first_failure(world):
    world.results = [(1, SUMMARY)]
    world.reruns = [(None, "")]
    pl.main(["--sha", SHA])
    assert world.poster.sent[0].splitlines()[1:3] == ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]


def test_a_run_that_gave_no_result_is_posted_without_a_rerun(world):
    world.results = [(2, "INTERNALERROR boom\n")]
    pl.main(["--sha", SHA])
    assert world.rerun_ids == []
    assert world.poster.sent[0].splitlines()[1] == "no result: pytest exit 2, no failed test listed"


def test_still_failing_is_empty_when_the_rerun_passed_else_what_it_lists_else_every_first_failure():
    first = ["a.py::t1", "a.py::t2"]
    assert pl.still_failing(first, 0, "2 passed") == []
    assert pl.still_failing(first, 1, "FAILED a.py::t2 - x\n") == ["a.py::t2"]
    assert pl.still_failing(first, 1, "") == first
    assert pl.still_failing(first, None, "") == first


def test_the_flaky_count_line_only_appears_when_there_is_one():
    assert "flaky" not in pl.message(SHA, "s", ids(1), 1)
    assert pl.message(SHA, "s", ids(1), 1, flaky=3).splitlines()[-2] == "3 more failed once and passed on rerun (flaky)"


# --- a forced checkout --------------------------------------------------------------------------------

def test_a_dirty_checkout_is_forced_to_the_sha_not_refused(tmp_path, monkeypatch):
    (tmp_path / ".git").write_text("gitdir: elsewhere")
    calls = []

    def fake_git(repo, *args):
        calls.append(args)
        return types.SimpleNamespace(returncode=0, stdout=" M scripts/run_tests.py\n", stderr="")

    monkeypatch.setattr(pl, "git", fake_git)
    assert pl.move_checkout(tmp_path, SHA, checkout=tmp_path) is None
    assert calls == [("checkout", "--force", "--detach", SHA)]


def test_a_failed_forced_checkout_is_reported(tmp_path, monkeypatch):
    (tmp_path / ".git").write_text("gitdir: elsewhere")
    monkeypatch.setattr(pl, "git", lambda repo, *args: types.SimpleNamespace(returncode=1, stdout="", stderr="bad object\n"))
    assert pl.move_checkout(tmp_path, SHA, checkout=tmp_path) == "checkout failed: bad object"


# --- the job lock, the workers and the cache check (loadgate and testsched, 2026-10-07) -----------------

@pytest.mark.integration      # the real testsched coalesce: lock and record files, psutil checks (~140 ms on Windows)
def test_a_crash_mid_run_clears_the_job_so_an_older_sha_never_runs_after_the_next_land(world, tmp_path):
    def land_then_crash():
        world.coalesce.submit(tmp_path, "postland", NEWER)      # another land records itself as pending
        raise RuntimeError("boom")
    world.during = [land_then_crash]
    with pytest.raises(RuntimeError):
        pl.main(["--sha", SHA])
    assert not (world.job / "running.json").exists() and not (world.job / "pending.json").exists()


def test_a_busy_lock_is_logged_and_exits_zero_without_running(world, monkeypatch):
    def busy(repo, name, sha, work=None):
        raise TimeoutError("loadgate lock busy for 10 s")
    monkeypatch.setattr(world.coalesce, "submit", busy)
    assert pl.main(["--sha", SHA]) == 0
    assert world.ran == [] and world.moved == []
    assert "lock busy for 10 s" in (pl.REPORTS / "postland-92f3ed7.log").read_text()


def test_the_suite_command_asks_run_tests_for_a_results_file_next_to_the_log(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(pl, "run_logged", lambda cmd, checkout, log, timeout: seen.append(cmd) or (0, ""))
    log = tmp_path / "postland-92f3ed7.log"
    pl.run_suite(tmp_path, log)
    assert seen[0][1:] == ["scripts/run_tests.py", "--full", "--results-json", str(tmp_path / "postland-92f3ed7.json")]


def test_a_clean_run_checks_the_cache_with_every_unit_passed(world):
    world.results = [(0, "40 passed in 9.0s\n")]
    pl.main(["--sha", SHA])
    assert world.verified == [({u: "passed" for u in UNITS}, SHA)]


def test_a_test_that_failed_twice_marks_only_its_file_failed_in_the_check(world):
    world.results = [(1, SUMMARY)]
    world.reruns = [(1, "FAILED tests/test_b.py::test_two - still\n")]
    pl.main(["--sha", SHA])
    assert world.verified == [({"tests/test_a.py": "passed", "tests/test_b.py": "failed",
                                "tests/test_c.py": "passed"}, SHA)]


def test_a_flaky_test_is_a_pass_in_the_check_not_a_lie(world):
    world.results = [(1, SUMMARY)]
    world.reruns = [(0, "2 passed in 3.0s\n")]
    pl.main(["--sha", SHA])
    assert world.verified == [({u: "passed" for u in UNITS}, SHA)]


def test_a_lie_the_check_finds_is_named_in_the_message(world):
    world.results = [(1, SUMMARY)]
    world.lies = ["tests/test_a.py"]
    pl.main(["--sha", SHA])
    lines = world.poster.sent[0].splitlines()
    assert lines[-2] == "cache lie: tests/test_a.py failed with a cached pass; the result cache is off"
    assert lines[-1] == "Rerun at 92f3ed7: python scripts/run_tests.py --full"


def test_a_run_that_gave_no_failed_ids_and_a_bad_exit_is_not_checked(world):
    world.results = [(2, "INTERNALERROR boom\n")]
    pl.main(["--sha", SHA])
    assert world.verified == []


def test_a_run_with_no_results_file_is_not_checked(world, monkeypatch):
    monkeypatch.setattr(pl, "run_suite", lambda checkout, log, timeout=None: (0, "40 passed\n"))
    pl.main(["--sha", SHA])
    assert world.verified == [] and world.poster.sent == []


def test_a_dead_cache_check_is_logged_and_does_not_hide_the_result(world, monkeypatch):
    def broken(repo, results, root=None, sha=None):
        raise OSError("disk gone")
    monkeypatch.setattr(pl.load_sched(), "cache", types.SimpleNamespace(verify=broken))
    world.results = [(1, SUMMARY)]
    assert pl.main(["--sha", SHA]) == 0
    assert len(world.poster.sent) == 1
    assert "cache check not made: OSError: disk gone" in (pl.REPORTS / "postland-92f3ed7.log").read_text()


def test_the_message_names_a_lie_only_when_there_is_one():
    assert "cache lie" not in pl.message(SHA, "s", ids(1), 1)
    text = pl.message(SHA, "s", ids(1), 1, lies=["tests/test_a.py", "tests/test_b.py"])
    assert "cache lie: tests/test_a.py, tests/test_b.py failed with a cached pass; the result cache is off" in text


def test_without_the_library_the_suite_runs_once_with_no_lock_and_no_check(world, monkeypatch):
    monkeypatch.setattr(pl, "load_sched", lambda: None)
    world.results = [(1, SUMMARY)]
    assert pl.main(["--sha", SHA]) == 0
    assert world.ran == ["postland-92f3ed7.log"] and world.verified == []
    assert len(world.poster.sent) == 1
