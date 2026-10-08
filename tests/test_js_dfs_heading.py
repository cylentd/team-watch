"""The DFS pool heading names the slate (2026-10-08, David, ledger #38), in Node.

The pool holds only the Sunday early + afternoon games (design/dfs_slate.py), so a reader must be told
why Thursday, Sunday night and Monday players are missing.
"""
import json
import pathlib

import pytest

COPY = json.loads((pathlib.Path(__file__).resolve().parent.parent / "design" / "src" / "content.json").read_text(encoding="utf-8"))
SITE = {"label": "Yahoo", "key": "yahoo", "cap": 200, "pool": [], "when": "Oct 8"}


@pytest.fixture(scope="module")
def head(node_js):
    js = node_js("builder/explain.js", globals={"SITE": SITE, "LIVE_YAHOO_DFS": None})
    js("(() => { globalThis.dfsSite = () => SITE; return 1; })()")
    return js("marketHead()")


def test_the_pool_heading_names_the_slate_it_holds(head):
    assert COPY["dfs.market.slate"] in head


def test_the_slate_line_says_sunday_early_and_afternoon():
    line = COPY["dfs.market.slate"]
    assert "Sunday" in line and "early" in line and "afternoon" in line


def test_the_slate_line_is_one_short_line():
    assert len(COPY["dfs.market.slate"]) <= 40, "must fit one line at 360px beside the Fetched pill"
