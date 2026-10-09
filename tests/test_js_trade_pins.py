"""Which pinned file is the reader's, and what its offers hold (data/tradepage.js, ledger #65, 2026-10-08) in Node.

ff-jarvis writes trade_pins/index.json {updated, rules, leagues: {league: {owner: "<league>/<file>.json"}}} beside one file per
owner. The page reads the index to find the owner's file, so our slug never has to match ff-jarvis's by guess, and the
file's offers name players by key (trade_pins_schema), which the page resolves to the player objects it draws."""
import copy

import pytest

OWNER = "Purdy Big in Japan"
INDEX = {"updated": "2026-10-08T05:00", "rules": {},
         "leagues": {"espn": {OWNER: "espn/purdy-big-in-japan.json", "Run It Back": "espn/run-it-back-2.json"},
                     "yahoo": {"Chat Take the Wheel": "yahoo/chat.json"}}}


@pytest.fixture(scope="module")
def tp(node_js):
    return node_js("data/tradepage.js")


# ---- the index names the file ------------------------------------------------------------------------------------

def test_the_index_names_the_owners_file_under_trade_pins(tp):
    assert tp("tpPinsFile", INDEX, "espn", OWNER) == "trade_pins/espn/purdy-big-in-japan.json"


def test_the_file_is_the_one_the_index_names_even_when_it_is_not_the_slug(tp):
    assert tp("tpPinsFile", INDEX, "espn", "Run It Back") == "trade_pins/espn/run-it-back-2.json"


@pytest.mark.parametrize("lg,owner", [("ayo", OWNER), ("espn", "Nobody"), ("yahoo", OWNER), ("espn", ""), ("toString", OWNER),
                                      ("espn", "constructor")])
def test_an_owner_the_index_does_not_list_has_no_file(tp, lg, owner):
    assert tp("tpPinsFile", INDEX, lg, owner) is None


@pytest.mark.parametrize("bad", [None, [], "x", {}, {"leagues": None}, {"leagues": []}, {"leagues": {"espn": None}},
                                 {"leagues": {"espn": []}}, {"leagues": {"espn": {OWNER: 5}}},
                                 {"leagues": {"espn": {OWNER: ""}}}])
def test_an_index_without_the_owner_in_its_shape_gives_no_file(tp, bad):
    assert tp("tpPinsFile", bad, "espn", OWNER) is None


@pytest.mark.parametrize("path", ["espn/../index.json", "/espn/a.json", "yahoo/a.json", "espn/a.txt", "espn/.json", "espn/b/a.json",
                                  "espn/a.json?x=1", "https://x.test/espn/a.json", "espn\\a.json", "a.json"])
def test_a_path_that_is_not_league_slash_name_json_is_never_fetched(tp, path):
    index = {"leagues": {"espn": {OWNER: path}}}
    assert tp("tpPinsFile", index, "espn", OWNER) is None, "the index must not point the page at any other file"


def test_the_cache_key_is_the_league_and_the_owner_not_a_guessed_path(tp):
    assert tp("tpPinsKey", "espn", OWNER) == "espn/Purdy Big in Japan"
    assert tp("tpPinsKey", "yahoo", OWNER) != tp("tpPinsKey", "espn", OWNER)


# ---- the file's offers hold player keys; the page draws player objects -------------------------------------------------

def player(slug, **kw):
    return {"name": slug.title(), "pos": "WR", "team": "SEA", "slug": slug, "seen": 1.0, "injury": None, "last2": None,
            "chips": [], "holder": "Alpha", **kw}


PINS = {"league": "espn", "owner": OWNER, "updated": "t",
        "players": {"a": player("a-slug"), "b": player("b-slug"), "c": player("c-slug"), "d": player("d-slug"), "e": player("e-slug")},
        "offers": [{"partner": "Alpha", "send": ["a"], "get": ["b", "c"], "gain": 5.0, "drop": ["d"], "ir_moves": ["e"],
                    "their": {"ir_moves": ["a"], "drop": ["b"], "gain": 1.0}},
                   {"partner": "Beta", "send": ["c"], "get": ["a"], "gain": 2.0, "drop": [], "ir_moves": [],
                    "their": {"ir_moves": [], "drop": [], "gain": 0.5}}],
        "get": {"b": [0]}, "send": {"a": {"Alpha": 0}}, "pairs": []}


def slugs(rows):
    return [p["slug"] for p in rows]


def test_every_player_list_of_an_offer_becomes_the_players_it_names(tp):
    got = tp("tpPinsResolve", PINS)["offers"][0]
    assert slugs(got["send"]) == ["a-slug"]
    assert slugs(got["get"]) == ["b-slug", "c-slug"], "in the offer's order"
    assert slugs(got["drop"]) == ["d-slug"]
    assert slugs(got["ir_moves"]) == ["e-slug"]
    assert slugs(got["their"]["ir_moves"]) == ["a-slug"]
    assert slugs(got["their"]["drop"]) == ["b-slug"]


def test_a_resolved_player_keeps_every_field_the_card_reads(tp):
    got = tp("tpPinsResolve", PINS)["offers"][1]["get"][0]
    assert got == PINS["players"]["a"]


def test_the_rest_of_the_file_and_each_offers_numbers_are_unchanged(tp):
    got = tp("tpPinsResolve", PINS)
    assert (got["get"], got["send"], got["players"], got["league"], got["owner"]) == \
        (PINS["get"], PINS["send"], PINS["players"], "espn", OWNER)
    assert [(o["partner"], o["gain"], o["their"]["gain"]) for o in got["offers"]] == [("Alpha", 5.0, 1.0), ("Beta", 2.0, 0.5)]


def test_resolving_does_not_change_the_file_it_was_given(tp):
    before = copy.deepcopy(PINS)
    tp("tpPinsResolve", PINS)
    assert PINS == before


def test_an_offer_that_already_holds_player_objects_is_left_as_it_is(tp):
    objects = copy.deepcopy(PINS)
    objects["offers"][0]["send"] = [player("x-slug")]
    assert slugs(tp("tpPinsResolve", objects)["offers"][0]["send"]) == ["x-slug"]


@pytest.mark.parametrize("where", ["send", "get", "drop", "ir_moves", "their.drop", "their.ir_moves"])
def test_a_key_the_file_has_no_player_for_makes_the_whole_file_unusable(tp, where):
    broken = copy.deepcopy(PINS)
    o = broken["offers"][0]
    (o["their"] if where.startswith("their.") else o)[where.split(".")[-1]] = ["nobody"]
    assert tp("tpPinsResolve", broken) is None, "an offer with a missing player would draw a hole; today's file serves instead"


@pytest.mark.parametrize("bad", [None, [], "x", 3])
def test_nothing_to_resolve_is_null(tp, bad):
    assert tp("tpPinsResolve", bad) is None


def test_a_file_with_no_players_map_cannot_resolve_keys(tp):
    no_players = {k: v for k, v in PINS.items() if k != "players"}
    assert tp("tpPinsResolve", no_players) is None
