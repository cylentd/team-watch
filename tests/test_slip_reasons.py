"""The data wiring of the Slips research board (2026-10-03): LIVE_REASONS from ff-jarvis's
slip_reasons.json, and the unpriced Longest reception (`LONG`) market in LIVE_PROPS. No browser."""
import json
import sys
from pathlib import Path

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
    assert set(reasons["tee-higgins"]) == {"why", "work", "tags"}
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
    for p in rows:
        assert p["model"] is None and p["pick"] is None and p["conf"] is None and p["edge"] is None
        assert not p.get("norole") and not p.get("stale"), "an unpriced market is not a no-role touchdown line"
        assert p["mu"] is not None and p["line"] is not None
        for x in p["books"].values():
            assert x["model"] is None and x["pick"] is None and x["conf"] is None
    higgins = next(p for p in rows if p["n"] == "Tee Higgins")
    assert higgins["books"]["Underdog"]["line"] == 23.5 and higgins["books"]["DraftKings"]["line"] == 22.5
    assert higgins["mu"] == 21.6 and higgins["games"] == 8


def test_long_rows_sort_after_the_priced_ones(built):
    props = block(built, "LIVE_PROPS")["props"]
    priced = [i for i, p in enumerate(props) if p.get("edge") is not None]
    assert priced and max(priced) < min(i for i, p in enumerate(props) if p["mkt"] == "LONG")
    assert block(built, "LIVE_PROPS")["model"]["modeled"] == len(priced), "LONG is never counted as priced"


def test_long_log_is_aligned_with_the_games(built):
    logs = block(built, "LIVE_PROPS")["logs"]
    for slug, log in logs.items():
        assert len(log["v"]["LONG"]) == len(log["g"]), slug
    assert logs["tee-higgins"]["v"]["LONG"][2] == 41


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
    for p in props["props"]:
        if p["mkt"] == "LONG":
            assert p["model"] is None and p["pick"] is None
