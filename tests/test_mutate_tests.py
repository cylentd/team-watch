"""scripts/mutate_tests.py: which tests the shared mutator runs against a source file (2026-10-06).

The testing skill's mutate.py calls it through `.testing.json` `mutate.select_command`, one source path at a time.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mutate_tests  # noqa: E402

JS = "design/src/js/data/x.js"


def _suite(root, files):
    (root / "tests").mkdir(exist_ok=True)
    for name, text in files.items():
        (root / "tests" / name).write_text(text, encoding="utf-8")


def test_tests_that_name_the_file_are_picked_and_the_light_ones_come_first(tmp_path):
    _suite(tmp_path, {
        "test_js_x.py": 'node_js("data/x.js")\n',
        "test_view_x.py": 'def test(browser):\n    page = "design/src/js/data/x.js"\n',
        "test_budgets.py": "design/src/js/data/x.js\n",
        "test_other.py": "nothing\n",
    })
    assert mutate_tests.tests_for(JS, tmp_path) == ["tests/test_js_x.py"]


def test_a_python_file_is_found_by_its_import(tmp_path):
    _suite(tmp_path, {"test_y.py": "import y\n", "test_z.py": "import yy\nx = 'xy'\n"})
    assert mutate_tests.tests_for("design/y.py", tmp_path) == ["tests/test_y.py"]


def test_heavy_files_are_used_when_no_light_one_covers_it(tmp_path):
    _suite(tmp_path, {"test_view_x.py": 'def test(browser):\n    "data/x.js"\n'})
    assert mutate_tests.tests_for(JS, tmp_path) == ["tests/test_view_x.py"]


def test_a_heavy_file_that_names_it_is_kept_when_no_light_file_names_it(tmp_path, monkeypatch):
    # 2026-10-06: design/avatars.py scored 0% at land. Its own tests sat in a file with one `built` test, so the
    # picker kept only impact.json's light files for it, which never call avatars.py: every mutant survived.
    monkeypatch.setattr(mutate_tests.impact, "select", lambda paths: {"files": ["tests/test_near.py"] if paths else []})
    _suite(tmp_path, {"test_near.py": "import other\n", "test_y.py": "import y\ndef test(built):\n    pass\n"})
    assert mutate_tests.tests_for("design/y.py", tmp_path) == ["tests/test_near.py", "tests/test_y.py"]


def test_the_whole_repo_checks_are_never_picked(tmp_path):
    _suite(tmp_path, {name + ".py": "import y\n" for name in mutate_tests.META})
    assert mutate_tests.tests_for("design/y.py", tmp_path) == []


def test_the_command_prints_one_test_file_per_line_for_the_mutator():
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "mutate_tests.py"), "design/src/js/data/stock.js"],
                         capture_output=True, text=True, encoding="utf-8", cwd=ROOT, check=True).stdout
    assert out.splitlines() == ["tests/test_js_stock.py"]
