"""Start/Sit's lineup card and paged calls (ledger #94, draft A) in Node: data/lineup.js. The card that draws
them is checked in the browser (test_matchups_view.py)."""
import pytest

REQ = pytest.mark.req("Start/Sit", ac="the lineup leads, with our one swap on top")


@pytest.fixture(scope="module")
def lu(node_js):
    return node_js("data/lineup.js")


def p(slug, pos, slot, team="NYJ", start=None):
    return {"slug": slug, "n": slug.title(), "pos": pos, "team": team, "slot": slot,
            "start": slot not in ("BN", "OUT") if start is None else start}


ROSTER = [p("qb1", "QB", "QB"), p("rb1", "RB", "RB"), p("wr1", "WR", "WR", team="KC"), p("flex", "RB", "FLEX"),
          p("k1", "K", "K"), p("dst", "DST", "DST"), p("bn1", "RB", "BN"), p("bn2", "WR", "BN", team="KC"),
          p("ir1", "WR", "OUT")]
PTS = {"qb1": 19.1, "rb1": 15.9, "wr1": None, "flex": 9.8, "bn1": 9.4, "bn2": 7.0}


@REQ
def test_the_lineup_is_his_skill_starters_then_his_bench_with_points_call_and_bye(lu):
    got = lu("muLineup", ROSTER, PTS, {"qb1": "SMASH", "bn1": "SIT"}, ["KC"])
    assert [r["slug"] for r in got["starters"]] == ["qb1", "rb1", "wr1", "flex"], "K, DST and the injured list are not lineup calls"
    assert [r["slug"] for r in got["bench"]] == ["bn1", "bn2"]
    assert got["starters"][0] == {"slug": "qb1", "n": "Qb1", "pos": "QB", "team": "NYJ", "slot": "QB",
                                  "pts": 19.1, "call": "SMASH", "bye": False}
    assert (got["starters"][2]["pts"], got["starters"][2]["bye"]) == (None, True)
    assert got["bench"][0]["call"] == "SIT" and got["bench"][1]["call"] == ""


@REQ
def test_an_empty_roster_is_an_empty_lineup(lu):
    assert lu("muLineup", [], {}, {}, []) == {"starters": [], "bench": []}


def col(slug):
    return {"p": {"slug": slug}}


@REQ
@pytest.mark.parametrize("verdict, want", [
    ({"flip": False, "win": col("bn1"), "gap": 1.1}, {"kind": "swap", "in": "bn1", "out": "rb1", "gap": 1.1}),
    ({"flip": False, "win": col("rb1"), "gap": 2.0}, {"kind": "keep", "in": "rb1", "out": "bn1", "gap": 2.0}),
    ({"flip": True, "gap": 0.3}, {"kind": "flip", "in": "bn1", "out": "rb1", "gap": 0.3}),
], ids=["bench-wins", "starter-wins", "coin-flip"])
def test_the_swap_is_the_pickers_own_verdict_on_the_closest_pair(lu, verdict, want):
    """`in` is the one we would start; the gap is the verdict's, never recomputed."""
    assert lu("muSwap", ["bn1", "rb1"], verdict) == want


@REQ
@pytest.mark.parametrize("pair, verdict", [([], None), (["bn1", "rb1"], None), (["bn1"], {"flip": True, "gap": 0})],
                         ids=["no-pair", "no-verdict", "one-player"])
def test_no_pair_or_no_verdict_is_no_swap(lu, pair, verdict):
    assert lu("muSwap", pair, verdict) is None


SS3 = {"smash": [{"slug": "a"}, {"slug": "b"}],
       "takes": [{"slug": "c", "call": "START"}, {"slug": "d", "call": "SIT"}, {"slug": "e", "call": "START"}]}


@pytest.mark.req("Start/Sit", ac="the calls page one kind at a time")
@pytest.mark.parametrize("kind, want", [("smash", ["a", "b"]), ("start", ["c", "e"]), ("sit", ["d"])])
def test_each_kind_holds_its_own_calls_in_the_builds_order(lu, kind, want):
    assert [r["slug"] for r in lu("muCallRows", SS3, kind)] == want


@pytest.mark.req("Start/Sit", ac="the calls page one kind at a time")
def test_a_kind_with_no_calls_is_an_empty_list(lu):
    assert lu("muCallRows", {"smash": [], "takes": []}, "sit") == []


@pytest.mark.req("Start/Sit", ac="the calls page one kind at a time")
@pytest.mark.parametrize("target, rest, want", [(900, 270, 11), (600, 270, 6), (0, 270, 6)],
                         ids=["fills-a-tall-lineup", "never-under-six", "no-lineup"])
def test_beside_the_lineup_the_calls_hold_the_rows_that_end_them_level(lu, target, rest, want):
    """(900 - 270) / 53 = 11.9: eleven 53px rows; a short lineup never takes the card under its phone page."""
    assert lu("muFitRows", target, rest) == want


@pytest.mark.req("Start/Sit", ac="the calls page one kind at a time")
@pytest.mark.parametrize("n, page, want", [
    (14, 0, {"from": 0, "to": 6, "page": 0, "pages": 3}),
    (14, 2, {"from": 12, "to": 14, "page": 2, "pages": 3}),
    (14, 9, {"from": 12, "to": 14, "page": 2, "pages": 3}),
    (14, -1, {"from": 0, "to": 6, "page": 0, "pages": 3}),
    (0, 0, {"from": 0, "to": 0, "page": 0, "pages": 1}),
], ids=["first", "last", "past-the-end", "before-the-start", "empty"])
def test_a_page_is_clamped_to_the_list(lu, n, page, want):
    assert lu("muPage", n, page, 6) == want
