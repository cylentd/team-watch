"""A test that passes must mean something: no hardcoded waits, no silent skips (2026-10-05).

A fixed wait (wait_for_timeout, time.sleep, a setTimeout the test awaits) is a guess about how long
something takes: too short and the test flakes on a busy machine, too long and every run pays for it.
A test waits for the condition it needs instead (CLAUDE.md, "Writing a browser test"). David,
2026-10-05: "hardcoded waits are really bad in test frameworks."

A skipped test prints as an "s" among the dots and is read as a pass. A skip is allowed only when the
machine lacks a tool (node, PowerShell, an ff-jarvis checkout), never because the fixture lacks the
data: that is an assert, or the test plants the data itself.
"""
import pathlib
import re

TESTS = pathlib.Path(__file__).resolve().parent
SELF = pathlib.Path(__file__).name

# wait_for_timeout, any sleep() (time., asyncio., or bare), and a Promise the test awaits around a
# setTimeout, however its arrow is spelled: `r => setTimeout(`, `(r) => { setTimeout(`, on one line.
WAIT = re.compile(r"wait_for_timeout\(|\bsleep\(|new Promise\(\s*\(?\s*\w+\s*\)?\s*=>\s*\{?\s*setTimeout\(")
SKIP = re.compile(r"pytest\.skip\(|skipif\(|mark\.skip\b|importorskip\(|\bxfail\(")
# wait_for_function returns at once when the predicate returns a Promise (an object is truthy) and
# never re-checks it, so the condition it seems to wait for is never waited for.
PROMISE_WAIT = re.compile(r"wait_for_function\(\s*(?:f?\"\"\"|f?\")[^\n]*new Promise")

# Not fixed waits, though they match the pattern: a setTimeout inside a JS stub that stands for
# network latency (nothing waits on its length), and the interval of a loop that polls for a
# condition until a deadline. file -> how many such lines it holds.
LATENCY_STUBS = {
    "test_left_hurt.py": 1,       # gsFetchSummary's stub takes 5 ms, so two requests could overlap
    "test_land_queue.py": 1,      # 50 ms between looks for the first lander's ticket file, 30 s deadline
}

# file -> (skips, why). Each is about the machine, or about a mode of the run, never the fixture.
ENV_SKIPS = {
    "test_dfs_backtest.py": (1, "node"),
    "test_dfs_solver.py": (1, "node"),
    "test_js_syntax.py": (1, "node"),
    "test_land_queue.py": (1, "PowerShell"),
    "test_leagues.py": (1, "an ff-jarvis checkout beside team-watch"),
    "test_sources_behind.py": (2, "an ff-jarvis checkout, and one new enough"),
    "test_yt_channels.py": (1, "an ff-jarvis checkout"),
    "test_render.py": (1, "--update-golden: the golden was just written, so there is nothing to compare"),
}


def found(pattern):
    out = {}
    for p in sorted(TESTS.glob("*.py")):
        if p.name == SELF:
            continue
        n = sum(1 for line in p.read_text(encoding="utf-8").splitlines() if pattern.search(line))
        if n:
            out[p.name] = n
    return out


def test_no_test_waits_a_fixed_time():
    over = {f: n for f, n in found(WAIT).items() if n > LATENCY_STUBS.get(f, 0)}
    assert over == {}, ("file: fixed waits. Wait for the condition instead: an expect(), "
                        "wait_for_function, wait_for_selector, or the page's clock (VCLOCK)")


def test_no_wait_for_function_returns_a_promise():
    assert found(PROMISE_WAIT) == {}, "wait_for_function needs a plain predicate; keep state on window to compare frames"


def test_the_patterns_catch_the_forms_that_have_been_written():
    for line in ("page.wait_for_timeout(500)", "time.sleep(0.2)", "await asyncio.sleep(1)",
                 'page.evaluate("new Promise(r => setTimeout(r, 450))")',
                 'page.evaluate("new Promise((r) => { setTimeout(() => { gsPaint(); r(); }, 0) })")'):
        assert WAIT.search(line), line
    assert not WAIT.search("await new Promise(r => requestAnimationFrame(r))")
    for line in ("@pytest.mark.skip(reason='x')", "pytest.importorskip('numpy')", "pytest.xfail('x')"):
        assert SKIP.search(line), line
    assert PROMISE_WAIT.search('page.wait_for_function("""(s) => new Promise(done => {')


def test_skips_are_about_the_machine_only():
    over = {f: n for f, n in found(SKIP).items() if n > ENV_SKIPS.get(f, (0,))[0]}
    assert over == {}, "file: skips. A fixture that lacks data is an assert, or the test plants the data"


def test_the_allowances_are_current():
    """An allowance nobody uses any more is removed, so it cannot quietly cover a new one."""
    waits, skips = found(WAIT), found(SKIP)
    stale = {f: (waits.get(f, 0), n) for f, n in LATENCY_STUBS.items() if waits.get(f, 0) < n}
    stale |= {f: (skips.get(f, 0), n) for f, (n, _) in ENV_SKIPS.items() if skips.get(f, 0) < n}
    assert stale == {}, f"file: (now, allowed). Lower or remove: {stale}"
