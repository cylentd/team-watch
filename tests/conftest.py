"""Every test builds against tests/fixtures, never against ff-jarvis: the inputs are pinned, so
a failure is a change in this repo, not in tonight's data.

    pytest tests/test_x.py     # the files for what you changed, seconds
    pytest tests/test_js_*.py  # the JS unit layer, in Node: no build, no browser, under a second
    pytest -n auto --dist loadgroup  # everything in parallel, about 50 s (serial about 200 s)
    pytest -m "not render"     # no browser, about 30 s
    pytest --update-golden     # rewrite tests/golden/render.json after an intended visual change
"""
import contextlib
import os
import pathlib
import sys
import warnings

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
DESIGN = REPO / "design"
FIXTURES = REPO / "tests" / "fixtures"
GOLDEN = REPO / "tests" / "golden"

# build.py reads these at import, so they are set before anything imports it.
os.environ["TEAM_WATCH_DATA"] = str(FIXTURES / "data")
os.environ["TEAM_WATCH_HEADS"] = str(FIXTURES / "heads")
os.environ["TEAM_WATCH_FEED"] = str(FIXTURES / "feed.json")
sys.path.insert(0, str(DESIGN))


def pytest_addoption(parser):
    parser.addoption("--update-golden", action="store_true", default=False,
                     help="rewrite tests/golden/*.json from the current render")
    parser.addoption("--areas", default="",
                     help="comma-separated impact areas (tests/impact.json): a test marked "
                          "@pytest.mark.area runs only when its area is listed; unmarked tests always run")
    parser.addoption("--no-quarantine", action="store_true", default=False,
                     help="deselect tests marked @pytest.mark.quarantine (the land gate; tests/README.md)")


def pytest_configure(config):
    config.addinivalue_line("markers", "area(name): the impact area a test covers (scripts/impact.py)")
    config.addinivalue_line("markers", "req(section, ac=None): the design/DESIGN.md section (its `## ` "
                            "heading up to the first ` (`) this test proves, and which behaviour (scripts/trace.py)")
    config.addinivalue_line("markers", "quarantine(reason): a known-flaky test; --no-quarantine drops it "
                            "from a gating run, and scripts/trace.py lists it")
    config.addinivalue_line("markers", "journey: an end-to-end test that needs the full page: navigation, "
                            "hash, Back, cross-view (tests/test_layer_ratchet.py does not count its page loads)")
    config.addinivalue_line("markers", "xdist_group(name): set by the hook below; one group runs on one worker")
    if hasattr(config.option, "loadscopereorder"):
        config.option.loadscopereorder = False   # the order the hook below sets is the queue's order
    import runlog
    runlog.register(config)


CHUNK = 12   # tests per xdist group outside the golden slices

# The test layers, cheapest first (2026-10-05): python, node, build, browser. A test's layer is the
# costliest thing it asks for. tests/runlog.py prints each layer's tests and worker seconds at the
# end of a run (the layers line) and records the run in the test history (scripts/testlog.py).
def layer_of(item):
    names = set(getattr(item, "fixturenames", ()))
    if "mount" in names:        # a component test drives Chromium through `mount`, and stays a component test
        return "component"
    if "browser" in names:
        return "browser"
    if names & {"built", "page_file"}:
        return "build"
    return "node" if "node_js" in names else "python"


def rep_of(item):
    """The repetition index scripts/run_tests.py --repeat-new parametrizes a test with, else None."""
    return getattr(getattr(item, "callspec", None), "params", {}).get("_tw_rep")


