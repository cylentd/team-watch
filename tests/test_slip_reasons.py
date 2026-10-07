"""The data wiring of the Slips research board (2026-10-03): LIVE_REASONS from ff-jarvis's
slip_reasons.json, and the unpriced Longest reception (`LONG`) market in LIVE_PROPS. No browser."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import build  # noqa: E402
import contract  # noqa: E402
import slips  # noqa: E402
import sources  # noqa: E402
from test_build import injected  # noqa: E402


def block(built, name):
    return injected(built.fragment)[name]


def longs(built):
    return [p for p in block(built, "LIVE_PROPS")["props"] if p["mkt"] == "LONG"]


def test_reasons_are_cut_to_players_with_a_line(built):
    reasons = block(built, "LIVE_REASONS")
    slugs = {p["slug"] for p in block(built, "LIVE_PROPS")["props"] if p["slug"]}
    assert set(reasons) == {"tee-higgins", "amonra-st-brown", "george-kittle", "jahmyr-gibbs"}
    assert set(reasons) <= slugs, "a player with no line this week is not carried"
    assert "lamar-jackson" not in reasons, "the fixture's fifth player has no line"
    assert set(reasons["tee-higgins"]) == {"why", "work", "tags", "vacated"}, "vacated rides through whole"
    assert set(reasons["george-kittle"]) == {"why", "work", "tags"}, "and is absent when no teammate is out"
    assert reasons["tee-higgins"]["vacated"] == [{"name": "J. Chase", "last": "Chase", "status": "IR", "work": "tgt"}]
    assert contract.problems("LIVE_REASONS", reasons) == []
    assert "Reasons: 4 players with a line this week" in built.report


def test_no_file_is_an_empty_map():
    props = {"props": [{"slug": "tee-higgins"}]}
    assert slips.live_reasons(None, props) == {}
    assert slips.live_reasons({"players": {"tee-higgins": {}}}, None) == {}
    assert contract.problems("LIVE_REASONS", {}) == []
    assert "no slip_reasons.json" in slips.report({})


def test_a_player_without_a_headshot_keeps_his_reason():
    """A row with no `slug` (no headshot) is named by slugify(name) on the page, so his reason stays."""
    props = {"props": [{"n": "Amon-Ra St. Brown", "slug": None}, {"n": "Tee Higgins", "slug": "tee-higgins"}]}
    raw = {"players": {"amonra-st-brown": {"why": "a"}, "tee-higgins": {"why": "b"}, "lamar-jackson": {"why": "c"}}}
    assert set(slips.live_reasons(raw, props)) == {"amonra-st-brown", "tee-higgins"}


def test_a_reason_missing_a_field_fails_the_contract():
    got = contract.problems("LIVE_REASONS", {"tee-higgins": {"why": "x", "tags": []}})
    assert got == ["LIVE_REASONS['tee-higgins'].work"]
    assert contract.problems("LIVE_REASONS", {"tee-higgins": {"why": "x", "work": None, "tags": []}}) == []


def test_vacated_is_optional_but_whole_when_sent():
    ok = {"x": {"why": "", "work": None, "tags": [], "vacated": [{"name": "J. Reed", "last": "Reed", "status": "Out", "work": "tgt"}]}}
    assert contract.problems("LIVE_REASONS", ok) == []
    bad = {"x": {"why": "", "work": None, "tags": [], "vacated": [{"name": "J. Reed", "last": "Reed"}]}}
    assert contract.problems("LIVE_REASONS", bad) == ["LIVE_REASONS['x'].vacated[0].status", "LIVE_REASONS['x'].vacated[0].work"]


def by_line(built):
    return {(p["n"], p["mkt"]): p for p in block(built, "LIVE_PROPS")["props"]}


def test_every_tier_rides_on_the_row_and_each_books_own_line(built):
    """ff-jarvis's `tier` and `side` pass through as sent, on the row and on each book (a book's line is its own
    row in the model), never cut from the chance here. TD, Longest reception and an Out player carry none."""
    rows = by_line(built)
    got = {k: (p.get("side"), p.get("tier")) for k, p in rows.items() if p["mkt"] != "TD" and p["mkt"] != "LONG"}
    assert got[("Chase Brown", "RUSH")] == ("higher", "very")
    assert got[("Joe Burrow", "PASS")] == ("lower", "confident")
    assert got[("Brock Purdy", "PASS")] == ("lower", "slight")
    assert got[("George Kittle", "REC")] == ("higher", "none")
    assert got[("Amon-Ra St. Brown", "REC")] == ("higher", "slight")
    assert got[("Jahmyr Gibbs", "RUSH")] == ("lower", "very")
    assert got[("Tee Higgins", "REC")] == (None, None), "an Out row has no pick"
    assert all("tier" not in p for k, p in rows.items() if k[1] in ("TD", "LONG"))
    brown = rows[("Chase Brown", "RUSH")]
    assert {b: (x["side"], x["tier"]) for b, x in brown["books"].items() if "tier" in x} == {"DraftKings": ("higher", "very"), "Underdog": ("higher", "very")}
    assert contract.problems("LIVE_PROPS", block(built, "LIVE_PROPS")) == []


@pytest.mark.integration      # a real build of the page
def test_a_producer_without_tiers_still_builds(monkeypatch):
    """Today's ff-jarvis data has no tier or side: the page builds and draws no pick."""
    real = build.load_model_raw

    def old():
        m = real()
        for r in m["lines"]:
            r.pop("tier", None)
            r.pop("side", None)
        return m

    monkeypatch.setattr(build, "load_model_raw", old)
    props = injected(build.render().fragment)["LIVE_PROPS"]
    assert all("tier" not in p and "side" not in p for p in props["props"])
    assert any(p.get("model") is not None for p in props["props"])


