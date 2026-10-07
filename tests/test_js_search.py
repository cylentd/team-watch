"""Player search's index and matcher (data/search.js), in Node, on the build's own data (2026-10-06).

Moved out of tests/test_search.py, where each of these was a page.evaluate on a full page load. The sandbox
holds the page's data chain (the rosters hydrated from the build's LIVE_* blocks, the leaguemates, the props,
the usage grid) and nothing that draws; the sheet that shows the results is tests/test_search.py, mounted.

The fixture carries Amon-Ra St. Brown (WR, DET), Chase Brown (RB, CIN) and Tee Higgins (WR, CIN) on the
rosters, which is enough to prove prefix, hyphen halves, a typo, and a position/team filter.
"""
import json
import re

import pytest

from component import injected

FILES = ("data/teams.js", "data/signals.js", "data/rbrules.js", "data/hydrate.js", "data/mates.js",
         "data/owner.js", "data/waiver.js", "lib/kick.js", "data/market.js", "data/dfs.js", "data/usage.js", "data/pool.js",
         "surface/parlay/gamelog.js", "data/search.js")


@pytest.fixture(scope="module")
def blocks(built):
    """Every `const NAME = <json>;` the build injected, parsed: the data the page's own files read."""
    return {name: json.loads(raw.replace("<\\/", "</"))
            for name, raw in re.findall(r"^const (\w+) = (.*);$", injected(built.fragment), re.M)}


@pytest.fixture
def search(node_js, blocks):
    """A fresh sandbox per test: a test may switch the team on screen, and the index it builds is cached."""
    return node_js(*FILES, globals={**blocks, "VIEW": "yahoo"})


def slugs(search, q):
    return search("(q) => searchFind(q, 8).map(r => r.e.slug)", q)


def test_the_index_holds_each_player_once_and_every_rostered_one(search):
    dupes = search("(() => { const s = searchIndex().map(e => e.slug); return s.length - new Set(s).size; })()")
    assert dupes == 0
    # A leaguemate's team is rostered only while it is on screen (data/search.js); a player with no
    # headshot is indexed by his name's slug.
    missing = search("""Object.values(TEAMS).filter(tm => !tm.mate || tm.key === VIEW)
        .flatMap(tm => tm.roster.map(p => [p.slug || slugOf(p.n), tm.key]))
        .filter(([s, k]) => !searchIndex().some(e => e.slug === s && e.tier === 3 && e.leagues.includes(k)))""")
    assert missing == []


def test_a_leaguemates_players_are_yours_only_on_their_team(search):
    mate = search("(MATES[0] || {}).key")
    assert mate, "the fixture carries a leaguemate team (MATES[0])"
    tagged = lambda: search("(k) => searchIndex().filter(e => e.leagues.includes(k)).length", mate)
    assert tagged() == 0, "another team's players are not the reader's"
    search("(k) => { VIEW = k; SEARCH_INDEX = null; }", mate)
    assert tagged() > 0, "the reader's own pick is"


@pytest.mark.parametrize("q,first", [
    ("amonra", "amonra-st-brown"),     # a hyphenated name typed without its hyphen
    ("Amon-Ra", "amonra-st-brown"),    # and with it
    ("st. brown", "amonra-st-brown"),  # punctuation dropped, two words both required
    ("higg", "tee-higgins"),           # the start of a surname
    ("higins", "tee-higgins"),         # one letter missing, 4+ letters typed
])
def test_the_best_match_comes_first(search, q, first):
    assert slugs(search, q)[0] == first


def test_a_hyphenated_name_answers_to_its_second_half(search):
    assert "amonra-st-brown" in slugs(search, "ra")


def test_position_and_team_words_filter(search):
    got = search("searchFind('wr det', 50).map(r => [r.e.pos, r.e.team])")
    assert got and all(pos == "WR" and team == "DET" for pos, team in got)


def test_no_typo_allowance_under_four_letters(search):
    # "brw" is one edit from "bro", but at three letters that would match half the league.
    assert "chase-brown" not in slugs(search, "brw")


def test_ties_break_toward_the_players_you_roster(search):
    ranked = search("searchFind('a', 400).map(r => [r.score, r.e.tier])")
    assert ranked == sorted(ranked, key=lambda r: (-r[0], -r[1]))


def test_the_matched_letters_are_bold(search):
    html = search("searchNameHTML('Amon-Ra St. Brown', searchFind('ra', 8).find(r => r.e.slug === 'amonra-st-brown').marks)")
    assert html == "Amon-<b>Ra</b> St. Brown"
