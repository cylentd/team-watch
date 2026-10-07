"""A land runs unit + component; the browser layer only where the change points (2026-10-07).

When impact.py says "run everything" (a shared file changed), scripts/run_tests.py passes
--e2e-only-in <impact's files>: tests/conftest.py then deselects every browser-layer test outside
those files. The golden slices keep following --areas. The after-land run covers the rest.
The decision is pure (conftest.e2e_split, run_tests.e2e_args); one test runs a real pytest on a
throwaway directory to prove the option deselects.
"""
import os
import pathlib
import subprocess
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import conftest  # noqa: E402  tests/conftest.py
import run_tests as runner  # noqa: E402

PICK_ALL = {"all": True, "why": ["design/build.py is shared"], "files": ["tests/test_a.py", "tests/test_b.py"],
            "areas": ["ranks"]}


def item(nodeid, *fixtures):
    return types.SimpleNamespace(nodeid=nodeid, fixturenames=list(fixtures))


# ---- the runner's side ----

def test_everything_picked_keeps_browser_tests_only_in_impacts_files():
    args = runner.e2e_args(PICK_ALL, [])
    assert "--e2e-only-in=tests/test_a.py,tests/test_b.py" in args


def test_the_run_says_why_in_the_args_the_suite_prints():
    args = runner.e2e_args({**PICK_ALL, "why": ["a is shared", "b is shared", "c is shared", "d is shared"]}, [])
    assert "--e2e-why=shared file: a is shared; b is shared; c is shared; +1 more" in args


def test_a_pick_that_is_not_everything_adds_nothing():
    assert runner.e2e_args({**PICK_ALL, "all": False}, []) == []


def test_a_path_given_after_the_double_dash_is_a_wish_for_that_test_so_nothing_is_dropped():
    assert runner.e2e_args(PICK_ALL, ["tests/test_profile.py"]) == []
    assert runner.e2e_args(PICK_ALL, ["tests/test_profile.py::test_x", "-x"]) == []


def test_a_flag_only_extra_keeps_the_rule():
    assert runner.e2e_args(PICK_ALL, ["-x", "-k", "dossier"]) != []


def test_a_directory_given_after_the_double_dash_is_a_wish_too_so_nothing_is_dropped():
    assert runner.e2e_args(PICK_ALL, ["tests"]) == []
    assert runner.e2e_args(PICK_ALL, ["-x", "design"]) == []


def test_a_word_that_is_no_path_after_the_double_dash_keeps_the_rule():
    assert runner.e2e_args(PICK_ALL, ["-k", "no_such_file_or_folder_here"]) != []


def test_everything_picked_with_owned_areas_runs_golden_for_those_areas_only():
    args = runner.e2e_args({**PICK_ALL, "areas": ["ranks", "digest"]}, [])
    assert args[-2:] == ["--areas", "ranks,digest"]


def test_everything_picked_with_no_owned_area_passes_no_areas_flag():
    args = runner.e2e_args({**PICK_ALL, "areas": []}, [])
    assert "--areas" not in args


def picked(monkeypatch, pick):
    monkeypatch.setattr(runner.impact, "changed", lambda base, worktree: ([], []))
    monkeypatch.setattr(runner.impact, "select", lambda paths, golden: pick)


def test_a_gating_run_of_everything_passes_the_option_to_pytest(monkeypatch, capsys):
    picked(monkeypatch, PICK_ALL)
    args = runner.picked_args(False, "origin/main", True)
    assert "--e2e-only-in=tests/test_a.py,tests/test_b.py" in args
    assert "design/build.py" in capsys.readouterr().out      # the whole-suite line still says why


def test_a_gating_run_of_everything_names_the_owned_areas_to_pytest(monkeypatch):
    picked(monkeypatch, {**PICK_ALL, "areas": ["ranks"]})
    args = runner.picked_args(False, "origin/main", True)
    assert args == ["--e2e-only-in=tests/test_a.py,tests/test_b.py",
                    "--e2e-why=shared file: design/build.py is shared", "--areas", "ranks"]


def test_a_run_that_is_not_everything_is_unchanged(monkeypatch):
    picked(monkeypatch, {**PICK_ALL, "all": False})
    args = runner.picked_args(False, "origin/main", True)
    assert args == ["tests/test_a.py", "tests/test_b.py", "--areas", "ranks"]


def test_full_passes_nothing_new(monkeypatch):
    picked(monkeypatch, PICK_ALL)
    assert runner.picked_args(True, "origin/main", True) == []
    assert not [a for a in runner.command(True, "origin/main", True, []) if a.startswith("--e2e")]


def test_the_ten_run_passes_nothing_new():
    cmd = runner.repeat_command(["tests/test_x.py::test_a"], 10, [])
    assert not [a for a in cmd if a.startswith("--e2e")]


