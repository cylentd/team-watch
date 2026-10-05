"""LIVE_CLIPS: official YouTube clips per player and per game (2026-10-05), from ff-jarvis's clips.json.

`players` is {slug: [{id, title, kind, secs, embed, shape}]}, best_plays first then plays by posting time, the
order ff-jarvis wrote. `shape` is "tall" (a vertical Short) or "wide" (2026-10-05, Clips v2: the player
takes the clip's shape). `games` is {team: {id, title, secs, embed, shape}} (`alias` {nflverse code: schedule code}): the NFL "Game Highlights" video, once
per club, both clubs of a game pointing at the same video. The page only opens a video by its id.
`embed` is whether YouTube lets the video play on another site (the NFL channel, MIN, SEA and SF
refuse, error 150); a file from before ff-jarvis wrote it reads as true, and the page's runtime
fallback (error 150 -> a link) still catches a channel not yet known.

The decision cache (`matched`), the clock and the LLM status stay in ff-jarvis; the page never reads them.
Self-contained like the other cuts: the loaded file comes in as an argument. Slugs are already
team-watch's (ff-jarvis mirrors slugify). Team codes arrive nflverse (LA, WAS) and leave in the
schedule's spelling (LAR, WSH), the one `schedCode` and LIVE_SCHEDULE.alias speak. `alias` carries
that pair map too, so a page built with no schedule still finds a club's game video under LA or WAS.
"""
from schedule import TO_ESPN

CLIP_FIELDS = ("id", "title", "kind", "secs", "embed", "shape", "posted")
GAME_FIELDS = ("id", "title", "secs", "embed", "shape")


def _pick(row, fields):
    out = {k: row.get(k) for k in fields}
    out["embed"] = row.get("embed") is not False     # missing (an older file) plays
    out["shape"] = "tall" if row.get("shape") == "tall" else "wide"   # missing (an older file) is wide
    return out


def live_clips(raw):
    """None when ff-jarvis has written no file. A player with no clip, and a clip with no id, drop."""
    if not isinstance(raw, dict) or not (raw.get("players") or raw.get("games")):
        return None
    players = {}
    for slug, rows in (raw.get("players") or {}).items():
        clips = [_pick(c, CLIP_FIELDS) for c in rows or [] if c.get("id")]
        if clips:
            players[slug] = clips
    games = {TO_ESPN.get(team, team): _pick(g, GAME_FIELDS)
             for team, g in (raw.get("games") or {}).items() if g.get("id")}
    return {"week": raw.get("week"), "players": players, "games": games, "alias": dict(TO_ESPN)}


def problems(obj):
    """Missing fields of a LIVE_CLIPS as `LIVE_CLIPS.players['a-b'][0].id`, for contract.py (a map of
    lists is beyond its one-level row specs)."""
    miss = [f"LIVE_CLIPS.players[{s!r}][{i}].{k}" for s, rows in (obj.get("players") or {}).items()
            for i, c in enumerate(rows) for k in CLIP_FIELDS if k not in c]
    miss += [f"LIVE_CLIPS.games[{t!r}].{k}" for t, g in (obj.get("games") or {}).items()
             for k in GAME_FIELDS if k not in g]
    return miss


def report(block):
    if not block:
        return "Clips: no clips.json, so the page draws no clips"
    n = sum(len(v) for v in block["players"].values())
    return f"Clips: week {block['week']}, {n} clips over {len(block['players'])} players, {len(block['games'])} club game videos"