def test_an_unknown_tier_fails_the_contract():
    props = {"props": [{"tier": "huge", "side": "up", "books": {"Underdog": {"tier": "slight"}}}]}
    assert slips.problems_props(props) == ["LIVE_PROPS.props[0].tier", "LIVE_PROPS.props[0].side"]


def test_the_record_is_cut_to_the_three_tiers(built):
    rec = block(built, "LIVE_PROPS_RECORD")
    assert rec["through_week"] == 4 and rec["season"] == 2026
    assert {k: (v["w"], v["l"]) for k, v in rec["tiers"].items()} == {"slight": (205, 165), "confident": (305, 275), "very": (241, 182)}
    assert set(rec) == {"season", "through_week", "tiers"}, "rules and the weekly list stay in ff-jarvis's file"
    assert contract.problems("LIVE_PROPS_RECORD", rec) == []


def test_no_record_file_is_no_block():
    assert slips.props_record(None) is None
    assert slips.props_record({"tiers": {"slight": {"w": 1, "l": 0}}}) is None, "a tier missing: no strip"
    assert contract.problems("LIVE_PROPS_RECORD", {"season": 2026, "through_week": 1, "tiers": {"slight": {}, "confident": {"w": 1, "l": 0}, "very": {"w": 0, "l": 0}}}) \
        == ["LIVE_PROPS_RECORD.tiers['slight'].w", "LIVE_PROPS_RECORD.tiers['slight'].l"]


