"""Logic tested through the browser, and full page loads, as two ratchets (2026-10-05). The second
is described above FULL_LOADS below.

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
    "test_gameday.py": 4,
    "test_leagues.py": 1, "test_left_hurt.py": 9, "test_mates_page.py": 2,
    "test_search.py": 8, "test_startsit.py": 1, "test_waiver_owner.py": 6,
    "test_weather.py": 3,
    "pages/clips.py": 1, "pages/digest.py": 6, "pages/profile.py": 4, "pages/profile_head.py": 2,
    "pages/recap.py": 2, "pages/roster.py": 1, "pages/roster_pack.py": 1,
}   # 51 in all (2026-10-06: test_brief.py's schedWeek call now goes through RosterPage's, already counted).
# 52 before that. Superseded (later on 2026-10-06): the earlier "39 in all" missed 14 calls that had moved into
# tests/pages/, which this counter did not read until then; they are listed under pages/ now. Test files
# hold 35 of the 52 (Recap's 2 moved into pages/recap.py later that day). test_trade_edit's 33 moved to tests/test_js_trade_score.py (Node) on 2026-10-05


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
    """tests/pages/ is read too, keyed "pages/x.py": a call moved into a page object is still a call."""
    call = re.compile(r"\b(" + "|".join(sorted(pure_data_functions())) + r")\s*\(")
    out = {}
    for p in sorted(TESTS.glob("test_*.py")) + sorted((TESTS / "pages").glob("*.py")):
        n = sum(len(call.findall(s)) for s in evaluated_js(p))
        if n:
            out[p.relative_to(TESTS).as_posix()] = n
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


# ---- Full page loads, as a ratchet (2026-10-05) ----
#
# A test of one view mounts it (tests/component.py: the view's own page, a kept context, ~53 ms) instead
# of loading the whole page into a new context (~148 ms, measured 2026-10-05). Every place a test file
# loads the full page is counted: a `.goto(` call, or a call of a loader, a function in tests/ whose body
# calls `.goto(` or another loader (open_at, open_page, startsit_page.open_view, a file's own helper).
# The call inside a loader's own body is its implementation and is not counted; tests/component.py is
# the component layer, not a full page, and is never read. The counts below are today's and only go
# down; a new file has none. Move a one-view test to `mount` and lower its file's number.
# A loader call inside a test marked `@pytest.mark.journey` (navigation, hash, Back, cross-view: it needs
# the full page) is not counted, in any file; a helper's loads count where the helper is called.
FULL_LOADS = {
    "test_accuracy_view.py": 4, "test_claude_calls.py": 1, "test_claude_record.py": 1,
    "test_clip_sheet.py": 2,
    "test_gameday.py": 5, "test_gestures.py": 1, "test_highlights.py": 1,
    "test_leagues.py": 6, "test_left_hurt.py": 4, "test_legsheet.py": 6, "test_live_mine.py": 6,
    "test_live_modal.py": 5, "test_live_swipe.py": 2,
    "test_mates_page.py": 2, "test_news_tab.py": 2,
    "test_preview.py": 3, "test_profile_journeys.py": 1, "test_prop_picks.py": 1,
    "test_range_view.py": 1, "test_render.py": 10,
    "test_render_connect.py": 3, "test_role.py": 1, "test_roster_sheet.py": 5,
    "test_scope.py": 1, "test_search.py": 4, "test_startsit.py": 1,
    "test_startsit_v3.py": 1, "test_style_rules.py": 2,
    "test_teamswitch.py": 6, "test_top_calls.py": 1,
    "test_waiver_owner.py": 5, "test_weather.py": 5, "test_yahoo_lineup.py": 2,
}   # 101 in all (2026-10-06: test_sos_view.py's 8 and test_brief.py's 7 moved to `mount` with pages/schedule.py and
# pages/roster_brief.py; 2 Schedule nav tests stay as journeys); 116 before (test_live_tds.py's 6 and test_gamesheet_v2.py's 6 moved to `mount` with pages/live_tds.py
# and pages/gamesheet.py, the 128 below);
# 128 before that (2026-10-06: test_live_tabs.py's 10 moved to `mount` with pages/live_tabs.py, the 138 below);
# 138 before that (2026-10-06: test_teams_board.py's 12 moved to `mount` with pages/teams.py, the 150 below);
# 150 before that (2026-10-06: test_trade_edit.py (20) and test_trade_offers.py (17) moved to `mount` with the trade finder;
# 187 before it, after the second wave: clip reel, pack stage, Recap and the Digest's
# live tests moved to `mount`); 240 earlier that day (profile, Digest, roster cards, Bets, strip and TD clips;
# test_profile_journeys.py's 1 is the shared page its journey tests use); test_ranks.py's 4 and 4 of test_ranks_dst.py's 6 moved to `mount` on 2026-10-05, its
# other 2 are `journey` tests (Waivers link, another view), which the count skips
NOT_FULL = {"component.py"}


def _calls(node):
    return [n for n in ast.walk(node) if isinstance(n, ast.Call)]


def _helpers(tree):
    """Functions a test calls by name: not a test, not a fixture (pytest calls those, and a fixture's
    load is counted where it is written)."""
    def fixture(f):
        return any("fixture" in ast.dump(d) for d in f.decorator_list)
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("test_") and not fixture(n)]


def _journeys(tree):
    """Test functions marked `@pytest.mark.journey`: they need the full page, so their loads are free."""
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(isinstance(d, ast.Attribute) and d.attr == "journey" for d in n.decorator_list)]


def _known(tree, trees, found, own):
    """What loads the full page when called in this module: bare names (its own loaders and the ones it
    imports by name from another tests/ module) and module aliases with their loaders."""
    bare, attrs = set(own), {}
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module in trees:
            bare |= {a.asname or a.name for a in n.names if a.name in found[n.module]}
        elif isinstance(n, ast.Import):
            attrs.update({a.asname or a.name: found[a.name] for a in n.names if a.name in trees})
    return bare, attrs


def _loads(call, bare, attrs):
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr == "goto" or (isinstance(f.value, ast.Name) and f.attr in attrs.get(f.value.id, ()))
    return isinstance(f, ast.Name) and f.id in bare


def full_loads(sources):
    """{test file: full page loads} over {file name: source}; a loader's own body is not counted."""
    trees = {name[:-3].replace("/", "."): ast.parse(src) for name, src in sources.items() if name not in NOT_FULL}
    found = {m: set() for m in trees}
    while True:                          # loaders call goto or another loader, across imports
        grew = False
        for m, tree in trees.items():
            bare, attrs = _known(tree, trees, found, found[m])
            for f in _helpers(tree):
                if f.name not in found[m] and any(_loads(c, bare, attrs) for c in _calls(f)):
                    found[m].add(f.name)
                    grew = True
        if not grew:
            break
    out = {}
    for m, tree in trees.items():
        if not m.startswith("test_"):
            continue
        bare, attrs = _known(tree, trees, found, found[m])
        inside = {id(c) for f in _helpers(tree) if f.name in found[m] for c in _calls(f)}
        inside |= {id(c) for f in _journeys(tree) for c in _calls(f)}
        n = sum(1 for c in _calls(tree) if id(c) not in inside and _loads(c, bare, attrs))
        if n:
            out[m + ".py"] = n
    return out


