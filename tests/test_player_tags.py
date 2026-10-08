"""LIVE_PLAYER_TAGS (2026-10-08, ledger #41): ff-jarvis's player_tags block, cut by design/player_tags.py for the
tags on Roster rows, Ranks rows and the profile. The file holds numbers only; every word is the page's.

David's decisions (2026-10-08): show RISING, TRENDING and POTENTIAL (named Sleeper on the page); hide LUCKY until
ff-jarvis re-tests a sharper rule; never show ff-jarvis's own SLEEPER tag. The cut drops both; the effect number travels
only with the signals the file names for it.

The fixture (tests/fixtures/data/player_tags.json) is the producer's shape since ff-jarvis 0bb6610 (no SLEEPER entry,
`league` always null): Chase Brown has two POTENTIAL signals, and two George Kittles share a name, so each is keyed
`<slug>-<team>`.
"""
import copy
import json
import pathlib

import pytest

import contract
from player_tags import SHOWN, SIGNALS, live_player_tags, problems, report

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "data" / "player_tags.json"
REQ = "Player tags"


@pytest.fixture(scope="module")
def raw():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def block(raw):
    return live_player_tags(raw)


@pytest.mark.req(REQ, ac="ff-jarvis's own SLEEPER tag is never shown: an older file's entries are dropped, and a player with only one has no tags")
def test_an_older_files_sleeper_entries_are_dropped(raw):
    """ff-jarvis stopped writing SLEEPER (0bb6610); a file from before it still must not show one."""
    old = copy.deepcopy(raw)
    old["players"]["brock-purdy"] = [{"tag": "SLEEPER", "kind": "fact", "league": "yahoo", "nums": {"rank": 11}}]
    old["players"]["chase-brown"].insert(0, {"tag": "SLEEPER", "kind": "fact", "league": "espn", "nums": {"rank": 14}})
    got = live_player_tags(old)
    assert "SLEEPER" not in {e["tag"] for es in got["players"].values() for e in es}
    assert "brock-purdy" not in got["players"]
    assert [e["tag"] for e in got["players"]["chase-brown"]] == ["POTENTIAL", "POTENTIAL"]


@pytest.mark.req(REQ, ac="each shown entry keeps its tag, kind and numbers, in the file's order")
def test_an_entry_keeps_its_tag_kind_and_numbers(block):
    assert block["players"]["breece-hall"] == [
        {"tag": "RISING", "kind": "fact", "nums": {"last": 16.6, "earlier": 10.0, "delta": 6.6}},
        {"tag": "TRENDING", "kind": "fact", "nums": {"rank": 9, "adds": 236169}}]
    assert block["players"]["chase-brown"][1]["nums"]["signal"] == "ROUTES_FIRST"


@pytest.mark.req(REQ, ac="LUCKY is hidden: its entries are dropped, and a player with only a LUCKY tag has no tags")
def test_lucky_is_hidden_until_ff_jarvis_retests_it(raw, block):
    assert any(e["tag"] == "LUCKY" for es in raw["players"].values() for e in es), "the fixture carries LUCKY entries"
    assert "LUCKY" not in {e["tag"] for es in block["players"].values() for e in es}
    assert "joe-burrow" not in block["players"]


@pytest.mark.req(REQ, ac="two players who share a name stay apart under their slug-team keys")
def test_a_shared_name_keeps_both_team_keys(block):
    assert block["players"]["george-kittle-sf"][0]["tag"] == "RISING"
    assert block["players"]["george-kittle-buf"][0]["tag"] == "TRENDING"
    assert "george-kittle" not in block["players"]


@pytest.mark.req(REQ, ac="the numbers the page's words need pass through from the rules: games counted, hours, the effect and its signals")
def test_the_rule_numbers_the_words_need_pass_through(raw, block):
    assert (block["last_n"], block["hours"]) == (3, 24)
    assert block["effect"] == 1.17
    assert block["effect_signals"] == ["ROOKIE_RAMP", "ROUTES_FIRST", "EFFICIENT_PARTTIMER"]
    assert "VACATED" not in block["effect_signals"]
    assert (block["season"], block["week"], block["through"]) == (2026, 3, 2)
    assert block["alias"]["LA"] == "LAR"


