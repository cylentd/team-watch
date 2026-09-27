"""LIVE_WX_HITS: who a game's weather hits, for This week > Weather's "Who it hits" (2026-09-26).

Per team, the players at the positions the projections adjust for weather (QB, WR, TE) that a
fantasy lineup would start: the top-projected QB, the top two WRs and the top TE, picked by the
projection's own points. A player Sleeper lists as not playing is skipped, the same out-list the
roster cards and Ranks use. Each row carries `wx` ({adj, cond}, the points ff-jarvis already moved
for the weather) or null, and `src`: "line" is a book-priced row, whose projection comes from the
sportsbook lines that already price the forecast, so ff-jarvis leaves it unadjusted.

The view is league-wide and the page is public, so this reads the projections, never a roster.
"""
from projections import unavailable

TAKE = {"QB": 1, "WR": 2, "TE": 1}


def live_wx_hits(raw, slugify, status=None):
    """-> {"teams": {team: [{slug, n, pos, team, wx, src}]}} in QB, WR, TE order, or None."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    gone = unavailable(status, slugify)
    best = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if not slug or slug in gone or p.get("pos") not in TAKE or p.get("pts") is None or not p.get("team"):
            continue
        if slug not in best or p["pts"] > best[slug]["pts"]:
            best[slug] = {"slug": slug, "n": p.get("name"), "pos": p["pos"], "team": p["team"],
                          "wx": p.get("wx"), "src": p.get("src"), "pts": p["pts"]}
    teams = {}
    for r in sorted(best.values(), key=lambda r: (-r["pts"], r["slug"])):
        rows = teams.setdefault(r["team"], [])
        if sum(x["pos"] == r["pos"] for x in rows) < TAKE[r["pos"]]:
            rows.append(r)
    order = list(TAKE)
    return {"teams": {t: [{k: v for k, v in r.items() if k != "pts"}
                          for r in sorted(rs, key=lambda r: order.index(r["pos"]))]
                      for t, rs in sorted(teams.items())}}
