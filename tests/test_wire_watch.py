"""design/wire_watch.py: the Breaking rail's block, against the fixture, and its contract."""
import copy
import json
import re

import contract
import wire_watch
from conftest import FIXTURES


def _wire(built):
    m = re.search(r"^const LIVE_WIRE = (.*);$", built.fragment, re.M)
    return json.loads(m.group(1).replace("<\\/", "</"))


def test_block_keeps_both_leagues_and_every_kind(built):
    w = _wire(built)
    assert w["asof"] == "2026-09-23T14:30:00-07:00"
    assert list(w["leagues"]) == ["espn", "yahoo"]
    kinds = {e["kind"] for lg in w["leagues"].values() for e in lg["events"]}
    assert kinds == {"path", "drop", "status", "adds"}
    path = next(e for e in w["leagues"]["espn"]["events"] if e["kind"] == "path")
    assert path["because"] == {"key": "de'von achane", "name": "De'Von Achane", "status": "O",
                               "practice": "DNP", "note": "hamstring"}
    assert contract.problems("LIVE_WIRE", w) == []


def test_a_starting_drop_and_an_unknown_status_pass_through(built):
    yahoo = _wire(built)["leagues"]["yahoo"]["events"]
    start = next(e for e in yahoo if e["kind"] == "drop" and e["verdict"]["start"])
    assert (start["verdict"]["kind"], start["verdict"]["slot"]) == ("bench", "FLEX")
    need = next(e for e in yahoo if e["kind"] == "drop" and e["verdict"]["kind"] == "need")
    assert need["verdict"]["start"] is None and need["verdict"]["slot"] is None   # optional, null
    assert next(e for e in yahoo if e["kind"] == "path")["status"] == "unknown"


def test_producer_order_is_kept(built):
    """Newest first within a league is the producer's promise; the rail's kind order is the JS's."""
    ats = [e["at"] for e in _wire(built)["leagues"]["espn"]["events"]]
    assert ats == sorted(ats, reverse=True)


def _write(tmp_path, file_asof, feed_asof):
    lg = {"espn": {"events": []}}
    (tmp_path / "feed.json").write_text(json.dumps({"wire_watch": {"data": {"asof": feed_asof, "leagues": lg, "src": "feed"}}}))
    (tmp_path / "wire_watch.json").write_text(json.dumps({"asof": file_asof, "leagues": lg, "src": "file"}))


def test_a_tie_reads_the_file_and_a_newer_feed_wins(tmp_path):
    _write(tmp_path, "2026-09-23T14:30:00-07:00", "2026-09-23T14:30:00-07:00")
    assert wire_watch.load_wire(tmp_path / "feed.json", tmp_path)["src"] == "file"
    # Same instant in another zone is still a tie: parsed, not compared as strings.
    _write(tmp_path, "2026-09-23T14:30:00-07:00", "2026-09-23T17:30:00-04:00")
    assert wire_watch.load_wire(tmp_path / "feed.json", tmp_path)["src"] == "file"
    _write(tmp_path, "2026-09-23T14:30:00-07:00", "2026-09-23T15:00:00-07:00")
    assert wire_watch.load_wire(tmp_path / "feed.json", tmp_path)["src"] == "feed"


def test_missing_block_is_none(tmp_path):
    (tmp_path / "feed.json").write_text("{}")
    assert wire_watch.live_wire(tmp_path / "feed.json", tmp_path) is None


def test_a_dropped_field_fails_the_contract(tmp_path):
    """The loader never fills a required field, so the gap reaches the contract by name."""
    bad = copy.deepcopy(json.loads((FIXTURES / "data" / "wire_watch.json").read_text(encoding="utf-8")))
    del bad["leagues"]["espn"]["events"][2]["because"]["status"]    # the path event
    del bad["leagues"]["yahoo"]["events"][0]["mine"]                  # the status event
    (tmp_path / "wire_watch.json").write_text(json.dumps(bad))
    (tmp_path / "feed.json").write_text("{}")
    w = wire_watch.live_wire(tmp_path / "feed.json", tmp_path)
    assert contract.problems("LIVE_WIRE", w) == [
        "LIVE_WIRE.leagues['espn'].events[2].because.status",
        "LIVE_WIRE.leagues['yahoo'].events[0].mine",
    ]


def test_an_optional_field_may_be_absent(tmp_path):
    src = {"asof": "2026-09-23T14:30:00-07:00", "leagues": {"espn": {"events": [
        {"kind": "adds", "at": "2026-09-23T13:10:00-07:00", "key": "x", "name": "X Y", "pos": "RB", "team": "SEA", "count": 2},
        {"kind": "pass", "at": "2026-09-23T13:10:00-07:00"}]}}}          # an unknown kind is dropped
    (tmp_path / "wire_watch.json").write_text(json.dumps(src))
    (tmp_path / "feed.json").write_text("{}")
    w = wire_watch.live_wire(tmp_path / "feed.json", tmp_path)
    assert w["leagues"]["espn"]["events"][0]["headline"] is None
    assert len(w["leagues"]["espn"]["events"]) == 1
    assert contract.problems("LIVE_WIRE", w) == []
