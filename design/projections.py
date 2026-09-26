"""The profile modal's projection-vs-actual line: ff-jarvis's `model.market.projections`
(next-game half-PPR points, already loaded for DFS by sources.load_player_proj()), re-keyed by
slug and cut to the `wanted` set, same reason pedigree.py and gamelog.py give.

Self-contained like the other profile-data cuts: the raw block and slugify come in as arguments.
"""


def report(proj):
    """build.py's one-line summary of LIVE_PROJECTIONS."""
    return f"Projections: {len(proj['players'])} players" if proj else "Projections: none, so no next-game line"


# Sleeper injury designations that mean he will not play this week (2026-09-25). The projection
# model reads usage, not the injury report, so it kept projecting Josh Jacobs (NA, "Personal", the
# RB4 on the depth chart) as the #24 RB. Questionable and Doubtful still play often enough to keep
# their number; the page flags them from the same report elsewhere.
OUT_INJURY = {"Out", "IR", "PUP", "Sus", "NA", "DNR", "COV"}


def unavailable(status, slugify):
    """slug -> Sleeper's injury code, for every player it lists as not playing this week."""
    out = {}
    for r in (status or {}).values():
        slug = slugify(r.get("name") or "")
        if slug and r.get("injury") in OUT_INJURY:
            out[slug] = r["injury"]
    return out


def position_ranks(players, slugify, skip=()):
    """slug -> (rank, of): where this week's projected points put a player among every player
    ff-jarvis projects at his position, 1 = most. Ranked over the whole list, before the cut to
    `wanted`, or a roster would only be ranked against itself. The roster cards' tier is this rank
    (js/surface/teams/cards.js). Plain half-PPR, so an ESPN rank is approximate. A player in
    `skip` (not playing this week) is not ranked, so everyone below him moves up."""
    best = {}
    for p in players:
        slug, pts = slugify(p.get("name") or ""), p.get("pts")
        if not slug or pts is None or not p.get("pos") or slug in skip:
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


def live_projections(raw, slugify, wanted, status=None):
    """LIVE_PROJECTIONS: {players: {slug -> {pts, mu, games, src, rank, of, out}}, meta: {scoring,
    through}} or None when ff-jarvis has not written the file. Two players on the same slug keep
    the model source over a line-only fallback, same tie-break as build.py's _stock_by_slug().
    A player Sleeper lists as not playing (`status`, OUT_INJURY) keeps his row with `out` set to
    the code, `pts` null and no rank: the page says OUT rather than a number he will not score.

    `meta` carries the producer's own header so the modal can say whose projection it is showing
    and on what scoring, rather than printing a number with no owner."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    gone = unavailable(status, slugify)
    ranks = position_ranks(players, slugify, gone)
    out = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if slug not in wanted or p.get("pts") is None:
            continue
        prev = out.get(slug)
        if prev is None or (p.get("src") == "model" and prev.get("src") != "model"):
            rank, of = ranks.get(slug, (None, None))
            out[slug] = {"pts": None if slug in gone else p.get("pts"), "mu": p.get("mu"), "games": p.get("games"),
                        "src": p.get("src"), "rank": rank, "of": of, "out": gone.get(slug)}
    if not out:
        return None
    meta = {k: (raw or {}).get(k) for k in ("scoring", "through", "generated")}
    return {"players": out, "meta": meta}
