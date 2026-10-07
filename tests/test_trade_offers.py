"""League > Trades, the finder's file (2026-10-06; Teams > Find trades from 2026-10-05): ff-jarvis's trade_offers.json (v2, priced in
rest-of-season points since 2026-10-06, METHODOLOGY 12.99) is checked and written beside the page by design/trade_offers.py, and
the finder fetches it on first open. The file is tested against tests/fixtures/data/trade_offers.json (Purdy Big in Japan's three
offers to Run It Back and Run It Back's three back, a cut of the producer's file; an AYO owner, hand-made); what the finder draws
from it is test_trade_finder.py, the edit page test_trade_edit.py. A file in the weekly shape (before 2026-10-06) fails the build."""
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
    unnamed = [at for at in ("['Purdy Big in Japan'][0].gain", "[0].send[1].injury", "['Purdy Big in Japan'][1].partner", "leagues['ayo'].week")
               if at not in msg]
    assert unnamed == [], msg
    assert contract.problems("TRADE_OFFERS", None) == []


def test_the_producers_whole_file_passes_the_contract():
    """ff-jarvis trade-ros 1b1fe82: 381 offers in three leagues, every owner and every partner's values."""
    real = json.loads((FIXTURES / "trade_offers_ffjarvis.json").read_text(encoding="utf-8"))
    assert sum(len(o) for lg in real["leagues"].values() for o in lg["teams"].values()) == 381
    assert trade_offers.problems(real) == []


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


def test_the_rules_numbers_the_unit_and_the_two_rule_texts_are_required():
    """The producer's search ran on these numbers (`rules.max_losses` is gone, `min_gain_week` is new on 2026-10-06); the page
    reads the unit and the two texts it ports (`scoring`, `drop`) and the contract proves they are there."""
    assert trade_offers.problems(FIXTURE) == []
    def problems_without(k):
        bad = copy.deepcopy(FIXTURE)
        del bad["rules"][k]
        return trade_offers.problems(bad)

    required = ("min_gain_week", "min_gain", "per_pos", "per_partner_pos", "top", "max_out", "max_in", "unit", "scoring", "drop")
    assert [k for k in required if f"TRADE_OFFERS.rules.{k}" not in problems_without(k)] == []
    no_rules = copy.deepcopy(FIXTURE)
    del no_rules["rules"]
    assert "TRADE_OFFERS.rules" in trade_offers.problems(no_rules)
    gone = copy.deepcopy(FIXTURE)
    gone["rules"].pop("max_losses", None)
    assert trade_offers.problems(gone) == [], "max_losses went with the three-view test; no file carries it now"


def test_a_unit_other_than_rest_of_season_points_fails_closed():
    """The card says "pts rest of season": a file in another unit would print a wrong number under the right words."""
    assert trade_offers.UNIT == "rest of season points" == FIXTURE["rules"]["unit"]
    bad = copy.deepcopy(FIXTURE)
    bad["rules"]["unit"] = "points a week"
    assert trade_offers.problems(bad) == ["TRADE_OFFERS.rules.unit"]


def weekly_shape(doc):
    """The file as it was before 2026-10-06 (weekly gains by proj): no weeks_left, ros_floor, ros_pg / games / priced or
    their.gain, no unit, and rules.max_losses and rules.views."""
    old = copy.deepcopy(doc)
    for k in ("unit", "min_gain_week"):
        del old["rules"][k]
    old["rules"].update(max_losses=1, views=["proj", "work", "pace"])
    for lg in old["leagues"].values():
        del lg["weeks_left"]
        del lg["lineup"]["ros_floor"]
        for rows in lg["values"].values():
            for p in rows:
                for k in ("ros_pg", "games", "priced"):
                    del p[k]
    for o in each_offer(old):
        del o["their"]["gain"]
    return old


def test_the_weekly_shape_fails_the_build_and_names_the_new_fields():
    """Fail closed: a build on data from before 2026-10-06 stops, rather than print a weekly number as rest-of-season points."""
    miss = trade_offers.problems(weekly_shape(FIXTURE))
    assert "TRADE_OFFERS.rules.min_gain_week" in miss and "TRADE_OFFERS.rules.unit" in miss
    assert "TRADE_OFFERS.leagues['espn'].weeks_left" in miss, miss


@pytest.mark.parametrize("path, at", [
    (("leagues", "espn", "weeks_left"), "leagues['espn'].weeks_left"),
    (("leagues", "espn", "lineup", "ros_floor"), "leagues['espn'].lineup.ros_floor"),
    (("leagues", "espn", "values", PARTNER, 0, "ros_pg"), "['Run It Back'][0].ros_pg"),
    (("leagues", "espn", "values", PARTNER, 0, "games"), "['Run It Back'][0].games"),
    (("leagues", "espn", "values", PARTNER, 0, "priced"), "['Run It Back'][0].priced"),
    (("leagues", "espn", "teams", OWNER, 0, "their", "gain"), "['Purdy Big in Japan'][0].their.gain"),
])
def test_each_rest_of_season_field_is_required_on_its_own(path, at):
    bad = copy.deepcopy(FIXTURE)
    node = bad
    for k in path[:-1]:
        node = node[k]
    del node[path[-1]]
    assert any(m.endswith(at) for m in trade_offers.problems(bad)), trade_offers.problems(bad)


