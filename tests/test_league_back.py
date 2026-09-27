"""design/league_back.py through live_league_yahoo against the 4-team fixture plus a week 2 box score
and roast: each game's records, dig, stamp and box; the bench award; the tape; the record book."""
import json
import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))
import contract                              # noqa: E402
from league_recap import live_league_yahoo   # noqa: E402
from _espn import slugify                    # noqa: E402

FIX = REPO / "tests" / "fixtures" / "data"
read = lambda n: json.loads((FIX / n).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def back():
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify, read("yahoo_league_box.json"), read("yahoo_league_recap.json"))
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    return b


def test_a_roasted_week_carries_its_words(back):
    w2 = back["weeks"][1]
    assert w2["head"] == "CHAT SURVIVES BY 0.44" and w2["dek"].startswith("Jaxon The Box")
    g = {f"{x['a']}-{x['b']}": x for x in w2["games"]}
    assert g["7-3"]["stamp"] == "BURIED" and g["10-9"]["stamp"] is None
    assert g["10-9"]["dig"].startswith("Jaxon The Box started")


def test_a_skipped_week_draws_scores_without_words(back):
    w1 = back["weeks"][0]
    assert w1["head"] is None and w1["dek"] is None
    assert all(g["dig"] is None and g["box"] is None for g in w1["games"])


def test_records_are_after_that_week(back):
    w1, w2 = ({f"{x['a']}-{x['b']}": x for x in w["games"]} for w in back["weeks"])
    assert (w1["9-10"]["ar"], w1["9-10"]["br"]) == ("0–1", "1–0")
    assert (w2["10-9"]["ar"], w2["10-9"]["br"]) == ("1–1", "1–1")


def test_box_is_slim_and_keeps_empty_slots_and_the_mistake(back):
    box = {f"{x['a']}-{x['b']}": x for x in back["weeks"][1]["games"]}["10-9"]["box"]
    assert box["slots"] == [["QB", "Justin Herbert", 20.24, "Josh Allen", 40.82], ["RB", "Jaylen Warren", 6.5, None, None]]
    assert box["proj"] == [104.5, 110.2]
    assert box["left"] == [{"benched": "Rico Dowdle", "bp": 15.5, "started": "Jaylen Warren", "sp": 6.5, "lost": 9.0}, None]


def test_bench_award_is_the_weeks_biggest_mistake(back):
    assert back["weeks"][1]["awards"]["bench"] == {"id": 10, "v": 9.0, "name": "Rico Dowdle"}
    assert "bench" not in back["weeks"][0]["awards"]


def test_tape_fields_on_every_team(back):
    for tm in back["teams"]:
        assert len(tm["all"]) == 3 and isinstance(tm["titles"], list) and isinstance(tm["lasts"], list)


def test_book_splits_fame_and_shame(back):
    fame = [f["k"] for f in back["book"]["fame"]]
    shame = [f["k"] for f in back["book"]["shame"]]
    assert fame[:2] == ["high", "blow"] and shame[0] == "low"
    assert "robbed" in shame and "stole" in shame
    assert not set(fame) & set(shame)


def test_without_box_or_roast_the_block_still_draws():
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify)
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    assert all(w["head"] is None for w in b["weeks"])
