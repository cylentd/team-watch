"""Serve the built page with a fake /api/live, so the Live view can be worked on without a game.

    python design/build.py              # the page it serves
    python scripts/mock_live.py         # http://127.0.0.1:8777/#live
    python scripts/mock_live.py --speed 30 --port 8777

"Me" is the real ESPN roster the build inlined (LIVE_ESPN); the opponent is a fixed made-up
lineup. The clock starts when the server does: one game minute every `60 / speed` seconds, so the
default speed 6 plays a 60-minute game in 10 real minutes. Early games kick off at once, late
games at game minute 30, and a third of each side never plays inside the window, so the board
always shows played, playing and not-yet rows together. Points are a function of the clock and
the player's name only, so a reload shows the same numbers and a refresh shows them grown.

The page only polls every 90 s while a real kickoff is live (js/surface/live/live.js), so tap the
board's refresh control to pull the next reply sooner. No ESPN request is ever made.
"""
import argparse
import datetime
import functools
import hashlib
import http.server
import json
import math
import pathlib
import re
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent

# ESPN's slot labels (api/_espn.py SLOT) for a lineup: QB, 2 RB, 2 WR, TE, 2 FLEX, D/ST.
STARTERS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "D/ST"]

OPPONENT = [  # (slot, name, team, projected)
    ("QB", "Justin Herbert", "LAC", 19.8), ("RB", "Chase Brown", "CIN", 14.1),
    ("RB", "Kyren Williams", "LAR", 15.3), ("WR", "Jaxon Smith-Njigba", "SEA", 15.9),
    ("WR", "Garrett Wilson", "NYJ", 13.2), ("TE", "Trey McBride", "ARI", 12.0),
    ("FLEX", "Courtland Sutton", "DEN", 11.4), ("FLEX", "Breece Hall", "NYJ", 12.6),
    ("D/ST", "Lions D/ST", "DET", 6.5),
    ("BE", "Drake Maye", "NE", 18.2), ("BE", "Javonte Williams", "DAL", 9.9),
    ("BE", "Jerry Jeudy", "CLE", 8.4), ("BE", "Dallas Goedert", "PHI", 7.7),
    ("BE", "Rhamondre Stevenson", "NE", 8.8), ("BE", "Jayden Reed", "GB", 9.1),
    ("IR", "Nico Collins", "HOU", 0.0),
]


def seed(name):
    return int(hashlib.sha1(name.encode()).hexdigest()[:8], 16)


def my_lineup():
    """The inlined ESPN roster as (slot, name, team, projected). Starters keep their ESPN slot
    when it is a starting one; the rest fill STARTERS in roster order, then the bench."""
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"^const LIVE_ESPN = (.*);$", html, re.M)
    if not m:
        raise SystemExit("index.html has no LIVE_ESPN block; run python design/build.py first")
    roster = json.loads(m.group(1).replace("<\\/", "</"))["roster"]
    proj = {"QB": 19.0, "RB": 12.5, "WR": 12.0, "TE": 9.0, "DST": 7.0}
    rows, open_slots = [], list(STARTERS)
    for p in roster:
        want = "D/ST" if p["pos"] == "DST" else p["pos"]
        fits = [s for s in open_slots if s == want or (s == "FLEX" and want in ("RB", "WR", "TE"))]
        slot = fits[0] if fits and p.get("slot") not in ("BE", "IR") else ("IR" if p.get("slot") == "IR" else "BE")
        if slot in open_slots:
            open_slots.remove(slot)
        base = proj.get(p["pos"], 8.0)
        name = p["n"] + " D/ST" if p["pos"] == "DST" and not p["n"].endswith("D/ST") else p["n"]
        rows.append((slot, name, p["team"], 0.0 if slot == "IR" else round(base * (0.7 + (seed(name) % 60) / 100), 1)))
    return rows


def kick_minute(name):
    """0 = early game, 30 = late game, None = does not play inside the window."""
    return (0, 30, None)[seed(name) % 3]


def actual(name, projected, minute):
    """Points so far: the projection spread over 60 minutes with this player's own lumps -- a
    touchdown lands as a step, not a slope, so the delta chips have something to show."""
    start = kick_minute(name)
    if start is None or minute < start:
        return None
    played = min(60.0, minute - start)
    s = seed(name)
    pace = projected * (0.5 + (s % 100) / 100)          # 0.5x to 1.5x of the projection
    steady = pace * 0.6 * played / 60
    tds = sum(1 for k in range(3) if played >= 12 + ((s >> (k * 5)) % 40) and (s >> k) % 2)
    return round(steady + tds * 6.0 * (0.4 if projected < 8 else 1.0), 1)


def side(team, rows, minute):
    lineup = []
    for slot, name, club, projected in rows:
        a = None if slot == "IR" else actual(name, projected, minute)
        lineup.append({"slot": slot, "starter": slot not in ("BE", "IR"), "name": name, "team": club,
                       "actual": a, "projected": projected, "started": a is not None,
                       "injury": "OUT" if slot == "IR" else ("QUESTIONABLE" if seed(name) % 11 == 0 else "ACTIVE")})
    starters = [r for r in lineup if r["starter"]]
    live = round(sum(r["actual"] or 0 for r in starters), 1)
    # Projected-live the way ESPN reports it: points banked plus what is still to come.
    left = sum(r["projected"] * (1 - min(1.0, max(0.0, (minute - (kick_minute(r["name"]) or 0)) / 60)))
               for r in starters if kick_minute(r["name"]) is not None)
    left += sum(r["projected"] for r in starters if kick_minute(r["name"]) is None)
    lineup.sort(key=lambda r: (not r["starter"], r["slot"], r["name"] or ""))
    return {"team": team, "live": live, "projected": round(live + left, 1), "lineup": lineup}


class Handler(http.server.SimpleHTTPRequestHandler):
    t0 = time.time()
    speed = 6.0
    mine = []

    def do_GET(self):
        if self.path.split("?")[0] != "/api/live":
            return super().do_GET()
        minute = (time.time() - self.t0) * self.speed / 60
        me = side("Purdy Big in Japan", self.mine, minute)
        opp = side("TeamMinh", OPPONENT, minute)
        edge = (me["projected"] - opp["projected"]) / 18
        me["winPct"] = round(1 / (1 + math.exp(-edge)), 3)
        opp["winPct"] = round(1 - me["winPct"], 3)
        body = json.dumps({"league": "espn", "week": 3, "mock": True,
                           "asof": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                           "me": me, "opponent": opp}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        print(f"  /api/live  game minute {minute:5.1f}  me {me['live']:6.1f}  opp {opp['live']:6.1f}")

    def log_message(self, fmt, *args):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8777)
    ap.add_argument("--speed", type=float, default=6.0, help="game minutes per real minute")
    ap.add_argument("--minute", type=float, default=0.0, help="start this many game minutes in")
    a = ap.parse_args()
    Handler.speed, Handler.mine = a.speed, my_lineup()
    Handler.t0 = time.time() - a.minute * 60 / a.speed
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", a.port), functools.partial(Handler, directory=str(ROOT)))
    print(f"mock live: http://127.0.0.1:{a.port}/#live  (speed {a.speed}x, Ctrl+C to stop)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
