"""Every test builds against tests/fixtures, never against ff-jarvis: the inputs are pinned, so
a failure is a change in this repo, not in tonight's data.

    pytest tests/test_x.py     # the files for what you changed, seconds
    pytest tests/test_js_*.py  # the JS unit layer, in Node: no build, no browser, under a second
    pytest -n auto --dist loadgroup  # everything in parallel, about 50 s (serial about 200 s)
    pytest -m "not render"     # no browser, about 30 s
    pytest --update-golden     # rewrite tests/golden/render.json after an intended visual change
"""
import os
import pathlib
import sys

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


def pytest_configure(config):
    config.addinivalue_line("markers", "area(name): the impact area a test covers (scripts/impact.py)")
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
    if "browser" in names:
        return "browser"
    if names & {"built", "page_file"}:
        return "build"
    return "node" if "node_js" in names else "python"


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
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
    the last test changed and checks the page raised no error while loading."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


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
    return p
