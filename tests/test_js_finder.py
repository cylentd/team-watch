"""The trade finder's pure logic (surface/finder/logic.js) in Node, no build and no browser (2026-10-06): the reader's gap
to the league median per position, which chip opens first, which offers a chip shows, and who is deep at a position.

The page draws these (tests/test_trade_finder.py, in Chromium); the numbers and the order are decided here."""
import pytest


@pytest.fixture(scope="module")
def tf(node_js):
    # lboard.js for lbTone and lbRecord (the 8% tint and the record are the Teams cards' own), then the finder's logic.
    return node_js("surface/lboard/lboard.js", "surface/finder/logic.js")


def player(slot, name, pos, pts):
    return {"slot": slot, "n": name, "pos": pos, "pts": pts}


def team(key, name, cols, lineup=(), w=None, l=None, tot=0):
    return {"key": key, "name": name, "cols": cols, "lineup": list(lineup), "bench": [], "spare": [], "w": w, "l": l, "t": 0, "tot": tot}


def cols(qb, rb, wr, te, flx=0):
    return {"QB": qb, "RB": rb, "WR": wr, "TE": te, "FLX": flx}


MEDIAN = {"QB": 18.0, "RB": 22.0, "WR": 20.0, "TE": 7.0, "FLX": 8.0}
ME = team("lg-me", "Mine", cols(20.0, 15.0, 24.0, 7.0))
LG = {"key": "lg", "slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1}, "median": MEDIAN, "teams": [
    ME,
    team("lg-a", "Alpha", cols(16.0, 30.0, 18.0, 9.0), [player("QB", "Quinn Alpha", "QB", 16.0), player("RB", "Rob Alpha", "RB", 17.0),
         player("RB", "Ray Allen", "RB", 13.0), player("WR", "Walt Alpha", "WR", 18.0), player("FLX", "Rex Amos", "RB", 9.0)], 3, 1, tot=80),
    team("lg-b", "Beta", cols(19.0, 22.0, 26.0, 5.0), [player("RB", "Rae Beta", "RB", 22.0)], 2, 2, tot=70),
    team("lg-c", "Gamma", cols(18.0, 30.0, 26.0, 7.0), [player("RB", "Rudy Gamma", "RB", 30.0)], tot=90),
]}


# ---- the gap row: the reader's column minus the league's median -------------------------------------------------

def test_a_gap_is_the_readers_column_minus_the_medians_in_position_order(tf):
    assert tf("tfGaps", LG, ME) == [{"pos": "QB", "gap": 2.0}, {"pos": "RB", "gap": -7.0}, {"pos": "WR", "gap": 4.0}, {"pos": "TE", "gap": 0.0}]


def test_a_position_the_league_has_no_slot_for_has_no_chip(tf):
    no_te = {**LG, "slots": {"QB": 1, "RB": 2, "WR": 2}}
    assert [g["pos"] for g in tf("tfGaps", no_te, ME)] == ["QB", "RB", "WR"]


@pytest.mark.parametrize("gaps,want", [
    ([("QB", 2.0), ("RB", -7.0), ("WR", -3.0), ("TE", 0.0)], "RB"),     # the most negative
    ([("QB", -1.5), ("RB", -1.5), ("WR", 4.0)], "QB"),                  # a tie: the first in QB RB WR TE order
    ([("QB", 5.0), ("RB", 1.2), ("WR", 3.0)], "RB"),                    # nobody short: the smallest lead
    ([], None),
])
def test_the_chip_that_opens_first_is_the_most_negative_gap(tf, gaps, want):
    assert tf("tfStartPos", [{"pos": p, "gap": g} for p, g in gaps]) == want


# 2026-10-06 review: a reader short at TE with no TE offer opened on an empty list. Once the offers are in, the first
# chip is the most negative gap among the positions that have an offer; with none anywhere, the plain rule.
@pytest.mark.parametrize("offered,want", [
    (["QB", "WR"], "WR"),           # RB (-7.0) has no offer: the most negative of the rest
    (["RB", "WR"], "RB"),           # the shortest position has one: it opens
    ([], "RB"),                     # no offer at any position: the most negative gap, to its empty state
    (None, "RB"),                   # the file is not in yet: the most negative gap
])
def test_the_first_chip_skips_a_position_with_no_offer_once_the_offers_are_in(tf, offered, want):
    gaps = [{"pos": p, "gap": g} for p, g in [("QB", 2.0), ("RB", -7.0), ("WR", -3.0), ("TE", 0.0)]]
    assert tf("tfStartPos", gaps, offered) == want