def test_a_weekly_shape_file_stops_the_build_at_the_offers_step(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    out = tmp_path / "out"
    out.mkdir()
    (data / "trade_offers.json").write_text(json.dumps(weekly_shape(FIXTURE)), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", tmp_path / "none.json")
    monkeypatch.setattr(sources, "DWR", data)
    with pytest.raises(SystemExit, match=r"TRADE_OFFERS\.rules\.unit"):
        trade_offers.build(out)
    assert list(out.iterdir()) == [], "nothing is written: the page keeps the last good file"


def test_the_drop_rules_fields_are_required():
    """A file from before the drop rule (2026-10-05) fails the build: no IR slots, no keep / ir_ok / protect, no ir_moves."""
    old = copy.deepcopy(FIXTURE)
    for lg in old["leagues"].values():
        lg["lineup"].pop("ir")
        for rows in lg["values"].values():
            for p in rows:
                for k in trade_offers.DROP_VALUE:
                    p.pop(k)
    for o in each_offer(old):
        o.pop("ir_moves")
    miss = trade_offers.problems(old)
    assert any(m.endswith(".lineup.ir") for m in miss), miss
    no_moves = copy.deepcopy(FIXTURE)
    del offers_of(no_moves)[0]["ir_moves"]
    assert any(m.endswith("['Purdy Big in Japan'][0].ir_moves") for m in trade_offers.problems(no_moves))
    no_ir = copy.deepcopy(FIXTURE)
    del no_ir["leagues"]["espn"]["values"][PARTNER][0]["keep"]
    assert any(m.endswith("['Run It Back'][0].keep") for m in trade_offers.problems(no_ir))
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["values"][PARTNER][0]["protect"]
    assert any(m.endswith("['Run It Back'][0].protect") for m in trade_offers.problems(bad))


def test_the_edit_fields_lineup_values_and_other_are_required():
    def problems_without(k):
        bad = copy.deepcopy(FIXTURE)
        del bad["leagues"]["espn"][k]
        return trade_offers.problems(bad)

    assert [k for k in ("lineup", "values", "other") if f"TRADE_OFFERS.leagues['espn'].{k}" not in problems_without(k)] == []
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["lineup"]["cap"]
    assert "TRADE_OFFERS.leagues['espn'].lineup.cap" in trade_offers.problems(bad)
    no_drop = copy.deepcopy(FIXTURE)
    del offers_of(no_drop)[0]["drop"]
    assert any(m.endswith("['Purdy Big in Japan'][0].drop") for m in trade_offers.problems(no_drop))


def test_a_rest_of_season_number_that_is_not_a_number_is_named():
    """The page ports the rule over these: a string or a missing bool would score NaN or the wrong lineup, so the build stops."""
    bad = copy.deepcopy(FIXTURE)
    row = bad["leagues"]["espn"]["values"][PARTNER][0]
    row["ros_pg"] = "14.6"
    row["priced"] = 1
    offers_of(bad)[0]["their"]["gain"] = None
    bad["leagues"]["espn"]["weeks_left"] = 0
    bad["leagues"]["espn"]["lineup"]["ros_floor"]["QB"] = None
    miss = trade_offers.problems(bad)
    unnamed = [at for at in ("['Run It Back'][0].ros_pg", "['Run It Back'][0].priced", ".their.gain", "leagues['espn'].weeks_left", "lineup.ros_floor.QB")
               if not any(m.endswith(at) for m in miss)]
    assert unnamed == [], miss


def test_option_bs_fields_are_required():
    """A file without last2, chips and their fails the build (since 2026-10-05, ff-jarvis 79b2b0b)."""
    old = copy.deepcopy(FIXTURE)
    for lg in old["leagues"].values():
        for rows in lg["values"].values():
            for p in rows:
                del p["last2"], p["chips"]
    assert any(m.endswith(".last2") for m in trade_offers.problems(old))
    no_their = copy.deepcopy(FIXTURE)
    for o in each_offer(no_their):
        del o["their"]
    assert any(m.endswith(".their") for m in trade_offers.problems(no_their))
    bad = copy.deepcopy(FIXTURE)
    del bad["leagues"]["espn"]["values"][PARTNER][0]["chips"]                          # last2 is there, chips is not
    offers = offers_of(bad)
    del offers[1]["their"]["drop"]
    offers[0]["send"][1]["chips"] = "Hot"                                               # a string, not a list
    del offers[0]["their"]["drop"][0]["last2"]
    miss = trade_offers.problems(bad)
    unnamed = [at for at in ("['Run It Back'][0].chips", "[1].their.drop", "[0].send[1].chips", "[0].their.drop[0].last2")
               if not any(m.endswith(at) for m in miss)]
    assert unnamed == [], miss


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
    assert line.startswith("Offers: espn 6 offers from 2 owners, yahoo 0 offers from 0 owners, ayo 2 offers from 1 owner, updated 2026-10-06T11:56"), line
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
    assert '"gain":21.7' not in built.fragment and '"gain": 21.7' not in built.fragment, "fetched, never injected"
    assert f'const TB_URL = "{trade_offers.NAME}"' in built.fragment


def test_vercel_serves_the_file_git_marks_it_generated_and_land_folds_it_in():
    assert f"!{trade_offers.NAME}" in (REPO / ".vercelignore").read_text(encoding="utf-8").split(), ".vercelignore is an allowlist"
    attrs = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(trade_offers.NAME)}\s+-diff merge=ours", attrs, re.M)
    assert f'"{trade_offers.NAME}"' in (REPO / "scripts" / "land.ps1").read_text(encoding="utf-8")
