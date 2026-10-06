"""A broken page must not leak browser contexts (2026-10-05).

A branch declared one top-level function twice, the page's script threw a SyntaxError at load, and a
serial `pytest --update-golden` failed nearly every browser test. Each failure left its context open:
one Chromium grew to 6.5 GB with ~300 renderers. conftest.py now gives every context an owner (`keep`).

This runs a small suite in its own pytest process, on this repo's conftest, against a page whose
script does not parse, in the four shapes that leaked: a module's shared page (SharedPages), a module
fixture whose setup fails after opening, a test whose helper fails inside the load, and a test that
fails after opening. Its last test asserts nothing is left open and each shared page opened once."""
import re
import subprocess
import sys

import pytest

from conftest import REPO

N = 8

INNER_CONFTEST = f"""
import importlib.util, sys, types
# This run's failures are planted: kept out of the suite's run history (tests/runlog.py).
sys.modules["runlog"] = types.SimpleNamespace(register=lambda config: None)
spec = importlib.util.spec_from_file_location("tw_conftest", r"{REPO / 'tests' / 'conftest.py'}")
mod = importlib.util.module_from_spec(spec)
sys.modules["tw_conftest"] = mod
spec.loader.exec_module(mod)
globals().update({{k: v for k, v in vars(mod).items() if not k.startswith("__")}})
"""

BROKEN = """
import pathlib
import pytest
from tw_conftest import SharedPages

N = {n}
URL = (pathlib.Path(__file__).parent / "broken.html").as_uri()
OPENED = []


def open_broken(browser, what):
    # The shape of the suite's page helpers: open, load, wait for the view, return (ctx, page, errors).
    OPENED.append(what)
    ctx = browser.new_context()
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_function("document.getElementById('view').children.length > 0", timeout=200)
    return ctx, page, errors


@pytest.fixture(scope="module")
def shared_pages(browser):
    pages = SharedPages()
    yield lambda: pages.get("phone", lambda: open_broken(browser, "shared"))
    pages.close()


@pytest.fixture(scope="module")
def eager(browser):
    ctx, page, errors = open_broken(browser, "eager")
    yield page
    ctx.close()


@pytest.mark.parametrize("i", range(N))
def test_shared(shared_pages, i):
    shared_pages()


@pytest.mark.parametrize("i", range(N))
def test_eager(eager, i):
    pass


@pytest.mark.parametrize("i", range(N))
def test_own_load_fails(browser, i):
    open_broken(browser, "own")


@pytest.mark.parametrize("i", range(N))
def test_own_assert_fails(browser, i):
    OPENED.append("after")
    browser.new_context().new_page()
    assert False, "fails with its page open"
""".format(n=N)

CHECK = """
from tw_conftest import open_contexts
from test_a_broken import N, OPENED


def test_nothing_is_left_open(browser):
    assert {k: OPENED.count(k) for k in set(OPENED)} == {"shared": 1, "eager": 1, "own": N, "after": N}
    assert open_contexts() == []
"""


@pytest.mark.render
def test_failing_tests_on_a_broken_page_leave_no_context_open(tmp_path):
    (tmp_path / "conftest.py").write_text(INNER_CONFTEST, encoding="utf-8")
    (tmp_path / "broken.html").write_text(
        "<div id='view'></div><script>function draw() {} function draw( { let x = ; }</script>", encoding="utf-8")
    (tmp_path / "test_a_broken.py").write_text(BROKEN, encoding="utf-8")
    (tmp_path / "test_z_check.py").write_text(CHECK, encoding="utf-8")
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:xdist",
                          str(tmp_path)],
                         cwd=tmp_path, capture_output=True, text=True, timeout=120)
    out = run.stdout + run.stderr
    counts = {k: int(n) for n, k in re.findall(r"(\d+) (passed|failed|errors?)\b", out)}
    counts["error"] = counts.pop("errors", 0) + counts.pop("error", 0)
    # Every broken test fails, the eager fixture's tests error in setup, none errors in teardown (the
    # bound), and the check passes.
    assert counts == {"passed": 1, "failed": 3 * N, "error": N}, out[-3000:]
