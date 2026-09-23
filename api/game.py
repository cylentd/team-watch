"""One NFL game as the drive strip draws it. GET /api/game?event=<espn event id>.

Third server-side file; `api/live.py` set the pattern and this one follows it: a Vercel Python
function, standard library only (requirements.txt must keep listing `anthropic` and nothing else,
or Vercel stops treating these as file-based functions), pure shaping under a thin handler.

Why a server, when this feed needs no cookies. Two reasons, neither of them secrecy:

  * Rate. The page would otherwise ask ESPN once per reader per poll. Behind the same edge cache
    live.py uses, ESPN sees at most one read per window no matter how many people are watching.
  * Reach. ESPN's public site API sits behind Akamai, which refuses some non-browser clients
    outright -- a plain urllib GET from a home IP is answered with 403 "Access Denied" (measured
    2026-09-22). Whether Vercel's egress is treated the same way is NOT yet known, so `fetch()`
    raises Blocked on a 403 and the handler says so plainly rather than reporting a generic
    outage. If it is blocked, the shaping below is unaffected: it is pure, and the feed can be
    delivered another way without touching it.

One endpoint serves live and finished games alike, which is the whole reason the strip can be
opened from Gameday and from a game log with the same code: ESPN's summary carries `drives` for a
game in progress and for one that ended a month ago, in the same shape.

Field position. Never read `start.yardLine`: it is the number printed on the field (BUF 15 -> 15),
so it says nothing about which half. `yardsToEndzone` is unambiguous, and this file turns it into
one absolute scale for the whole game:

    0 = the home team's goal line ... 100 = the away team's goal line

so a home drive runs 0 -> 100 (`dir` +1) and an away drive runs 100 -> 0 (`dir` -1). The strip
draws one fixed field and sends the figures the right way, instead of flipping the field per drive.

Headshots. A play carries NO athlete id -- only `teamParticipants`, which are team ids -- so the
only link from "J.Allen" in the play text to a face is his name. `faces()` builds that map from the
boxscore, and it has to strip generational suffixes to do it: ESPN writes "James Cook III" there
and "J.Cook" in the play text, which silently cost a starting running back every one of his 25
mentions until it was handled.
"""

import datetime
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from http.server import BaseHTTPRequestHandler

HOST = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary"
TIMEOUT = 15
CACHE_S = 30          # a drive turns over in minutes, but the clock inside one moves every play
SWR_S = 30
MIN_INTERVAL = 15     # a warm instance serves its memo rather than re-reading ESPN
MEMO_MAX = 8          # a handful of games at once on a Sunday; beyond that, evict the oldest

# What the strip can act out, and what each record becomes.
KIND = {
    "Rush": "rush", "Rushing Touchdown": "rush", "Sack": "rush",
    "Fumble Recovery (Own)": "rush",          # its own record in the feed, not a flag on the carry
    "Pass Reception": "pass", "Passing Touchdown": "pass",
    "Pass Incompletion": "inc",
    "Interception Return": "int", "Pass Interception Return": "int",
    "Field Goal Good": "fg", "Field Goal Missed": "fg", "Blocked Field Goal": "fg",
}
# Drive bookkeeping: real records, but nothing happens on the field that a figure can act out.
# Left out on purpose, so an unrecognised type is reported rather than silently dropped.
BOOKKEEPING = {
    "Kickoff", "Kickoff Return (Offense)", "Punt", "Penalty", "Timeout", "Official Timeout",
    "Two-minute warning", "Two-minute Warning", "End Period", "End of Half", "End of Game",
    "Extra Point Good", "Extra Point Missed", "Two-Point Conversion Good",
}

SUFFIX = {"Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV", "V"}
# A name in the play text: "J.Allen", and surnames that carry their own dot, "A.St. Brown".
NAME = r"[A-Z]\.[A-Z][A-Za-z'\-]*(?:\.\s?[A-Z][A-Za-z'\-]+)?"
# The verbs that follow a ball carrier, so a name is never taken from a formation note
# ("(Shotgun) J.Cook left tackle ...") or a substitution ("T.Grable reported in as eligible.").
CARRY = (r"up the middle|left end|right end|left tackle|right tackle|left guard|right guard|"
         r"scrambles|kneels|sacked|for (?:no gain|\-?\d+ yard)")


class Blocked(Exception):
    """ESPN's edge refused the request. A retry with the same client cannot fix it."""


