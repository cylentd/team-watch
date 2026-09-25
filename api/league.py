"""Leagues a visitor connects themselves. GET/POST/DELETE /api/league.

The page ships David's two leagues baked in. This function adds any ESPN league a visitor
connects: by link for a public league, plus the two ESPN cookies (espn_s2, SWID) for a private
one. It is the third server-side file here and follows api/chat.py's rules: stdlib only, a
`handler` class, no framework.

Where the connection lives: one HttpOnly cookie, `tw_leagues`, in the visitor's own browser,
scoped to this path and kept 400 days. Nothing is stored on the server, so there is nothing
here to leak. A server-set cookie also survives Safari, which erases localStorage after 7 days
without a visit. It is plain base64 JSON, not encrypted: it holds the visitor's own ESPN cookies,
in their own browser, where espn.com already keeps the same two values readable by script.

    GET     every connected league, shaped like the page's LIVE_ESPN block
    POST    {league, swid?, s2?, team_id?}: connect one; replies {pick: [...]} when it cannot
            tell which team is the visitor's (a public league read without SWID)
    DELETE  ?key=espn-<league id>: forget one
"""

import base64
import json
import os
import re
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _espn import BENCH, POS, PRO, SLOT, Expired, fetch, slugify  # noqa: E402

COOKIE = "tw_leagues"
MAX_AGE = 400 * 24 * 3600      # Chrome's ceiling for any cookie
MAX_LEAGUES = 5                # keeps the cookie well under the 4 KB browsers allow
MAX_BODY = 4000
MEMO_S = 60                    # a warm instance re-serves a league for a minute
# mRoster names every player; mTeam names teams and their owners; mSettings names the league.
VIEWS = ["mTeam", "mRoster", "mSettings"]
BADGE = {"QUESTIONABLE": "Q", "DOUBTFUL": "Q", "OUT": "OUT", "INJURY_RESERVE": "OUT", "SUSPENSION": "OUT"}

_memo = {}


def parse_league(text):
    """A league link (…?leagueId=1534545…) or a bare id -> int. ValueError otherwise."""
    text = (text or "").strip()
    m = re.search(r"[?&#]leagueId=(\d+)", text) or re.fullmatch(r"(\d{3,12})", text)
    if not m:
        raise ValueError("That is not an ESPN league link or league ID.")
    return int(m.group(1))


def read_cookie(header):
    """The connected leagues from a Cookie header; a damaged cookie reads as none."""
    for part in (header or "").split(";"):
        k, _, v = part.strip().partition("=")
        if k == COOKIE and v:
            try:
                got = json.loads(base64.urlsafe_b64decode(v + "=" * (-len(v) % 4)))
                return [e for e in got if isinstance(e, dict) and e.get("lid")][:MAX_LEAGUES]
            except (ValueError, TypeError):
                return []
    return []


def write_cookie(entries):
    value = base64.urlsafe_b64encode(json.dumps(entries, separators=(",", ":")).encode()).decode().rstrip("=")
    age = MAX_AGE if entries else 0
    return f"{COOKIE}={value}; Max-Age={age}; Path=/api/league; HttpOnly; Secure; SameSite=Lax"


def team_list(body):
    out = []
    for t in body.get("teams") or []:
        rec = ((t.get("record") or {}).get("overall")) or {}
        out.append({"id": t.get("id"), "name": t.get("name") or f"Team {t.get('id')}",
                    "record": f"{rec.get('wins', 0)}-{rec.get('losses', 0)}"})
    return out


def owner_team(body, swid):
    """The team whose primary owner is this SWID, or None."""
    want = ("{" + (swid or "").strip("{}") + "}").upper()
    return next((t.get("id") for t in body.get("teams") or []
                 if str(t.get("primaryOwner", "")).upper() == want), None)


