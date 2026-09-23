"""design/waiver.py: the Waivers sub-tab's block, against the fixture packet."""
import json
import re

import contract


def _waiver(built):
    m = re.search(r"^const LIVE_WAIVER = (.*);$", built.fragment, re.M)
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_block_carries_league_meta_in_packet_order(built):
    w = _waiver(built)
    assert w["week"] == 3 and w["clears"] == "2026-09-23T03:00:00-04:00"
    assert list(w["leagues_meta"]) == ["espn", "yahoo"]
    assert w["leagues_meta"]["espn"] == {"label": "ESPN", "faab_left": 64, "faab_budget": 100,
                                        "clears": "2026-09-23T03:00:00-04:00", "needs": ["TE"]}


def test_one_card_per_player_grouped_by_tier(built):
    """Emanuel Wilson is on both leagues' wires: one card, and the first league's record wins
    (the Yahoo copy has an empty `leagues` map and would drop his ESPN row)."""
    rows = _waiver(built)["players"]
    names = [r["n"] for r in rows]
    assert names.count("Emanuel Wilson") == 1
    assert [r["tier"] for r in rows] == ["must", "worth", "worth", "watch", "watch", "watch", "spec", "stash"]
    wilson = rows[0]
    assert wilson["slug"] == "emanuel-wilson" and set(wilson["leagues"]) == {"espn", "yahoo"}
    assert wilson["leagues"]["espn"]["verdict"] == {"kind": "start", "over": "Chase Brown", "slot": "FLEX", "margin": 4.6}
    assert wilson["leagues"]["espn"]["drop"] == {"name": "Tee Higgins", "pos": "WR", "pts": 6.1}


def test_rows_keep_injury_news_and_summary_source(built):
    rows = {r["n"]: r for r in _waiver(built)["players"]}
    pw = rows["Parker Washington"]
    assert (pw["injury"], pw["injury_note"], pw["practice"], pw["news_count"]) == ("Q", "ankle", "LP", 2)
    assert pw["summary"]["src"] == "rule" and pw["leagues"]["yahoo"]["status"] == "rostered"
    assert rows["Tyler Shough"]["summary"] is None
    assert rows["Tyler Allgeier"]["tier"] == "stash"


def test_a_same_day_tie_reads_the_file_not_the_feed(tmp_path):
    # 2026-09-22: the feed's older same-date copy won the tie and every card landed under Watch.
    import waiver
    lg = {"espn": {"wire": []}}
    (tmp_path / "feed.json").write_text(json.dumps({"waiver": {"data": {"date": "2026-09-22", "leagues": lg, "src": "feed"}}}))
    (tmp_path / "waiver_packet.json").write_text(json.dumps({"date": "2026-09-22", "leagues": lg, "src": "file"}))
    assert waiver.load_packet(tmp_path / "feed.json", tmp_path)["src"] == "file"


def _block(**row):
    base = {k: None for k in contract.WAIVER_ROW}
    base["leagues"] = {}
    base.update(row)
    meta = {k: None for k in contract.WAIVER_META}
    return {"date": "", "week": 3, "clears": "", "leagues_meta": {"espn": meta}, "players": [base]}


def test_a_row_missing_a_field_fails_the_contract():
    obj = _block()
    del obj["players"][0]["tier"]
    assert contract.problems("LIVE_WAIVER", obj) == ["LIVE_WAIVER.players[0].tier"]


def test_a_league_view_missing_a_field_fails_the_contract():
    lg = {"status": "fa", "clears": None, "need": False, "verdict": {"kind": "start", "over": "X", "slot": "RB"},
          "drop": None}
    obj = _block(leagues={"espn": lg})
    assert contract.problems("LIVE_WAIVER", obj) == ["LIVE_WAIVER.players[0].leagues['espn'].verdict.margin"]


def test_league_meta_missing_faab_fails_the_contract():
    obj = _block()
    del obj["leagues_meta"]["espn"]["faab_left"]
    assert contract.problems("LIVE_WAIVER", obj) == ["LIVE_WAIVER.leagues_meta['espn'].faab_left"]
