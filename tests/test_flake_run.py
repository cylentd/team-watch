"""scripts/flake_run.py: the weekly flake run posts to Discord only when a test is flaky or broken (2026-10-06).

The message and the post-or-not decision are pure and tested with a fake poster: nothing here touches the
network, runs the suite or reads the real webhook file.
"""
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("flake_run", ROOT / "scripts" / "flake_run.py")
fr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fr)

CLEAN = {"runs": [{"seed": s, "seconds": 1.0, "passed": 9, "failed": 0} for s in (11, 12, 13, 14, 15)],
         "flaky": [], "broken": [], "error": None}


def flaky(n, seeds=(12,)):
    return [{"nodeid": f"tests.test_x::test_{i}", "failed_seeds": list(seeds), "passed_seeds": [11]} for i in range(n)]


def report(**kw):
    return {**CLEAN, **kw}


class Poster:
    def __init__(self, fail=None):
        self.sent, self.fail = [], fail

    def __call__(self, text):
        if self.fail:
            raise self.fail
        self.sent.append(text)


def test_a_clean_run_has_no_message_and_posts_nothing():
    poster, said = Poster(), []
    assert fr.message(CLEAN) is None
    assert fr.notify(CLEAN, said.append, poster=poster) is False
    assert poster.sent == [] and said == ["clean: nothing to post"]


def test_the_first_line_counts_flaky_and_broken_over_the_runs():
    text = fr.message(report(flaky=flaky(2), broken=[{"nodeid": "tests.test_y::test_b", "failed_seeds": [11, 12]}]))
    assert text.splitlines()[0] == "team-watch flake run: 2 flaky, 1 broken (5 shuffled runs)"


def test_each_test_is_a_line_with_its_failing_seeds_and_the_message_ends_with_how_to_reproduce():
    text = fr.message(report(flaky=flaky(1, seeds=(12, 14))), skill="C:/skill")
    lines = text.splitlines()
    assert lines[1] == "tests.test_x::test_0 \u2014 failed on seed 12, 14"
    assert lines[-1] == "Reproduce: python -m pytest -p pytest_shuffle --shuffle 12 (PYTHONPATH=C:/skill)"


def test_only_ten_tests_are_named_and_the_rest_are_counted():
    lines = fr.message(report(flaky=flaky(13))).splitlines()
    assert sum(" \u2014 failed on seed" in ln for ln in lines) == 10
    assert lines[11].startswith("... and 3 more")


def test_a_run_that_gave_no_result_posts_its_error_with_no_test_lines():
    text = fr.message(fr.error_report("timeout: seed 7 gave no result in 900 s"), planned=5)
    assert text.splitlines() == ["team-watch flake run: 0 flaky, 0 broken (5 shuffled runs)",
                                 "error: timeout: seed 7 gave no result in 900 s"]


def test_a_flaky_run_posts_one_message_once():
    poster, said = Poster(), []
    assert fr.notify(report(flaky=flaky(1)), said.append, poster=poster) is True
    assert len(poster.sent) == 1 and poster.sent[0].startswith("team-watch flake run: 1 flaky, 0 broken")
    assert said == ["posted to Discord"]


def test_a_dry_run_prints_the_message_and_posts_nothing():
    poster, said = Poster(), []
    assert fr.notify(fr.SAMPLE, said.append, dry=True, poster=poster) is False
    assert poster.sent == [] and "team-watch flake run: 1 flaky, 0 broken" in said[0]


def test_a_failed_post_is_logged_not_raised():
    said = []
    assert fr.notify(report(flaky=flaky(1)), said.append, poster=Poster(fail=OSError("403"))) is False
    assert said == ["discord post failed: OSError: 403"]


def test_the_message_stays_under_discords_limit():
    long_id = {"nodeid": "tests.test_x::" + "t" * 400, "failed_seeds": [1], "passed_seeds": [2]}
    assert len(fr.message(report(flaky=[long_id] * 10))) <= 1900


