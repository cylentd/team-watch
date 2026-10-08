"""scripts/mutate_tests.py picks tests by what their code does, not what their prose says (2026-10-08).

Three lands failed the mutation gate at 0-48% with every test green: a docstring saying "no browser" hid a
light file (navmap.js), and a docstring or comment naming a module counted as a test of it (ranks.py,
sources.py). The sibling test_mutate_tests.py is frozen; these are the new cases.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import mutate_tests  # noqa: E402

JS = "design/src/js/data/zq.js"
PY = "design/zqmod.py"


def _suite(root, files):
    (root / "tests").mkdir(exist_ok=True)
    for name, text in files.items():
        (root / "tests" / name).write_text(text, encoding="utf-8")


def test_a_docstring_saying_no_browser_does_not_make_a_light_file_heavy(tmp_path):
    _suite(tmp_path, {
        "test_js_zq.py": '"""Pure data, no browser."""\ndef test_a():\n    node_js("data/zq.js")\n',
        "test_js_zq_other.py": 'def test_b():\n    node_js("data/zq.js")\n',
        "test_view_zq.py": 'def test_c(browser):\n    "data/zq.js"\n',
    })
    assert mutate_tests.tests_for(JS, tmp_path) == ["tests/test_js_zq.py", "tests/test_js_zq_other.py"]


def test_a_comment_saying_mount_does_not_make_a_light_file_heavy(tmp_path):
    _suite(tmp_path, {
        "test_zqmod.py": "import zqmod\n# never mount the page here\ndef test_a():\n    zqmod.f()\n",
        "test_zqmod_view.py": "import zqmod\ndef test_b(browser):\n    pass\n",
    })
    assert mutate_tests.tests_for(PY, tmp_path) == ["tests/test_zqmod.py"]


def test_every_light_file_that_names_the_source_is_kept(tmp_path):
    _suite(tmp_path, {
        "test_zqmod_a.py": "import zqmod\n",
        "test_zqmod_b.py": "from zqmod import f\n",
        "test_zqmod_c.py": "import zqmod\n",
    })
    assert mutate_tests.tests_for(PY, tmp_path) == [
        "tests/test_zqmod_a.py", "tests/test_zqmod_b.py", "tests/test_zqmod_c.py"]


def test_a_light_file_that_only_mentions_the_module_in_prose_does_not_hide_the_heavy_one_that_imports_it(tmp_path):
    _suite(tmp_path, {
        "test_prose.py": '"""Checks the rows that zqmod.py draws."""\n# see zqmod.py\ndef test_a():\n    pass\n',
        "test_zqmod_view.py": "import zqmod\ndef test_b(browser):\n    zqmod.f()\n",
    })
    assert mutate_tests.tests_for(PY, tmp_path) == ["tests/test_zqmod_view.py"]


def test_a_file_that_does_not_parse_still_gets_judged_by_its_text(tmp_path):
    _suite(tmp_path, {"test_zqmod_bad.py": "import zqmod\ndef (:\n    browser\n"})
    assert mutate_tests.tests_for(PY, tmp_path) == ["tests/test_zqmod_bad.py"]
