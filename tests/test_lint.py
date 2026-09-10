"""The theme rules: each fires on the thing it names, stays quiet on the thing it must allow,
and the real tree has no errors (warnings are the tracked backlog)."""
import lint_css

TRIPLES = lint_css.token_triples(":root{--lime:#c8ff2e;--down:#ff5a52;--mono:\"JetBrains Mono\",monospace}")


def rules(findings):
    return sorted({f.rule for f in findings})


def test_real_tree_has_no_errors():
    found = lint_css.lint()
    assert lint_css.errors(found) == []


def test_hex_outside_tokens_fires():
    assert rules(lint_css.lint_css_text("chrome/x.css", ".a{color:#0b0d05}", TRIPLES)) == ["hex-outside-tokens"]


def test_hex_in_tokens_file_is_allowed():
    assert lint_css.lint_css_text(lint_css.TOKENS, ":root{--lime:#c8ff2e}", TRIPLES) == []


def test_hex_in_comment_or_data_uri_is_prose():
    css = '.a{background:url("data:image/svg+xml,%3Crect fill=%23fff/%3E")} /* was #fff */'
    assert lint_css.lint_css_text("chrome/x.css", css, TRIPLES) == []


def test_rgba_spelling_out_a_token_fires_with_the_token_name():
    found = lint_css.lint_css_text("chrome/x.css", ".a{border:1px solid rgba(200,255,46,.4)}", TRIPLES)
    assert rules(found) == ["rgba-token-triple"]
    assert "--lime" in found[0].text


def test_rgba_of_a_non_token_colour_is_quiet():
    assert lint_css.lint_css_text("chrome/x.css", ".a{background:rgba(0,0,0,.5)}", TRIPLES) == []


def test_font_family_literal_fires_and_var_is_quiet():
    assert rules(lint_css.lint_css_text("x.css", '.a{font-family:"JetBrains Mono",monospace}', TRIPLES)) == ["font-family-literal"]
    assert lint_css.lint_css_text("x.css", ".a{font-family:var(--mono)}", TRIPLES) == []


def test_breakpoint_rule():
    assert lint_css.lint_css_text("responsive/x.css", "@media (max-width:760px){.a{display:none}}", TRIPLES) == []
    found = lint_css.lint_css_text("responsive/x.css", "@media (max-width:700px){.a{display:none}}", TRIPLES)
    assert [(f.rule, f.level) for f in found] == [("breakpoint", "error")]


def test_inline_colour_in_js():
    assert rules(lint_css.lint_inline("js/x.js", '`<i style="color:#fff"></i>`')) == ["inline-colour-in-js"]
    assert lint_css.lint_inline("js/x.js", '`<i style="color:var(--lime)"></i>`') == []
    assert lint_css.lint_inline("js/x.js", '`<i style="background:${dotColor}"></i>`') == []


def test_duplicate_selector_across_parts():
    parts = [("chrome/a.css", ".pill{color:red}\n"), ("surface/b.css", ".pill{color:blue}\n.other{}\n"),
             ("responsive/760.css", ".pill{display:none}\n")]
    dup = lint_css.duplicate_selectors(parts, acknowledged=set())
    assert dup == [(".pill", ["chrome/a.css", "surface/b.css"])]          # responsive/ is exempt
    assert lint_css.duplicate_selectors(parts, acknowledged={".pill"}) == []
