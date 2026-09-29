"""design/league_trades.py: ff-jarvis's trade verdicts cut for League > Trades. Built against
tests/fixtures/data/yahoo_trade_verdicts.json, ff-jarvis's file as landed 2026-09-28 (02e2276), with
Andrew's range lifted clear of 0 so the fixture holds a proven-good trader."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "design"))

import contract            # noqa: E402
import league_trades as T  # noqa: E402

sys.path.insert(0, str(ROOT / "api"))
from _espn import slugify  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "data"


def block(skip=frozenset()):
    verdicts = json.loads((FIX / "yahoo_trade_verdicts.json").read_text(encoding="utf-8"))
    managers = json.loads((FIX / "yahoo_league_managers.json").read_text(encoding="utf-8"))
    return T.live_trades(verdicts, managers, skip, slugify)


def test_the_block_passes_its_contract_and_every_side_is_whole():
    b = block()
    assert contract.problems("LIVE_TRADES", b) == []
    for tr in b["trades"]:
        for side in (tr["win"], tr["lose"]):
            assert set(side) == {"m", "got", "slugs", "tree", "par", "after", "via"}
            assert len(side["slugs"]) == len(side["got"])
        for d in tr["decided"]:
            assert set(d) == {"k", "m", "seed", "without"} and d["k"] in {"title", "in", "out", "bye", "nobye"}


def test_the_winner_is_the_tree_and_the_held_winner_rides_beside_it():
    """2020 week 4: David's Fuller trade. Held weeks say David by 0.7; the tree gives it to Theo,
    who flipped Jefferson for Thielen and Chubb."""
    tr = next(x for x in block()["trades"] if x["season"] == 2020 and x["week"] == 4 and "W. Fuller V" in x["lose"]["got"])
    assert tr["win"]["m"] == "12" and tr["held"]["win"] == "9" and tr["held"]["margin"] == 0.7


def test_the_title_trade_leads_what_decided_a_season_and_heists_are_the_three_biggest():
    b = block()
    first = next(x for x in b["trades"] if x["id"] == b["decided"][0])
    assert (first["season"], first["win"]["m"]) == (2021, "9")
    assert first["decided"][0] == {"k": "title", "m": "9", "seed": None, "without": None}
    margins = [next(x for x in b["trades"] if x["id"] == i)["margin"] for i in b["heists"]]
    assert margins == sorted(margins, reverse=True) and margins[0] == 130.1 and len(margins) == 3


def test_players_go_by_initial_and_a_curse_by_surname():
    b = block()
    chase = next(c for c in b["curses"] if c["player"] == "J. Chase")
    assert chase["surname"] == "Chase" and chase["kind"] == "curse" and chase["moves"][-1]["open"] is True
    godwin = next(c for c in b["curses"] if c["player"] == "C. Godwin Jr.")
    assert godwin["surname"] == "Godwin"
    # the headshot's slug is the full name's, suffix dropped: heads/jamarr-chase.webp, heads/chris-godwin.webp
    assert (chase["slug"], godwin["slug"]) == ("jamarr-chase", "chris-godwin")
    assert T.short("Bills") == "Bills"


def test_a_manager_kept_out_of_the_book_is_kept_out_of_the_ranking():
    everyone = {r["m"] for r in block()["ranking"]}
    assert "former-3" in everyone
    assert "former-3" not in {r["m"] for r in block(skip=frozenset({"former-3"}))["ranking"]}


def test_few_trades_dims_a_row_and_the_ranking_runs_best_to_worst():
    r = block()["ranking"]
    assert [x["shrunk"] for x in r] == sorted((x["shrunk"] for x in r), reverse=True)
    assert all(x["few"] == (x["trades"] < T.FEW) for x in r)
    assert r[-1]["m"] == "11" and r[-1]["hi"] < 0   # Chanel: the one proven-bad trader


def test_no_verdicts_is_no_block():
    assert T.live_trades(None, {}) is None and T.report(None).startswith("Trades: none")
