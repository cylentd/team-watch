"""Every test builds against tests/fixtures, never against ff-jarvis: the inputs are pinned, so
a failure is a change in this repo, not in tonight's data.

    pytest tests/test_x.py     # the files for what you changed, seconds
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


CHUNK = 12   # tests per xdist group outside the golden slices


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
    # - test_render.py's golden slice per area: the snapshot (a page per state, both viewports) is
    #   taken once and read by four tests. These are the longest units of work, so they go to the
    #   front of the queue; started last, alphabetically, they ran on after everything else.
    # - every other file in runs of CHUNK tests, so a module-scoped page is loaded once per run, and
    #   a long file still spreads over several workers. Until 2026-10-05 each file was one group,
    #   and test_profile.py's 58 browser tests took 67 s on one worker while the other 19 sat idle;
    #   with no groups at all every worker that drew one test loaded the file's shared pages.
    # Runs before xdist's hook, which is the one that reads the marker.
    slices, seen = [], {}
    for item in items:
        area = next((m.args[0] for m in item.iter_markers("area")), None)
        if area and item.path.name == "test_render.py" and "snapshot" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.xdist_group(f"render:{area}"))
            slices.append(item)
        else:
            n = seen[item.path.name] = seen.get(item.path.name, -1) + 1
            item.add_marker(pytest.mark.xdist_group(f"{item.path.name}#{n // CHUNK}"))
    if slices:
        first = set(map(id, slices))
        items[:] = slices + [i for i in items if id(i) not in first]


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


@pytest.fixture(scope="session")
def page_file(built, tmp_path_factory):
    p = tmp_path_factory.mktemp("page") / "index.html"
    p.write_text(built.page, encoding="utf-8")
    import build
    build.write_heads(p.parent)   # the page names heads by path, so they sit beside it as served
    return p
