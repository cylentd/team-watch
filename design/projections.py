"""The profile modal's projection-vs-actual line: ff-jarvis's `model.market.projections`
(next-game half-PPR points, already loaded for DFS by sources.load_player_proj()), re-keyed by
slug and cut to the `wanted` set, same reason pedigree.py and gamelog.py give.

Self-contained like the other profile-data cuts: the raw block and slugify come in as arguments.
"""


def report(proj):
    """build.py's one-line summary of LIVE_PROJECTIONS."""
    return f"Projections: {len(proj['players'])} players" if proj else "Projections: none, so no next-game line"


def live_projections(raw, slugify, wanted):
    """LIVE_PROJECTIONS: {players: {slug -> {pts, mu, games, src}}} or None when ff-jarvis has not
    written the file. Two players on the same slug keep the model source over a line-only
    fallback, same tie-break as build.py's _stock_by_slug()."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    out = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if slug not in wanted or p.get("pts") is None:
            continue
        prev = out.get(slug)
        if prev is None or (p.get("src") == "model" and prev.get("src") != "model"):
            out[slug] = {"pts": p.get("pts"), "mu": p.get("mu"), "games": p.get("games"),
                        "src": p.get("src")}
    return {"players": out} if out else None
