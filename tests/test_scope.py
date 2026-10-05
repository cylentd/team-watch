"""design/scope_css.py (2026-09-27): a view's CSS is fenced to the views that use it, so a change in
one view cannot restyle another. tests/golden proves the fence changed nothing on screen; these
prove the rewrite itself, and that the fence really keeps a rule out of another view."""
import json

import pytest

import assemble
import scope_css

MODAL = ["#modal"]
W = ":where(#modal, #modal *)"


@pytest.mark.parametrize("css,want", [
    (".a{x}", f".a{W}{{x}}"),
    (".a .b, .c > .d{x}", f".a{W} .b, .c{W} > .d{{x}}"),
    (".modal .lbl{x}", f".modal{W} .lbl{{x}}"),                    # the root may be the first element
    (".a::before{x}", f".a{W}::before{{x}}"),                         # a pseudo-element stays last
    (".a:is(.b .c) .d{x}", f".a:is(.b .c){W} .d{{x}}"),              # a space inside :is() is not a combinator
    ("body.hdr-away .gd{x}", f"body.hdr-away .gd{W}{{x}}"),          # a body class stays in front
    ("@media (max-width:430px){ .a{x} }", f"@media (max-width:430px){{ .a{W}{{x}} }}"),
    ("@keyframes k{from{x}to{y}}", "@keyframes k{from{x}to{y}}"),     # keyframe steps are not selectors
    ("/* .a{x} */ .b{y}", f"/* .a{{x}} */ .b{W}{{y}}"),
    ("[title='a,b'] .c{x}", f"[title='a,b']{W} .c{{x}}"),            # a comma inside a string is not a list
])
def test_fence_rewrites_each_selector(css, want):
    assert scope_css.fence(css, MODAL) == want


@pytest.mark.parametrize("css", ["body.pk-open{x}", ":root{x}", "html{x}"])
def test_a_rule_on_the_page_itself_cannot_be_fenced(css):
    with pytest.raises(ValueError):
        scope_css.fence(css, MODAL)


def test_fencing_keeps_every_line_in_place():
    for rel, names in scope_css.load(assemble.SCOPE)["fenced"].items():
        src = (assemble.SRC / "css" / rel).read_text(encoding="utf-8")
        assert assemble.part_text("css", rel).count("\n") == src.count("\n"), rel


def test_every_view_file_is_decided():
    assert assemble.scope_problems() == []


def test_a_new_view_file_must_be_decided(tmp_path, monkeypatch):
    scope = tmp_path / "scope.json"
    data = scope_css.load(assemble.SCOPE)
    data["fenced"].pop("surface/ranks/ranks.css")
    scope.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(assemble, "SCOPE", scope)
    assert assemble.scope_problems() == ["scope.json: surface/ranks/ranks.css is neither fenced nor shared"]


# A `.rk-tier` added to #view, styled or not by ranks.css (display:flex, padding 10px 16px).
STRAY_TIER = """() => { const d = document.createElement("div"); d.className = "rk-tier";
  document.getElementById("view").append(d); const s = getComputedStyle(d);
  return s.display + " " + s.paddingTop; }"""


@pytest.mark.render
def test_a_fenced_rule_stays_out_of_another_view(browser, page_file):
    """Ranks' class drawn inside Usage gets none of Ranks' style; inside Ranks it does."""
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.route("http*://**", lambda r: r.abort())
    seen = {}
    for leaf in ("ranks", "usage"):
        page.goto(page_file.as_uri() + "#" + leaf)
        page.wait_for_selector(f"#view[data-view='{leaf}'] > *")
        seen[leaf] = page.evaluate(STRAY_TIER)
    page.close()
    assert seen == {"ranks": "flex 10px", "usage": "block 0px"}
