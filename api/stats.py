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

`teams=CHI,PHI` (2026-09-28, the game sheet) adds `box {id: {n, pos, team, s}}`: every player of
those clubs with a stat, named, so the sheet can draw a box score and top scorers for players on
nobody's roster. `ids` may then be left out.

`lead=1` (2026-10-04) adds `lead {id: {n, pos, team, s, pts}}`: every player with a touchdown and
the week's top 25 by half-PPR, league-wide, for Live's TDs tab and the Digest's Right now.
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
TEAMS_MAX = 2
ID = re.compile(r"^(\d{1,8}|[A-Z]{2,3})$")
TEAM = re.compile(r"^[A-Z]{2,3}$")
BOX_POS = ("QB", "RB", "WR", "TE", "K")

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


def box(rows, teams):
    """Every player of `teams` with a kept stat -> {id: {n, pos, team, s}}. Defenses are left out:
    the box score is the players', and a defense's line is the other club's score."""
    out = {}
    for r in rows or []:
        p = r.get("player") or {}
        pos = p.get("position")
        if r.get("team") not in teams or pos not in BOX_POS:
            continue
        s = {k: v for k, v in (r.get("stats") or {}).items() if k in KEEP and v}
        if s:
            name = f"{p.get('first_name') or ''} {p.get('last_name') or ''}".strip()
            out[str(r.get("player_id"))] = {"n": name, "pos": pos, "team": r["team"], "s": s}
    return out


LEAD_TOP = 25
TD_KEYS = ("rush_td", "rec_td", "pass_td")


def half_ppr(s):
    """Sleeper's own half-PPR total when it carries one, else the standard sum. One yardstick for
    "who leads the league right now", whatever each reader's league scores."""
    if s.get("pts_half_ppr") is not None:
        return round(float(s["pts_half_ppr"]), 1)
    pts = (s.get("pass_yd", 0) * 0.04 + s.get("pass_td", 0) * 4 - s.get("pass_int", 0) * 2
           + s.get("rush_yd", 0) * 0.1 + s.get("rush_td", 0) * 6 + s.get("rec", 0) * 0.5
           + s.get("rec_yd", 0) * 0.1 + s.get("rec_td", 0) * 6 - s.get("fum_lost", 0) * 2)
    return round(pts, 1)


def lead(rows):
    """League-wide, for Live's TDs tab and the Digest's Right now (2026-10-04): every player who has
    scored a touchdown, plus the top LEAD_TOP by half-PPR points -> {id: {n, pos, team, s, pts}}."""
    cand = []
    for r in rows or []:
        p = r.get("player") or {}
        pos = p.get("position")
        if pos not in BOX_POS or not r.get("team"):
            continue
        raw = r.get("stats") or {}
        s = {k: v for k, v in raw.items() if k in KEEP and v}
        if not s:
            continue
        name = f"{p.get('first_name') or ''} {p.get('last_name') or ''}".strip()
        cand.append((str(r.get("player_id")), {"n": name, "pos": pos, "team": r["team"], "s": s,
                                               "pts": half_ppr(raw)}))
    top = {pid for pid, _ in sorted(cand, key=lambda c: -c[1]["pts"])[:LEAD_TOP]}
    return {pid: v for pid, v in cand if pid in top or any(v["s"].get(k) for k in TD_KEYS)}


def states(games, week):
    """{team: status} for the week's games; each team once."""
    out = {}
    for g in games or []:
        if g.get("week") == week:
            for side in ("home", "away"):
                if g.get(side):
                    out[g[side]] = g.get("status")
    return out


def live_stats(week, ids, teams=frozenset(), want_lead=False):
    season = season_of()
    rows = _memoized("stats", (season, week), STATS_MEMO_S, STATS.format(season=season, week=week))
    sched = _memoized("schedule", season, SCHEDULE_MEMO_S, SCHEDULE.format(season=season))
    stats, newest = trim(rows, ids | teams)
    out = {"week": week, "asof": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "updated": newest or None, "games": states(sched, week), "stats": stats}
    if teams:
        out["box"] = box(rows, teams)
    if want_lead:
        out["lead"] = lead(rows)
    return out


def parse(query):
    """(week, ids, teams) from the query, or a reason it is not one. A club's own row (its defense,
    whose points allowed are the other side's score) comes with `teams` at no extra cost."""
    q = parse_qs(query)
    try:
        week = int((q.get("week") or [""])[0])
    except ValueError:
        return None, "week must be a number"
    if not 1 <= week <= 22:
        return None, "week must be 1-22"
    ids = [i for i in (q.get("ids") or [""])[0].split(",") if i]
    teams = [i for i in (q.get("teams") or [""])[0].split(",") if i]
    if len(teams) > TEAMS_MAX or not all(TEAM.match(i) for i in teams):
        return None, "teams must be at most two team codes, comma-separated"
    if (not ids and not teams) or len(ids) > IDS_MAX or not all(ID.match(i) for i in ids):
        return None, "ids must be Sleeper ids or team codes, comma-separated"
    want_lead = (q.get("lead") or [""])[0] == "1"
    return (week, frozenset(ids), frozenset(teams), want_lead), None


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