def roster_rows(body, team_id):
    """One team's roster in the LIVE_ESPN row shape (design/contract.py)."""
    team = next((t for t in body.get("teams") or [] if t.get("id") == team_id), None)
    if team is None:
        raise LookupError(f"no team {team_id} in this league")
    rows, flex = [], 0
    for e in ((team.get("roster") or {}).get("entries")) or []:
        p = ((e.get("playerPoolEntry") or {}).get("player")) or {}
        slot_id = e.get("lineupSlotId")
        slot = SLOT.get(slot_id, str(slot_id))
        if slot == "FLEX":
            flex += 1
            slot = f"FLX{flex}"
        elif slot_id in BENCH:
            slot = "BN" if slot == "BE" else "OUT"
        name = (p.get("fullName") or "").replace(" D/ST", "")
        rows.append({"n": name, "pos": POS.get(p.get("defaultPositionId"), "?"),
                     "team": PRO.get(p.get("proTeamId"), ""), "slot": slot,
                     "slug": slugify(name) if name else None,
                     "status": BADGE.get(p.get("injuryStatus") or "")})
    return rows


def league_card(body, entry):
    teams = {t["id"]: t for t in team_list(body)}
    me = teams.get(entry["tid"]) or {}
    return {"key": f"espn-{entry['lid']}", "site": "espn", "league_id": entry["lid"],
            "team_id": entry["tid"], "league": (body.get("settings") or {}).get("name") or "ESPN league",
            "name": me.get("name", "My team"), "record": me.get("record", "0-0"),
            "roster": roster_rows(body, entry["tid"])}


def read_league(entry):
    key = (entry["lid"], bool(entry.get("s2")))
    hit = _memo.get(key)
    if hit and time.time() - hit[0] < MEMO_S:
        return hit[1]
    body = fetch(entry["lid"], VIEWS, entry.get("swid"), entry.get("s2"), agent="team-watch-league/1.0")
    _memo[key] = (time.time(), body)
    return body


class handler(BaseHTTPRequestHandler):

    def _send(self, code, payload, cookie=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "private, no-store")   # every reply is one visitor's
        if cookie is not None:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        out = []
        for entry in read_cookie(self.headers.get("Cookie")):
            try:
                out.append(league_card(read_league(entry), entry))
            except Expired:
                out.append({"key": f"espn-{entry['lid']}", "error": "expired"})
            except Exception:  # one broken league must not blank the others
                out.append({"key": f"espn-{entry['lid']}", "error": "unavailable"})
        self._send(200, {"leagues": out})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            req = json.loads(self.rfile.read(min(n, MAX_BODY)) or b"{}")
            lid = parse_league(str(req.get("league", "")))
        except ValueError as exc:
            return self._send(400, {"error": str(exc) or "Bad request."})
        swid, s2 = (req.get("swid") or "").strip() or None, (req.get("s2") or "").strip() or None
        try:
            body = read_league({"lid": lid, "swid": swid, "s2": s2})
        except Expired:
            return self._send(409, {"error": "private", "private": not s2})
        except Exception:
            return self._send(502, {"error": "ESPN did not answer. Try again in a minute."})
        tid = req.get("team_id") or (owner_team(body, swid) if swid else None)
        if tid is None:
            return self._send(200, {"pick": team_list(body),
                                    "league": (body.get("settings") or {}).get("name")})
        entry = {"lid": lid, "tid": int(tid), "swid": swid, "s2": s2}
        kept = [e for e in read_cookie(self.headers.get("Cookie")) if e["lid"] != lid]
        try:
            card = league_card(body, entry)
        except LookupError as exc:
            return self._send(400, {"error": str(exc)})
        self._send(200, {"league": card}, cookie=write_cookie((kept + [entry])[-MAX_LEAGUES:]))

    def do_DELETE(self):
        key = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get("key", [""])[0]
        kept = [e for e in read_cookie(self.headers.get("Cookie")) if f"espn-{e['lid']}" != key]
        self._send(200, {"ok": True}, cookie=write_cookie(kept))

    def log_message(self, fmt, *args):
        pass   # Vercel logs the request line; nothing here may log a cookie
