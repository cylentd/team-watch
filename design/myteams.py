"""David's Yahoo teams and every Yahoo league's own blocks, one loop over design/leagues.py (2026-09-29,
the third league AYO). Split out of build.py, which was at its line ratchet: a league added to the
list needs no line here or there.

Per Yahoo league: the roster (LIVE_YAHOO's shape), the League pages (league_recap.live_league_yahoo)
and Trades (league_trades.live_trades); each block is None when ff-jarvis has not written its file,
and the page draws that league's empty state.
"""
import json
import sys

import leagues
from league_recap import live_league_yahoo
from league_trades import live_trades
from mates import yahoo_rows
from sources import (REPO, YAHOO_ROSTERS, league_path, load_case_rosters, load_league_back, load_league_yahoo,
                     load_trades, read_first)

sys.path.insert(0, str(REPO / "api"))
from _espn import slugify  # noqa: E402


def roster_file(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def roster_path(key):
    """A league's roster file. The first Yahoo league's is YAHOO_ROSTERS, read when called, so a test can
    point it elsewhere (tests/test_yahoo_lineup.py)."""
    return YAHOO_ROSTERS if key == "yahoo" else league_path(key, "rosters")


def live_yahoo(available, path=None):
    """Yahoo comes from a website scrape with no injury status. Since 2026-09 the scrape carries
    each player's lineup slot, which is passed through (mates.YAHOO_SLOT); a scrape without one
    gives slot None, and the template falls back to inferring the lineup. `path` is another Yahoo
    league's roster file (AYO, 2026-09-29), in the same shape."""
    path = path or YAHOO_ROSTERS
    if not path.exists():
        return None
    d = json.loads(path.read_text(encoding="utf-8"))
    return {"name": d["me"], "league": d["league"], "league_id": d["league_id"],
            "updated": d["updated"], "roster": yahoo_rows(d["detail"][d["me"]], available, slugify)}


def yahoo_league_blocks(available):
    """Every Yahoo league's roster, League pages and Trades blocks, named by design/leagues.py."""
    out = {}
    for key in leagues.YAHOO:
        b, path = leagues.blocks(key), roster_path(key)
        out[b.roster] = live_yahoo(available, path)
        out[b.league] = live_league_yahoo(*load_league_yahoo(key), roster_file(path), slugify, *load_league_back(key),
                                          cases=load_case_rosters(key), key=key)
        out[b.trades] = live_trades(load_trades(key), load_league_back(key)[2], slugify=slugify, key=key)
    return out


def yahoo_rosters():
    """{key: parsed roster file or None} for every Yahoo league, in list order (design/mates.py's input)."""
    return {k: roster_file(roster_path(k)) for k in leagues.YAHOO}


def yahoo_gameday(key):
    """(this season, rosters, settings) of one Yahoo league, what design/gameday.py scores it from."""
    return load_league_yahoo(key)[0], roster_file(roster_path(key)), read_first(league_path(key, "settings"))


def roster_index(*sources):
    """slug -> {pos, team, leagues} across my teams, for the builder's `mine` flag."""
    idx = {}
    for key, src in sources:
        if not src:
            continue
        for p in src["roster"]:
            slug = slugify(p["n"])
            e = idx.setdefault(slug, {"pos": p["pos"], "team": p["team"], "leagues": []})
            e["leagues"].append(key)
    return idx
