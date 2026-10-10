"""Anytime TDs (data/tdwhy.js, data/tdcard.js, 2026-10-09), in Node: the words on a row, the group rule lines, which
rows a kickoff tab shows and in what order, when Claude's picks arrive, and the TD sort on the book's chance.

LIVE_TD_RESEARCH is ff-jarvis's td_research block cut by design/td_research.py (test_td_research.py). The fixture is
week 2: CIN @ NYJ in the morning window (LOCK Brown, Higgins, Chase, Hall; VALUE Wilson; MORE Gesicki; LONG Iosivas),
SEA @ SF Sunday night (VALUE Kittle), DET @ GB Monday (LOCK Gibbs). Claude's CIN @ NYJ call is pending, due 13:00Z.
"""
import json
import pathlib

import pytest

from slips import slugify
from td_research import live_td_research

DATA = pathlib.Path(__file__).parent / "fixtures" / "data"
RAW = json.loads((DATA / "td_research.json").read_text(encoding="utf-8"))
CLAUDE = json.loads((DATA / "claude_props.json").read_text(encoding="utf-8"))
FIX = live_td_research(RAW, CLAUDE)
REQ = "Parlay and DFS"
NOW = "2026-09-12T12:00:00Z"
PROPS = [{"commence": "2026-09-13T17:00:00Z", "win": "morning", "slug": slugify("Chase Brown"), "mkt": "TD"},
         {"commence": "2026-09-13T17:00:00Z", "win": "morning", "slug": slugify("Chase Brown"), "mkt": "RUSH"},
         {"commence": "2026-09-14T00:20:00Z", "win": "snf", "slug": slugify("George Kittle"), "mkt": "TD"},
         {"commence": "2026-09-15T00:15:00Z", "win": "mnf", "slug": slugify("Jahmyr Gibbs"), "mkt": "TD"}]


@pytest.fixture(scope="module")
def td(node_js):
    return node_js("data/tdwhy.js", "data/tdcard.js")


def row(name):
    return next(p for p in FIX["players"] if p["name"] == name)


@pytest.mark.req(REQ, ac="a row's for line is up to three passed checks, the against line the two misses")
def test_the_why_lines(td):
    assert td("tdWhy", row("Chase Brown")) == {
        "forText": "4 red-zone touches a game · 9th-most allowed to RBs · stopped at the 1 or 2 1x lately",
        "against": "Against: team total 21", "chips": []}
    chase = td("tdWhy", row("Ja'Marr Chase"))
    assert chase["forText"] == "1.7 red-zone touches a game · team expected to score 24.5 · NYJ missing 3 defensive starters"
    assert chase["against"] == "" and chase["chips"] == ["Rising"]
    assert td("tdWhy", row("Tee Higgins"))["against"] == "Against: thin red-zone work"
    assert td("tdWhy", row("Garrett Wilson"))["chips"] == ["New role"]


@pytest.mark.req(REQ, ac="an ordinal reads 1st, 2nd, 3rd, 11th, 22nd")
def test_ordinals(td):
    assert [td("tdOrd", n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23)] == [
        "1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd"]


@pytest.mark.req(REQ, ac="each group's rule line and the record come from the packet, never the page")
def test_rule_lines_and_record_come_from_the_packet(td):
    rules = FIX["rules"]
    assert td("tdRuleLine", "LOCK", rules) == "Book 55%+"
    assert td("tdRuleLine", "VALUE", rules) == "Book 30%+ and 3 of 6 checks"
    assert td("tdRuleLine", "LONG", rules) == "Book 20% to 30%"
    assert td("tdRuleLine", "LOCK", {**rules, "lock_min_p": 0.6}) == "Book 60%+"
    assert td("tdRuleLine", "LONG", {**rules, "list_min_p": None}) == ""
    assert td("tdRecordLine", FIX) == "Book 55%+ went 38-18 in weeks 1-4"
    assert td("tdRecordLine", {**FIX, "record": {"LOCK": None}}) == "Record starts week 2"
    assert td("tdTierRecord", "VALUE", FIX["record"]) == ""


