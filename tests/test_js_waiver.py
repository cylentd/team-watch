"""Who search can find: a visitor's player list holds no waiver rows (data/search.js, data/waiver.js,
data/owner.js; 2026-10-06).

Moved out of tests/test_waiver_owner.py, where the check cost a page load and four calls of pure data/
functions through page.evaluate. The Node sandbox has no localStorage, so `isOwner()` is false: a visitor.
The owner is the same sandbox with a localStorage that holds his token. What Waivers draws for a visitor is
tests/test_waiver_owner.py, in the component layer.
"""
import pytest

WAIVER_ROWS = [{"n": "Waiver One", "slug": "waiver-one", "pos": "WR", "team": "MIA"},
               {"n": "Waiver Two", "slug": "waiver-two", "pos": "RB", "team": "BUF"}]
PROP_ROWS = [{"n": "Prop One", "slug": "prop-one", "pos": "QB"}, {"n": "Prop Two", "slug": "prop-two", "pos": "TE"}]
ROSTER = [{"n": "Mine One", "slug": "mine-one", "pos": "WR", "team": "DAL"}]


@pytest.fixture
def search(node_js):
    return node_js("data/owner.js", "data/waiver.js", "data/search.js", globals={
        "LIVE_WAIVER": {"players": WAIVER_ROWS, "leagues_meta": {}}, "LIVE_MARKET": True, "PROPS": PROP_ROWS,
        "LIVE_YAHOO_DFS": False, "DFSPOOL_YAHOO": [], "USAGE_LIVE": False, "USAGE": {"rows": []},
        "LIVE_POOL": False, "POOL": [], "VIEW": "yahoo", "TEAMS": {"yahoo": {"key": "yahoo", "roster": ROSTER}}})


def test_a_visitors_search_holds_no_waiver_rows(search):
    """No owner token: the market rows are the props alone, and no waiver row is among any source."""
    market = search("searchSources().filter(([, src]) => src === 'market').length")
    assert market == search("searchSources().length - searchSources().filter(([, s]) => s !== 'market').length")
    assert market == len(PROP_ROWS), "the two prop rows, none of the waiver ones"
    assert search("waiverPlayers().every(w => !searchSources().some(([p]) => p === w))")


def test_the_owners_search_does_hold_the_waiver_rows(search):
    """The same data with his token: the waiver rows join the market, so the visitor's absence is a rule."""
    search("() => { globalThis.localStorage = {getItem: () => OWNER_HASH}; }")
    assert search("isOwner()") is True
    assert search("searchSources().filter(([, src]) => src === 'market').length") == len(PROP_ROWS) + len(WAIVER_ROWS)
    assert search("waiverPlayers().every(w => searchSources().some(([p]) => p === w))")