def design_sections():
    """The `## ` headings of design/DESIGN.md, up to the first ` (`: what `req` may name."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tw_trace", REPO / "scripts" / "trace.py")
    mod = importlib.util.module_from_spec(spec)     # by path: `trace` is also a stdlib module
    spec.loader.exec_module(mod)
    return mod.design_sections()


def bad_reqs(items, sections):
    """(nodeid, section) for every `req` naming a section DESIGN.md does not have; a req with no
    section at all counts as one named None."""
    bad = []
    for item in items:
        for m in item.iter_markers("req"):
            section = m.args[0] if m.args else m.kwargs.get("section")
            if section not in sections:
                bad.append((item.nodeid, section))
    return bad


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    if any(item.get_closest_marker("req") for item in items):
        sections = design_sections()
        bad = bad_reqs(items, sections)
        if bad:
            raise pytest.UsageError(
                "req names a section design/DESIGN.md does not have:\n"
                + "\n".join(f"  {nodeid}: {section!r}" for nodeid, section in bad)
                + "\nvalid sections:\n" + "\n".join(f"  {s}" for s in sections))
    if config.getoption("--no-quarantine"):
        quarantined = [i for i in items if i.get_closest_marker("quarantine")]
        if quarantined:
            config.hook.pytest_deselected(items=quarantined)
            items[:] = [i for i in items if i not in quarantined]
    areas = {a for a in config.getoption("--areas").split(",") if a}
    if areas:
        keep, drop = [], []
        for item in items:
            marked = {a for m in item.iter_markers("area") for a in m.args}
            (keep if not marked or marked & areas else drop).append(item)
        if drop:
            config.hook.pytest_deselected(items=drop)
            items[:] = keep
    # `-n auto --dist loadgroup` (land.ps1) runs one group on one worker. Two kinds of group:
    # - test_render.py's golden slices (test_render.SLICES, at most 6 states each; the area mark's
    #   `slice`): the snapshot (a page per state, both viewports) is taken once and read by the
    #   slice's tests. These are the longest units of work, so they go to the front of the queue,
    #   the biggest first; started last, alphabetically, they ran on after everything else.
    #   xdist would reorder groups by test count (a slice of 6 states is 9 tests, behind every
    #   12-test run below), so pytest_configure turns that reordering off.
    # - every other file in runs of CHUNK tests, so a module-scoped page is loaded once per run, and
    #   a long file still spreads over several workers. Until 2026-10-05 each file was one group,
    #   and test_profile.py's 58 browser tests took 67 s on one worker while the other 19 sat idle;
    #   with no groups at all every worker that drew one test loaded the file's shared pages.
    # Runs before xdist's hook, which is the one that reads the marker.
    slices, seen = {}, {}
    for item in items:
        item.user_properties.append(("layer", layer_of(item)))
        mark = next(item.iter_markers("area"), None)
        if mark and item.path.name == "test_render.py" and "snapshot" in getattr(item, "fixturenames", ()):
            group = f"render:{mark.kwargs.get('slice', mark.args[0])}"
            item.add_marker(pytest.mark.xdist_group(group))
            slices.setdefault(group, []).append(item)
        elif rep_of(item) is not None:      # --tw-repeat: one group per repetition, so a test's runs split over workers
            item.add_marker(pytest.mark.xdist_group(f"rep{rep_of(item)}"))
        else:
            n = seen[item.path.name] = seen.get(item.path.name, -1) + 1
            item.add_marker(pytest.mark.xdist_group(f"{item.path.name}#{n // CHUNK}"))
    if slices:
        first = {id(i) for g in slices.values() for i in g}
        biggest = sorted(slices.values(), key=len, reverse=True)   # stable: ties keep their order
        items[:] = [i for g in biggest for i in g] + [i for i in items if id(i) not in first]


@pytest.fixture(scope="session")
def update_golden(request):
    return request.config.getoption("--update-golden")


@pytest.fixture(scope="session")
def built():
    """One in-process build of the fixture page, shared by every test that needs it."""
    import build
    return build.render()


@pytest.fixture(scope="session")
def browser():
    """One Chromium per worker for every browser test; the launch (about 1 s) is what is shared.
    A test opens its own context, or borrows its file's module-scoped page, which resets what
    the last test changed and checks the page raised no error while loading. Who closes each
    context is decided below (`keep`), not left to the test."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        # Every kickoff is written in the reader's own clock (design/src/js/lib/kick.js, 2026-10-05), so a
        # context with no zone would print the machine's. Pacific is David's, and the golden's.
        new_context = b.new_context
        b.new_context = lambda **kw: new_context(**{"timezone_id": "America/Los_Angeles", **kw})
        _PW["browser"] = b
        try:
            yield b
        finally:
            _PW["browser"] = None
            b.close()


# Every browser context has an owner, so a failure never strands one (2026-10-05). A page whose
# script broke made every test fail in setup, and each failure left its context open: one Chromium
# grew to 6.5 GB and ~300 renderers in 25 minutes, and an earlier run ran the machine out of memory.
# - A context opened while a module- or session-scoped fixture sets up belongs to that scope; one a
#   module opens later and shares (SharedPages) is kept for the module by `keep`.
# - Any other context belongs to the test that opened it, and is closed when the test ends however
#   the test ended (_pages_closed). A test that passed and still left one open gets a warning.
# - A kept context its module did not close is closed when the module ends (_module_pages_closed).
# - A setup that fails closes what it opened at once.
# After every test at most MAX_CONTEXTS contexts and MAX_PAGES pages may stay open, or the test
# errors in teardown. The suite keeps at most 3 contexts and 3 pages open between tests (measured
# 2026-10-05: test_digest_story.py's planted Digests), so twice that is headroom, not a leak.
MAX_CONTEXTS = 6
MAX_PAGES = 12
_PW = {"browser": None, "module": ""}
_KEPT = {}          # context -> owner: a module's (or class's) nodeid, "" for the session


