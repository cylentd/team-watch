"""LIVE_SIGNED: who has earned an autograph (2026-09-25, David's pick). A card is signed when the
player finished top 3 at his position in the last completed week. The tier (colour) stays this
week's projected rank; the autograph is the other axis, something he did rather than something
a model expects. It was the #1-5 projected, which put five on two rosters, Schultz and Purdy
among them.

"Completed" is the latest week in which every team on the schedule has a game-log row: the game
log calls itself `through` week 3 after Thursday's game alone. Ranked over every player ff-jarvis
logged that week, before the cut to the page's players, or a roster would only be ranked against
itself. Self-contained like gamelog.py: every input comes in as an argument."""
TOP = 3
SKILL = ("QB", "RB", "WR", "TE")


def completed_week(rows, games):
    """The latest week whose game-log teams cover every team scheduled that week, or None."""
    scheduled, logged = {}, {}
    for g in games or []:
        if g.get("week"):
            scheduled.setdefault(g["week"], set()).update((g["home"], g["away"]))
    for r in rows:
        logged.setdefault(r.get("week"), set()).add(r.get("team"))
    done = [w for w, teams in scheduled.items() if len(logged.get(w, ())) >= len(teams)]
    return max(done) if done else None


def live_signed(gamelog, schedule, slugify, wanted):
    """{wk, players: {slug -> {rank, pts}}} for every page player who finished top 3 at his
    position in the last completed week, or None without a game log or a completed week."""
    rows = (gamelog or {}).get("rows") or []
    wk = completed_week(rows, (schedule or {}).get("games"))
    if not rows or wk is None:
        return None
    out = {}
    for pos in SKILL:
        week = sorted((r for r in rows if r.get("week") == wk and r.get("pos") == pos and r.get("pts") is not None),
                      key=lambda r: -r["pts"])
        for rank, r in enumerate(week[:TOP], 1):
            slug = slugify(r.get("name") or "")
            if slug in wanted:
                out[slug] = {"rank": rank, "pts": r["pts"]}
    return {"wk": wk, "players": out}


def report(block):
    if not block:
        return "Signed: no completed week in the game log, so no autographs"
    return f"Signed: {len(block['players'])} page players finished top {TOP} in week {block['wk']}"
