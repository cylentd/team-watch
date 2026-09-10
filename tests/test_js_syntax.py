"""The assembled script parses. A missing brace in one part is otherwise a blank page and one
console line; this makes it a failing test in under 200 ms."""
import re
import shutil
import subprocess

import pytest

import assemble

NODE = shutil.which("node")


def script_text():
    """The <script> body with the injection marker replaced by empty declarations, so the parse
    sees the same top-level names the built page will."""
    html = assemble.assemble()
    m = re.search(r"<script>\n(.*)</script>", html, re.S)
    assert m
    decls = "const HEADS={},LIVE_ESPN=null,LIVE_YAHOO=null,LIVE_FEED=null,LIVE_NEWS=null,LIVE_PROPS=null,LIVE_DFS_YAHOO=null;"
    return m.group(1).replace("/*__HEADS__*/", decls)


@pytest.mark.skipif(NODE is None, reason="node not on PATH")
def test_script_parses(tmp_path):
    js = tmp_path / "page.js"
    js.write_text(script_text(), encoding="utf-8")
    r = subprocess.run([NODE, "--check", str(js)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_style_block_braces_balance():
    """Cheap CSS sanity: an unclosed rule swallows every rule after it, silently."""
    html = assemble.assemble()
    m = re.search(r"<style>\n(.*)</style>", html, re.S)
    css = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
    css = re.sub(r'"[^"]*"|\'[^\']*\'', "", css)
    assert css.count("{") == css.count("}")
