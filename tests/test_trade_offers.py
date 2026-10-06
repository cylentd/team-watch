"""League > Trades, the finder's file (2026-10-06; Teams > Find trades from 2026-10-05): ff-jarvis's trade_offers.json (v2) is
checked and written beside the page by design/trade_offers.py, and the finder fetches it on first open. The file is tested
against tests/fixtures/data/trade_offers.json (Purdy Big in Japan's three offers to Run It Back and Run It Back's six back,
injured players, an AYO owner); what the finder draws from it is test_trade_finder.py, the edit page test_trade_edit.py."""
import copy
import json
import pathlib
import re
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402
import sources  # noqa: E402
import trade_offers  # noqa: E402
from conftest import FIXTURES, REPO  # noqa: E402

FIXTURE = json.loads((FIXTURES / "data" / "trade_offers.json").read_text(encoding="utf-8"))
OWNER, PARTNER = "Purdy Big in Japan", "Run It Back"


def offers_of(doc, owner=OWNER):
    return doc["leagues"]["espn"]["teams"][owner]


def each_offer(doc):
    for lg in doc["leagues"].values():
        for offers in lg["teams"].values():
            yield from offers


# ---- the file: read, checked, written ---------------------------------------------------------------

def test_the_offers_are_read_from_the_file_and_the_feed_block_wins(tmp_path, monkeypatch):
    assert sources.load_trade_offers() == FIXTURE, "the fixture feed has no block, so the file is read"
    block = {"updated": "2026-10-06T01:00", "season": 2026, "leagues": {"espn": {"week": 5, "teams": {}}}}
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"trade_offers": {"data": block, "fetched": block["updated"]}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert sources.load_trade_offers() == block


