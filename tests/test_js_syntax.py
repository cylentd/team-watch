"""The assembled script parses. A missing brace in one part is otherwise a blank page and one
console line; this makes it a failing test in under 200 ms."""
import re
import shutil
import subprocess

import pytest

import assemble

NODE = shutil.which("node")
pytestmark = pytest.mark.integration      # each test assembles the whole page; one also runs node


@pytest.fixture(scope="module")
def html():
    """The assembled page, once for the three tests that read it."""
    return assemble.assemble()


def script_text(html):
    """The <script> body with the injection marker replaced by empty declarations, so the parse
    sees the same top-level names the built page will."""
    m = re.search(r"<script>\n(.*)</script>", html, re.S)
    assert m
    decls = "const HEADS={},LIVE_ESPN=null,LIVE_YAHOO=null,LIVE_FEED=null,LIVE_NEWS=null,LIVE_PROPS=null,LIVE_DFS_YAHOO=null;"
    return m.group(1).replace("/*__HEADS__*/", decls)


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_script_parses(tmp_path, html):
    js = tmp_path / "page.js"
    js.write_text(script_text(html), encoding="utf-8")
    r = subprocess.run([NODE, "--check", str(js)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_no_top_level_function_is_declared_twice(html):
    """Every part shares one script scope, and a second `function x(` silently replaces the first:
    Role's roleHTML (2026-09-29) replaced the profile's, and the Target depth block vanished with
    no error anywhere. A const or let twice already fails the parse above; a function does not."""
    names = re.findall(r"^function\s+([A-Za-z_$][\w$]*)\s*\(", script_text(html), re.M)
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert dupes == [], f"declared more than once: {dupes}"


def test_style_block_braces_balance(html):
    """Cheap CSS sanity: an unclosed rule swallows every rule after it, silently."""
    m = re.search(r"<style>\n(.*)</style>", html, re.S)
    css = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    css = re.sub(r'"[^"]*"|\'[^\']*\'', "", css)
    assert css.count("{") == css.count("}")
