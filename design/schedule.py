"""LIVE_SCHEDULE: this week's NFL kickoffs, so the Live surface knows when to poll and when not to.

The Live board reads /api/live, which costs an ESPN request whenever the edge cache has expired.
Without a schedule the page would poll at full rate at 9am on a Sunday with nothing kicked off,
and again at midnight with everything final. With one it polls only while a game involving
somebody in the matchup is actually being played, and the rest of the week costs nothing.

Source: ff-jarvis's `data/history/games/<date>.jsonl`, written by `model.clients.results` from
nflverse. That is the schedule itself, not a by-product of one: the obvious alternative is the
BettingPros prop rows the page already loads, which carry `commence` per row and covered all 16
games this week -- but they cover the games a book chose to price. A game without priced markets
would vanish from the gate silently, and the symptom would be a board that quietly stopped
updating during a game. A schedule is the wrong place to accept that risk, so this pays for a
second reader instead.

The files are an append-only log: every pull re-states the whole season, so one game_id appears
in several files and several times within one. The latest `asof` per game_id wins.

Team codes come out in ESPN's spelling (LAR, WSH), not nflverse's (LA, WAS), because the only
consumer joins them against the club codes /api/live returns, which are ESPN's own. A block that
exists for one reader should speak that reader's dialect rather than make it translate.

The whole season ships, not a window around the build. A window would have to be measured from
"now", which makes the build's own output depend on the day it ran -- and this repo pins its
fixtures precisely so that a build is reproducible. The client has a clock and has to consult it
anyway. 272 games cost about 19 KB in a 2 MB page.
"""

import datetime
import json
import pathlib

UTC = datetime.timezone.utc

# nflverse -> ESPN, and only where they disagree. Not `build.TEAM_FIX` (which targets the book's
# spelling) and not ff-jarvis's `team_norm` (which targets nflverse's): a third seam, because the
# join at the other end is against ESPN's table in api/live.py.
TO_ESPN = {"LA": "LAR", "WAS": "WSH"}


def _rows(games_dir):
    """Every row in the log, oldest file first. A malformed line is skipped, not fatal: this
    block is optional, and half a schedule still gates better than none."""
    for path in sorted(pathlib.Path(games_dir).glob("*.jsonl")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def _latest_per_game(rows):
    """One row per game_id: the most recently stated version of it."""
    best = {}
    for r in rows:
        key = r.get("game_id")
        if not key or not r.get("kickoff"):
            continue
        prior = best.get(key)
        if prior is None or str(r.get("asof") or "") >= str(prior.get("asof") or ""):
            best[key] = r
    return best.values()


def load_schedule(dwr):
    """-> {"games": [{home, away, kickoff, week, espn}], "alias": {...}} , or None when the log
    is not there.

    `kickoff` is normalized to ISO-8601 UTC with a trailing Z, which Date.parse reads directly
    in the browser. No build clock is consulted, so the same log always yields the same block.

    `week` and `espn` are for the second reader, added 2026-09-23: the drive strip opens a game
    by ESPN event id, and the only two ways the page ever names a game are "the one this club is
    playing now" (Gameday) and "week 3, this club" (a game log). Both end here.

    `espn` is null for any game whose latest history row predates ff-jarvis carrying the column
    (it is in nflverse's games.csv and was being dropped). A null is a game the strip cannot open,
    which is why it is a null rather than an omission -- the gate above still works without it,
    and one `python -m model.clients.results` fills every game in the season.
    """
    games_dir = pathlib.Path(dwr) / "history" / "games"
    if not games_dir.is_dir():
        return None

    out = []
    for r in _latest_per_game(_rows(games_dir)):
        try:
            when = datetime.datetime.fromisoformat(str(r["kickoff"]).replace("Z", "+00:00"))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)
        home, away = r.get("home"), r.get("away")
        if not home or not away:
            continue
        week = r.get("week")
        out.append({"id": r.get("game_id"),
                    "home": TO_ESPN.get(home, home), "away": TO_ESPN.get(away, away),
                    "kickoff": when.astimezone(UTC).isoformat(timespec="seconds").replace(
                        "+00:00", "Z"),
                    "week": int(week) if isinstance(week, (int, float)) else None,
                    "espn": str(r["espn"]) if r.get("espn") else None})

    if not out:
        return None
    out.sort(key=lambda g: (g["kickoff"], g["away"]))
    # The same table, shipped, because a second reader arrived that does NOT speak ESPN's dialect:
    # the profile's game log carries nflverse's codes (LA, WAS) straight off ff-jarvis's box score,
    # so looking a club up in `games` above silently found nothing for the Rams and the Commanders.
    # Writing {"LA": "LAR"} again in JavaScript would be the same table in two places; sending it
    # keeps it in one. ESPN's own codes are not keys here, so they pass through untouched.
    return {"games": out, "alias": dict(TO_ESPN)}


def report(block):
    if not block:
        return "Schedule: no live file, so Live polls on its idle cadence only"
    games = block["games"]
    return f"Schedule: {len(games)} games, {games[0]['kickoff']} to {games[-1]['kickoff']}"
