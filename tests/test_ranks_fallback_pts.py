"""With no week_ranks file, Ranks falls back to the projections and orders every position by our `pts`, running backs
included (ledger #96, 2026-10-09; David chose our own rank over the books' on 2026-10-08). The books' `rank_pts`, the
"No line" flag and the producer's cut-back fields no longer reach the rows. Light: dicts in, dicts out."""
import pytest

import projections
from ranks import live_ranks, natural_breaks
from test_week_ranks_units import doc, slug

# (name, our pts, the books' rank_pts): the books would put B Back first, our points put A Back first.
BACKS = [("A Back", 16.2, 15.4), ("B Back", 15.0, 16.6), ("C Back", 12.0, None), ("D Back", 3.1, None)]


def players():
    out = [{"name": n, "pos": "RB", "team": f"T{i}", "game": f"T{i} @ OPP{i}", "pts": pts, "rank_pts": rp, "src": "model"}
           for i, (n, pts, rp) in enumerate(BACKS)]
    out[3].update(unlined_backup=True, pts_before_unlined=10.3)
    return out


def fallback():
    return live_ranks({"scoring": "half", "players": players()}, slug)


def backs(block):
    return [r for r in block["rows"] if r["pos"] == "RB"]


def test_the_back_list_is_ordered_and_ranked_by_our_points():
    rows = backs(fallback())
    assert [(r["slug"], r["rank"]) for r in rows] == [("a-back", 1), ("b-back", 2), ("c-back", 3), ("d-back", 4)]


def test_the_back_tiers_are_natural_breaks_of_our_points():
    rows = backs(fallback())
    assert [r["tier"] for r in rows] == natural_breaks([16.2, 15.0, 12.0, 3.1], 12)


@pytest.mark.parametrize("field", ["rank_pts", "unlined_backup", "pts_before_unlined"])
def test_a_fallback_row_carries_none_of_the_books_fields(field):
    block = fallback()
    assert [field in r for r in block["rows"] + block["flex"]] == [False] * (len(block["rows"]) + len(block["flex"]))


def test_the_roster_cards_rank_a_back_by_our_points_too():
    got = projections.position_ranks(players(), slug)
    assert [got[s] for s in ("a-back", "b-back", "c-back", "d-back")] == [(1, 4), (2, 4), (3, 4), (4, 4)]


def test_an_out_back_carries_no_books_number_on_his_card():
    """The Start/Sit picker still reads a card's rank_pts; a player ruled out has no points, so no price either."""
    out = {"x": {"name": "B Back", "injury": "Out"}}
    cards = projections.live_projections({"players": players()}, slug, {"a-back", "b-back"}, out)["players"]
    assert (cards["a-back"]["rank_pts"], cards["b-back"]["rank_pts"]) == (15.4, None)


def shipped(name, rank, tier, pts):
    return {"key": name.lower(), "name": name, "pos": "RB", "team": "AAA", "opp": "BBB", "kickoff": "2026-09-13T17:00:00Z",
            "rank": rank, "tier": tier, "val": pts, "pts": pts, "src": "ours", "rank_pts": 9.0}


def test_a_week_ranks_list_is_drawn_as_it_ships_without_a_second_sort_or_cut():
    """ff-jarvis #88 orders and tiers the lists on pts, frozen at kickoff (ledger #98): the page keeps its rank and
    tier even where the projections' points have since moved to a different order or spacing."""
    lists = {"RB": [shipped("A Back", 1, 1, 10.0), shipped("B Back", 2, 2, 9.9), shipped("C Back", 3, 2, 9.8)]}
    live = [{"name": "A Back", "pos": "RB", "team": "AAA", "game": "AAA @ BBB", "pts": 5.0},
            {"name": "B Back", "pos": "RB", "team": "AAA", "game": "AAA @ BBB", "pts": 14.0},
            {"name": "C Back", "pos": "RB", "team": "AAA", "game": "AAA @ BBB", "pts": 9.8}]
    rows = backs(live_ranks({"players": live}, slug, None, None, doc(lists)))
    assert [(r["slug"], r["rank"], r["tier"], r["pts"]) for r in rows] == [
        ("a-back", 1, 1, 5.0), ("b-back", 2, 2, 14.0), ("c-back", 3, 2, 9.8)]


def test_the_books_order_key_is_gone():
    assert not hasattr(projections, "order_key")
