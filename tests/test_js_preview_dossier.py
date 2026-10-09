"""Preview's dossier numbers (data/pvdossier.js), in Node: a player's yards and touchdown chance from his
lines, and Claude's own numbers in Vegas's units.

Ledger #82 (David, 2026-10-07: the players are "the best part and buried"; the Moneyline / Spread / Total rows
"hard to read"). Storyboard draft A, "Ledger", 2026-10-09: each player row leads with the yards our model
expects and his chance to score, never fantasy points; each bet shows Vegas's number and ours in the same
unit ("CHI by 1.5" beside "CHI by 4"), then the pick. Where it sits on the screen is test_preview_dossier.py."""
import pytest

from wording import words


@pytest.fixture(scope="module")
def dz(node_js):
    return node_js("data/preview.js", "data/pvdossier.js")


def line(mkt, mu=None, model=None):
    return {"mkt": mkt, "mu": mu, "model": model, "line": 1.5}


def test_a_back_shows_his_rushing_yards_and_touchdown_chance(dz):
    rows = [line("RECS", 2.04), line("RUSH", 68.85), line("TD", 0.59, 43), line("REC", 16.56)]
    assert dz("pvPlayerLine", "RB", rows) == {"yds": 69, "unit": words("preview.pl.rush"), "td": 43, "n": 4}


@pytest.mark.parametrize("pos, unit", [("QB", "preview.pl.pass"), ("WR", "preview.pl.rec"), ("TE", "preview.pl.rec")])
def test_each_position_reads_its_own_yards_market(dz, pos, unit):
    rows = [line("RUSH", 12.2), line("PASS", 221.4), line("REC", 55.5)]
    assert dz("pvPlayerLine", pos, rows)["unit"] == words(unit)


def test_without_his_own_market_another_yards_line_stands_in(dz):
    got = dz("pvPlayerLine", "QB", [line("RUSH", 24.6), line("TD", None, 12)])
    assert (got["yds"], got["unit"], got["td"]) == (25, words("preview.pl.rush"), 12)


def test_a_player_with_no_lines_has_no_yards_and_no_chance(dz):
    assert dz("pvPlayerLine", "WR", []) == {"yds": None, "unit": "", "td": None, "n": 0}


def test_a_yards_line_without_a_model_number_is_skipped(dz):
    assert dz("pvPlayerLine", "RB", [line("RUSH", None), line("REC", 18.2)])["yds"] == 18


def game(**over):
    g = {"home": "GB", "away": "CHI",
         "take": {"pick": {"winner": "CHI", "score": {"GB": 19, "CHI": 23}}, "win": {"CHI": 57}}}
    g.update(over)
    return g


def test_ours_is_the_pick_in_vegas_units(dz):
    assert dz("pvOurs", game()) == {"ml": "CHI 57%", "spread": "CHI by 4", "total": "42"}


def test_a_tied_score_is_even_and_no_chance_leaves_the_win_cell_empty(dz):
    g = game(take={"pick": {"winner": "GB", "score": {"GB": 20, "CHI": 20}}, "win": None})
    assert dz("pvOurs", g) == {"ml": "", "spread": words("preview.line.even"), "total": "40"}


def test_no_take_has_no_numbers_of_ours(dz):
    assert dz("pvOurs", game(take=None)) is None
    assert dz("pvOurs", game(take={"head": "x", "pick": None})) is None