def test_no_feed_block_and_no_file_is_none(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert sources.load_trade_offers() is None


def test_the_contract_passes_the_fixture_and_names_every_missing_field():
    contract.validate("TRADE_OFFERS", FIXTURE)
    bad = copy.deepcopy(FIXTURE)
    offers = offers_of(bad)
    del offers[0]["gain"]
    del offers[0]["send"][1]["injury"]
    del offers[1]["partner"]
    del bad["leagues"]["ayo"]["week"]
    with pytest.raises(SystemExit) as e:
        contract.validate("TRADE_OFFERS", bad)
    msg = str(e.value)
    for at in ("['Purdy Big in Japan'][0].gain", "[0].send[1].injury", "['Purdy Big in Japan'][1].partner", "leagues['ayo'].week"):
        assert at in msg, at
    assert contract.problems("TRADE_OFFERS", None) == []


def test_every_offer_names_its_partner_and_the_v1_shape_fails_the_build():
    """v2 (2026-10-06): owner -> one flat list, each offer with its `partner`. v1 was owner -> partner -> {bold, fair}."""
    assert all(isinstance(o["partner"], str) and o["partner"] for o in each_offer(FIXTURE))
    v1 = copy.deepcopy(FIXTURE)
    v1["leagues"]["espn"]["teams"][OWNER] = {PARTNER: {"bold": offers_of(FIXTURE), "fair": []}}
    assert trade_offers.problems(v1), "a dict of partners where the list of offers belongs"
    flat_no_partner = copy.deepcopy(FIXTURE)
    for o in each_offer(flat_no_partner):
        del o["partner"]
    assert any(m.endswith("[0].partner") for m in trade_offers.problems(flat_no_partner))


def test_the_rules_numbers_are_required_and_max_losses_is_one_of_them():
    """The producer's search ran on these (`rules.max_losses` is new in v2); the page reads none, the contract proves they are there."""
    assert trade_offers.problems(FIXTURE) == []
    for k in ("max_losses", "per_pos", "per_partner_pos"):
        bad = copy.deepcopy(FIXTURE)
        del bad["rules"][k]
        assert f"TRADE_OFFERS.rules.{k}" in trade_offers.problems(bad), k
    no_rules = copy.deepcopy(FIXTURE)
    del no_rules["rules"]
    assert "TRADE_OFFERS.rules" in trade_offers.problems(no_rules)


def without_drop_rule(doc):
    """The file as it was before the drop rule: no IR slots, no keep / ir_ok / protect, no ir_moves."""
    old = copy.deepcopy(doc)
    for lg in old["leagues"].values():
        lg["lineup"].pop("ir")
        for rows in lg["values"].values():
            for p in rows:
                for k in trade_offers.DROP_VALUE:
                    p.pop(k)
    for o in each_offer(old):
        o.pop("ir_moves")
    return old


def test_the_drop_rules_fields_are_required(monkeypatch):
    """Required since 2026-10-05 (ff-jarvis 4e69378): a file from before the drop rule fails the build."""
    old = without_drop_rule(FIXTURE)
    assert trade_offers.DROP_RULE_REQUIRED is True
    miss = trade_offers.problems(old)
    assert any(m.endswith(".lineup.ir") for m in miss), miss
    monkeypatch.setattr(trade_offers, "DROP_RULE_REQUIRED", False)
    assert trade_offers.problems(old) == [], "with the flag off the old shape passes, so the flag is what enforces it"
    monkeypatch.undo()
    assert trade_offers.problems(FIXTURE) == [], "the fixture follows the spec exactly"
    no_moves = copy.deepcopy(FIXTURE)
    del offers_of(no_moves)[0]["ir_moves"]
    assert any(m.endswith("['Purdy Big in Japan'][0].ir_moves") for m in trade_offers.problems(no_moves))
    no_ir = copy.deepcopy(FIXTURE)
    del no_ir["leagues"]["espn"]["values"][PARTNER][0]["keep"]
    assert any(m.endswith("['Run It Back'][0].keep") for m in trade_offers.problems(no_ir))


def test_present_drop_rule_fields_are_checked_even_while_optional():
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["values"][PARTNER][0]["protect"]      # keep and ir_ok are there, protect is not
    del offers_of(bad, PARTNER)[1]["ir_moves"][0]["slug"]
    miss = trade_offers.problems(bad)
    assert any(m.endswith("['Run It Back'][0].protect") for m in miss), miss
    assert any(m.endswith("['Run It Back'][1].ir_moves[0].slug") for m in miss), miss


def without_option_b(doc, their=True, players=True):
    """The file as it was before option B: no `last2` or `chips` on any player, no `their` on any offer."""
    old = copy.deepcopy(doc)
    for lg in old["leagues"].values():
        for rows in lg["values"].values():
            for p in rows:
                if players:
                    del p["last2"], p["chips"]
    for o in each_offer(old):
        if players:
            for side in ("send", "get", "drop", "ir_moves"):
                for p in o[side]:
                    del p["last2"], p["chips"]
            for side in ("ir_moves", "drop"):
                for p in o["their"][side]:
                    del p["last2"], p["chips"]
        if their:
            del o["their"]
    return old


def test_option_bs_fields_are_required(monkeypatch):
    """Required since 2026-10-05 (ff-jarvis 79b2b0b): a file without last2, chips and their fails the build."""
    assert trade_offers.OPTION_B_REQUIRED is True
    assert any(m.endswith(".last2") for m in trade_offers.problems(without_option_b(FIXTURE, their=False)))
    assert any(m.endswith(".their") for m in trade_offers.problems(without_option_b(FIXTURE, players=False)))
    monkeypatch.setattr(trade_offers, "OPTION_B_REQUIRED", False)
    assert trade_offers.problems(without_option_b(FIXTURE)) == [], "with the flag off the old shape passes"
    monkeypatch.undo()
    assert trade_offers.problems(FIXTURE) == [], "the fixture follows the spec exactly"
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["values"][PARTNER][0]["chips"]                          # last2 is there, chips is not
    offers = offers_of(bad)
    del offers[1]["their"]["drop"]
    offers[0]["send"][1]["chips"] = "Hot"                                               # a string, not a list
    del offers[0]["their"]["ir_moves"][0]["last2"]
    miss = trade_offers.problems(bad)
    for at in ("['Run It Back'][0].chips", "[1].their.drop", "[0].send[1].chips", "[0].their.ir_moves[0].last2"):
        assert any(m.endswith(at) for m in miss), (at, miss)


def test_a_null_last2_is_a_value_and_a_missing_one_is_not():
    ok = copy.deepcopy(FIXTURE)
    ok["leagues"]["espn"]["values"][PARTNER][0]["last2"] = None             # a rookie with one game
    assert trade_offers.problems(ok) == []
    del ok["leagues"]["espn"]["values"][PARTNER][0]["last2"]
    assert any(m.endswith("['Run It Back'][0].last2") for m in trade_offers.problems(ok))


def test_a_null_injury_is_a_value_and_a_missing_one_is_not():
    ok = copy.deepcopy(FIXTURE)
    assert offers_of(ok)[0]["send"][1]["injury"] is None
    assert trade_offers.problems(ok) == []


def test_build_writes_the_same_data_compact_beside_the_page(tmp_path):
    line = trade_offers.build(tmp_path)
    assert line.startswith("Offers: espn 9 offers from 2 owners, yahoo 0 offers from 0 owners, ayo 2 offers from 1 owner, updated 2026-10-05T14:07"), line
    text = (tmp_path / trade_offers.NAME).read_text(encoding="utf-8")
    assert json.loads(text) == FIXTURE
    assert text == json.dumps(FIXTURE, ensure_ascii=False, separators=(",", ":")), "compact: the file is fetched by every reader"


def test_the_summary_counts_an_owner_less_league_as_zero():
    doc = copy.deepcopy(FIXTURE)
    doc["leagues"]["yahoo"]["teams"] = {}
    assert "yahoo 0 offers from 0 owners" in trade_offers.summary(doc)


def test_build_with_no_offers_writes_nothing_and_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    assert trade_offers.build(out).startswith("Offers: none")
    assert list(out.iterdir()) == []


def test_build_refuses_a_file_missing_a_field(tmp_path, monkeypatch):
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["ayo"]["teams"]["Taylor Made for Sundays"][1]["get"][0]["slug"]
    (tmp_path / "trade_offers.json").write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", tmp_path)
    with pytest.raises(SystemExit, match=r"\[1\]\.get\[0\]\.slug"):
        trade_offers.build(tmp_path)


def test_the_offers_are_not_in_the_page_and_the_page_names_the_file_the_build_writes(built):
    assert '"gain":8.5' not in built.fragment and '"gain": 8.5' not in built.fragment, "fetched, never injected"
    assert f'const TB_URL = "{trade_offers.NAME}"' in built.fragment


def test_vercel_serves_the_file_git_marks_it_generated_and_land_folds_it_in():
    assert f"!{trade_offers.NAME}" in (REPO / ".vercelignore").read_text(encoding="utf-8").split(), ".vercelignore is an allowlist"
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(trade_offers.NAME)}\s+-diff merge=ours", attrs, re.M)
    assert f'"{trade_offers.NAME}"' in (REPO / "scripts" / "land.ps1").read_text(encoding="utf-8")
