"""A broken page must not leak browser contexts (2026-10-05).

A branch declared one top-level function twice, the page's script threw a SyntaxError at load, and a
serial `pytest --update-golden` failed nearly every browser test. Each failure left its context open:
one Chromium grew to 6.5 GB with ~300 renderers. conftest.py now gives every context an owner (`keep`).

This runs a small suite in a pytest session of its own (in this process, on the worker's Chromium, so
it pays no launch), on this repo's conftest, against a page whose script does not parse, in the four
shapes that leaked: a module's shared page (SharedPages), a module fixture whose setup fails after
opening, a test whose helper fails inside the load, and a test that fails after opening. Its last
test asserts nothing is left open and each shared page opened once."""
import sys
import types

import pytest

from conftest import REPO

pytest_plugins = ["pytester"]

N = 3    # per shape; a leak is caught by the check's final "nothing open", so N needs no more than the bound's 6 across shapes

INNER_CONFTEST = f"""
import importlib.util, sys, types
import pytest
# This run's failures are planted: kept out of the suite's run history (tests/runlog.py).
sys.modules["runlog"] = types.SimpleNamespace(register=lambda config: None)
spec = importlib.util.spec_from_file_location("tw_conftest", r"{REPO / 'tests' / 'conftest.py'}")
mod = importlib.util.module_from_spec(spec)
sys.modules["tw_conftest"] = mod
spec.loader.exec_module(mod)
globals().update({{k: v for k, v in vars(mod).items() if not k.startswith("__")}})


@pytest.fixture(scope="session")
def browser():
    # The outer run's Chromium: a launch of its own is the slowest part of this test. Contexts the outer
    # run holds open are the baseline the check compares with.
    b = sys.modules["tw_outer"].browser
    mod._PW["browser"] = b
    mod.BASELINE = list(b.contexts)
    yield b
    mod._PW["browser"] = None
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
    if not page.evaluate("document.getElementById('view').children.length > 0"):
        raise TimeoutError("the view never drew")     # what the suite's wait_for_function raises, without the wait
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
import tw_conftest
from tw_conftest import open_contexts
from test_a_broken import N, OPENED


def test_nothing_is_left_open(browser):
    assert {k: OPENED.count(k) for k in set(OPENED)} == {"shared": 1, "eager": 1, "own": N, "after": N}
    assert open_contexts() == tw_conftest.BASELINE
"""


@pytest.mark.render
def test_failing_tests_on_a_broken_page_leave_no_context_open(browser, pytester):
    sys.modules["tw_outer"] = types.SimpleNamespace(browser=browser)     # read by INNER_CONFTEST's browser
    pytester.makeconftest(INNER_CONFTEST)
    (pytester.path / "broken.html").write_text(
        "<div id='view'></div><script>function draw() {} function draw( { let x = ; }</script>", encoding="utf-8")
    pytester.makepyfile(test_a_broken=BROKEN, test_z_check=CHECK)
    run = pytester.runpytest_inprocess("-p", "no:cacheprovider")
    # Every broken test fails, the eager fixture's tests error in setup, none errors in teardown (the
    # bound), and the check passes.
    assert run.parseoutcomes() == {"passed": 1, "failed": 3 * N, "errors": N}, run.stdout.str()[-3000:]
