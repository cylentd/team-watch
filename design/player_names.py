"""LIVE_NAMES: each player's jersey number and nicknames (2026-10-05), from ff-jarvis's player_names.json.

The page's live clip matcher reads it: a clip title or a play's text names a player by number or by
nickname more often than by his full name. The block is {slug: {"n": number|null, "t": club, "k": [nicks]}}
and nothing else: the ff-jarvis file's `name` and `pos` stay there, the page already has them.
`t` arrives nflverse (LA, WAS) and leaves in the schedule's spelling (LAR, WSH), the one `schedCode`
and LIVE_SCHEDULE.alias speak. A missing number is null, a missing nick list is []. Slugs are already
team-watch's (ff-jarvis mirrors slugify). Self-contained like clips.py: the loaded file comes in as an
argument, and None comes out when ff-jarvis has written none (a real build before its file lands).
"""
from schedule import TO_ESPN

FIELDS = ("n", "t", "k")


def _cut(row):
    num = row.get("num")
    return {"n": num if isinstance(num, int) and not isinstance(num, bool) else None,
            "t": TO_ESPN.get(row.get("team"), row.get("team")),
            "k": [str(k) for k in row.get("nick") or [] if k]}


def live_names(raw):
    """None when ff-jarvis has written no file or no player in it. A row that is not a dict drops."""
    players = raw.get("players") if isinstance(raw, dict) else None
    if not isinstance(players, dict):
        return None
    out = {slug: _cut(row) for slug, row in players.items() if isinstance(row, dict)}
    return out or None


def problems(obj):
    """Missing fields of a LIVE_NAMES as `LIVE_NAMES['a-b'].t`, for contract.py (the block is a map of
    rows, beyond its one-level row specs)."""
    return [f"LIVE_NAMES[{slug!r}].{k}" for slug, row in (obj or {}).items() for k in FIELDS if k not in row]


def report(block):
    if not block:
        return "Names: no player_names.json, so the page matches clips by name alone"
    return f"Names: {len(block)} players, {sum(1 for r in block.values() if r['n'] is not None)} with a jersey number"
