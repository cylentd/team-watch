"""The profile sheet's YPRR axis: routes run and yards per route run, season to date, from
ff-jarvis's `model.clients.routes` (heatradar.app), keyed by norm_name there and re-keyed by slug
here like gamelog.py, cut to the `wanted` slug set for the same reason.

Self-contained like gamelog.py: the routes block and slugify come in as arguments.
"""


def report(routes):
    """build.py's one-line summary of LIVE_ROUTES."""
    if not routes:
        return "Routes: no routes_run.json, profile sheet shows no YPRR"
    return f"Routes: {len(routes['players'])} players with routes run, as of {routes.get('fetched')}"


def _row(r):
    return {"n": r.get("name"), "pos": r.get("pos"), "team": r.get("team"),
            "routes": r.get("routes"), "yprr": r.get("yprr"), "tprr": r.get("tprr"),
            "target_share": r.get("target_share")}


def live_routes(raw, slugify, wanted):
    """LIVE_ROUTES: {fetched, week, players: {slug -> {n, pos, team, routes, yprr, ...}}} or None
    when ff-jarvis has not written the file yet or none of its players are on the page."""
    players = (raw or {}).get("players") or {}
    out = {}
    for rec in players.values():
        slug = slugify(rec.get("name") or "")
        if slug in wanted and slug not in out:
            out[slug] = _row(rec)
    if not out:
        return None
    return {"fetched": raw.get("fetched"), "week": raw.get("week"), "players": out}
