"""The live gameday scoreboard behind the Live surface. GET /api/live.

Second server-side file in this repo; `api/chat.py` set the rules and this one follows them.
A Vercel Python function is file-based only while NO Python web framework is detected, so
requirements.txt must keep listing `anthropic` and nothing else -- which is why the ESPN call
below is `urllib.request` from the standard library rather than `requests`.

Why a server at all: the same reason as chat. ESPN authenticates with two browser cookies that
read the whole league as David, and the page is one public 1.4 MB blob. Anything the page
holds, everyone holds.

Why NO passphrase, unlike chat. The thing worth protecting here was never the data -- it is a
fantasy lineup, and the opponent can see it anyway. It was the cookies: an open endpoint lets a
stranger make this server hit ESPN with them at whatever rate they choose, and ESPN's answer to
that is to invalidate them. A cache solves that better than a secret does. Because the reply is
allowed to be a minute stale, the CDN serves repeats and ESPN sees at most one read per window
NO MATTER how many callers there are. A passphrase would have to be typed on every device and
would make the response uncacheable, which is the opposite of what protects the credential.

    Cache-Control: public, max-age=0, s-maxage=60, stale-while-revalidate=30

max-age=0 keeps the browser honest (it asks every time); s-maxage is what the edge obeys. Errors
are never cached -- a 30-second-old "ESPN is down" outliving the outage is worse than asking
again. Verify the edge is really doing this by reading `x-vercel-cache` on two calls in a row:
MISS then HIT.

There is deliberately NO storage. Each response replaces the last, so a poll needs nothing from
the poll before it: request in, one ESPN read, shaped JSON out, forget.

Env vars, all set in the Vercel project, never in the repo:

    ESPN_SWID          the SWID cookie, braces included
    ESPN_S2            espn_s2, percent-encoded exactly as the browser shows it
    ESPN_LEAGUE_ID     1534545
    ESPN_SEASON        optional override; otherwise inferred (Jan/Feb belong to last autumn)

The week is never computed here. ESPN states its own `scoringPeriodId` in the reply, so this
file carries no season calendar to drift out of date.

Live scoring, as verified against the live league 2026-09-20:

    totalPointsLive           the live team score. `totalPoints` stays 0.0 until the week
                              settles, so reading that one shows 0 all Sunday.
    totalProjectedPointsLive  projected final: points banked plus what is still to come.
    winProbability            ESPN's own, 0..1, both sides summing to 1.
    stats[] statSourceId 0    a player's ACTUAL points, in this league's custom scoring, which
                              is the whole reason this reads ESPN's number instead of computing
                              one. statSourceId 1 is the projection.

A player's game state is not in this payload. The one honest signal it does carry is whether an
actual row exists at all -- that means his game has started -- so `started` is reported, and the
page decides when to poll from the kickoff times it already holds.
"""

import datetime
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from http.server import BaseHTTPRequestHandler

HOST = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl"
# Three views, each earning its place, measured against the live league 2026-09-20:
#   mMatchupScore  both lineups' point rows, the live totals, the win probability
#   mTeam          team names, and the primaryOwner that identifies which team is mine
#   mBoxscore      the player NAMES. Without it every roster entry comes back anonymous --
#                  points and lineup slot, no name, not even on my own team.
# 589 KB together, against 6,009 KB for the five-view combo the ESPN front end asks for: the
# view left out is mRoster, which alone inflated the teams block to 2.9 MB.
# No scoringPeriodId is sent: ESPN states its own current period in the reply.
VIEWS = ["mMatchupScore", "mTeam", "mBoxscore"]
TIMEOUT = 15

CACHE_S = 60          # what the edge serves without asking this function again
SWR_S = 30            # ... and how long past that it may serve a stale copy while refreshing
# A warm instance serves its memo rather than re-reading ESPN. Belt to the CDN's braces: it is
# what catches a burst that lands on several cold regions at once, where the edge cannot help.
MIN_INTERVAL = 20

ACTUAL, PROJECTED = 0, 1
BENCH = (20, 21)
SLOT = {0: "QB", 2: "RB", 3: "RB/WR", 4: "WR", 5: "WR/TE", 6: "TE", 7: "OP", 16: "D/ST",
        17: "K", 20: "BE", 21: "IR", 23: "FLEX"}
PRO = {0: "FA", 1: "ATL", 2: "BUF", 3: "CHI", 4: "CIN", 5: "CLE", 6: "DAL", 7: "DEN", 8: "DET",
       9: "GB", 10: "TEN", 11: "IND", 12: "KC", 13: "LV", 14: "LAR", 15: "MIA", 16: "MIN",
       17: "NE", 18: "NO", 19: "NYG", 20: "NYJ", 21: "PHI", 22: "ARI", 23: "PIT", 24: "LAC",
       25: "SF", 26: "SEA", 27: "TB", 28: "WSH", 29: "CAR", 30: "JAX", 33: "BAL", 34: "HOU"}

_memo = {"at": 0.0, "body": None}


class Expired(Exception):
    """ESPN rejected the cookies. Distinct from a transient failure: retrying cannot fix it."""


def season():
    override = os.environ.get("ESPN_SEASON")
    if override:
        return int(override)
    today = datetime.date.today()
    return today.year - 1 if today.month <= 2 else today.year


