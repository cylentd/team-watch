"""design/signals.py: the My Teams trend series and news counts, against fixtures and by hand."""
import json
import re

from build import slugify
import signals


def _signals(built):
    m = re.search(r"^const LIVE_SIGNALS = (.*);$", built.fragment, re.M)
    return json.loads(m.group(1).replace("<\\/", "</"))


def _item(title, created, team=None, cats=None):
    return {"title": title, "created": created, "team_id": team, "categories": cats}


def test_fixture_rows_carry_series_verdict_and_news(built):
    p = _signals(built)["players"]
    assert p["chase-brown"]["series"] == [58.0, 71.0]
    assert p["chase-brown"]["verdict"] == "RISING"
    assert p["george-kittle"]["series"] == [None, 70.0]          # filled from the pool
    assert p["chase-brown"]["news"] == 1                          # on both rosters, counted once
    assert p["amonra-st-brown"] == {"series": [], "verdict": None, "why": None, "news": 0, "hot": False}


def test_headline_must_start_with_the_whole_name():
    players = [{"slug": "chase-brown", "team": "CIN"}]
    items = [_item("Chase Brown (hamstring) questionable", "2026-09-10 12:00:00", "CIN"),
             _item("Chase Browning signs with Bengals", "2026-09-10 12:00:00", "CIN"),
             _item("Bengals say Chase Brown is fine", "2026-09-10 12:00:00", "CIN")]
    assert signals.news_by_slug(items, players, slugify) == {"chase-brown": {"n": 1, "hot": False}}


def test_team_must_agree_with_aliases_applied():
    players = [{"slug": "travis-etienne", "team": "JAX"}, {"slug": "josh-allen", "team": "BUF"}]
    items = [_item("Travis Etienne (ankle) limited", "2026-09-10 12:00:00", "JAC", ["Injury"]),
             _item("Josh Allen (knee) sacks leader", "2026-09-10 12:00:00", "JAC")]
    assert signals.news_by_slug(items, players, slugify) == {"travis-etienne": {"n": 1, "hot": True}}


def test_window_is_measured_from_the_newest_story():
    players = [{"slug": "brock-purdy", "team": "SF"}]
    items = [_item("Brock Purdy (toe) full", "2026-09-10 12:00:00", "SF"),
             _item("Brock Purdy (toe) limited", "2026-09-07 11:59:59", "SF"),
             _item("Brock Purdy (toe) bad date", "bad-timestamp", "SF")]
    assert signals.news_by_slug(items, players, slugify)["brock-purdy"]["n"] == 1


def test_my_league_row_wins_over_the_pool():
    usage = {"leagues": [{"players": [{"name": "Chase Brown", "verdict": "RISING", "why": "", "series": [1, 2]}]}],
             "pool": [{"name": "Chase Brown", "verdict": "hold", "why": "", "series": [9, 9]}, "a bare name"]}
    assert signals.usage_by_slug(usage, slugify)["chase-brown"]["verdict"] == "RISING"
