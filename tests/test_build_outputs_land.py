"""S2: `main` carries a current build. The build runs at land time, after the tests, so the committed
pages cannot be compared with the sources here. What can be proved: every path design/build.py main()
writes is one scripts/land.ps1 folds into the landed commit (and .testsched.json tolerates as dirty), and
build.json is the hash of the data the page carries, so a rebuild with unchanged data changes nothing."""
import json
import re
import shutil

import pytest

import build
from conftest import REPO

pytestmark = pytest.mark.integration      # one real build() run writing files


@pytest.fixture(scope="module")
def written(tmp_path_factory):
    """The top-level names build.main() creates under a throwaway repo root, and its build.json."""
    root = tmp_path_factory.mktemp("repo")
    tokens = root / "design" / "src" / "css" / "base"      # the one source file build.py reads through ROOT
    tokens.mkdir(parents=True)
    shutil.copy(build.ROOT / "src" / "css" / "base" / "tokens.css", tokens)
    shutil.copytree(build.REPO / "icons", root / "icons")      # the favicon the page head inlines
    saved = build.REPO, build.ROOT
    build.REPO, build.ROOT = root, root / "design"
    try:
        build.main()
    finally:
        build.REPO, build.ROOT = saved
    return root


def folded_by_land():
    """The $generated array in scripts/land.ps1: what the fold stages after the build."""
    text = (REPO / "scripts" / "land.ps1").read_text(encoding="utf-8")
    body = re.search(r"\$generated = @\((.*?)\)", text, re.S).group(1)
    return re.findall(r'"([^"]+)"', body)


def test_every_file_the_build_writes_is_folded_by_the_land(written):
    folded = folded_by_land()
    files = [p.relative_to(written).as_posix() for p in written.rglob("*") if p.is_file() and not {"src", "icons"} & set(p.parts)]   # src, icons: copied in as inputs
    unfolded = [f for f in files if not any(f == g or f.startswith(g + "/") for g in folded)]
    assert unfolded == [], f"the build writes {unfolded}, which land.ps1 would leave out of the landed commit"


def test_the_testsched_land_tolerates_exactly_what_land_ps1_folds():
    conf = json.loads((REPO / ".testsched.json").read_text(encoding="utf-8"))
    assert sorted(conf["dirty_ok"]) == sorted(folded_by_land())


def test_both_pages_and_the_stamp_are_written(written):
    assert (written / "index.html").read_text(encoding="utf-8").startswith("<!doctype html>")
    assert (written / "design" / "index.html").is_file()
    assert set(json.loads((written / "build.json").read_text(encoding="utf-8"))) == {"id", "week"}


def test_the_stamp_is_the_pages_own_data_hash(written, built):
    stamp = json.loads((written / "build.json").read_text(encoding="utf-8"))
    assert stamp == built.stamp
    assert f"const BUILD = {json.dumps(stamp)};" in (written / "index.html").read_text(encoding="utf-8")


def test_the_film_edition_is_folded_as_generated_build_output():
    assert "showcase/madden-curse/edition.json" in folded_by_land()
