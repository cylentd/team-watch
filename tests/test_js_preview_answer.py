"""Preview's answer block (data/preview.js pvAnswer), in Node: the line, the total, the win chance and
Claude's pick as data, before any of it is drawn (plan U3, 2026-10-05).

The audit's first-time visitor found a game's line and pick under five paragraphs of prose. The block
puts them first; this file pins what is in it and in which order. Where it sits on the screen is
test_preview.py, in the browser."""
import pytest


@pytest.fixture(scope="module")
def pv(node_js):
    return node_js("data/preview.js")


def game(**over):
    g = {
        "home": "CAR", "away": "DET", "kickoff": "2026-10-11T17:00:00Z",
        "line": {"fav": "DET", "by": 3.5, "total": 50.5, "implied": {"DET": 27, "CAR": 23.5},
                 "open": {"fav": "DET", "by": 3, "total": 49.5}},
        "market_win": {"DET": 64.4, "CAR": 35.6},
        "take": {"pick": {"winner": "DET", "score": {"DET": 30, "CAR": 19}},
                 "ats": {"side": "DET", "conf": "solid", "edge": "Carolina without Coker"},
                 "win": {"DET": 74, "CAR": 26}, "total": {"call": "under", "conf": "lean"}},
    }
    g.update(over)
    return g


def by_id(cells):
    return {c["id"]: c for c in cells}


def test_the_answer_is_pick_then_line_then_total_then_win(pv):
    assert [c["id"] for c in pv("pvAnswer", game())] == ["pick", "line", "total", "win"]


def test_the_pick_is_claudes_score_with_the_markets_implied_score_beside_it(pv):
    c = by_id(pv("pvAnswer", game()))["pick"]
    assert c["main"] == "DET 30, CAR 19" and c["sub"] == "market DET 27, CAR 23.5"
    assert c["ats"] == {"side": "DET", "conf": "solid", "edge": "Carolina without Coker"}


def test_the_line_and_total_say_where_they_opened_only_when_they_moved(pv):
    cells = by_id(pv("pvAnswer", game()))
    assert (cells["line"]["main"], cells["line"]["sub"]) == ("DET by 3.5", "opened DET by 3")
    assert (cells["total"]["main"], cells["total"]["sub"]) == ("50.5", "opened 49.5")
    assert cells["total"]["call"] == {"call": "under", "conf": "lean"}
    still = game(line={"fav": "DET", "by": 3, "total": 50, "implied": None, "open": {"fav": "DET", "by": 3, "total": 50}})
    cells = by_id(pv("pvAnswer", still))
    assert (cells["line"]["main"], cells["line"]["sub"], cells["total"]["main"], cells["total"]["sub"]) == ("DET by 3", "", "50", "")
    assert by_id(pv("pvAnswer", still))["pick"]["sub"] == ""            # no implied score, no market line


def test_the_win_chance_is_claudes_for_his_winner_beside_the_markets_with_a_bar(pv):
    c = by_id(pv("pvAnswer", game()))["win"]
    assert (c["main"], c["sub"], c["claude"]) == ("DET 74%", "market 64%", True)
    assert c["bar"] == {"mk": 64.4, "cl": 74}


def test_no_market_win_means_claudes_number_alone_and_no_bar(pv):
    c = by_id(pv("pvAnswer", game(market_win=None)))["win"]
    assert (c["main"], c["sub"], c["bar"]) == ("DET 74%", "", None)


def test_a_game_with_no_take_still_answers_with_the_line_total_and_the_markets_win(pv):
    cells = pv("pvAnswer", game(take=None))
    assert [c["id"] for c in cells] == ["line", "total", "win"]
    win = by_id(cells)["win"]
    assert (win["main"], win["claude"], win["bar"]) == ("DET 64%", False, None)
    assert by_id(cells)["total"]["call"] is None


def test_a_game_with_nothing_has_no_block(pv):
    assert pv("pvAnswer", game(line=None, market_win=None, take=None)) == []


def test_a_take_from_before_confidence_still_gives_its_pick_without_a_side(pv):
    old = game()
    del old["take"]["ats"], old["take"]["win"], old["take"]["total"]
    cells = by_id(pv("pvAnswer", old))
    assert cells["pick"]["ats"] is None and cells["total"]["call"] is None
    assert cells["win"]["claude"] is False                                # only the market's number is left


def test_text_in_a_club_code_is_escaped(pv):
    c = by_id(pv("pvAnswer", game(line={"fav": "<b>", "by": 1, "total": None, "implied": None, "open": None})))["line"]
    assert c["main"] == "&lt;b&gt; by 1"
