"""Live stats for Gameday > Live, trimmed. GET /api/stats?week=3&ids=8183,9226,SEA

Sleeper's week file holds every player in the league, about 2,000 rows: 277 KB compressed, measured
2026-09-28, which a phone polling every 30 s through a three-hour window would pay 100 MB for. This
reads it once per window for every caller and hands back only the requested players, only the
fields the page's scorer and stat lines use (a few KB), plus each team's game state from Sleeper's
schedule, so the page needs one request per poll.

No credentials: Sleeper's stats and schedule are public. The edge serves repeats for CACHE_S, and a
warm instance memoizes Sleeper's replies, so Sleeper sees about one read per window whatever the
number of readers. Errors are never cached: a cached "Sleeper is down" would outlive the outage.

A reply: {week, asof, updated (newest Sleeper row, ms), games {TEAM: "pre_game"|"in_game"|"complete"},
stats {id: {key: value}}}. An id Sleeper has no row for yet (before kickoff) is simply absent.
"""
import datetime
import gzip
import json
import os
import re
import sys
import time
import urllib.request

from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _scoring  # noqa: E402

STATS = "https://api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular"
SCHEDULE = "https://api.sleeper.com/schedule/nfl/regular/{season}"
CACHE_S = 15          # the edge's window; the page polls every 30 s
SWR_S = 15
STATS_MEMO_S = 10     # a warm instance's own window on Sleeper's stats
SCHEDULE_MEMO_S = 60  # game states change at kickoff and the final whistle, not every play
IDS_MAX = 600
ID = re.compile(r"^(\d{1,8}|[A-Z]{2,3})$")

# What a stat line shows beside what the rules score.
LINE = ("pass_att", "pass_cmp", "pass_yd", "pass_td", "pass_int", "rush_att", "rush_yd", "rush_td",
        "rec", "rec_tgt", "rec_yd", "rec_td", "fum_lost", "fgm", "fga", "fgm_lng", "xpm", "xpa",
        "pts_allow", "yds_allow", "sack", "int", "fum_rec", "def_td", "def_st_td", "safe")


def keep_keys():
    """Every Sleeper key a rule in api/_scoring.py can read, plus the stat-line keys."""
    keys = set(LINE)
    for off, dst in _scoring.ESPN.values():
        keys.update(k for t in (off, dst) if t for k in t["s"])
    for table in (_scoring.YAHOO, _scoring.YAHOO_DST):
        keys.update(k for ks in table.values() for k in ks)
    keys.add("pts_allow")
    return frozenset(keys)


KEEP = keep_keys()
_memo = {"stats": {}, "schedule": {}}


def season_of(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return now.year if now.month >= 3 else now.year - 1


def _get(url):
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip", "User-Agent": "team-watch/1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        body = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)
    return json.loads(body)


def _memoized(kind, key, ttl, url):
    hit = _memo[kind].get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    value = _get(url)
    _memo[kind] = {key: (time.time(), value)}
    return value


def trim(rows, ids):
    """Sleeper's rows -> {id: {kept key: value}} for the wanted ids, zeros dropped; and the newest stamp."""
    out, newest = {}, 0
    for r in rows or []:
        pid = str(r.get("player_id"))
        if pid not in ids:
            continue
        s = {k: v for k, v in (r.get("stats") or {}).items() if k in KEEP and v}
        out[pid] = s
        newest = max(newest, r.get("updated_at") or 0)
    return out, newest


def states(games, week):
    """{team: status} for the week's games; each team once."""
    out = {}
    for g in games or []:
        if g.get("week") == week:
            for side in ("home", "away"):
                if g.get(side):
                    out[g[side]] = g.get("status")
    return out


def live_stats(week, ids):
    season = season_of()
    rows = _memoized("stats", (season, week), STATS_MEMO_S, STATS.format(season=season, week=week))
    sched = _memoized("schedule", season, SCHEDULE_MEMO_S, SCHEDULE.format(season=season))
    stats, newest = trim(rows, ids)
    return {"week": week, "asof": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "updated": newest or None, "games": states(sched, week), "stats": stats}


def parse(query):
    """(week, ids) from the query, or a reason it is not one."""
    q = parse_qs(query)
    try:
        week = int((q.get("week") or [""])[0])
    except ValueError:
        return None, "week must be a number"
    if not 1 <= week <= 22:
        return None, "week must be 1-22"
    ids = [i for i in (q.get("ids") or [""])[0].split(",") if i]
    if not ids or len(ids) > IDS_MAX or not all(ID.match(i) for i in ids):
        return None, "ids must be Sleeper ids or team codes, comma-separated"
    return (week, frozenset(ids)), None


class handler(BaseHTTPRequestHandler):

    def _send(self, code, payload, cache=False):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", f"public, max-age=0, s-maxage={CACHE_S}, stale-while-revalidate={SWR_S}"
                         if cache else "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed, why = parse(urlparse(self.path).query)
        if not parsed:
            return self._send(400, {"error": why})
        try:
            self._send(200, live_stats(*parsed), cache=True)
        except Exception as exc:                                       # noqa: BLE001
            print(f"stats: {type(exc).__name__}: {exc}")
            self._send(502, {"error": "Could not reach Sleeper. Trying again."})

    def log_message(self, fmt, *args):
        """Vercel already logs the request line; this would double every entry."""
