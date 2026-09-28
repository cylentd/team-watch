"""Every test builds against tests/fixtures, never against ff-jarvis: the inputs are pinned, so
a failure is a change in this repo, not in tonight's data.

    pytest tests/test_x.py     # the files for what you changed, seconds
    pytest -n auto --dist loadfile   # everything in parallel, about 65 s (serial about 195 s)
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


def pytest_collection_modifyitems(config, items):
    areas = {a for a in config.getoption("--areas").split(",") if a}
    if not areas:
        return
    keep, drop = [], []
    for item in items:
        marked = {a for m in item.iter_markers("area") for a in m.args}
        (keep if not marked or marked & areas else drop).append(item)
    if drop:
        config.hook.pytest_deselected(items=drop)
        items[:] = keep


@pytest.fixture(scope="session")
def update_golden(request):
    return request.config.getoption("--update-golden")


@pytest.fixture(scope="session")
def built():
    """One in-process build of the fixture page, shared by every test that needs it."""
    import build
    return build.render()


@pytest.fixture(scope="session")
def page_file(built, tmp_path_factory):
    p = tmp_path_factory.mktemp("page") / "index.html"
    p.write_text(built.page, encoding="utf-8")
    import build
    build.write_heads(p.parent)   # the page names heads by path, so they sit beside it as served
    return p