def open_contexts():
    b = _PW["browser"]
    if b is None:
        return []
    try:
        return list(b.contexts)
    except Exception:       # the browser is gone: nothing of it is open
        return []


def _close(contexts):
    for c in contexts:
        try:
            c.close()
        except Exception:
            pass


@contextlib.contextmanager
def keep(owner=None):
    """Contexts opened inside the block outlive the test: they belong to `owner` (the running test's
    module by default), whose own teardown closes them. If the block raises they are closed at once."""
    before = set(open_contexts())
    try:
        yield
    except BaseException:
        _close([c for c in open_contexts() if c not in before])
        raise
    for c in open_contexts():
        if c not in before and c not in _KEPT:
            _KEPT[c] = _PW["module"] if owner is None else owner


class SharedPages:
    """A module's pages, opened once per key and shared: `pages.get(key, opener)` returns what
    opener() returned the first time (a tuple whose first item is the context). A failed open is
    remembered: every later test that asks for that key fails at once with the first error instead
    of opening, and stranding, a page of its own. `close()` in the module fixture's teardown."""

    def __init__(self):
        self.items, self.failed = {}, {}

    def get(self, key, opener):
        if key in self.failed:
            pytest.fail(f"the shared page {key!r} failed to open in an earlier test: {self.failed[key]}",
                        pytrace=False)
        if key not in self.items:
            try:
                with keep():
                    self.items[key] = opener()
            except BaseException as e:
                self.failed[key] = (f"{type(e).__name__}: {e}".strip().splitlines() or ["?"])[0][:300]
                raise
        return self.items[key]

    def values(self):
        return self.items.values()

    def close(self):
        _close([v[0] for v in self.items.values()])


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef, request):
    if fixturedef.scope == "function":
        return (yield)
    with keep(request.node.nodeid):
        return (yield)


_FAILED = pytest.StashKey[bool]()


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    if rep.failed:
        item.stash[_FAILED] = True
    return rep


@pytest.fixture(autouse=True)
def _pages_closed(request):
    """Close what the test opened and did not hand to its module, then hold the bound."""
    module = request.node.getparent(pytest.Module)
    _PW["module"] = module.nodeid if module else ""
    before = set(open_contexts())
    yield
    left = [c for c in open_contexts() if c not in before and c not in _KEPT]
    _close(left)
    if left and not request.node.stash.get(_FAILED, False):
        warnings.warn(f"{request.node.nodeid} left {len(left)} browser context(s) open; closed them",
                      pytest.PytestWarning)
    contexts = open_contexts()
    pages = sum(len(c.pages) for c in contexts)
    if len(contexts) > MAX_CONTEXTS or pages > MAX_PAGES:
        pytest.fail(f"{len(contexts)} browser contexts and {pages} pages are open after "
                    f"{request.node.nodeid} (bound {MAX_CONTEXTS} and {MAX_PAGES}): something keeps "
                    "opening pages it never closes", pytrace=False)


@pytest.fixture(scope="module", autouse=True)
def _module_pages_closed(request):
    """Torn down after the module's own fixtures: close what they kept and did not close."""
    yield
    mine = [c for c, owner in list(_KEPT.items()) if owner == request.node.nodeid]
    for c in mine:
        del _KEPT[c]
    still = set(open_contexts())
    left = [c for c in mine if c in still]
    _close(left)
    if left:
        warnings.warn(f"{request.node.nodeid} kept {len(left)} browser context(s) it never closed; closed them",
                      pytest.PytestWarning)


@pytest.fixture(scope="module")
def node_js():
    """node_js("data/x.js", ..., globals={...}) -> a callable sandbox of those files in Node, closed
    when the module ends. The JS unit layer: tests/jsunit.py says how to use it."""
    from jsunit import NodeJS
    opened = []

    def load(*files, globals=None):
        opened.append(NodeJS(*files, globals=globals))
        return opened[-1]
    yield load
    for js in opened:
        js.close()


@pytest.fixture(scope="session")
def page_file(built, tmp_path_factory):
    p = tmp_path_factory.mktemp("page") / "index.html"
    p.write_text(built.page, encoding="utf-8")
    import build
    build.write_heads(p.parent)   # the page names heads by path, so they sit beside it as served
    build.write_avatars(p.parent)  # and the team avatars the same way
    return p
