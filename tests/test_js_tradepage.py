"""The trade page per player (data/tradepage.js, ledger #51, 2026-10-08) in Node: the hash it lives at, which footer
button the profile shows, and which offers fill the Get and Send lists, from ff-jarvis's pinned search when it is
there and from today's trade_offers.json when it is not.

The page draws these (tests/test_trade_page.py); the rows, their order and the reasons are decided here."""
import pytest


@pytest.fixture(scope="module")
def tp(node_js):
    return node_js("data/tradepage.js")


def pl(slug, pos="WR"):
    return {"name": slug.replace("-", " ").title(), "pos": pos, "slug": slug}


def offer(partner, send, get, gain, their=0.0, **kw):
    return {"partner": partner, "send": [pl(s) for s in send], "get": [pl(g) for g in get], "gain": gain,
            "their": {"ir_moves": [], "drop": [], "gain": their}, **kw}


# ---- the hash ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("hash_,want", [
    ("trades/get/jaxon-smith-njigba", {"side": "get", "slugs": ["jaxon-smith-njigba"]}),
    ("trades/send/brock-purdy", {"side": "send", "slugs": ["brock-purdy"]}),
    ("trades/send/brock-purdy+tee-higgins", {"side": "send", "slugs": ["brock-purdy", "tee-higgins"]}),
])
def test_a_players_trade_page_hash_names_the_side_and_the_players(tp, hash_, want):
    assert tp("tpParse", hash_) == want


@pytest.mark.parametrize("hash_", [
    "trades", "trades/", "trades/get/", "trades/get/a+b", "trades/send/a+b+c", "trades/swap/a",
    "roster/get/a", "trades/get/A Name", "trades/send/a+", "trades/send/a+a", "",
])
def test_any_other_hash_is_not_a_trade_page(tp, hash_):
    assert tp("tpParse", hash_) is None, "get takes one player, send one or two, each a slug, never the same twice"


def test_the_hash_is_written_back_the_way_it_is_read(tp):
    assert tp("tpHash", "send", ["brock-purdy", "tee-higgins"]) == "trades/send/brock-purdy+tee-higgins"
    assert tp("tpParse", tp("tpHash", "get", ["puka-nacua"])) == {"side": "get", "slugs": ["puka-nacua"]}


# ---- the profile's footer -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("pos,owner,me,want", [
    ("WR", "espn-b", "espn", "get"),      # another team's player: Trade for him
    ("QB", "espn", "espn", "send"),       # the reader's own: Shop him
    ("TE", None, "espn", None),           # nobody's in the reader's league: nothing to trade
    ("RB", "espn-b", None, None),         # no team picked: no side to trade from
    ("K", "espn-b", "espn", None),        # the search prices QB, RB, WR and TE only
    ("DST", "espn", "espn", None),
])
def test_the_footer_offers_trade_for_him_or_shop_him_by_who_owns_him(tp, pos, owner, me, want):
    assert tp("tpAction", pos, owner, me) == want


# ---- the gains a row shows ----------------------------------------------------------------------------------------

def test_a_row_shows_your_rest_of_season_gain_and_his_without_lenses(tp):
    assert tp("tpGains", offer("A", ["x"], ["y"], 12.5, their=0.7)) == {"me": 12.5, "them": 0.7}


def test_a_lensed_offer_shows_each_side_on_the_lens_that_judges_it(tp):
    o = offer("A", ["x"], ["y"], 12.5, their=0.7, lens={"me": "now", "them": None},
              lenses={"now": {"gain": 4.1, "their": -1.0}, "ros": {"gain": 12.5, "their": 0.7}})
    assert tp("tpGains", o) == {"me": 4.1, "them": 0.7}, "a side with no lens named is judged on rest of season"


def test_an_offer_naming_a_lens_but_carrying_no_lenses_shows_its_rest_of_season_gains(tp):
    o = offer("A", ["x"], ["y"], 12.5, their=0.7, lens={"me": "now", "them": "now"})
    assert tp("tpGains", o) == {"me": 12.5, "them": 0.7}