def fetch(swid, s2, league_id):
    """One GET against the league. Returns the parsed body."""
    if not swid.startswith("{"):
        swid = "{" + swid.strip("{}") + "}"
    url = (f"{HOST}/seasons/{season()}/segments/0/leagues/{league_id}?"
           + urllib.parse.urlencode([("view", v) for v in VIEWS]))
    req = urllib.request.Request(url, headers={
        "Cookie": f"SWID={swid}; espn_s2={s2}",
        "Accept": "application/json",
        "User-Agent": "team-watch-live/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise Expired(f"ESPN returned {exc.code}") from exc
        raise


def points(player, week, source):
    """This week's applied total from the stat row of `source`, or None when there is none.

    A missing actual row is the signal that his game has not started, so None is meaningful
    here and must not be flattened to 0.0.
    """
    for s in player.get("stats") or []:
        if (s.get("scoringPeriodId") == week and s.get("statSourceId") == source
                and s.get("statSplitTypeId") == 1):
            return s.get("appliedTotal")
    return None


def lineup(side, week):
    """One team's roster for this scoring period, starters first, each slot in a stable order."""
    rows = []
    entries = ((side.get("rosterForCurrentScoringPeriod") or {}).get("entries")) or []
    for e in entries:
        player = ((e.get("playerPoolEntry") or {}).get("player")) or {}
        slot = e.get("lineupSlotId")
        actual = points(player, week, ACTUAL)
        rows.append({
            "slot": SLOT.get(slot, str(slot)),
            "starter": slot not in BENCH,
            "name": player.get("fullName"),
            "team": PRO.get(player.get("proTeamId"), ""),
            "actual": actual,
            "projected": points(player, week, PROJECTED),
            "started": actual is not None,
            "injury": player.get("injuryStatus"),
        })
    rows.sort(key=lambda r: (not r["starter"], r["slot"], r["name"] or ""))
    return rows


def side_summary(side, names, week):
    return {
        "team": names.get(side.get("teamId"), f"Team {side.get('teamId')}"),
        "live": side.get("totalPointsLive"),
        "projected": side.get("totalProjectedPointsLive"),
        "winPct": side.get("winProbability"),
        "lineup": lineup(side, week),
    }


def shape(body, swid):
    """The whole 589 KB reply reduced to the one matchup the page draws.

    Raises LookupError when my team or my matchup is missing, which is a real failure worth
    saying out loud rather than rendering an empty board.
    """
    week = body.get("scoringPeriodId")
    period = (body.get("status") or {}).get("currentMatchupPeriod")
    teams = body.get("teams") or []
    names = {t.get("id"): (t.get("name") or f"Team {t.get('id')}") for t in teams}

    want = ("{" + swid.strip("{}") + "}").upper()
    me = next((t for t in teams if str(t.get("primaryOwner", "")).upper() == want), None)
    my_id = me.get("id") if me else int(os.environ.get("ESPN_TEAM_ID") or 0) or None
    if my_id is None:
        raise LookupError("could not identify my team from the SWID cookie")

    def involves_me(m):
        return my_id in ((m.get("home") or {}).get("teamId"), (m.get("away") or {}).get("teamId"))

    rows = [m for m in (body.get("schedule") or [])
            if involves_me(m) and (period is None or m.get("matchupPeriodId") == period)]
    if not rows:
        raise LookupError(f"no matchup for team {my_id} in period {period}")
    m = rows[0]
    mine = m["home"] if (m.get("home") or {}).get("teamId") == my_id else m["away"]
    opp = m["away"] if (m.get("home") or {}).get("teamId") == my_id else m["home"]

    return {
        "league": "espn",
        "week": week,
        "asof": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "me": side_summary(mine, names, week),
        "opponent": side_summary(opp, names, week),
    }


def live():
    """The shaped scoreboard, memoized for MIN_INTERVAL seconds on a warm instance."""
    now = time.time()
    if _memo["body"] is not None and now - _memo["at"] < MIN_INTERVAL:
        return dict(_memo["body"], cached=True)

    swid = os.environ["ESPN_SWID"]
    out = shape(fetch(swid, os.environ["ESPN_S2"], os.environ["ESPN_LEAGUE_ID"]), swid)
    _memo["at"], _memo["body"] = now, out
    return dict(out, cached=False)


def configured():
    return all(os.environ.get(k) for k in ("ESPN_SWID", "ESPN_S2", "ESPN_LEAGUE_ID"))


class handler(BaseHTTPRequestHandler):

    def _send(self, code, payload, cache=False):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # Only a good board is cacheable. A cached failure would outlive the thing that caused
        # it, and the page would keep being told ESPN is down after it came back.
        self.send_header("Cache-Control",
                         f"public, max-age=0, s-maxage={CACHE_S}, stale-while-revalidate={SWR_S}"
                         if cache else "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not configured():
            return self._send(503, {"error": "Live is not configured on the server yet."})
        try:
            self._send(200, live(), cache=True)
        except Expired:
            # The one failure a retry cannot fix, so the page says so instead of spinning.
            self._send(409, {"error": "ESPN cookies have expired. Re-copy SWID and espn_s2.",
                             "expired": True})
        except LookupError as exc:
            print(f"live: {exc}")
            self._send(502, {"error": "ESPN replied, but this week's matchup was not in it."})
        except Exception as exc:                                       # noqa: BLE001
            # Can carry a cookie or a request id, so it goes to the function log, never the page.
            print(f"live: {type(exc).__name__}: {exc}")
            self._send(502, {"error": "Could not reach ESPN. Try again."})

    def log_message(self, fmt, *args):
        """Vercel already logs the request line; this would double every entry."""