def test_a_file_with_no_effect_carries_none(raw):
    bare = copy.deepcopy(raw)
    del bare["rules"]["POTENTIAL"]["thresholds"]["effect_xfp_pg"]
    got = live_player_tags(bare)
    assert (got["effect"], got["effect_signals"]) == (None, [])


@pytest.mark.req(REQ, ac="a tag the page has no words for is dropped, never drawn blank")
def test_an_unknown_tag_is_dropped(raw):
    odd = copy.deepcopy(raw)
    odd["players"]["jahmyr-gibbs"].append({"tag": "STREAKY", "kind": "fact", "league": None, "nums": {"n": 1}})
    assert [e["tag"] for e in live_player_tags(odd)["players"]["jahmyr-gibbs"]] == ["RISING", "TRENDING"]


def test_the_shown_tags_are_davids_three_and_the_signals_the_producers_four():
    assert set(SHOWN) == {"RISING", "TRENDING", "POTENTIAL"}
    assert SIGNALS == ("VACATED", "ROOKIE_RAMP", "ROUTES_FIRST", "EFFICIENT_PARTTIMER")


@pytest.mark.req(REQ, ac="no file, an empty one or one with no shown tag is no block, and the page draws no tags")
@pytest.mark.parametrize("raw_in", [None, {}, {"players": {}},
                                    {"rules": {}, "players": {"x": [{"tag": "SLEEPER", "kind": "fact", "nums": {"rank": 1}}]}}])
def test_no_players_means_no_block(raw_in):
    assert live_player_tags(raw_in) is None
    assert "no player_tags" in report(None)


@pytest.mark.req(REQ, ac="the block meets the contract, and a missing field is named")
def test_the_block_meets_the_contract_and_names_a_gap(block):
    assert contract.problems("LIVE_PLAYER_TAGS", block) == []
    assert contract.problems("LIVE_PLAYER_TAGS", None) == []
    bad = copy.deepcopy(block)
    del bad["hours"]
    assert contract.problems("LIVE_PLAYER_TAGS", bad) == ["LIVE_PLAYER_TAGS.hours"]


@pytest.mark.req(REQ, ac="an entry whose numbers the words need are missing, or whose kind or signal is unknown, fails the build by name")
def test_a_bad_entry_fails_by_name(block):
    bad = copy.deepcopy(block)
    del bad["players"]["jahmyr-gibbs"][0]["nums"]["earlier"]
    bad["players"]["tee-higgins"][0]["kind"] = "maybe"
    bad["players"]["chase-brown"][1]["nums"]["signal"] = "HUNCH"
    assert problems(bad) == ["LIVE_PLAYER_TAGS.players['chase-brown'][1].nums.signal 'HUNCH'",
                             "LIVE_PLAYER_TAGS.players['jahmyr-gibbs'][0].nums.earlier",
                             "LIVE_PLAYER_TAGS.players['tee-higgins'][0].kind 'maybe'"]
    with pytest.raises(SystemExit, match="LIVE_PLAYER_TAGS"):
        contract.validate("LIVE_PLAYER_TAGS", bad)


@pytest.mark.req(REQ, ac="the feed block is read first, then the file, else nothing")
def test_the_feed_block_beats_the_file_and_neither_means_none(raw, tmp_path, monkeypatch):
    import player_tags
    import sources
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"player_tags": {"data": {**raw, "week": 9}, "fetched": "x"}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    monkeypatch.setattr(player_tags, "DWR", tmp_path / "nowhere")
    assert player_tags.load_player_tags()["week"] == 9
    feed.write_text(json.dumps({"player_tags": {"data": None, "fetched": None}}), encoding="utf-8")
    assert player_tags.load_player_tags() is None
    (tmp_path / "nowhere").mkdir()
    (tmp_path / "nowhere" / "player_tags.json").write_text(json.dumps(raw), encoding="utf-8")
    assert player_tags.load_player_tags()["week"] == 3


def test_the_report_counts_players_and_tags(block):
    assert report(block) == "Player tags: week 3, 6 players (POTENTIAL 2, RISING 3, TRENDING 4)"
