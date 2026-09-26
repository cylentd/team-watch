"""design/mates.py: every other team in David's two leagues (leaguemates phase 1, 2026-09-25)."""
import mates
from build import slugify

ESPN = {"me": "Mine", "detail": {
    "Mine": [{"name": "A Qb", "pos": "QB", "team": "BUF", "slot": "QB"}],
    "zeta": [{"name": "B Wr", "pos": "WR", "team": "ATL", "slot": "BE"},
             {"name": "C Rb", "pos": "RB", "team": "BUF", "slot": "RB"},
             {"name": "D Flex", "pos": "WR", "team": "DAL", "slot": "FLEX"},
             {"name": "E Qb", "pos": "QB", "team": "KC", "slot": "QB", "status": "OUT"}],
    "Alpha": [{"name": "Buffalo D/ST", "pos": "DEF", "team": "BUF", "slot": "D/ST"}],
}}
YAHOO = {"me": "Chat", "detail": {"Chat": [], "Other": [{"name": "F Te", "pos": "TE", "team": "SF", "slot": "W/R/T"}]}}
NO_BADGE = lambda name, espn: {"OUT": "OUT"}.get(espn or "")


def test_every_team_but_davids_by_name_under_its_league():
    got = mates.live_mates(ESPN, YAHOO, set(), NO_BADGE, slugify)
    assert [(t["league"], t["name"]) for t in got["teams"]] == [("espn", "Alpha"), ("espn", "zeta"), ("yahoo", "Other")]
    assert [t["key"] for t in got["teams"]] == ["espn-alpha", "espn-zeta", "yahoo-other"]


def test_a_leaguemates_rows_come_in_lineup_order():
    """ESPN lists another team's players in no slot order; the page draws QB first."""
    zeta = next(t for t in mates.live_mates(ESPN, None, set(), NO_BADGE, slugify)["teams"] if t["name"] == "zeta")
    assert [r["slot"] for r in zeta["roster"]] == ["QB", "RB", "FLX1", "BN"]
    assert zeta["roster"][0]["status"] == "OUT", "the badge rule is build.py's, passed in"


def test_rows_keep_the_pages_shape():
    got = mates.live_mates(ESPN, YAHOO, set(), NO_BADGE, slugify)
    dst = got["teams"][0]["roster"][0]
    assert (dst["n"], dst["pos"]) == ("Buffalo", "DST")
    assert got["teams"][2]["roster"][0]["slot"] == "FLEX", "Yahoo's W/R/T is the page's FLEX"


def test_no_roster_files_means_no_block():
    assert mates.live_mates(None, None, set(), NO_BADGE, slugify) is None
    assert mates.slugs(None) == [] and mates.report(None) == "Leaguemates: none"
