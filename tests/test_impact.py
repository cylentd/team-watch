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
    # An area may share a file with another area (test_trace.py is in testtools and designdoc: either
    # area's change runs it); core and full_only never overlap an area or each other.
    twice = [name for name, a in AREAS.items() if len(a["tests"]) != len(set(a["tests"]))]
    assert twice == [], f"{twice} list a test file twice"
    in_areas = sorted({t for a in AREAS.values() for t in a["tests"]})
    listed = CFG["core"] + list(CFG["full_only"]) + in_areas
    on_disk = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "tests").glob("test_*.py"))
    assert sorted(set(listed)) == on_disk
    assert len(listed) == len(set(listed)), "a test file is listed twice"


def test_every_path_exists_and_has_one_owner():
    claimed = [p for a in AREAS.values() for p in a["paths"]]
    assert len(claimed) == len(set(claimed))
    missing = [p for p in claimed if not ((ROOT / p).is_dir() if p.endswith("/") else (ROOT / p).is_file())]
    assert missing == []
    inside = {p: [q for q in claimed if q != p and q.endswith("/") and p.startswith(q)] for p in claimed}
    assert {p: o for p, o in inside.items() if o} == {}, "a path sits inside another claimed folder"
    # select() reads every tests/ path before the map, so a claim there would never take effect.
    assert not [p for p in claimed if p.startswith("tests/") and not p.startswith("tests/test_")]


def test_the_render_areas_are_the_goldens():
    import test_render
    mapped = [r for a in AREAS.values() for r in a["render"]]
    assert sorted(mapped) == sorted(set(mapped)) == test_render.AREAS


RANKS_TESTS = ["tests/test_ranks.py", "tests/test_week_ranks.py", "tests/test_ranks_dst.py", "tests/test_js_dst.py", "tests/test_ros.py", "tests/test_ros_fp.py", "tests/test_js_ros.py", "tests/test_ros_view.py"]


@pytest.mark.parametrize("paths,areas,extra", [
    (["design/src/css/surface/ranks/ranks.css"], ["ranks"], RANKS_TESTS + ["tests/test_render.py"]),
    (["design/ranks.py", "README.md"], ["ranks"], RANKS_TESTS + ["tests/test_render.py"]),
    (["tests/test_ranks.py"], [], ["tests/test_ranks.py"]),
    (["CLAUDE.md"], [], []),
    (["design/DESIGN.md"], [], ["tests/test_trace.py"]),   # the one .md a test reads
    (["scripts/land.ps1"], [], ["tests/test_land_queue.py", "tests/test_testlog.py"]),
])
def test_select_narrows_to_its_areas_and_files(paths, areas, extra):
    got = impact.select(paths, CFG, SCOPE)
    assert got["all"] is False, got["why"]
    assert got["areas"] == areas
    assert got["files"] == sorted(set(CFG["core"] + extra))


@pytest.mark.parametrize("paths", [
    ["design/src/css/surface/strip/panel.css"],  # shared CSS styles any view
    ["design/src/css/component/pool.css"],       # so does a component
    ["design/src/js/chrome/nav.js"],             # no area owns chrome
    ["design/build.py"],
    ["tests/conftest.py"],
    ["tests/golden/ranks.json"],
])
def test_select_runs_everything(paths):
    got = impact.select(paths, CFG, SCOPE)
    assert got["all"] is True, got["why"]


def test_every_fenced_css_file_has_an_area():
    runs_all = [rel for rel in SCOPE["fenced"]
                if impact.select([impact.CSS_SURFACE + rel[len("surface/"):]], CFG, SCOPE)["all"]]
    assert runs_all == []


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


@pytest.mark.parametrize("key", ["nav.tab.grid", "chrome.head.title"])
def test_copy_said_by_chrome_or_the_shell_still_runs_everything(key):
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
    old = {"desk": {"live-feed": {"a": 1}, "live-tds": {"a": 1}}, "phone": {"live-feed": {"a": 1}}}
    new = {"desk": {"live-feed": {"a": 1}, "live-tds": {"a": 2}}, "phone": {"live-feed": {"a": 1}, "teams-x": {}}}
    paths, golden = expand("tests/golden/live.json", json.dumps(old), json.dumps(new))
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


# ---- the files on disk, and scripts/run_tests.py (2026-10-05) ----

