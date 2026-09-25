"""What every ESPN read in this repo shares: the host, the id maps, the one GET, and the name slug.

Underscore-prefixed, so Vercel does not turn it into an endpoint; api/live.py and api/league.py
import it, and design/build.py imports `slugify` from it so the page and the functions compute
one slug for one name. It was three copies of the maps and two of the slug before 2026-09-24.
"""

import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request

HOST = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
TIMEOUT = 15

BENCH = (20, 21)
SLOT = {0: "QB", 2: "RB", 3: "RB/WR", 4: "WR", 5: "WR/TE", 6: "TE", 7: "OP", 16: "D/ST",
        17: "K", 20: "BE", 21: "IR", 23: "FLEX"}
PRO = {0: "FA", 1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
       9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
       17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
       25: "SF", 26: "SEA", 27: "TB", 28: "WSH", 29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU"}
# defaultPositionId, not lineupSlotId: the two id spaces overlap (4 is TE here, WR as a slot).
POS = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DST"}

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def slugify(name):
    """Display name -> headshot slug, matching ff-jarvis's file naming."""
    cleaned = "".join(c if (c.isalnum() or c == " ") else "" for c in name.lower())
    parts = [p for p in cleaned.split() if p not in SUFFIXES]
    return "-".join(parts)


class Expired(Exception):
    """ESPN refused the read (401/403): the cookies expired, or the league is private and none
    were sent. Distinct from a transient failure: retrying cannot fix it."""


def season():
    override = os.environ.get("ESPN_SEASON")
    if override:
        return int(override)
    today = datetime.date.today()
    return today.year - 1 if today.month <= 2 else today.year


def fetch(league_id, views, swid=None, s2=None, agent="team-watch/1.0"):
    """One GET against a league. A public league is read with no cookies at all."""
    url = (f"{HOST}/seasons/{season()}/segments/0/leagues/{int(league_id)}?"
           + urllib.parse.urlencode([("view", v) for v in views]))
    headers = {"Accept": "application/json", "User-Agent": agent}
    if swid and s2:
        swid = "{" + swid.strip("{}") + "}"
        headers["Cookie"] = f"SWID={swid}; espn_s2={s2}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise Expired(f"ESPN returned {exc.code}") from exc
        raise
