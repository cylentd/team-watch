"""design/league_back.py through live_league_yahoo against the 4-team fixture plus a week 2 box score
and roast: each game's records, punchline, facts, stamp and box; the bench award; the tape; the record book."""
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
                          read("league_rosters.json"), slugify, read("yahoo_league_box.json"), read("yahoo_league_recap.json"),
                          read("yahoo_league_managers.json"))
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    return b


def test_managers_name_teams_champions_and_records(back):
    assert {t["id"]: t["mgr"] for t in back["teams"]} == {3: "Kearny", 7: "Crystal W.", 9: "David", 10: "Jon"}
    assert all(c["mgr"] for c in back["champs"] if c["id"] is not None)
    every = back["book"]["fame"] + back["book"]["shame"]
    # A former manager's record keeps its manager's name after its id is dropped.
    assert any(f.get("id") is None and f.get("mgr") == "Justin" for f in every) or not any(
        f.get("id") is None and "y" in f for f in every)
    assert all(f.get("mgr") for f in every if f.get("id") is not None)


def test_a_roasted_week_carries_its_words(back):
    w2 = back["weeks"][1]
    assert w2["head"] == "CHAT SURVIVES BY 0.44" and w2["dek"].startswith("Jaxon The Box")
    g = {f"{x['a']}-{x['b']}": x for x in w2["games"]}
    assert g["7-3"]["stamp"] == "BURIED" and g["10-9"]["stamp"] is None
    assert g["10-9"]["punch"] == "Jaxon The Box benched the win."
    assert g["10-9"]["beats"] == ["Rico Dowdle on the bench: 15.5", "Jaylen Warren started: 6.5", "Lost by 0.44"]


def test_a_skipped_week_draws_scores_without_words(back):
    w1 = back["weeks"][0]
    assert w1["head"] is None and w1["dek"] is None
    assert all(g["punch"] is None and g["beats"] == [] and g["box"] is None for g in w1["games"])


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
    assert back["weeks"][1]["awards"]["bench"] == {"id": 10, "v": 9.0, "name": "Rico Dowdle", "bp": 15.5, "started": "Jaylen Warren", "sp": 6.5}
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


def test_standings_after_each_week(back):
    t1, t2 = (w["table"] for w in back["weeks"])
    assert [r["id"] for r in t1][:2] == [10, 3]                     # both 1-0, Jaxon The Box on points
    top = t2[0]
    assert (top["id"], top["w"], top["l"], top["pf"], top["pfr"]) == (3, 2, 0, 292.08, 1)
    assert all(r["move"] == 0 for r in t1)                           # week 1 has no week before it
    assert sum(r["move"] for r in t2) == 0                           # every place gained is one lost


def test_next_grudge_is_the_most_lopsided_pairing(back):
    from league_back import next_grudge
    rec = lambda w, l: {"w": w, "l": l, "t": 0}
    h2h = {"1": {"2": rec(5, 6)}, "2": {"1": rec(6, 5)}, "3": {"4": rec(0, 10)}, "4": {"3": rec(10, 0)},
           "5": {"6": rec(2, 0)}, "6": {"5": rec(0, 2)}}
    now = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5, "b": 6}]
    assert next_grudge(now, h2h) == {"a": 4, "b": 3}          # 10-0, told from the side that leads it
    assert next_grudge([{"a": 5, "b": 6}], h2h) is None        # 2 meetings is not a grudge yet
    assert back["grudge"] is None                              # the fixture's pairings met at most twice


def test_the_lead_photo_is_found_in_the_box_and_greyed_when_the_player_flopped():
    from league_back import photo_of
    p = lambda n, pts, proj: {"name": n, "pts": pts, "proj": proj}
    box = {"slots": [{"a": p("Josh Allen", 40.82, 22.0), "b": p("DJ Moore", -0.1, 12.0)},
                     {"a": p("Colston Loveland", 0.0, 7.5), "b": p("Jaxon Smith-Njigba", 12.0, 16.0)}],
           "bench": {"a": [p("Rico Dowdle", 3.0, 9.0)], "b": []}}
    slug = lambda n: n.lower().replace(" ", "-")
    assert photo_of(box, "Josh Allen", slug) == {"name": "Josh Allen", "slug": "josh-allen", "pts": 40.82, "flop": False}
    assert photo_of(box, "DJ Moore", slug)["flop"] and photo_of(box, "Colston Loveland", slug)["flop"]
    assert not photo_of(box, "Jaxon Smith-Njigba", slug)["flop"]             # 12 of 16 is a quiet day, not a flop
    assert photo_of(box, "Rico Dowdle", slug)["flop"]                          # the bench counts too
    assert photo_of(box, "Nobody", slug) is None and photo_of(None, "Josh Allen", slug) is None


def test_every_week_names_its_lead_game(back):
    for w in back["weeks"]:
        assert w["lead"] in {f"{g['a']}-{g['b']}" for g in w["games"]}


def test_a_private_pair_leaves_the_page_and_draws_without_names():
    from league_back import classify, next_grudge
    rec = lambda w, l, m: {"w": w, "l": l, "t": 0, "m": m}
    h2h = {"3": {"4": rec(0, 3, [[2024, 1, -5.0, 0]] * 3), "5": rec(1, 0, [])}, "4": {"3": rec(3, 0, [[2024, 1, 5.0, 0]] * 3)}}
    hidden = classify(h2h, [(3, 4)])
    assert hidden == [{"w": 3, "l": 0, "t": 0, "m": [[2024, 1, 5.0, 0]] * 3}]    # the leader's side, no ids
    assert "4" not in h2h["3"] and "3" not in h2h["4"] and "5" in h2h["3"]     # gone both ways, the rest kept
    assert next_grudge([{"a": 3, "b": 4}], h2h) is None                        # nor can it be next week's grudge


def test_the_private_file_names_no_one():
    """design/league_private.json holds ids and dates only: the repo is not the place for the story."""
    import json, pathlib
    raw = json.loads((pathlib.Path(__file__).parents[1] / "design" / "league_private.json").read_text(encoding="utf-8"))
    assert all(set(p) <= {"a", "b", "asked"} for p in raw["pairs"])


def test_without_box_or_roast_the_block_still_draws():
    b = live_league_yahoo(read("yahoo_league.json"), read("yahoo_league_history.json"), read("yahoo_league_owners.json"),
                          read("league_rosters.json"), slugify)
    contract.validate("LIVE_LEAGUE_YAHOO", b)
    assert all(w["head"] is None for w in b["weeks"])