def fake_git(monkeypatch, outputs):
    """impact.git answering from a table, keyed by its first two arguments."""
    calls = []
    def git(*args):
        calls.append(args)
        return outputs[args[:2]]
    monkeypatch.setattr(impact, "git", git)
    monkeypatch.setattr(impact, "at", lambda rev, path: "old")
    return calls


def test_the_worktree_mode_sees_edits_not_yet_committed(monkeypatch):
    calls = fake_git(monkeypatch, {
        ("merge-base", "origin/main"): "abc\n",
        ("diff", "--no-renames"): "design/ranks.py\n",
        ("ls-files", "--others"): "design/src/js/surface/ranks/new.js\n"})
    monkeypatch.setattr(impact, "on_disk", lambda path: "new")
    paths, _ = impact.changed("origin/main", worktree=True)
    assert paths == ["design/ranks.py", "design/src/js/surface/ranks/new.js"]
    assert ("diff", "--no-renames", "--name-only", "abc") in calls  # the tree, not HEAD


def test_the_committed_mode_reads_head_only(monkeypatch):
    calls = fake_git(monkeypatch, {
        ("merge-base", "origin/main"): "abc\n",
        ("diff", "--no-renames"): "design/ranks.py\n"})
    paths, _ = impact.changed("origin/main")
    assert paths == ["design/ranks.py"]
    assert ("diff", "--no-renames", "--name-only", "origin/main...HEAD") in calls
    assert not [c for c in calls if c[0] == "ls-files"]


def gone_in_head(monkeypatch, listed):
    """A diff that deletes `listed`: each file is in the fork point and not in HEAD."""
    fake_git(monkeypatch, {("merge-base", "origin/main"): "abc\n", ("diff", "--no-renames"): listed})
    monkeypatch.setattr(impact, "at", lambda rev, path: "old" if rev == "abc" else None)


def test_a_deleted_file_no_area_owns_does_not_force_the_whole_suite(monkeypatch):
    # 2026-10-07: removing scripts/worker_slots.py and tests/test_slots.py ran everything and named a deleted test file
    gone_in_head(monkeypatch, "scripts/worker_slots.py\ntests/test_slots.py\n")
    paths, golden = impact.changed("origin/main")
    assert (paths, golden) == ([], [])
    picked = impact.select(paths, golden=golden)
    assert picked["all"] is False and "tests/test_slots.py" not in picked["files"]


def test_a_deleted_file_an_area_owns_still_runs_that_areas_tests(monkeypatch):
    gone_in_head(monkeypatch, "design/ranks.py\n")
    paths, golden = impact.changed("origin/main")
    assert paths == ["design/ranks.py"]
    assert impact.select(paths, golden=golden)["all"] is False


def test_deleted_shared_test_setup_still_runs_everything(monkeypatch):
    gone_in_head(monkeypatch, "tests/conftest.py\n")
    paths, golden = impact.changed("origin/main")
    assert paths == ["tests/conftest.py"]
    assert impact.select(paths, golden=golden)["why"] == ["tests/conftest.py is shared test setup"]


@pytest.mark.integration      # impact.at reads HEAD through git
def test_a_binary_file_in_the_diff_is_read_not_a_crash(monkeypatch, tmp_path):
    # 2026-10-06: the team avatars' .webp fixtures stopped the picker with a UnicodeDecodeError, at HEAD and on disk
    assert isinstance(impact.at("HEAD", "tests/fixtures/data/avatars/yahoo/3.webp"), str)
    (tmp_path / "a.webp").write_bytes(b"RIFF\x8a\xff\x00\x00WEBPVP8 ")
    monkeypatch.setattr(impact, "ROOT", tmp_path)
    assert isinstance(impact.on_disk("a.webp"), str)


import run_tests as runner  # noqa: E402  scripts/run_tests.py


def test_the_runner_passes_files_and_areas():
    pick = {"all": False, "why": [], "files": ["tests/a.py", "tests/test_render.py"], "areas": ["preview"]}
    assert runner.selection(pick) == ["tests/a.py", "tests/test_render.py", "--areas", "preview"]
    assert runner.selection({**pick, "areas": []}) == ["tests/a.py", "tests/test_render.py"]


def test_the_runner_runs_everything_when_impact_says_all(capsys):
    assert runner.selection({"all": True, "why": ["design/build.py"], "files": [], "areas": []}) == []
    assert "design/build.py" in capsys.readouterr().out


def test_update_golden_never_runs_in_parallel():
    """An area's slices share its one golden file, so two workers would overwrite each other."""
    assert runner.parallel(["--update-golden"]) == []
