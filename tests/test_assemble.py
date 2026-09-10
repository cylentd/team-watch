"""The assembler: manifests and tree agree, the cut is a pure concatenation, and a part can
neither drop out of the page nor join it unlisted."""
import shutil

import pytest

import assemble


def test_tree_and_manifests_agree():
    assert assemble.check() == []


def test_every_part_listed_exactly_once():
    for kind in ("css", "js"):
        listed = assemble.manifest(kind)
        on_disk = sorted(p.relative_to(assemble.SRC / kind).as_posix()
                         for p in (assemble.SRC / kind).rglob("*") if p.is_file() and p.suffix in (".css", ".js"))
        assert sorted(listed) == on_disk
        assert len(listed) == len(set(listed))


def test_assembly_is_deterministic():
    assert assemble.assemble() == assemble.assemble()


def test_banners_are_the_only_difference():
    with_banners = assemble.assemble(banners=True)
    without = assemble.assemble(banners=False)
    assert assemble.strip_banners(with_banners) == without
    n_parts = len(assemble.manifest("css")) + len(assemble.manifest("js"))
    assert with_banners.count("\n") - without.count("\n") == n_parts


def test_parts_are_contiguous_in_the_output():
    """line_map's ranges tile each slot: no gaps (a lost line) and no overlaps."""
    rows = assemble.line_map(banners=True)
    by_kind = {}
    for name, s, e in rows:
        by_kind.setdefault(name.split("/", 1)[0], []).append((s, e))
    for kind, ranges in by_kind.items():
        for (s1, e1), (s2, e2) in zip(ranges, ranges[1:]):
            assert s2 == e1 + 2, f"{kind}: gap or overlap between {e1} and {s2}"   # +1 is the next banner


def test_every_part_ends_with_a_newline():
    """Concatenation has no separators, so a part without a trailing newline would glue its last
    line to the next part's banner."""
    for kind in ("css", "js"):
        for path in assemble.parts(kind):
            assert path.read_bytes().endswith(b"\n"), path


def test_placeholders_do_not_survive():
    out = assemble.assemble()
    for ph in assemble.PLACEHOLDER.values():
        assert ph not in out
    assert out.count("/*__HEADS__*/") == 1


@pytest.fixture
def scratch_tree(tmp_path, monkeypatch):
    """A copy of design/src the test may break, with the module pointed at it."""
    src = tmp_path / "src"
    shutil.copytree(assemble.SRC, src)
    monkeypatch.setattr(assemble, "SRC", src)
    monkeypatch.setattr(assemble, "SHELL", src / "shell.html")
    monkeypatch.setattr(assemble, "KINDS", {"css": src / "order.css.txt", "js": src / "order.js.txt"})
    return src


def test_unlisted_file_is_a_problem(scratch_tree):
    (scratch_tree / "css" / "chrome" / "stray.css").write_text(".x{}\n", encoding="utf-8")
    assert any("stray.css" in p and "not in order" in p for p in assemble.check())
    with pytest.raises(SystemExit):
        assemble.assemble()


def test_listed_but_missing_file_is_a_problem(scratch_tree):
    (scratch_tree / "js" / "main.js").unlink()
    assert any("main.js" in p and "no such file" in p for p in assemble.check())


def test_duplicate_manifest_line_is_a_problem(scratch_tree):
    m = scratch_tree / "order.css.txt"
    m.write_text(m.read_text(encoding="utf-8") + "base/tokens.css\n", encoding="utf-8")
    assert any("listed twice" in p for p in assemble.check())