def test_a_lensed_offer_with_a_blank_lens_cell_shows_no_number_for_that_side(tp):
    o = offer("A", ["x"], ["y"], 12.5, lens={"me": "push", "them": "push"}, lenses={"push": {}})
    assert tp("tpGains", o) == {"me": None, "them": None}


# ---- Get: every package that lands him ----------------------------------------------------------------------------

TODAY = [
    offer("Run It Back", ["a", "b"], ["jsn"], 21.7, their=0.2),
    offer("Run It Back", ["c"], ["jsn", "other"], 38.4, their=0.2),
    offer("Run It Back", ["d"], ["nobody"], 50.0),
    offer("Big Salty", ["e"], ["jsn"], 21.7, their=1.1),
    offer("Alpha", ["f", "g"], ["jsn"], 21.7, their=0.5),
]


def test_get_from_todays_file_is_every_offer_that_lands_him_your_gain_first(tp):
    got = tp("tpGet", None, TODAY, "jsn")
    assert [(o["partner"], o["gain"], len(o["send"])) for o in got["rows"]] == [
        ("Run It Back", 38.4, 1), ("Big Salty", 21.7, 1), ("Alpha", 21.7, 2), ("Run It Back", 21.7, 2)], \
        "best gain first; a tie goes to the smaller trade, then the partner's name"
    assert got["reason"] is None


def test_get_with_nothing_in_todays_file_says_tonights_search_missed_him(tp):
    assert tp("tpGet", None, TODAY, "puka-nacua") == {"rows": [], "reason": "today"}


def test_get_with_no_file_at_all_is_the_same_plain_line(tp):
    assert tp("tpGet", None, None, "puka-nacua") == {"rows": [], "reason": "today"}


PINS = {
    "updated": "2026-10-08T05:50", "league": "espn", "owner": "Purdy Big in Japan",
    "players": {"jsn": pl("jsn"), "puka-nacua": pl("puka-nacua"), "brock-purdy": pl("brock-purdy", "QB"),
                "tee-higgins": pl("tee-higgins")},
    "offers": [
        offer("Run It Back", ["a"], ["jsn"], 10.0),                     # 0
        offer("Run It Back", ["b", "c"], ["jsn"], 30.0),                # 1
        offer("Big Salty", ["brock-purdy"], ["x"], 34.0, their=0.5),    # 2
        offer("Alpha", ["brock-purdy"], ["y"], 38.4, their=1.1),        # 3
        offer("Beta", ["brock-purdy", "tee-higgins"], ["z"], 21.9),     # 4
    ],
    "get": {"jsn": [0, 1], "puka-nacua": {"reason": "no_gain_for_him"}},
    "send": {"brock-purdy": {"Big Salty": 2, "Alpha": 3}, "tee-higgins": {"reason": "lens_gate"}},
    "pairs": [],
}


def test_get_from_the_pinned_search_is_its_packages_your_gain_first(tp):
    got = tp("tpGet", PINS, TODAY, "jsn")
    assert [o["gain"] for o in got["rows"]] == [30.0, 10.0], "the pinned packages, not today's"
    assert got["reason"] is None


def test_get_with_a_pinned_reason_says_that_reason(tp):
    assert tp("tpGet", PINS, TODAY, "puka-nacua") == {"rows": [], "reason": "no_gain_for_him"}


def test_get_for_a_player_the_pinned_search_skipped_falls_back_to_todays_file(tp):
    got = tp("tpGet", PINS, TODAY, "nobody")
    assert [o["gain"] for o in got["rows"]] == [50.0]


def test_a_pinned_index_past_the_offers_is_left_out(tp):
    pins = {**PINS, "get": {"jsn": [1, 9]}}
    assert [o["gain"] for o in tp("tpGet", pins, [], "jsn")["rows"]] == [30.0]


def test_a_pinned_player_is_found_by_his_slug_when_the_key_is_not_one(tp):
    pins = {**PINS, "players": {"p17": pl("jsn")}, "get": {"p17": [0]}}
    assert [o["gain"] for o in tp("tpGet", pins, [], "jsn")["rows"]] == [10.0]


# ---- Send: each team's best return --------------------------------------------------------------------------------