def test_the_feed_block_wins_over_the_file(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"slip_reasons": {"data": {"players": {"x": {"why": "from the feed"}}}}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert sources.load_slip_reasons()["players"]["x"]["why"] == "from the feed"
    feed.write_text("{}", encoding="utf-8")
    assert "tee-higgins" in sources.load_slip_reasons()["players"], "no feed block: the file is read"


def test_long_rows_carry_nulls_not_a_price_or_a_pick(built):
    rows = longs(built)
    assert {p["n"] for p in rows} == {"Tee Higgins", "Amon-Ra St. Brown", "George Kittle"}
    priced = [p["n"] for p in rows if not (p["model"] is None and p["pick"] is None and p["conf"] is None and p["edge"] is None)]
    assert priced == []
    flagged = [p["n"] for p in rows if p.get("norole") or p.get("stale")]
    assert flagged == [], "an unpriced market is not a no-role touchdown line"
    assert [p["n"] for p in rows if p["mu"] is None or p["line"] is None] == []
    book_priced = [(p["n"], b) for p in rows for b, x in p["books"].items()
                   if not (x["model"] is None and x["pick"] is None and x["conf"] is None)]
    assert book_priced == []
    higgins = next(p for p in rows if p["n"] == "Tee Higgins")
    assert higgins["books"]["Underdog"]["line"] == 23.5 and higgins["books"]["DraftKings"]["line"] == 22.5
    assert higgins["mu"] == 21.6 and higgins["games"] == 8


def test_claude_calls_are_cut_to_player_market_line_side_and_why(built):
    """LIVE_CLAUDE_PROPS (2026-10-05): per player slug a list of {mkt, line, side, why}; the model's side,
    Claude's confidence and the chance stay in ff-jarvis's file, the page never shows them."""
    blk = block(built, "LIVE_CLAUDE_PROPS")
    assert blk["week"] == 4 and set(blk["calls"]) == {"chase-brown", "joe-burrow", "george-kittle", "brock-purdy"}
    assert blk["calls"]["joe-burrow"] == [{"mkt": "PASS", "line": 245.5, "side": "higher",
                                           "why": "Over 245.5 in 4 of his last 5, and CIN trail late more often than not."}]
    assert contract.problems("LIVE_CLAUDE_PROPS", blk) == []


def test_no_claude_file_is_no_block_and_a_bad_call_is_dropped_or_fails():
    assert slips.claude_props(None) is None and slips.claude_props({"calls": []}) is None
    raw = {"week": 4, "calls": [{"name": "A B", "market": "REC", "line": 1.5, "side": "lower", "why": "x" * 200},
                                {"name": "C D", "market": "REC", "line": None, "side": "lower"},
                                {"market": "REC", "line": 2.5, "side": "lower"}]}
    out = slips.claude_props(raw)
    assert list(out["calls"]) == ["a-b"] and len(out["calls"]["a-b"][0]["why"]) == 120, "a call with no line or no name is dropped"
    assert contract.problems("LIVE_CLAUDE_PROPS", None) == [], "optional"
    bad = {"week": 4, "asof": None, "calls": {"a-b": [{"mkt": "REC", "line": 1.5, "side": "up", "why": ""}]}}
    assert contract.problems("LIVE_CLAUDE_PROPS", bad) == ["LIVE_CLAUDE_PROPS.calls['a-b'][0].side"]


def test_the_claude_feed_block_wins_over_the_file(tmp_path, monkeypatch):
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"claude_props": {"data": {"calls": [{"name": "X Y"}]}}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert sources.load_claude_props()["calls"] == [{"name": "X Y"}]
    feed.write_text("{}", encoding="utf-8")
    assert len(sources.load_claude_props()["calls"]) == 4, "no feed block: the file is read"


def test_long_rows_sort_after_the_priced_ones(built):
    props = block(built, "LIVE_PROPS")["props"]
    priced = [i for i, p in enumerate(props) if p.get("edge") is not None]
    assert priced and max(priced) < min(i for i, p in enumerate(props) if p["mkt"] == "LONG")
    assert block(built, "LIVE_PROPS")["model"]["modeled"] == len(priced), "LONG is never counted as priced"


def test_long_log_is_aligned_with_the_games(built):
    logs = block(built, "LIVE_PROPS")["logs"]
    assert [slug for slug, log in logs.items() if len(log["v"]["LONG"]) != len(log["g"])] == []
    assert logs["tee-higgins"]["v"]["LONG"][2] == 41


@pytest.mark.integration      # a real build of the page
def test_a_log_without_long_still_builds(monkeypatch):
    """A producer older than Longest reception sends logs with no `v.LONG`; nothing may need it."""
    real = build.load_model_raw

    def old():
        m = real()
        for log in m["logs"].values():
            log["v"].pop("LONG", None)
        m["lines"] = [r for r in m["lines"] if r["market"] != "LONG"]
        return m

    monkeypatch.setattr(build, "load_model_raw", old)
    b = build.render()
    props = injected(b.fragment)["LIVE_PROPS"]
    assert all("LONG" not in log["v"] for log in props["logs"].values())
    # the lines are still in the book's pull: they ride with no model row at all, still null
    longs_ = [p for p in props["props"] if p["mkt"] == "LONG"]
    assert longs_
    assert [p for p in longs_ if not (p["model"] is None and p["pick"] is None)] == []
