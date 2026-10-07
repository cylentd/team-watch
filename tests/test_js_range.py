"""The floor and ceiling beside every projection (plan U5, 2026-10-05), in Node.

ff-jarvis's `model.market.ranges` writes `floor` and `ceil` on every `player_projections` row: the 10th
and 90th percentile outcome in half-PPR points, given he plays. The page never computes a band;
`rangeFor` (ui/player.js, beside `projFor`) hands back the file's own two numbers and the one string
the profile strip, Ranks and the Start/Sit picker all print. A player with no points (ruled out, played
already, a bye) or no band (a position the table does not cover, a file from before it) shows nothing.
Holdout on 2025: 82.3% of games inside the band (QB 74.6%, RB 81.8%, WR 84.8%, TE 82.1%)."""
import pytest

PROJ = {"players": {
    "back": {"pts": 19.7, "floor": 7.4, "ceil": 31.2, "out": None, "done": None},
    "hurt": {"pts": None, "floor": None, "ceil": None, "out": "Out", "done": None},
    "leaky": {"pts": None, "floor": 4.0, "ceil": 20.0, "out": "Out", "done": None},   # a stale band on a ruled-out row
    "gone": {"pts": None, "floor": 5.0, "ceil": 21.0, "out": None, "done": "played"},
    "nopos": {"pts": 8.0, "floor": None, "ceil": None, "out": None, "done": None},
    "older": {"pts": 11.0, "out": None, "done": None},                                 # a file from before the band
    "zero": {"pts": 0.0, "floor": 0.0, "ceil": 0.0, "out": None, "done": None},
    "half": {"pts": 12.0, "floor": 6.0, "ceil": None, "out": None, "done": None},
}}


@pytest.fixture(scope="module")
def rng(node_js):
    return node_js("ui/player.js", "data/lede.js", globals={"LIVE_PROJECTIONS": PROJ})


def test_a_player_with_a_band_gets_the_files_own_numbers(rng):
    assert rng("rangeFor", {"slug": "back"}) == {"floor": 7.4, "ceil": 31.2, "text": "7.4–31.2"}


def test_the_text_keeps_one_decimal_on_a_whole_number(rng):
    assert rng("rangeText", 6, 20) == "6.0–20.0"


@pytest.mark.parametrize("slug", ["hurt", "leaky", "gone"])
def test_a_ruled_out_or_finished_player_shows_no_band(rng, slug):
    assert rng("rangeFor", {"slug": slug}) is None


@pytest.mark.parametrize("slug", ["nopos", "older", "half", "nobody"])
def test_a_null_or_missing_band_shows_nothing(rng, slug):
    assert rng("rangeFor", {"slug": slug}) is None


def test_a_band_of_zero_to_zero_is_no_band(rng):
    # ff-jarvis writes 0 and 0 for a row it zeroed; "0.0–0.0" would read as a certainty.
    assert rng("rangeFor", {"slug": "zero"}) is None


def test_without_the_projections_block_there_is_no_band(node_js):
    bare = node_js("ui/player.js", "data/lede.js")
    assert bare("rangeFor", {"slug": "back"}) is None


def test_a_ranks_row_reads_its_own_fields_the_same_way(rng):
    """Ranks rows carry pts, floor and ceil themselves (design/ranks.py): the same two numbers."""
    assert rng("rangeFrom", {"pts": 19.7, "floor": 7.4, "ceil": 31.2}) == {"floor": 7.4, "ceil": 31.2, "text": "7.4–31.2"}
    assert rng("rangeFrom", {"pts": 19.7, "floor": None, "ceil": None}) is None
    assert rng("rangeFrom", None) is None


def cells(rng, **kw):
    inp = {"proj": {"pts": 19.7, "out": None, "done": None}, "ppg": 26.2, "rank": "WR3",
           "share": None, "snaps": None, "range": {"floor": 7.4, "ceil": 31.2, "text": "7.4–31.2"}}
    inp.update(kw)
    return rng("ledeCells", inp)


def test_the_strip_puts_the_range_on_the_projection_cell_only(rng):
    got = cells(rng)
    assert got[0]["id"] == "proj" and got[0]["range"] == "7.4–31.2"
    assert all("range" not in c for c in got[1:])


def test_the_strip_draws_no_range_for_out_played_or_without_one(rng):
    assert "range" not in cells(rng, proj={"pts": None, "out": "Out", "done": None})[0]
    assert "range" not in cells(rng, proj={"pts": None, "out": None, "done": "bye"})[0]
    assert "range" not in cells(rng, range=None)[0]
    assert "range" not in rng("ledeCells", {"proj": {"pts": 19.7, "out": None, "done": None}, "ppg": None,
                                            "rank": None, "share": None, "snaps": None})[0]
