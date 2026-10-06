"""One projection per player (data/stock.js stockPts, ui/player.js projFor), in Node.

Monday 2026-10-05: Jaxon Smith-Njigba read 16.7 on his profile's Season tab (projFor, ff-jarvis's
player_projections: the model after the opponent, Vegas and the line blend) and 16.8 on its Matchup tab
(market_stock's `pts`, the books' own number, or its model fallback without the line blend). Two sources
for "his points this week". The projection is the one number: Season, Ranks, Start/Sit and Matchup read it.
The books' number stays, labelled as theirs, on a row the books priced."""
import pytest

PROJ = {"players": {"jsn": {"pts": 16.7}, "nobody": {"pts": None}}}


@pytest.fixture(scope="module")
def stock(node_js):
    return node_js("ui/player.js", "data/stock.js", globals={"LIVE_PROJECTIONS": PROJ})


def row(**kw):
    return {"src": "market", "pts": 16.8, **kw}


def test_a_priced_row_leads_with_the_projection_and_keeps_the_books_number_apart(stock):
    assert stock("stockPts", row(), {"slug": "jsn"}) == {"model": 16.7, "books": 16.8}


def test_a_model_fallback_row_reads_the_projection_too(stock):
    """The fallback row's own 16.8 is the model without the line blend: the projection replaces it."""
    assert stock("stockPts", row(src="model", pts=16.8), {"slug": "jsn"}) == {"model": 16.7, "books": None}


def test_without_a_projection_the_stock_row_stands_in(stock):
    assert stock("stockPts", row(src="model"), {"slug": "nobody"}) == {"model": 16.8, "books": None}
    assert stock("stockPts", row(), {"slug": "unknown"}) == {"model": None, "books": 16.8}


def test_a_row_the_books_did_not_price_has_no_books_number(stock):
    assert stock("stockPts", row(no_market=True), {"slug": "jsn"}) == {"model": 16.7, "books": None}
