"""scripts/impact.py (2026-09-27): land runs the tests a diff can break, not all of them. These keep
tests/impact.json honest: a test file no area lists would only ever run in the full suite."""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import impact  # noqa: E402

CFG, SCOPE = impact.load()
AREAS = CFG["areas"]


def test_every_test_file_is_listed_once():
    listed = CFG["core"] + list(CFG["full_only"]) + [t for a in AREAS.values() for t in a["tests"]]
    on_disk = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_*.py"))
    assert sorted(set(listed)) == on_disk
    assert len(listed) == len(set(listed)), "a test file is listed twice"


def test_every_path_exists_and_has_one_owner():
    claimed = [p for a in AREAS.values() for p in a["paths"]]
    assert len(claimed) == len(set(claimed))
    for p in claimed:
        assert (ROOT / p).is_dir() if p.endswith("/") else (ROOT / p).is_file(), p
    for p in claimed:
        others = [q for q in claimed if q != p and q.endswith("/") and p.startswith(q)]
        assert not others, f"{p} sits inside {others}"


def test_the_render_areas_are_the_goldens():
    import test_render
    mapped = [r for a in AREAS.values() for r in a["render"]]
    assert sorted(mapped) == sorted(set(mapped)) == test_render.AREAS


@pytest.mark.parametrize("paths,want", [
    (["design/src/css/surface/ranks/ranks.css"], {"all": False, "areas": ["ranks"], "extra": ["tests/test_ranks.py", "tests/test_render.py"]}),
    (["design/ranks.py", "README.md"], {"all": False, "areas": ["ranks"], "extra": ["tests/test_ranks.py", "tests/test_render.py"]}),
    (["tests/test_ranks.py"], {"all": False, "areas": [], "extra": ["tests/test_ranks.py"]}),
    (["CLAUDE.md"], {"all": False, "areas": [], "extra": []}),
    (["scripts/land.ps1"], {"all": False, "areas": [], "extra": ["tests/test_land_queue.py"]}),
    (["design/src/css/surface/strip/panel.css"], {"all": True}), # shared CSS styles any view
    (["design/src/css/component/pool.css"], {"all": True}),      # so does a component
    (["design/src/js/chrome/nav.js"], {"all": True}),            # no area owns chrome
    (["design/build.py"], {"all": True}),
    (["tests/conftest.py"], {"all": True}),
    (["tests/golden/render.json"], {"all": True}),
])
def test_select(paths, want):
    got = impact.select(paths, CFG, SCOPE)
    assert got["all"] == want["all"], got["why"]
    if not want["all"]:
        assert got["areas"] == want["areas"]
        assert got["files"] == sorted(set(CFG["core"] + want["extra"]))


def test_every_fenced_css_file_has_an_area():
    for rel in SCOPE["fenced"]:
        path = impact.CSS_SURFACE + rel[len("surface/"):]
        assert not impact.select([path], CFG, SCOPE)["all"], path


def test_the_cli_prints_json(capsys):
    impact.main(["--paths", "design/ranks.py"])
    assert json.loads(capsys.readouterr().out)["areas"] == ["ranks"]
