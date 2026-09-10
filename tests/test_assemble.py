"""The assembler: manifests and tree agree, the cut is a pure concatenation, a part can
neither drop out of the page nor join it unlisted, and every user-facing string resolves to a
key in content.json."""
import json
import shutil

import pytest

import assemble


def write_copy(scratch_tree, copy):
    (scratch_tree / "content.json").write_text(
        json.dumps(copy, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def read_copy(scratch_tree):
    return json.loads((scratch_tree / "content.json").read_text(encoding="utf-8"))


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
    monkeypatch.setattr(assemble, "CONTENT", src / "content.json")
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


# ---------------------------- copy is data ----------------------------

def test_content_json_is_a_canonical_flat_map():
    """One key per line, sorted, str -> str: the file is diffable and a merge is line-wise."""
    raw = assemble.CONTENT.read_text(encoding="utf-8")
    copy = json.loads(raw)
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in copy.items())
    assert raw == json.dumps(copy, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def test_copy_is_declared_before_the_first_js_part():
    """t() is called from every part, so COPY has to exist before any of them runs."""
    js = assemble.concat("js")
    assert js.startswith("const COPY = ")
    assert js.index("const COPY = ") < js.index("/* ── js/")
    assert assemble.copy_decl().count("\n") == 1


def test_markup_in_copy_cannot_close_the_script():
    """Copy carries intentional <b>/<em>; an unescaped </b> would end <script> mid-page."""
    decl = assemble.copy_decl()
    assert "<\\/b>" in decl, "content.json should still hold markup for this test to mean anything"
    assert "</" not in decl


def test_shell_copy_slot_is_substituted_and_html_escaped(scratch_tree):
    copy = read_copy(scratch_tree)
    copy["chrome.head.title"] = 'Ale & "Bo" <i>x</i>'
    write_copy(scratch_tree, copy)
    out = assemble.assemble()
    assert "<title>Ale &amp; &quot;Bo&quot; &lt;i&gt;x&lt;/i&gt;</title>" in out
    assert "{{copy:" not in out


def test_line_map_accounts_for_the_injected_copy():
    """A part's reported range has to name its real first and last line in the output."""
    out = assemble.assemble(banners=True).split("\n")
    for name, start, end in assemble.line_map(banners=True):
        kind, rel = name.split("/", 1)
        body = (assemble.SRC / kind / rel).read_text(encoding="utf-8").split("\n")
        assert out[start - 1] == body[0], name
        assert out[end - 1] == body[-2], name


def test_unknown_copy_key_in_js_is_a_problem(scratch_tree):
    p = scratch_tree / "js" / "chrome" / "nav.js"
    p.write_text(p.read_text(encoding="utf-8").replace('t("nav.pool.full")', 't("nav.pool.nope")'),
                 encoding="utf-8")
    assert any("nav.pool.nope" in x and "not a key" in x for x in assemble.check())
    with pytest.raises(SystemExit):
        assemble.assemble()


def test_unknown_copy_key_in_shell_is_a_problem(scratch_tree):
    s = scratch_tree / "shell.html"
    s.write_text(s.read_text(encoding="utf-8").replace("{{copy:chrome.head.title}}",
                                                       "{{copy:chrome.head.nope}}"), encoding="utf-8")
    assert any("chrome.head.nope" in x and "not a key" in x for x in assemble.check())


def test_unreferenced_copy_key_is_a_problem(scratch_tree):
    """Dead copy is a problem: a string nothing renders is a string nobody can trust."""
    copy = read_copy(scratch_tree)
    copy["chrome.footer.ghost"] = "nobody says this"
    write_copy(scratch_tree, copy)
    assert any("chrome.footer.ghost" in x and "never referenced" in x for x in assemble.check())


def test_non_string_copy_value_is_a_problem(scratch_tree):
    copy = read_copy(scratch_tree)
    copy["chrome.head.title"] = ["Team", "Watch"]
    write_copy(scratch_tree, copy)
    assert any("chrome.head.title" in x and "want a string" in x for x in assemble.check())


def test_missing_content_json_is_a_problem(scratch_tree):
    (scratch_tree / "content.json").unlink()
    assert any("content.json" in x and "missing" in x for x in assemble.check())