def tidy(name):
    """'J.Allen' as the play text writes it -> 'J. Allen' as the page prints it."""
    return re.sub(r"\.\s*", ". ", name).strip() if name else None


def name_key(display):
    """A boxscore displayName reduced to the play text's form: 'James Cook III' -> 'J.Cook'."""
    parts = [w for w in (display or "").split() if w not in SUFFIX]
    return f"{parts[0][0]}.{''.join(parts[1:])}" if len(parts) > 1 else None


def passer(text):
    m = re.search(rf"({NAME})\s+pass\b", text or "")
    return tidy(m.group(1)) if m else None


def target(text):
    """Who the ball was thrown to. None is a real answer: some incompletions name nobody."""
    m = re.search(rf"(?:\bto|\bintended for)\s+({NAME})", text or "")
    return tidy(m.group(1)) if m else None


def carrier(text):
    m = re.search(rf"({NAME})\s+(?:{CARRY})", text or "")
    if m:
        return tidy(m.group(1))
    stripped = re.sub(r"^\s*\([^)]*\)\s*|^[^.]*reported in as eligible\.\s*", "", text or "")
    m = re.search(rf"({NAME})", stripped)
    return tidy(m.group(1)) if m else None


def spot(side, home_ball):
    """One end-to-end scale: 0 is the home goal line, 100 the away one. None when unstated."""
    ytg = (side or {}).get("yardsToEndzone")
    if ytg is None:
        return None
    return 100 - ytg if home_ball else ytg


def play_row(p, home_ball):
    """One play as the strip draws it, or None when it is drive bookkeeping or unusable."""
    kind = KIND.get(((p.get("type") or {}).get("text") or "").strip())
    if kind is None:
        return None
    start, end = p.get("start") or {}, p.get("end") or {}
    a, b = spot(start, home_ball), spot(end, home_ball)
    if a is None or b is None:
        return None
    text, dirn = p.get("text") or "", 1 if home_ball else -1
    row = {"k": kind, "from": a, "to": b, "tx": text,
           "dd": start.get("shortDownDistanceText") or start.get("downDistanceText") or "",
           "clock": clock_of(p)}
    distance = start.get("distance")
    if distance is not None and start.get("down"):
        row["line"] = a + dirn * distance           # the line to gain, on the same scale
    if kind in ("pass", "inc", "int"):
        row["who"], row["qb"] = target(text), passer(text)
    else:
        row["who"] = carrier(text)
    if kind == "pass" and p.get("yardsAfterCatch") is not None:
        row["yac"] = p["yardsAfterCatch"]
    if kind == "fg":
        row["to"] = 100 if home_ball else 0        # the kick ends at the posts, not at the spot
        row["made"] = "Good" in ((p.get("type") or {}).get("text") or "")
    if p.get("scoringPlay") and "Touchdown" in ((p.get("type") or {}).get("text") or ""):
        row["td"] = True
    if p.get("isTurnover"):
        row["turnover"] = True
    return row


def clock_of(p):
    q = ((p.get("period") or {}).get("number"))
    t = ((p.get("clock") or {}).get("displayValue"))
    return f"Q{q} {t}" if q and t else (t or "")


def athletes(summary):
    """Two tables off the boxscore, both keyed the way the PLAY TEXT writes a name:

        faces   'J. Allen' -> headshot url
        names   'Josh Allen' -> 'J. Allen'

    `names` exists so the page never has to reduce a name itself. team-watch knows its players as
    'Josh Allen'; every play in this payload calls him 'J. Allen'; and the reduction is not
    obvious (a generational suffix has to go, or 'James Cook III' never matches 'J.Cook'). A
    lookup table shipped with the data beats the same rule written twice in two languages.
    """
    faces, names = {}, {}
    for team in (summary.get("boxscore") or {}).get("players") or []:
        for cat in team.get("statistics") or []:
            for row in cat.get("athletes") or []:
                a = row.get("athlete") or {}
                display, key = a.get("displayName"), name_key(a.get("displayName"))
                if not key:
                    continue
                key = tidy(key)
                names.setdefault(display, key)
                href = (a.get("headshot") or {}).get("href")
                if href:
                    faces.setdefault(key, href)
    return faces, names


