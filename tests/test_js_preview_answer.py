"""Preview's answer block (data/preview.js pvAnswer), in Node: Claude's score, then one row per bet
(Moneyline, Spread, Total) with Vegas beside Claude, as data before any of it is drawn.

Plan U3 (2026-10-05) put the line and the pick above the prose. Storyboard 3A of the same day
(https://claude.ai/artifact/NTeV8W2N9mFnYgftfbuqPV; David: "it's saying the same thing many times") cut it
to one row per bet: "Spread PIT by 2.5" read as Claude's call when it was Vegas's line. Each row now names
Vegas's number and Claude's call apart, and says in points what the call needs. Where it sits on the
screen is test_preview.py, in the browser."""
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


def rows(a):
    return {r["id"]: r for r in a["rows"]}


def test_the_answer_is_claudes_score_then_moneyline_spread_total(pv):
    a = pv("pvAnswer", game())
    assert a["score"] == "DET 30, CAR 19"
    assert [r["id"] for r in a["rows"]] == ["ml", "spread", "total"]


def test_moneyline_is_the_market_favourite_beside_claudes_winner_and_his_chance(pv):
    r = rows(pv("pvAnswer", game()))["ml"]
    assert (r["vegas"], r["claude"], r["sub"], r["conf"]) == ("DET 64%", "DET wins", "74% chance", None)


def test_spread_is_vegas_line_then_claudes_side_and_what_it_needs_in_points(pv):
    r = rows(pv("pvAnswer", game()))["spread"]
    assert (r["vegas"], r["claude"], r["conf"], r["sub"]) == ("DET by 3.5", "DET covers", "solid", "wins by 4 or more")


def test_the_underdogs_cover_says_it_may_lose_by_less_than_the_line(pv):
    # PIT @ CLE, 2026-10-02: Vegas PIT by 2.5, Claude CLE. The row David asked about.
    g = game(home="CLE", away="PIT", line={"fav": "PIT", "by": 2.5, "total": 38.5, "implied": None, "open": None},
             market_win={"CLE": 42.8, "PIT": 57.2},
             take={"pick": {"winner": "CLE", "score": {"CLE": 20, "PIT": 18}}, "win": {"CLE": 54},
                   "ats": {"side": "CLE", "conf": "solid", "edge": ""}, "total": {"call": "under", "conf": "lean"}})
    r = rows(pv("pvAnswer", g))
    assert (r["spread"]["vegas"], r["spread"]["claude"], r["spread"]["sub"]) == ("PIT by 2.5", "CLE covers", "wins, or loses by 2 or less")
    assert (r["ml"]["vegas"], r["ml"]["claude"], r["ml"]["sub"]) == ("PIT 57%", "CLE wins", "54% chance")
    assert (r["total"]["vegas"], r["total"]["claude"], r["total"]["sub"]) == ("38.5", "Under", "38 points or fewer")


def test_a_whole_number_line_counts_its_push_out_of_the_points(pv):
    g = game(line={"fav": "DET", "by": 3, "total": 50, "implied": None, "open": None},
             take={**game()["take"], "ats": {"side": "CAR", "conf": "lean", "edge": ""}, "total": {"call": "over", "conf": "lean"}})
    r = rows(pv("pvAnswer", g))
    assert r["spread"]["sub"] == "wins, or loses by 2 or less"          # by exactly 3 is a push
    assert r["total"]["sub"] == "51 points or more"                      # exactly 50 is a push


def test_total_is_vegas_number_beside_claudes_over_or_under(pv):
    r = rows(pv("pvAnswer", game()))["total"]
    assert (r["vegas"], r["claude"], r["conf"], r["sub"]) == ("50.5", "Under", "lean", "50 points or fewer")


def test_no_side_means_no_call_on_that_row(pv):
    g = game(take={**game()["take"], "ats": {"side": None, "conf": None, "edge": None}, "total": None})
    r = rows(pv("pvAnswer", g))
    assert (r["spread"]["claude"], r["spread"]["conf"], r["spread"]["sub"]) == ("", None, "")
    assert (r["total"]["claude"], r["total"]["sub"]) == ("", "")


def test_a_game_with_no_take_still_gives_vegas_on_every_row(pv):
    a = pv("pvAnswer", game(take=None))
    assert a["score"] == ""
    assert [(r["id"], r["vegas"], r["claude"]) for r in a["rows"]] == [
        ("ml", "DET 64%", ""), ("spread", "DET by 3.5", ""), ("total", "50.5", "")]


def test_a_game_with_nothing_has_no_rows(pv):
    assert pv("pvAnswer", game(line=None, market_win=None, take=None)) == {"score": "", "rows": []}


def test_a_graded_game_marks_each_row_hit_or_miss(pv):
    rg = {"su": "hit", "hit": "push", "total_hit": "miss", "result": {"home": 27, "away": 24}}
    r = rows(pv("pvAnswer", game(), rg))
    assert (r["ml"]["hit"], r["spread"]["hit"], r["total"]["hit"]) == ("hit", "push", "miss")
    assert rows(pv("pvAnswer", game()))["ml"]["hit"] is None


def test_the_final_names_the_winner_first(pv):
    assert pv("pvFinal", game(), {"result": {"home": 27, "away": 24}}) == "CAR 27, DET 24"
    assert pv("pvFinal", game(), {"result": {"home": 13, "away": 30}}) == "DET 30, CAR 13"
    assert pv("pvFinal", game(), None) == ""


def test_text_in_a_club_code_is_escaped(pv):
    a = pv("pvAnswer", game(line={"fav": "<b>", "by": 1, "total": None, "implied": None, "open": None}, take=None, market_win=None))
    assert rows(a)["spread"]["vegas"] == "&lt;b&gt; by 1"