def test_the_post_is_json_with_the_browser_user_agent_and_a_20_second_timeout():
    seen = {}

    class Resp:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def opener(req, timeout):
        seen.update(url=req.full_url, body=req.data, method=req.get_method(), timeout=timeout,
                    agent=req.get_header("User-agent"), kind=req.get_header("Content-type"))
        return Resp()
    assert fr.post_discord("hello \u2014 there", url="https://example.invalid/hook", opener=opener) == 204
    assert seen == {"url": "https://example.invalid/hook", "method": "POST", "timeout": 20,
                    "agent": "Mozilla/5.0 (team-watch flake)", "kind": "application/json",
                    "body": json.dumps({"content": "hello \u2014 there"}).encode("utf-8")}


def test_the_webhook_comes_from_the_discord_json_field(tmp_path):
    f = tmp_path / "discord.json"
    f.write_text(json.dumps({"webhook": "https://example.invalid/h", "other": 1}), encoding="utf-8")
    assert fr.webhook_url(f) == "https://example.invalid/h"
    f.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="no webhook"):
        fr.webhook_url(f)


def test_flake_py_runs_from_the_skill_dir_with_the_runs_only_when_asked(tmp_path):
    cmd = fr.flake_command(tmp_path, "C:/repo")
    assert cmd[1:] == [str(tmp_path / "flake.py"), "--repo", "C:/repo", "--json"]
    assert fr.flake_command(tmp_path, "C:/repo", 3)[-2:] == ["--runs", "3"]


def test_the_skill_dir_is_testing_skill_else_the_installed_copy(tmp_path):
    assert fr.skill_dir({"TESTING_SKILL": str(tmp_path)}) == tmp_path
    assert fr.skill_dir({}) == pathlib.Path.home() / ".agents" / "skills" / "testing" / "scripts"


def test_flake_pys_json_is_the_report_and_anything_else_is_an_error():
    assert fr.parse_report(1, json.dumps(report(flaky=flaky(1))), "")["flaky"][0]["nodeid"] == "tests.test_x::test_0"
    broken = fr.parse_report(2, "", "flake: no such directory: C:/nope")
    assert broken["error"] == "flake.py exit 2: flake: no such directory: C:/nope"
    assert broken["flaky"] == [] and broken["broken"] == []


# --- suite wall-time budgets (David, 2026-10-06) --------------------------------------------------
# Each suite in .testing.json limits.suites runs 3 times after the shuffled runs; the fastest wall time is
# the number. The runner is faked: nothing here starts pytest.

SUITES = {"fast": 10, "component": 35}


class Runner:
    """A fake suite runner: the wall times it returns per suite, in call order; None is a run with no result."""
    def __init__(self, **walls):
        self.walls, self.calls = {k: list(v) for k, v in walls.items()}, []

    def __call__(self, name):
        self.calls.append(name)
        return self.walls[name].pop(0)


def timed(**fastest):
    """A suite result as measure_suites makes it, for the message tests."""
    return {n: {"fastest_s": s, "budget_s": SUITES[n], "runs_s": [s]} for n, s in fastest.items()}


def test_each_suite_runs_three_times_and_the_fastest_wall_is_the_number():
    run = Runner(fast=[14.0, 12.4, 13.1], component=[30.0, 29.0, 41.0])
    got = fr.measure_suites(SUITES, run)
    assert run.calls == ["fast"] * 3 + ["component"] * 3
    assert got["fast"] == {"fastest_s": 12.4, "budget_s": 10, "runs_s": [14.0, 12.4, 13.1]}
    assert got["component"]["fastest_s"] == 29.0


def test_a_run_with_no_result_is_skipped_and_a_suite_with_none_has_no_number():
    got = fr.measure_suites(SUITES, Runner(fast=[None, 9.0, None], component=[None, None, None]))
    assert got["fast"]["fastest_s"] == 9.0 and got["fast"]["runs_s"] == [9.0]
    assert got["component"]["fastest_s"] is None


def test_a_suite_over_budget_is_a_line_with_the_fastest_time_and_the_budget():
    text = fr.message(report(suites=timed(fast=12.44, component=29.0)))
    assert text.splitlines() == ["team-watch flake run: 0 flaky, 0 broken (5 shuffled runs)",
                                 "suite fast: 12.4 s, budget 10 s (fastest of 3)"]


