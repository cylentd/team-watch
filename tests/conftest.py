"""Every test builds against tests/fixtures, never against ff-jarvis: the inputs are pinned, so
a failure is a change in this repo, not in tonight's data.

    pytest                     # everything, about 5 s
    pytest -m "not render"     # no browser, under a second
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
    return p
