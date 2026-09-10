"""build.py against the fixtures: every live path taken, the injected data parses, and the two
guards that fail the build (contract, script terminator) actually fail it."""
import json
import re

import pytest

import build
import contract

BLOCKS = ["HEADS", "LIVE_ESPN", "LIVE_YAHOO", "LIVE_FEED", "LIVE_NEWS", "LIVE_PROPS", "LIVE_DFS_YAHOO"]


def injected(fragment):
    """{name: parsed JSON} for every `const X = ...;` line the build injected."""
    out = {}
    for name in BLOCKS:
        m = re.search(rf"^const {name} = (.*);$", fragment, re.M)
        assert m, f"{name} not injected"
        out[name] = json.loads(m.group(1).replace("<\\/", "</"))
    return out


def test_every_source_is_live(built):
    fallbacks = [l for l in built.report if "falls back" in l or "no live file" in l]
    assert fallbacks == [], "a fixture is missing or mis-shaped:\n" + "\n".join(fallbacks)


def test_injected_blocks_parse(built):
    d = injected(built.fragment)
    assert d["LIVE_ESPN"]["roster"] and d["LIVE_YAHOO"]["roster"]
    assert d["LIVE_PROPS"]["props"] and d["LIVE_PROPS"]["windows"]
    assert d["LIVE_DFS_YAHOO"]["players"]
    assert d["LIVE_NEWS"]["items"]
    assert d["LIVE_FEED"]["fetched"]["espn"]


def test_injected_blocks_meet_the_contract(built):
    d = injected(built.fragment)
    for name in contract.CONTRACT:
        assert contract.problems(name, d[name]) == []


def test_heads_are_inlined(built):
    assert built.heads, "no headshot inlined -- fixtures/heads is empty or slugs do not match"
    assert built.fragment.count("data:image/webp;base64,") == len(built.heads)
    for slug in built.heads:
        assert f'"{slug}"' in built.fragment


def test_page_wraps_fragment(built):
    assert built.page.startswith("<!doctype html>")
    assert built.fragment in built.page
    assert built.page.rstrip().endswith("</html>")


def test_one_script_block(built):
    """The injected JSON must not be able to close the <script> early."""
    assert built.fragment.count("</script>") == 1


def test_build_is_deterministic(built):
    assert build.render().page == built.page


def test_script_terminator_in_data_is_escaped(monkeypatch):
    real = build.load_news

    def poisoned():
        d = real()
        d["items"][0]["title"] = 'He said "</script><b>x</b>" on air'
        return d

    monkeypatch.setattr(build, "load_news", poisoned)
    b = build.render()
    assert b.fragment.count("</script>") == 1
    assert "<\\/script><b>x<\\/b>" in b.fragment


def test_missing_field_fails_the_build(monkeypatch):
    real = build.live_espn

    def broken(available):
        d = real(available)
        for row in d["roster"]:
            row.pop("slot")
        return d

    monkeypatch.setattr(build, "live_espn", broken)
    with pytest.raises(SystemExit, match=r"contract: LIVE_ESPN is missing LIVE_ESPN\.roster\[0\]\.slot"):
        build.render()


def test_absent_source_is_not_a_contract_violation():
    assert contract.problems("LIVE_ESPN", None) == []


def test_contract_reports_top_level_and_row_fields():
    obj = {"name": "x", "roster": [{"n": "a"}]}
    got = contract.problems("LIVE_ESPN", obj)
    assert "LIVE_ESPN.league" in got
    assert "LIVE_ESPN.roster[0].pos" in got


def test_contract_checks_keyed_maps():
    """A game log without its `g` array crashed the parlay tab (gamelog.js reads log.g[k])."""
    obj = {k: None for k in contract.CONTRACT["LIVE_PROPS"]["keys"]}
    obj["props"] = []
    obj["logs"] = {"chase-brown": {"v": {}}}
    assert contract.problems("LIVE_PROPS", obj) == ["LIVE_PROPS.logs['chase-brown'].g"]


def test_lint_error_fails_the_build(monkeypatch):
    import lint_css
    monkeypatch.setattr(lint_css, "lint", lambda: [lint_css.Finding("breakpoint", "error", "x.css", 1, "500px")])
    with pytest.raises(SystemExit, match="lint: x.css:1 breakpoint 500px"):
        build.render()
