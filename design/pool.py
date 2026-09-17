"""The Pool page's data: ff-jarvis's `model.season.watch` league-wide pool (every player with real
usage), cut to the fields the page draws. Every number is watch's own: the share move a row plots
is the one verdict() read (carries for a back, targets for a receiver, snaps for a quarterback).

Self-contained like signals.py: the usage block and slugify come in as arguments."""

# The share that says a player's role, by position; a quarterback has no carry or target share
# that means anything, so his role is his snaps.
SHARE = {"RB": ("car", "d_car"), "WR": ("tgt", "d_tgt"), "TE": ("tgt", "d_tgt"), "QB": ("snap", "d_snap")}


def _r1(v):
    return None if v is None else round(float(v), 1)


def _leagues(rostered_by, mine):
    """{"espn": team or None, "yahoo": team or None} and whether one of those teams is mine."""
    out = {"espn": None, "yahoo": None}
    for tag in rostered_by or []:
        label, _, team = tag.partition(":")
        if label.lower() in out:
            out[label.lower()] = team
    return out, any(f"{k}:{v}" in mine for k, v in out.items() if v)


def report(pool):
    """build.py's one-line summary of LIVE_POOL."""
    if not pool:
        return "Pool: no watch.json pool, template falls back to its sample"
    return (f"Pool: {len(pool['players'])} players through week {pool['through_week']}, "
            f"{pool['trended']} with a share move")


def live_pool(usage, slugify):
    """LIVE_POOL: {through_week, generated, trended, players: [...]} ranked by role share, or
    None when watch has no pool. `trended` is how many rows have a share move to plot: 0 until a
    player has two weeks, which is the whole of week 1."""
    rows = (usage or {}).get("pool") or []
    rows = [r for r in rows if isinstance(r, dict)]
    if not rows:
        return None
    mine = {f"{(L.get('label') or '').lower()}:{L.get('me')}" for L in usage.get("leagues") or []}
    players = []
    for r in rows:
        share, d_share = SHARE.get(r.get("pos"), ("tgt", "d_tgt"))
        leagues, is_mine = _leagues(r.get("rostered_by"), mine)
        players.append({
            "n": r.get("name"), "slug": slugify(r.get("name") or ""), "pos": r.get("pos"), "team": r.get("team"),
            "snaps": _r1(r.get("snap")), "dSnap": _r1(r.get("d_snap")),
            "share": _r1(r.get(share)), "dShare": _r1(r.get(d_share)),
            "opp": r.get("opp"), "rz": r.get("rz"), "ppg": _r1(r.get("ppg")),
            # watch's luck is a ratio (points over what the usage bought); the page reads percent
            "luck": None if r.get("luck") is None else round(float(r["luck"]) * 100),
            "v": r.get("verdict") or "hold", "why": r.get("why") or "",
            "leagues": leagues, "mine": is_mine,
        })
    # Role share first, skill players ahead of quarterbacks: a quarterback's dropbacks count as
    # opportunities and his share is his snaps, so either key alone put every QB on top.
    players.sort(key=lambda p: (p["pos"] == "QB", -(p["share"] or 0), -(p["opp"] or 0), p["n"] or ""))
    return {"through_week": usage.get("through_week"), "generated": usage.get("generated"),
            "trended": sum(1 for p in players if p["dShare"] is not None), "players": players}
