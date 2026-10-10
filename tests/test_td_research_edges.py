"""design/td_research.py edges (2026-10-09): the loader's order, a row with no usable price or name, the producer's
book order, and the build report's exact line. The happy path is test_td_research.py."""
import json
import pathlib

import pytest

import td_research
from td_research import live_td_research, report

DATA = pathlib.Path(__file__).parent / "fixtures" / "data"
RAW = json.loads((DATA / "td_research.json").read_text(encoding="utf-8"))
CLAUDE = json.loads((DATA / "claude_props.json").read_text(encoding="utf-8"))

pytestmark = pytest.mark.req("Parlay and DFS", ac="Anytime TDs card")


def test_the_loader_reads_the_feed_block_first_then_the_file(monkeypatch, tmp_path):
    asked = []
    monkeypatch.setattr(td_research, "DWR", tmp_path)
    monkeypatch.setattr(td_research, "read_first", lambda *p: asked.append(p) or {"from": "file"})
    monkeypatch.setattr(td_research, "feed_block", lambda keys, must: {"from": "feed", "keys": keys, "must": must})
    assert td_research.load_td_research() == {"from": "feed", "keys": ("td_research",), "must": "players"}
    assert asked == []
    monkeypatch.setattr(td_research, "feed_block", lambda keys, must: None)
    assert td_research.load_td_research() == {"from": "file"}
    assert asked == [(tmp_path / "td_research.json",)]
    monkeypatch.setattr(td_research, "read_first", lambda *p: None)
    assert td_research.load_td_research() is None


def _one(**row):
    base = dict(RAW["players"][0])
    base.update(row)
    return live_td_research({**RAW, "players": [base]})["players"][0]


def test_a_row_with_no_number_for_a_price_carries_no_book():
    assert _one(book=None)["book"] is None
    assert _one(book={"p": "0.6", "price": -150})["book"] is None
    assert _one(book={"p": 0.6, "price": -150, "books": {"DraftKings": -150}})["book"] == {"p": 0.6, "price": -150, "book": "DraftKings"}


def test_the_slug_is_the_name_else_the_key_else_empty():
    assert _one(name="Chase Brown", key="someone else")["slug"] == td_research.slugify("Chase Brown")
    assert _one(name=None, key="chase brown")["slug"] == td_research.slugify("chase brown")
    assert _one(name=None, key=None)["slug"] == td_research.slugify("")


def test_the_shown_book_follows_the_producers_order_else_draftkings_first():
    tie = {"p": 0.55, "price": -125, "books": {"DraftKings": -125, "Consensus": -125}}
    rules = {k: v for k, v in RAW["rules"].items() if k != "book_order"}
    row = {**RAW["players"][0], "book": tie}
    plain = live_td_research({**RAW, "rules": rules, "players": [row]})["players"][0]
    assert plain["book"]["book"] == "DraftKings"
    flipped = live_td_research({**RAW, "rules": {**rules, "book_order": {"value": ["Consensus", "DraftKings"]}}, "players": [row]})
    assert flipped["players"][0]["book"]["book"] == "Consensus"


def test_the_build_report_line():
    assert report(None) == "Anytime TDs: no td_research block, so no card on Slips"
    assert report(live_td_research(RAW, CLAUDE)) == "Anytime TDs: week 2, LOCK 5, VALUE 2, MORE 1, LONG 1, 1 pending"
    assert report(live_td_research(RAW)) == "Anytime TDs: week 2, LOCK 5, VALUE 2, MORE 1, LONG 1, 0 pending"