TEAMS = ["Alpha", "Beta", "Big Salty", "Run It Back"]
TODAY_SEND = [
    offer("Alpha", ["brock-purdy"], ["x"], 20.0),
    offer("Alpha", ["brock-purdy", "q"], ["x"], 29.6, their=1.3),
    offer("Run It Back", ["brock-purdy", "tee-higgins"], ["y"], 34.5, their=2.1),
    offer("Big Salty", ["tee-higgins"], ["z"], 40.0),
]


def test_send_from_todays_file_is_one_row_per_team_its_best_return(tp):
    got = tp("tpSend", None, TODAY_SEND, ["brock-purdy"], TEAMS)
    assert [(o["partner"], o["gain"]) for o in got["rows"]] == [("Run It Back", 34.5), ("Alpha", 29.6)]
    assert got["none"] == ["Beta", "Big Salty"], "the teams with no offer, in the league's order, for one folded line"
    assert got["reason"] is None


def test_shopping_two_keeps_only_offers_that_send_both(tp):
    got = tp("tpSend", None, TODAY_SEND, ["brock-purdy", "tee-higgins"], TEAMS)
    assert [o["partner"] for o in got["rows"]] == ["Run It Back"]
    assert got["none"] == ["Alpha", "Beta", "Big Salty"]


def test_send_with_no_offer_anywhere_says_so_in_one_line_and_folds_no_team(tp):
    assert tp("tpSend", None, TODAY_SEND, ["nobody"], TEAMS) == {"rows": [], "none": [], "reason": "today"}


def test_send_from_the_pinned_search_is_its_best_offer_per_team(tp):
    got = tp("tpSend", PINS, TODAY_SEND, ["brock-purdy"], TEAMS)
    assert [(o["partner"], o["gain"]) for o in got["rows"]] == [("Alpha", 38.4), ("Big Salty", 34.0)]
    assert got["none"] == ["Beta", "Run It Back"]


def test_send_with_a_pinned_reason_says_that_reason(tp):
    assert tp("tpSend", PINS, TODAY_SEND, ["tee-higgins"], TEAMS) == {"rows": [], "none": [], "reason": "lens_gate"}


def test_two_shopped_with_the_pinned_search_filter_its_offers_to_both(tp):
    got = tp("tpSend", PINS, TODAY_SEND, ["brock-purdy", "tee-higgins"], TEAMS)
    assert [(o["partner"], o["gain"]) for o in got["rows"]] == [("Beta", 21.9)], "the pinned offers that send both"


def test_send_for_a_player_the_pinned_search_skipped_falls_back_to_todays_file(tp):
    got = tp("tpSend", PINS, TODAY_SEND, ["q"], TEAMS)
    assert [o["partner"] for o in got["rows"]] == ["Alpha"]


# ---- which pinned file belongs to the reader ----------------------------------------------------------------------

def test_a_pinned_file_is_used_only_for_its_own_league_and_owner(tp):
    assert tp("tpPinsFor", PINS, "espn", "Purdy Big in Japan") == PINS
    assert tp("tpPinsFor", PINS, "yahoo", "Purdy Big in Japan") is None
    assert tp("tpPinsFor", PINS, "espn", "Run It Back") is None


@pytest.mark.parametrize("bad", [None, [], "x", {"league": "espn", "owner": "Purdy Big in Japan"},
                                 {**PINS, "offers": None}, {**PINS, "get": []}, {**PINS, "send": None}])
def test_a_pinned_file_missing_its_parts_is_not_used(tp, bad):
    assert tp("tpPinsFor", bad, "espn", "Purdy Big in Japan") is None


@pytest.mark.parametrize("name,want", [
    ("Purdy Big in Japan", "purdy-big-in-japan"), ("TEAM MURICA", "team-murica"), ("FAFO!", "fafo"),
    ("Larry's World", "larrys-world"), ("  Lets rock  Mate ", "lets-rock-mate"), ("Half Asian Lives Matter", "half-asian-lives-matter"),
])
def test_an_owners_pinned_file_is_named_by_his_team_as_a_slug(tp, name, want):
    assert tp("tpOwnerSlug", name) == want


def test_the_pinned_file_path_is_league_then_owner(tp):
    assert tp("tpPinsUrl", "espn", "TEAM MURICA") == "trade_pins/espn/team-murica.json"
