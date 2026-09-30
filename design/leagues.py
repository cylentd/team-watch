"""David's leagues, the one list the build reads (2026-09-29: a third league, AYO, a second Yahoo login).

ff-jarvis's model/common/registry.py is the source; this is the page's copy, held to it by
tests/test_leagues.py (architecture.md: a copy is allowed only with a test that fails when the two
diverge). A league's data files keep ff-jarvis's names: ESPN's and the first Yahoo league's legacy
ones, `<key>_<kind>.json` for every league added since.

Each Yahoo league's page blocks and its two hand-kept files (private pairs, record skip) are named
here too, so build.py loops over the list instead of branching on a key. The JS names its blocks
literally (data/teams.js), because a top-level const cannot be looked up by a string.
"""
import pathlib
from collections import namedtuple

HERE = pathlib.Path(__file__).resolve().parent

League = namedtuple("League", "key platform label")

LEAGUES = (
    League("espn", "espn", "ESPN"),
    League("yahoo", "yahoo", "Yahoo"),
    League("ayo", "yahoo", "AYO"),
)
KEYS = tuple(lg.key for lg in LEAGUES)
YAHOO = tuple(lg.key for lg in LEAGUES if lg.platform == "yahoo")

# The names these two leagues' files had before ff-jarvis had a list; anything not listed falls to the rule.
LEGACY = {
    "espn": {k: f"espn_{k}.json" for k in
             ("rosters", "free_agents", "settings", "draft", "transactions", "league", "league_history")},
    "yahoo": {"rosters": "league_rosters.json", "settings": "yahoo_settings.json",
              "waivers": "yahoo_waivers.json", "free_agents": "yahoo_free_agents.json",
              "transactions": "yahoo_transactions.json", "draft": "yahoo_draft.json",
              "league": "yahoo_league.json", "league_history": "yahoo_league_history.json",
              "league_box": "yahoo_league_box.json", "league_recap": "yahoo_league_recap.json",
              "league_managers": "yahoo_league_managers.json", "league_owners": "yahoo_league_owners.json",
              "league_trades": "yahoo_league_trades.json", "trade_verdicts": "yahoo_trade_verdicts.json",
              "case_rosters": "yahoo_case_rosters.json"},
}


def file(key, kind):
    """ff-jarvis's data file name for one league's `kind`: file("ayo", "rosters") -> "ayo_rosters.json"."""
    if key not in KEYS:
        raise KeyError(f"unknown league {key!r}; known: {', '.join(KEYS)}")
    return LEGACY.get(key, {}).get(kind) or f"{key}_{kind}.json"


Blocks = namedtuple("Blocks", "roster league trades")


def blocks(key):
    """A Yahoo league's injected blocks: its roster, its League pages, its Trades. The first league's
    names predate the list and stay, so nothing that reads them moves."""
    if key == "yahoo":
        return Blocks("LIVE_YAHOO", "LIVE_LEAGUE_YAHOO", "LIVE_TRADES")
    k = key.upper()
    return Blocks(f"LIVE_{k}", f"LIVE_LEAGUE_{k}", f"LIVE_TRADES_{k}")


def private_file(key):
    """design/league_private.json for the first Yahoo league, league_private_<key>.json after; a
    league without one has no private pairs."""
    return HERE / ("league_private.json" if key == "yahoo" else f"league_private_{key}.json")


def skip_file(key):
    """design/league_record_skip.json for the first Yahoo league, league_record_skip_<key>.json after."""
    return HERE / ("league_record_skip.json" if key == "yahoo" else f"league_record_skip_{key}.json")
