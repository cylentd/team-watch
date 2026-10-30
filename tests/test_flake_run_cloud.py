"""scripts/flake_run.py off this PC: a Linux runner has no taskkill and no webhook file (2026-10-30).

Fakes stand in for the kill and the environment, so these run the same on Windows and Linux.
"""
import importlib.util
import pathlib
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("flake_run", ROOT / "scripts" / "flake_run.py")
fr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fr)

PID = 4321
SIGKILL = 9
URL = "https://example.invalid/cloud"


def stopped_by(windows):
    calls = []
    fr.stop_tree(types.SimpleNamespace(pid=PID), windows=windows,
                 run=lambda cmd, **kw: calls.append(cmd), killpg=lambda *a: calls.append(a))
    return calls


def test_a_timeout_on_windows_stops_the_tree_with_taskkill():
    assert stopped_by(windows=True) == [["taskkill", "/T", "/F", "/PID", str(PID)]]


def test_a_timeout_on_linux_kills_the_process_group():
    assert stopped_by(windows=False) == [(PID, SIGKILL)]


def test_linux_starts_the_run_in_its_own_group_so_the_kill_reaches_its_workers():
    assert fr.popen_options(windows=False) == {"start_new_session": True}


def test_windows_starts_the_run_as_before():
    assert fr.popen_options(windows=True) == {}


def test_the_webhook_comes_from_the_environment_when_a_runner_sets_it(tmp_path):
    no_file = tmp_path / "absent.json"
    assert fr.webhook_url(no_file, environ={fr.WEBHOOK_ENV: URL}) == URL
