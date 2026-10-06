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
    # select() reads every tests/ path before the map, so a claim there would never take effect.
    assert not [p for p in claimed if p.startswith("tests/") and not p.startswith("tests/test_")]


def test_the_render_areas_are_the_goldens():
    import test_render
    mapped = [r for a in AREAS.values() for r in a["render"]]
    assert sorted(mapped) == sorted(set(mapped)) == test_render.AREAS


RANKS_TESTS = ["tests/test_ranks.py", "tests/test_ranks_dst.py", "tests/test_js_dst.py"]


@pytest.mark.parametrize("paths,want", [
    (["design/src/css/surface/ranks/ranks.css"], {"all": False, "areas": ["ranks"], "extra": RANKS_TESTS + ["tests/test_render.py"]}),
    (["design/ranks.py", "README.md"], {"all": False, "areas": ["ranks"], "extra": RANKS_TESTS + ["tests/test_render.py"]}),
    (["tests/test_ranks.py"], {"all": False, "areas": [], "extra": ["tests/test_ranks.py"]}),
    (["CLAUDE.md"], {"all": False, "areas": [], "extra": []}),
    (["scripts/land.ps1"], {"all": False, "areas": [], "extra": ["tests/test_land_queue.py", "tests/test_testlog.py"]}),
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


def test_a_fence_beyond_its_owner_adds_that_view():
    """The bet slip's CSS belongs to Bets but is fenced to Preview too, so Preview's slice runs."""
    path = impact.CSS_SURFACE + "builder/slip.css"
    assert "preview" in SCOPE["fenced"]["surface/builder/slip.css"]
    assert "preview" in impact.select([path], CFG, SCOPE)["areas"]


# ---- shared files, read by what changed inside them (2026-10-05) ----

SRC_TEXTS = [("design/src/js/surface/ranks/ranks.js", 'x(t("ranks.head.title"));\n'),
             ("design/src/js/chrome/nav.js", 'n(t("nav.tab.grid"));\n'),
             ("design/src/shell.html", "<title>{{copy:chrome.head.title}}</title>\n")]


def expand(path, old, new):
    return impact.expand(path, old, new, lambda: iter(SRC_TEXTS))


def test_a_changed_copy_key_counts_as_the_file_that_says_it():
    old = json.dumps({"ranks.head.title": "Ranks", "nav.tab.grid": "Grid"})
    new = json.dumps({"ranks.head.title": "Ranks this week", "nav.tab.grid": "Grid", "gone": None})
    paths, golden = expand("design/src/content.json", old, new)
    assert paths == ["design/src/js/surface/ranks/ranks.js"] and golden == []
    assert not impact.select(paths, CFG, SCOPE)["all"]


def test_copy_said_by_chrome_or_the_shell_still_runs_everything():
    for key in ("nav.tab.grid", "chrome.head.title"):
        paths, _ = expand("design/src/content.json", "{}", json.dumps({key: "x"}))
        assert impact.select(paths, CFG, SCOPE)["all"], key


def test_a_key_that_is_a_prefix_of_another_is_not_confused_with_it():
    paths, _ = expand("design/src/content.json", "{}", json.dumps({"ranks.head": "x"}))
    assert paths == []


def test_a_manifest_line_added_counts_as_its_part():
    old = "# pin: data first\ndata/teams.js\nsurface/ranks/ranks.js\nmain.js\n"
    added, _ = expand("design/src/order.js.txt", old, old.replace("main.js", "surface/ranks/new.js\nmain.js"))
    assert added == ["design/src/js/surface/ranks/new.js"]
    assert expand("design/src/order.css.txt", "a.css # x\n", "a.css # y\n") == ([], [])


def test_a_moved_js_part_runs_everything_a_moved_css_part_counts_as_itself():
    """Moving a JS part changes load order for every part it passed (review, 2026-10-05)."""
    old = "data/teams.js\nsurface/ranks/ranks.js\nsurface/usage/usage.js\nmain.js\n"
    new = "data/teams.js\nsurface/usage/usage.js\nsurface/ranks/ranks.js\nmain.js\n"
    assert expand("design/src/order.js.txt", old, new) is None
    paths, _ = expand("design/src/order.css.txt", old.replace(".js", ".css"), new.replace(".js", ".css"))
    assert len(paths) == 1 and paths[0] in ("design/src/css/surface/ranks/ranks.css", "design/src/css/surface/usage/usage.css")


def test_a_scope_entry_counts_as_its_css_file():
    old = {"fenced": {"surface/ranks/ranks.css": ["ranks"]}, "shared": {}}
    new = {"fenced": {"surface/ranks/ranks.css": ["ranks", "usage"]}, "shared": {}}
    paths, golden = expand("design/src/scope.json", json.dumps(old), json.dumps(new))
    assert paths == ["design/src/css/surface/ranks/ranks.css"] and golden == []


def test_a_view_dropped_from_a_fence_runs_that_views_slice():
    """Usage loses ranks.css's styling, so Usage's golden must run (review, 2026-10-05)."""
    old = {"fenced": {"surface/ranks/ranks.css": ["ranks", "usage"]}, "shared": {}}
    new = {"fenced": {"surface/ranks/ranks.css": ["ranks"]}, "shared": {}}
    paths, golden = expand("design/src/scope.json", json.dumps(old), json.dumps(new))
    assert golden == ["usage"]
    assert {"ranks", "usage"} <= set(impact.select(paths, CFG, SCOPE, golden=golden)["areas"])
    old["fenced"]["surface/ranks/ranks.css"].append("#modal")
    assert expand("design/src/scope.json", json.dumps(old), json.dumps(new)) is None


def test_a_file_leaving_shared_runs_everything():
    old = {"fenced": {}, "shared": {"surface/ranks/ranks.css": "every view"}}
    new = {"fenced": {"surface/ranks/ranks.css": ["ranks"]}, "shared": {}}
    assert expand("design/src/scope.json", json.dumps(old), json.dumps(new)) is None


def test_a_changed_golden_state_counts_as_its_area():
    old = {"desk": {"ranks": {"a": 1}, "live-tds": {"a": 1}}, "phone": {"ranks": {"a": 1}}}
    new = {"desk": {"ranks": {"a": 1}, "live-tds": {"a": 2}}, "phone": {"ranks": {"a": 1}, "teams-x": {}}}
    paths, golden = expand("tests/golden/render.json", json.dumps(old), json.dumps(new))
    assert paths == [] and golden == ["live", "roster"]
    got = impact.select([], CFG, SCOPE, golden=golden)
    assert not got["all"] and got["areas"] == ["live", "roster"]
    assert "tests/test_render.py" in got["files"]


def test_an_unknown_golden_area_runs_everything():
    assert impact.select([], CFG, SCOPE, golden=["nosuchview"])["all"]


def test_any_other_file_is_not_expanded():
    assert expand("design/build.py", "a", "b") is None


def test_the_cli_prints_json(capsys):
    impact.main(["--paths", "design/ranks.py"])
    assert json.loads(capsys.readouterr().out)["areas"] == ["ranks"]
