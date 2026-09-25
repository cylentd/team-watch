"""The profile modal's projection-vs-actual line: ff-jarvis's `model.market.projections`
(next-game half-PPR points, already loaded for DFS by sources.load_player_proj()), re-keyed by
slug and cut to the `wanted` set, same reason pedigree.py and gamelog.py give.

Self-contained like the other profile-data cuts: the raw block and slugify come in as arguments.
"""


def report(proj):
    """build.py's one-line summary of LIVE_PROJECTIONS."""
    return f"Projections: {len(proj['players'])} players" if proj else "Projections: none, so no next-game line"


def position_ranks(players, slugify):
    """slug -> (rank, of): where this week's projected points put a player among every player
    ff-jarvis projects at his position, 1 = most. Ranked over the whole list, before the cut to
    `wanted`, or a roster would only be ranked against itself. The roster cards' tier is this rank
    (js/surface/teams/cards.js). Plain half-PPR, so an ESPN rank is approximate."""
    best = {}
    for p in players:
        slug, pts = slugify(p.get("name") or ""), p.get("pts")
        if not slug or pts is None or not p.get("pos"):
            continue
        if slug not in best or pts > best[slug][1]:
            best[slug] = (p["pos"], pts)
    by_pos = {}
    for slug, (pos, pts) in best.items():
        by_pos.setdefault(pos, []).append((pts, slug))
    out = {}
    for rows in by_pos.values():
        rows.sort(key=lambda r: (-r[0], r[1]))
        for i, (_, slug) in enumerate(rows):
            out[slug] = (i + 1, len(rows))
    return out


def live_projections(raw, slugify, wanted):
    """LIVE_PROJECTIONS: {players: {slug -> {pts, mu, games, src, rank, of}}, meta: {scoring, through}} or
    None when ff-jarvis has not written the file. Two players on the same slug keep the model
    source over a line-only fallback, same tie-break as build.py's _stock_by_slug().

    `meta` carries the producer's own header so the modal can say whose projection it is showing
    and on what scoring, rather than printing a number with no owner."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    ranks = position_ranks(players, slugify)
    out = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if slug not in wanted or p.get("pts") is None:
            continue
        prev = out.get(slug)
        if prev is None or (p.get("src") == "model" and prev.get("src") != "model"):
            rank, of = ranks.get(slug, (None, None))
            out[slug] = {"pts": p.get("pts"), "mu": p.get("mu"), "games": p.get("games"),
                        "src": p.get("src"), "rank": rank, "of": of}
    if not out:
        return None
    meta = {k: (raw or {}).get(k) for k in ("scoring", "through", "generated")}
    return {"players": out, "meta": meta}