def full_load_counts():
    """tests/pages/ is read too: a loader moved into a page object (`from pages.x import loader`) still
    counts where a test calls it."""
    files = sorted(TESTS.glob("*.py")) + sorted((TESTS / "pages").glob("*.py"))
    return full_loads({p.relative_to(TESTS).as_posix(): p.read_text(encoding="utf-8") for p in files})


def test_the_full_load_counter_sees_helpers_and_skips_their_bodies():
    src = {
        "helper.py": "def open_x(b, f):\n    p = b.new_page()\n    p.goto(f)\n    return p\n",
        "test_a.py": ("from helper import open_x\ndef load(b, f):\n    return open_x(b, f)\n"
                      "def test_1(b, f):\n    load(b, f)\n    load(b, f)\n"
                      "def test_2(b, f, page):\n    page.goto(f)\n    pages.get(1, lambda: open_x(b, f))\n"),
        "test_b.py": "def test_3(mount):\n    mount('ranks')\n    open('x')\n",
        "component.py": "def mount(page, u):\n    page.goto(u)\n",
    }
    assert full_loads(src) == {"test_a.py": 4}, "two load() calls, one goto, one open_x; mount is no full load"


def test_a_journey_test_may_load_the_full_page_free():
    src = {"test_j.py": ("import pytest\n@pytest.mark.journey\ndef test_1(p):\n    p.goto(1)\n    p.goto(2)\n"
                         "@pytest.mark.render\n@pytest.mark.journey\ndef test_2(p):\n    p.goto(1)\n"
                         "def test_3(p):\n    p.goto(1)\n")}
    assert full_loads(src) == {"test_j.py": 1}, "only the unmarked test counts"


def test_full_page_loads_only_go_down():
    over = {f: (n, FULL_LOADS.get(f, 0)) for f, n in full_load_counts().items() if n > FULL_LOADS.get(f, 0)}
    assert over == {}, ("file: (now, allowed). A test that needs the whole page (navigation, hash, Back) "
                        "is marked @pytest.mark.journey (tests/README.md); otherwise a test of one view mounts it "
                        "instead (tests/component.py)")


def test_the_full_load_counts_are_current():
    """A file that moved tests to `mount` lowers its number here, so the ratchet keeps the progress."""
    now = full_load_counts()
    stale = {f: (now.get(f, 0), n) for f, n in FULL_LOADS.items() if now.get(f, 0) < n}
    assert stale == {}, f"file: (now, listed). Lower these in FULL_LOADS: {stale}"