def test_the_positions_offered_are_those_some_offer_brings_back(tf):
    offers = [offer("Alpha", ["RB"], 3.0), offer("Beta", ["WR", "TE"], 2.0, send=("QB",))]
    assert tf("tfOffered", offers) == ["RB", "WR", "TE"]


@pytest.mark.parametrize("n,want", [(2.0, "+2.0"), (-7.04, "−7.0"), (0.0, "0.0"), (-0.04, "0.0"), (12.36, "+12.4")])
def test_a_gap_is_signed_to_one_decimal_with_a_true_minus_and_no_sign_on_zero(tf, n, want):
    assert tf("tfSigned", n) == want


# ---- the offers a chip shows ------------------------------------------------------------------------------------

def pl(name, pos):
    return {"name": name, "pos": pos}


def offer(partner, get, gain, send=("RB",)):
    return {"partner": partner, "send": [pl(f"s{i}", p) for i, p in enumerate(send)], "get": [pl(f"g{i}", p) for i, p in enumerate(get)], "gain": gain}


def test_a_chip_shows_only_the_offers_whose_get_holds_that_position_best_gain_first(tf):
    offers = [offer("A", ["WR"], 3.0), offer("B", ["QB", "WR"], 5.5), offer("C", ["RB"], 9.0), offer("D", ["TE"], 4.0)]
    wr = tf("tfOffersFor", offers, "WR", None)
    assert [(o["partner"], o["gain"]) for o in wr] == [("B", 5.5), ("A", 3.0)], "the RB and the TE offers are not WR offers"
    assert [o["partner"] for o in tf("tfOffersFor", offers, "QB", None)] == ["B"]
    assert tf("tfOffersFor", offers, "TE", None)[0]["partner"] == "D"


def test_equal_gains_go_to_the_smaller_trade_then_the_partner_name(tf):
    offers = [offer("Zed", ["WR"], 4.0), offer("Abe", ["WR"], 4.0, send=("RB", "RB")), offer("Cal", ["WR"], 4.0)]
    assert [o["partner"] for o in tf("tfOffersFor", offers, "WR", None)] == ["Cal", "Zed", "Abe"]


def test_a_chip_shows_at_most_five(tf):
    offers = [offer(f"P{i}", ["WR"], 10.0 - i) for i in range(8)]
    assert [o["gain"] for o in tf("tfOffersFor", offers, "WR", None)] == [10.0, 9.0, 8.0, 7.0, 6.0]


def test_a_partner_shows_every_offer_with_him_whatever_the_position_and_nothing_with_anyone_else(tf):
    offers = [offer("A", ["WR"], 3.0), offer("A", ["QB"], 6.0), offer("B", ["WR"], 9.0)] + [offer("A", ["TE"], 1.0 + i / 10) for i in range(6)]
    got = tf("tfOffersFor", offers, "WR", "A")
    assert len(got) == 8 and {o["partner"] for o in got} == {"A"}, "no cap of five on a partner"
    assert got[0]["gain"] == 6.0, "best first"


def test_no_offers_for_a_position_is_an_empty_list_and_so_is_an_owner_with_no_list(tf):
    assert tf("tfOffersFor", [offer("A", ["WR"], 3.0)], "TE", None) == []
    assert tf("tfOffersFor", [], "WR", None) == []
    assert tf("tfOffersFor", None, "WR", None) == []


# ---- who is deep at a position ----------------------------------------------------------------------------------

def test_every_other_team_is_ranked_by_the_column_with_ties_to_the_higher_lineup_total(tf):
    got = tf("tfDeep", LG, "RB", "lg-me")
    assert [(d["name"], d["val"]) for d in got] == [("Gamma", 30.0), ("Alpha", 30.0), ("Beta", 22.0)], "the reader is not in his own list; Gamma beats Alpha on total"


def test_a_row_is_tinted_8_percent_off_the_median_and_names_its_starters_there_as_initials(tf):
    got = {d["name"]: d for d in tf("tfDeep", LG, "RB", "lg-me")}
    assert (got["Alpha"]["tone"], got["Beta"]["tone"]) == ("up", ""), "30 against a median of 22, and 22 against 22"
    assert got["Alpha"]["starters"] == ["R. Alpha", "R. Allen", "R. Amos"], "two RB slots and the flex, each a row; names as initials"
    assert got["Alpha"]["record"] == "3–1" and got["Gamma"]["record"] == ""


def test_a_team_below_the_median_is_tinted_down(tf):
    got = {d["name"]: d for d in tf("tfDeep", LG, "TE", "lg-me")}
    assert got["Beta"]["tone"] == "dn" and got["Alpha"]["tone"] == "up"


def test_no_reader_means_every_team_is_listed(tf):
    assert len(tf("tfDeep", LG, "RB", None)) == 4