# ---- conftest's side, on fake items ----

def test_a_browser_test_outside_the_list_is_left_and_one_inside_stays():
    inside = item("tests/test_a.py::test_one", "browser")
    outside = item("tests/test_z.py::test_two", "browser")
    keep, left = conftest.e2e_split([inside, outside], ["tests/test_a.py"])
    assert keep == [inside] and left == [outside]


def test_component_build_and_python_tests_always_stay():
    kinds = [item("tests/test_z.py::c", "mount", "browser"), item("tests/test_z.py::b", "built"),
             item("tests/test_z.py::p"), item("tests/test_z.py::n", "node_js")]
    keep, left = conftest.e2e_split(kinds, ["tests/test_a.py"])
    assert keep == kinds and left == []


def test_the_list_reads_backslashes_and_the_nodeid_reads_its_file_only():
    t = item("tests/test_a.py::TestX::test_one[a-b]", "browser")
    assert conftest.e2e_split([t], ["tests\\test_a.py"]) == ([t], [])


def test_the_golden_is_left_when_test_render_is_not_listed_and_kept_when_it_is():
    g = item("tests/test_render.py::test_state_renders_something[ranks-a]", "snapshot", "browser")
    assert conftest.e2e_split([g], ["tests/test_a.py"]) == ([], [g])
    assert conftest.e2e_split([g], ["tests/test_a.py", "tests/test_render.py"]) == ([g], [])


# ---- a real pytest, on a throwaway directory ----

CONFTEST = '''import importlib.util
import sys

spec = importlib.util.spec_from_file_location("tw_conftest", {path!r})
real = importlib.util.module_from_spec(spec)
sys.modules["tw_conftest"] = real
sys.path.insert(0, {scripts!r})
spec.loader.exec_module(real)

import pytest

pytest_addoption = real.pytest_addoption
pytest_collection_modifyitems = real.pytest_collection_modifyitems
pytest_terminal_summary = real.pytest_terminal_summary


def pytest_configure(config):
    for m in ("area(name)", "req(section)", "quarantine(reason)", "journey", "integration", "xdist_group(name)"):
        config.addinivalue_line("markers", m)


@pytest.fixture
def browser():
    return None


@pytest.fixture
def mount():
    return None


@pytest.fixture
def snapshot(browser):
    return None
'''

TESTS = {
    "test_in.py": "def test_browser_in(browser):\n    pass\n",
    "test_out.py": ("def test_browser_out(browser):\n    pass\n\n"
                    "def test_component_out(mount, browser):\n    pass\n\n"
                    "def test_python_out():\n    pass\n"),
    "test_render.py": ("import pytest\n\n"
                       "@pytest.mark.area('ranks')\ndef test_golden_ranks(snapshot):\n    pass\n\n"
                       "@pytest.mark.area('digest')\ndef test_golden_digest(snapshot):\n    pass\n"),
}


def collect(tmp_path, *flags):
    (tmp_path / "conftest.py").write_text(
        CONFTEST.format(path=str(ROOT / "tests" / "conftest.py"), scripts=str(ROOT / "tests")), encoding="utf-8")
    for name, body in TESTS.items():
        (tmp_path / name).write_text(body, encoding="utf-8")
    env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    done = subprocess.run([sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-v", *flags], cwd=tmp_path,
                          env=env, capture_output=True, text=True, timeout=120)
    ran = {ln.split("::")[1].split(" ")[0] for ln in done.stdout.splitlines() if " PASSED" in ln}
    return ran, done.stdout + done.stderr


@pytest.mark.integration      # a real pytest subprocess
def test_a_real_run_drops_browser_tests_outside_the_list_and_says_how_many(tmp_path):
    ran, out = collect(tmp_path, "--e2e-only-in=test_in.py")
    assert ran == {"test_browser_in", "test_component_out", "test_python_out"}, out
    assert "e2e: 3 browser tests left to the after-land run" in out    # test_browser_out and both golden


@pytest.mark.integration      # a real pytest subprocess
def test_a_real_run_keeps_the_golden_for_its_areas_only(tmp_path):
    ran, out = collect(tmp_path, "--e2e-only-in=test_in.py,test_render.py", "--areas=ranks")
    assert ran == {"test_browser_in", "test_component_out", "test_python_out", "test_golden_ranks"}, out
    assert "e2e: 1 browser tests left to the after-land run" in out    # test_browser_out


@pytest.mark.integration      # a real pytest subprocess
def test_a_real_run_without_the_option_runs_everything_and_prints_no_e2e_line(tmp_path):
    ran, out = collect(tmp_path)
    assert len(ran) == 6, out
    assert "e2e:" not in out
