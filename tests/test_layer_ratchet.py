"""Logic tested through the browser, as a ratchet (2026-10-05).

A function in design/src/js/data/ that touches no browser API is data to data: its test belongs in
Node (tests/jsunit.py), where it costs a millisecond, not in a page.evaluate on a built page, where
the file pays for a build and a page load first. On 2026-10-05 the browser held 27% of the tests and
92% of the worker time. Every page.evaluate that calls such a function is counted per test file; the
counts below are what was there when the ratchet was set and may only go down. A new test file has
none. Move a test to Node and lower its file's number, or the next test fails and asks you to.

What counts: a call `name(` inside a string handed to `.evaluate(` (directly, or through a module
constant such as PLANT), where `name` is a top-level function of a data/ file that never mentions
document, window, localStorage or fetch. A render trigger (render(), paintLive()) is a surface
function and is not counted: a test that renders and then reads the DOM is a browser test.
"""
import ast
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "design" / "src" / "js" / "data"
TESTS = ROOT / "tests"
BROWSER_API = re.compile(r"\b(document|window|localStorage|sessionStorage|fetch)\b")
COMMENT = re.compile(r"/\*.*?\*/|(?:^|(?<=\s))//[^\n]*", re.S)     # "kickoff window" in a comment is no API
TOP = re.compile(r"^(?:async )?function (\w+)\(|^(?:const|let) (\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*=>", re.M)

# Calls of pure data/ functions through the browser, per test file, 2026-10-05. Only shrinks.
BACKLOG = {
    "test_brief.py": 1, "test_clip_reel.py": 1, "test_digest.py": 16, "test_gameday.py": 4,
    "test_leagues.py": 1, "test_left_hurt.py": 9, "test_live_tdclips.py": 13, "test_mates_page.py": 2,
    "test_pack_stage.py": 1, "test_profile.py": 6, "test_recap_view.py": 2, "test_roster_cards.py": 1,
    "test_search.py": 8, "test_startsit.py": 1, "test_waiver_owner.py": 6,
    "test_weather.py": 3,
}   # 75 in all; test_trade_edit's 33 moved to tests/test_js_trade_score.py (Node) on 2026-10-05


def pure_data_functions():
    names = set()
    for p in DATA.rglob("*.js"):
        src = p.read_text(encoding="utf-8")
        if not BROWSER_API.search(COMMENT.sub("", src)):
            names.update(a or b for a, b in TOP.findall(src))
    return names


def strings_in(node):
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def evaluated_js(path):
    """Every string a test file hands to .evaluate(), module constants resolved."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    consts = {t.id: node.value for node in tree.body if isinstance(node, ast.Assign)
              for t in node.targets if isinstance(t, ast.Name)}
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "evaluate" and n.args:
            arg = n.args[0]
            out += strings_in(consts[arg.id] if isinstance(arg, ast.Name) and arg.id in consts else arg)
    return out


def counts():
    call = re.compile(r"\b(" + "|".join(sorted(pure_data_functions())) + r")\s*\(")
    out = {}
    for p in sorted(TESTS.glob("test_*.py")):
        n = sum(len(call.findall(s)) for s in evaluated_js(p))
        if n:
            out[p.name] = n
    return out


def test_the_pure_data_functions_are_found():
    names = pure_data_functions()
    assert {"gdHurtScan", "muGame", "ss3Graded"} <= names       # function, arrow, one-liner
    assert "lgLeagueSave" not in names                          # data/league.js reads localStorage


def test_the_counter_sees_a_call_through_a_constant(tmp_path):
    (tmp_path / "t.py").write_text('P = """(c) => { muGame(c) }"""\ndef f(page):\n    page.evaluate(P, 1)\n'
                                   '    page.evaluate(f"ss3Wl({1})")\n    page.evaluate("render()")\n', encoding="utf-8")
    strings = evaluated_js(tmp_path / "t.py")
    assert sum(len(re.findall(r"\b(muGame|ss3Wl|render)\(", s)) for s in strings) == 3


def test_no_new_logic_is_tested_through_the_browser():
    over = {f: (n, BACKLOG.get(f, 0)) for f, n in counts().items() if n > BACKLOG.get(f, 0)}
    assert over == {}, ("file: (now, allowed). A pure data/ function is called through page.evaluate; "
                        "test it in Node instead (tests/jsunit.py)")


def test_the_backlog_is_current():
    """A file that moved tests to Node lowers its number here, so the ratchet keeps the progress."""
    now = counts()
    stale = {f: (now.get(f, 0), n) for f, n in BACKLOG.items() if now.get(f, 0) < n}
    assert stale == {}, f"file: (now, listed). Lower these in BACKLOG: {stale}"
