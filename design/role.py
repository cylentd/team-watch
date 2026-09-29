"""LIVE_ROLE: Players > Role (leaf `movers`, 2026-09-29), from ff-jarvis's role_board.json.

What each RB, WR and TE's work this season is worth -- his targets, carries and passes at the
position's league half-PPR points per opportunity, the recap's own number -- beside what he scored,
with the work itself and last season's same gap. Descriptive only: METHODOLOGY 12.41 and 12.44
found the gap does not beat the projection, so nothing here says buy or sell.

The page computes nothing; this cut keeps the positions and the sample the view shows.
Self-contained like the other cuts: the loaded file and slugify come in as arguments.
"""

POS = ("RB", "WR", "TE")
MIN_GAMES = 2          # one game is a box score, not a role
MIN_XFP = 5.0          # below this a role is a depth player's, and the list runs past 150 rows


def _prev(p):
    """Last season's gap, or None: ff-jarvis leaves it null under 4 games."""
    v = p.get("prev")
    if not v or v.get("gap_g") is None:
        return None
    return {"season": v.get("season"), "g": v.get("g"), "gap": v["gap_g"]}


def _row(p, slugify):
    w = p.get("work") or {}
    return {"slug": slugify(p["name"]), "n": p["name"], "pos": p["pos"], "team": p.get("team"),
            "g": p["g"], "xfp": p["xfp_g"], "pts": p["pts_g"], "gap": p["gap_g"], "td": p.get("td") or 0,
            "work": {k: w.get(k) for k in ("tgt_g", "car_g", "air_g", "rz_g", "gl_g")},
            "prev": _prev(p)}


def live_role(raw, slugify):
    """None when ff-jarvis has written no role board: the view then says so."""
    players = (raw or {}).get("players") or []
    rows = [_row(p, slugify) for p in players
            if p.get("pos") in POS and (p.get("g") or 0) >= MIN_GAMES and (p.get("xfp_g") or 0) >= MIN_XFP]
    if not rows:
        return None
    rows.sort(key=lambda r: (-r["xfp"], r["n"]))
    return {"season": raw.get("season"), "through": raw.get("through"), "min_games": MIN_GAMES, "rows": rows}


def report(block):
    if not block:
        return "Role: no role_board.json, so the view says so"
    with_prev = sum(1 for r in block["rows"] if r["prev"])
    return f"Role: {len(block['rows'])} players through week {block['through']}, {with_prev} with last season"