def sides(summary):
    """The two teams, home first, with the score the header carries."""
    comp = ((summary.get("header") or {}).get("competitions") or [{}])[0]
    out = {}
    for c in comp.get("competitors") or []:
        team = c.get("team") or {}
        out[c.get("homeAway")] = {
            "id": team.get("id"), "abbr": team.get("abbreviation"),
            "name": team.get("shortDisplayName") or team.get("name"),
            "score": int(c["score"]) if str(c.get("score", "")).isdigit() else None,
        }
    return comp, out.get("home", {}), out.get("away", {})


def shape(summary):
    """The whole summary reduced to what the strip draws.

    Raises LookupError when the payload carries no drives at all, which is what a game that has
    not kicked off looks like -- worth saying, rather than drawing an empty field.
    """
    comp, home, away = sides(summary)
    previous = ((summary.get("drives") or {}).get("previous")) or []
    current = (summary.get("drives") or {}).get("current")
    raw = previous + ([current] if current else [])
    if not raw:
        raise LookupError("no drives in the summary yet")

    unknown, drives = {}, []
    for d in raw:
        team_id = ((d.get("team") or {}).get("id"))
        home_ball = team_id == home.get("id")
        plays = []
        for p in d.get("plays") or []:
            label = ((p.get("type") or {}).get("text") or "").strip()
            row = play_row(p, home_ball)
            if row:
                plays.append(row)
            elif label and label not in BOOKKEEPING:
                unknown[label] = unknown.get(label, 0) + 1
        if not plays:
            continue
        scored = [q for q in d.get("plays") or [] if "homeScore" in q]
        before = [scored[0]["homeScore"], scored[0]["awayScore"]] if scored else [0, 0]
        after = [scored[-1]["homeScore"], scored[-1]["awayScore"]] if scored else before
        drives.append({
            "team": (d.get("team") or {}).get("abbreviation"),
            "dir": 1 if home_ball else -1,
            "result": d.get("displayResult") or d.get("result") or "",
            "label": d.get("description") or "",
            "clock": plays[0]["clock"],
            "score": before,
            "end": {"dd": d.get("displayResult") or d.get("result") or "",
                    "tx": d.get("description") or "", "score": after},
            "plays": plays,
        })
    if not drives:
        raise LookupError("drives carried no play the strip can draw")

    status = (comp.get("status") or {}).get("type") or {}
    faces, names = athletes(summary)
    return {
        "event": str((summary.get("header") or {}).get("id") or ""),
        "state": status.get("state"),                      # pre | in | post
        "detail": status.get("detail"),
        "asof": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "home": home, "away": away,
        "current": len(drives) - 1,                        # the drive being played, or the last one
        "drives": drives,
        "faces": faces,
        "names": names,
        # Named, not silently dropped: a type nobody has seen before should show up in the log.
        "unknownPlayTypes": unknown or None,
    }


def fetch(event):
    """One GET against ESPN's public summary. Returns the parsed body."""
    url = f"{HOST}?{urllib.parse.urlencode({'event': event})}"
    req = urllib.request.Request(url, headers={
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.espn.com/",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"),
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise Blocked("ESPN's edge refused this client") from exc
        raise


_memo = {}


def game(event):
    """The shaped game, memoized per event for MIN_INTERVAL seconds on a warm instance."""
    now = time.time()
    hit = _memo.get(event)
    if hit and now - hit[0] < MIN_INTERVAL:
        return dict(hit[1], cached=True)
    out = shape(fetch(event))
    if len(_memo) >= MEMO_MAX:
        del _memo[min(_memo, key=lambda k: _memo[k][0])]
    _memo[event] = (now, out)
    return dict(out, cached=False)


class handler(BaseHTTPRequestHandler):

    def _send(self, code, payload, cache=False):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control",
                         f"public, max-age=0, s-maxage={CACHE_S}, stale-while-revalidate={SWR_S}"
                         if cache else "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        event = (query.get("event") or [""])[0].strip()
        if not event.isdigit():
            return self._send(400, {"error": "Pass ?event= with an ESPN event id."})
        try:
            self._send(200, game(event), cache=True)
        except Blocked:
            print(f"game: blocked by ESPN's edge for event {event}")
            self._send(502, {"error": "ESPN would not serve this game to the server.",
                             "blocked": True})
        except LookupError as exc:
            self._send(404, {"error": str(exc)})
        except Exception as exc:                                       # noqa: BLE001
            print(f"game: {type(exc).__name__}: {exc}")
            self._send(502, {"error": "Could not reach ESPN. Try again."})

    def log_message(self, fmt, *args):
        """Vercel already logs the request line; this would double every entry."""
