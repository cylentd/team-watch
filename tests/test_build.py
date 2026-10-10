"""build.py against the fixtures: every live path taken, the injected data parses, and the two
guards that fail the build (contract, script terminator) actually fail it."""
import json
import re

import pytest

import build
import contract

BLOCKS = ["HEADS", "LIVE_ESPN", "LIVE_YAHOO", "LIVE_MATES", "LIVE_FEED", "LIVE_NEWS", "LIVE_PROPS", "LIVE_REASONS", "LIVE_DFS_YAHOO",
          "LIVE_PROFILES", "LIVE_WAIVER", "LIVE_WAIVER_TEAMS", "LIVE_WIRE", "LIVE_POOL", "LIVE_USAGE", "LIVE_MARKET_STOCK",
          "LIVE_SIGNALS", "LIVE_SCHEDULE", "LIVE_PEDIGREE", "LIVE_GAMELOG", "LIVE_PROJECTIONS",
          "LIVE_RANKS", "LIVE_INJURY", "LIVE_SIGNED", "LIVE_WEATHER", "LIVE_WX_HISTORY", "LIVE_WX_HITS","LIVE_LINES", "LIVE_ROUTES", "LIVE_ARCHETYPE", "LIVE_TRENCHES",
          "LIVE_STARTSIT", "LIVE_ROLE", "LIVE_CLIPS", "LIVE_NAMES", "LIVE_PROPS_RECORD", "LIVE_CLAUDE_PROPS", "LIVE_CLAUDE_RECORD", "LIVE_RECAP", "LIVE_DIGEST", "LIVE_PREVIEW", "LIVE_LEAGUE", "LIVE_LEAGUE_YAHOO", "LIVE_DEFENSE", "LIVE_TRADES", "LIVE_GAMEDAY", "LIVE_SSB", "LIVE_SS3", "LIVE_TEAMS",
          "LIVE_AYO", "LIVE_LEAGUE_AYO", "LIVE_TRADES_AYO",   # the third league (2026-09-29)
          "LIVE_ACCURACY", "LIVE_DST", "LIVE_SOS", "LIVE_D_STARTERS", "LIVE_ROS", "LIVE_USAGE_MOVERS", "LIVE_KDST", "LIVE_PLAYER_TAGS",
          "LIVE_TD_RESEARCH"]   # design/audit_blocks.py (2026-10-05; the last three 2026-10-06; LIVE_KDST 2026-10-07; LIVE_PLAYER_TAGS 2026-10-08; LIVE_TD_RESEARCH 2026-10-09)


FILE_BLOCKS = {"TRADE_OFFERS"}   # contract blocks written as a file beside the page, not injected (design/trade_offers.py)


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


def test_defense_speaks_the_pages_team_codes(built):
    """LIVE_DEFENSE (the leg sheet's matchup line, 2026-09-27): nflverse's LA is the page's LAR, the
    same spelling a prop's `opp` now carries, and only starters who will not play are kept (NYJ's
    questionable starter and its hurt backup are not)."""
    d = injected(built.fragment)
    D = d["LIVE_DEFENSE"]
    assert "LAR" in D["form"] and "LA" not in D["form"] and D["out"]["LAR"][0]["name"] == "Jared Verse"
    assert [o["name"] for o in D["out"]["NYJ"]] == ["Sauce Gardner", "Quinnen Williams"]
    assert D["form"]["GB"]["prior"] is None
    assert {p["opp"] for p in d["LIVE_PROPS"]["props"] if p.get("opp")} <= set(D["form"])
    assert set(d["LIVE_PROPS"]["logs"]["tee-higgins"]["u"]) >= {"tgt", "rz_tgt", "team_rz"}
    assert "u" not in d["LIVE_PROPS"]["logs"]["jahmyr-gibbs"], "a log without usage still passes"


def test_injected_blocks_meet_the_contract(built):
    d = injected(built.fragment)
    for name in contract.CONTRACT:
        if name in FILE_BLOCKS:
            continue
        assert contract.problems(name, d[name]) == []


def test_heads_are_files_not_inlined(built):
    """Every head ff-jarvis has is named, not only the wanted ones -- a connected league's players
    are only known at runtime -- and none is a data URI any more."""
    assert built.heads, "no headshot named -- fixtures/heads is empty"
    assert set(built.heads) == {p.stem for p in build.HEADS_SRC.glob("*.webp")}
    assert "data:image/webp;base64," not in built.fragment
    assert injected(built.fragment)["HEADS"] == {s: f"heads/{s}.webp" for s in built.heads}


def test_the_build_names_the_fixture_avatars_on_the_yahoo_league(built):
    # design/avatars.py (2026-10-06); the fixture data holds avatars for Yahoo teams 3 and 9 only (tests/test_avatars.py)
    teams = {t["id"]: t["avatar"] for t in injected(built.fragment)["LIVE_LEAGUE_YAHOO"]["teams"]}
    assert teams[3] == "avatars/yahoo/3.webp" and teams[7] == ""


def test_write_heads_mirrors_the_source(tmp_path):
    (tmp_path / "heads").mkdir()
    (tmp_path / "heads" / "gone-player.webp").write_bytes(b"old")
    n = build.write_heads(tmp_path)
    written = {p.name for p in (tmp_path / "heads").glob("*.webp")}
    assert written == {p.name for p in build.HEADS_SRC.glob("*.webp")} and n == len(written)


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

    def poisoned(feed_path, dwr_path):
        d = real(feed_path, dwr_path)
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


def test_site_icon_is_smug_blip(built):
    """The favicon is Smug Blip (2026-09-29), cut from lib/blip.js by design/icons.py and inlined;
    the apple-touch icon is its 180px PNG, a file the page names by path, as served."""
    from urllib.parse import quote, unquote
    svg = (build.REPO / "icons" / "favicon.svg").read_text(encoding="utf-8").strip()
    m = re.search(r'<link rel="icon" type="image/svg\+xml" href="data:image/svg\+xml,([^"]+)">', built.page)
    assert m and m.group(1) == quote(svg), "the favicon link is not icons/favicon.svg"
    assert 'fill="#c8ff2e"' in unquote(m.group(1))       # the lit lime screen, not the old block
    assert '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">' in built.page
    png = (build.REPO / "icons" / "apple-touch-icon.png").read_bytes()
    assert png[1:4] == b"PNG" and png[16:24] == (180).to_bytes(4, "big") * 2   # a 180x180 PNG