@pytest.mark.req(REQ, ac="the sheet lists the six checks with their numbers, his work and the weather")
def test_the_sheet_words(td):
    c = td("tdSheetChecks", row("Chase Brown"))
    assert c["n"] == 3 and len(c["rows"]) == 6
    assert [(r["key"], r["passed"], r["num"]) for r in c["rows"][:3]] == [
        ("rz_work", True, "4"), ("implied_total", False, "21"), ("opp_allowed", True, "9th-most allowed to RBs")]
    assert td("tdWork", row("Chase Brown")) == ["4 red-zone touches a game", "1.3 goal-line carries a game", "11.2% of targets", "71% of snaps"]
    assert td("tdWeather", row("Chase Brown")) == "9 mph wind, 10% rain, 71°F"
    assert td("tdWeather", row("Tee Higgins")) == ""


@pytest.mark.req(REQ, ac="the card follows the open kickoff tab, the book's chance first")
def test_rows_follow_the_tab_in_book_order(td):
    now = td(f"Date.parse('{NOW}')")
    names = [r["name"] for r in td("tdRows", FIX, ["morning"], PROPS, now)]
    assert names == ["Chase Brown", "Tee Higgins", "Ja'Marr Chase", "Breece Hall", "Garrett Wilson", "Mike Gesicki", "Andrei Iosivas"]
    assert [r["name"] for r in td("tdRows", FIX, ["snf", "mnf"], PROPS, now)] == ["Jahmyr Gibbs", "George Kittle"]
    after = td("Date.parse('2026-09-13T17:05:00Z')")
    assert td("tdRows", FIX, ["morning"], PROPS, after) == [], "a game under way drops off"
    g = td("tdGroups", td("tdRows", FIX, ["morning"], PROPS, now))
    assert {k: len(v) for k, v in g.items()} == {"LOCK": 4, "VALUE": 1, "MORE": 1, "LONG": 1}


@pytest.mark.req(REQ, ac="the wait strip shows only while Claude's game in the tab is pending")
def test_pending_and_countdown(td):
    now = td(f"Date.parse('{NOW}')")
    at = td("tdPendingAt", FIX["pending"], ["morning"], PROPS, now)
    assert at == td("Date.parse('2026-09-13T13:00:00Z')")
    assert td("tdPendingAt", FIX["pending"], ["snf", "mnf"], PROPS, now) is None
    assert td("tdLeft", at, now) == "in 25h 0m"
    assert td("tdLeft", 5 * 60000, 0) == "in 5m"
    assert td("tdLeft", 0, 1) == "any minute"


@pytest.mark.req(REQ, ac="the + finds his anytime-TD line, or there is no +")
def test_prop_index(td):
    assert td("tdPropIdx", slugify("Chase Brown"), PROPS) == 0
    assert td("tdPropIdx", slugify("Tee Higgins"), PROPS) == -1


@pytest.mark.req(REQ, ac="TD legs on DraftKings sort by the book's chance; edge is no TD sort")
def test_td_sort_is_the_books_chance(node_js):
    js = node_js("lib/odds.js", "builder/state.js")
    legs = [{"n": "A", "book": "DraftKings", "books": {"DraftKings": {"over": 200}}, "edge": 9},
            {"n": "B", "book": "DraftKings", "books": {"DraftKings": {"over": -150}}, "edge": 1},
            {"n": "C", "book": None, "edge": 5},
            {"n": "D", "book": "DraftKings", "books": {"DraftKings": {"over": 110}}, "edge": 3}]
    assert js("legs => legs.sort(SORTS.book).map(p => p.n)", legs) == ["B", "D", "A", "C"]
    assert js("kindSort", "TD", "dk") == "book"
    assert js("kindSort", "TD", "underdog") == "model"
    assert js("kindSort", "RUSH", "dk") == "edge"