def test_a_suite_under_budget_adds_nothing_and_a_clean_run_posts_nothing():
    clean = report(suites=timed(fast=9.9, component=35.0))     # exactly on budget is not over
    poster, said = Poster(), []
    assert fr.message(clean) is None
    assert fr.notify(clean, said.append, poster=poster) is False
    assert poster.sent == [] and said == ["clean: nothing to post"]


def test_an_over_budget_suite_alone_posts_one_message():
    poster, said = Poster(), []
    assert fr.notify(report(suites=timed(fast=15.0)), said.append, poster=poster) is True
    assert len(poster.sent) == 1 and "suite fast: 15.0 s, budget 10 s" in poster.sent[0]


def test_flaky_tests_and_an_over_budget_suite_share_one_message():
    text = fr.message(report(flaky=flaky(1), suites=timed(fast=15.0)), skill="C:/skill")
    lines = text.splitlines()
    assert lines[0].startswith("team-watch flake run: 1 flaky")
    assert "suite fast: 15.0 s, budget 10 s (fastest of 3)" in lines
    assert lines[-1].startswith("Reproduce:")


def test_a_suite_that_never_gave_a_time_is_posted_not_passed_over():
    text = fr.message(report(suites={"fast": {"fastest_s": None, "budget_s": 10, "runs_s": []}}))
    assert "suite fast: no timing in 3 runs, budget 10 s" in text.splitlines()


def test_the_log_holds_every_suites_fastest_time_over_budget_or_not():
    said = []
    fr.log_report(report(suites=timed(fast=9.0, component=41.0)), said.append)
    assert "suite fast: fastest 9.0 s, budget 10 s (runs 9.0)" in said
    assert "suite component: fastest 41.0 s, budget 35 s, OVER (runs 41.0)" in said


def test_the_suites_come_from_testing_json_limits(tmp_path):
    (tmp_path / ".testing.json").write_text(json.dumps({"limits": {"suites": {
        "fast": {"layers": ["unit"], "wall_s": 10}, "component": {"layers": ["component"], "wall_s": 35}}}}),
        encoding="utf-8")
    assert fr.suites_from(tmp_path) == SUITES
    assert fr.suites_from(tmp_path / "nowhere") == {}
    (tmp_path / ".testing.json").write_text("{}", encoding="utf-8")
    assert fr.suites_from(tmp_path) == {}


def test_a_suite_runs_pytest_in_parallel_with_the_plugin_the_suite_flag_and_a_json_path():
    cmd = fr.suite_command("fast", "C:/tmp/s.json")
    assert cmd[1:3] == ["-m", "pytest"]
    assert cmd[cmd.index("--limits-suite") + 1] == "fast"
    assert cmd[cmd.index("--limits-suite-json") + 1] == "C:/tmp/s.json"
    assert cmd[cmd.index("-p") + 1] == "pytest_limits"
    assert ["-n", "auto", "--dist", "loadgroup"] == cmd[cmd.index("-n"):cmd.index("-n") + 4]


def test_a_suite_run_sees_the_skill_dir_on_pythonpath_and_the_flake_kind(tmp_path):
    env = fr.suite_env(tmp_path, {"PYTHONPATH": "C:/other", "X": "1"})
    assert env["PYTHONPATH"].split(";" if ";" in env["PYTHONPATH"] else ":")[0] == str(tmp_path)
    assert "C:/other" in env["PYTHONPATH"] and env["TW_RUN_KIND"] == "flake" and env["X"] == "1"


def test_the_suite_wall_is_read_from_the_json_the_plugin_wrote(tmp_path):
    f = tmp_path / "s.json"
    assert fr.read_wall(f) is None                                  # no file: the run gave no result
    f.write_text(json.dumps({"suite": "fast", "wall_s": 12.5, "budget_s": 10, "tests": 9}), encoding="utf-8")
    assert fr.read_wall(f) == 12.5
    f.write_text("not json", encoding="utf-8")
    assert fr.read_wall(f) is None
