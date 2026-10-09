"""One projection, one home (ledger #81, 2026-10-09): the number Players > Ranks prints for a player is the projection
every other view prints (LIVE_PROJECTIONS `pts`: Roster cards, profile, Start/Sit), and the list's order, its tiers
and the card's rank all follow that number. David chose "our own rank and tiers, with Vegas as a supporting input,
over the books' rank" (2026-10-08), so the books' price (`rank_pts`) and the producer's list order do not decide a
row. Since ff-jarvis #88 (2026-10-09) the producer orders and tiers each list on our points, so the page draws the
order, rank and tier as shipped (ledger #98). Light: dicts in, dicts out; the fixture build is the one whole-block check."""
import pytest

from projections import live_projections
from ranks import live_ranks, ranks_places
from test_build import injected
from test_week_ranks_pts import doc, player, row
from test_week_ranks_units import slug

pytestmark = pytest.mark.req("Ranks", ac="a player's Ranks number, order and tiers are his projection's")

# name, our projection (the file's `pts`), the books' price, and the week_ranks list `pts` (frozen at a kickoff, so it may be stale)
RBS = [("Gil Gibbs", 20.31, 24.6, 20.31), ("Bo Bijan", 19.06, 19.72, 19.06), ("Tay Taylor", 15.97, 17.39, 15.97),
       ("Mac Mccaffrey", 15.73, 17.12, 15.73), ("Hal Henry", 15.87, 13.68, 15.87), ("Jay Jones", 13.09, 15.85, 13.09),
       ("Sam Stale", 13.11, 16.36, 13.83), ("Lo Low", 8.36, 14.18, 8.36)]
# the producer's list: our points' order (descending list pts), tiered by ff-jarvis, as it writes it since #88
OUR_ORDER = sorted(RBS, key=lambda r: -r[3])
TIER_SIZE = 3   # the sample's shipped tiers: three backs each


def lists():
    rb = [row(n, "RB", i + 1, 1 + i // TIER_SIZE, lp, bp) for i, (n, ours, bp, lp) in enumerate(OUR_ORDER)]
    flex = [{**r, "rank": i + 1} for i, r in enumerate(rb)]
    return {"RB": rb, "FLEX": flex}


def projections():
    return [player(n, "RB", ours, rank_pts=bp, floor=5.0, ceil=25.0) for n, ours, bp, _ in RBS]


def built_block():
    return live_ranks({"players": projections()}, slug, None, None, doc(lists()))


def rb_rows(block):
    return [r for r in block["rows"] if r["pos"] == "RB"]


def test_ranks_prints_the_projection_the_cards_print():
    block = built_block()
    wanted = {slug(n) for n, *_ in RBS}
    cards = live_projections({"players": projections()}, slug, wanted, None, None, doc(lists()), ranks=ranks_places(block))["players"]
    ranks = {r["slug"]: r["shown"] for r in block["rows"] + block["flex"]}
    assert {s: ranks[s] for s in wanted} == {s: cards[s]["pts"] for s in wanted}, "Henry 15.87, Sam Stale 13.11: not the books' 13.68 or the frozen 13.83"


def test_the_list_is_ordered_by_the_number_it_prints_and_a_back_the_books_doubt_is_not_demoted():
    block = built_block()
    got = [(r["slug"], r["shown"], r["rank"]) for r in rb_rows(block)]
    assert [s for s, *_ in got] == ["gil-gibbs", "bo-bijan", "tay-taylor", "hal-henry", "mac-mccaffrey", "sam-stale", "jay-jones", "lo-low"]
    assert [r for *_, r in got] == list(range(1, 9)), "rank is his place in the list as drawn"
    assert [p for _, p, _ in got] == sorted((p for _, p, _ in got), reverse=True)


@pytest.mark.parametrize("name", ["RB", "FLEX"])
def test_tiers_are_the_lists_own_as_shipped_in_every_list(name):
    block = built_block()
    rows = block["flex"] if name == "FLEX" else rb_rows(block)
    assert [r["tier"] for r in rows] == [r["tier"] for r in lists()[name]]


def test_the_sample_has_gaps_wide_enough_to_cut_into_tiers():
    assert max(r["tier"] for r in rb_rows(built_block())) > 1


def test_the_cards_rank_is_the_rank_ranks_prints():
    block = built_block()
    wanted = {slug(n) for n, *_ in RBS}
    cards = live_projections({"players": projections()}, slug, wanted, None, None, doc(lists()), ranks=ranks_places(block))["players"]
    assert {s: (c["rank"], c["of"]) for s, c in cards.items()} == {r["slug"]: (r["rank"], len(RBS)) for r in rb_rows(block)}
    assert cards["hal-henry"]["rank"] == 4


def test_the_band_and_the_matchup_stay_because_the_number_is_ours():
    henry = {r["slug"]: r for r in rb_rows(built_block())}["hal-henry"]
    assert (henry["floor"], henry["ceil"]) == (5.0, 25.0)


def test_flex_is_ordered_by_the_same_number_and_keeps_the_position_rank():
    flex = built_block()["flex"]
    assert [r["slug"] for r in flex][:5] == ["gil-gibbs", "bo-bijan", "tay-taylor", "hal-henry", "mac-mccaffrey"]
    assert [(r["slug"], r["rank"]) for r in flex if r["slug"] == "hal-henry"] == [("hal-henry", 4)]


def test_a_row_the_projections_do_not_hold_prints_the_lists_points():
    block = live_ranks({"players": []}, slug, None, None, doc({"RB": [row("Ann Arm", "RB", 1, 1, 8.126, 14.5)]}))
    assert (block["rows"][0]["shown"], block["rows"][0]["pts"]) == (8.13, 8.13)


def test_the_fixture_build_prints_one_number_per_player(built):
    page = injected(built.fragment)
    cards = page["LIVE_PROJECTIONS"]["players"]
    rows = page["LIVE_RANKS"]["rows"] + page["LIVE_RANKS"]["flex"]
    assert [(r["slug"], r["shown"], cards[r["slug"]]["pts"]) for r in rows if r["slug"] in cards and r["shown"] != cards[r["slug"]]["pts"]] == []
    assert [(r["slug"], r["rank"]) for r in page["LIVE_RANKS"]["rows"] if r["slug"] in cards and cards[r["slug"]]["rank"] != r["rank"]] == []
