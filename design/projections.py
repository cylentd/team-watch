"""The profile modal's projection-vs-actual line: ff-jarvis's `model.market.projections`
(next-game half-PPR points, already loaded for DFS by sources.load_player_proj()), re-keyed by
slug and cut to the `wanted` set, same reason pedigree.py and gamelog.py give.

Self-contained like the other profile-data cuts: the raw block and slugify come in as arguments.
"""
import week_ranks as week_ranks_module   # design/week_ranks.py: the roster card's rank reads ff-jarvis's lists


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


def kick_iso(p):
    """ff-jarvis writes kickoff as "2026-09-27 17:00:00", UTC (checked against the schedule's Z
    times on 2026-09-26). ISO with a Z, so a browser shows it in the reader's own zone."""
    k = p.get("kickoff") or ""
    return k.replace(" ", "T") + "Z" if len(k) >= 16 else None


def _week_of(kick, team, schedule):
    """The schedule week of this kickoff for this team, or None."""
    code = ((schedule or {}).get("alias") or {}).get(team, team)
    for g in (schedule or {}).get("games") or []:
        if g.get("kickoff") == kick and code in (g.get("home"), g.get("away")):
            return g.get("week")
    return None


def slate(players, slugify, schedule, week=None):
    """(week, off): the week this file speaks for, and slug -> "played" | "bye" for every player
    whose projected game is not in the page week (2026-09-26; an earlier week too since 2026-10-05).

    The week is the site's page week (2026-10-05): `week`, else `schedule["week"]`, which is
    ff-jarvis's `page_week` (model/common/nflweek.py), the one rule every view shares. It turns at
    the first rebuild after the week's last game is final, so on Monday before the final it is still
    N and the file's only week-N rows are the Monday game's players. No week: (None, {}).

    The file projects each player's NEXT game, so once a game is over, that team's rows are next
    week's. Ranked beside everyone else's this-week number, Bijan Robinson led the week-3 RBs for a
    game he had already played. A team with a game in the page week and a row in a later one has
    played it ("played"); a team without a game in it is on a bye ("bye").

    Superseded 2026-10-05: the week was inferred from the rows (the one most rows fall in, held at N
    while a non-Monday game of N was still some team's next game, so Monday said N+1; the 2026-10-05
    rule). The page week replaces it; the rows no longer decide it, and no build clock either."""
    week = week if week is not None else (schedule or {}).get("week")
    if week is None:
        return None, {}
    alias = (schedule or {}).get("alias") or {}
    playing = {t for g in (schedule or {}).get("games") or [] if g.get("week") == week
               for t in (g.get("home"), g.get("away"))}
    off = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if not slug:
            continue
        wk = _week_of(kick_iso(p), p.get("team"), schedule)
        if wk is None or wk == week:
            continue
        # A row for an earlier week (a file written before Monday night, read after the turn) is a
        # game already played; a later week is "played" when his team has a game in the page week.
        off[slug] = ("played" if wk < week or alias.get(p.get("team"), p.get("team")) in playing
                     else "bye")
    return week, off


def order_key(p):
    """What a player is ordered by within his position: for a running back the books' implied points
    (`rank_pts`) where his game's RB markets are priced, else his projection. The books' number ranks
    backs better than ours but reads about 0.5 high in level, so it orders and never displays
    (ff-jarvis METHODOLOGY 12.86, 2026-10-05, weekly Spearman 0.527 -> 0.551). Every other position
    orders by `pts`: 12.86 tested running backs only. Null when he has no points."""
    pts = p.get("pts")
    rp = p.get("rank_pts")
    if p.get("pos") == "RB" and isinstance(rp, (int, float)) and pts is not None:
        return rp
    return pts


def position_ranks(players, slugify, skip=()):
    """slug -> (rank, of): where this week's projected points put a player among every player
    ff-jarvis projects at his position, 1 = most (running backs: by `order_key`). Ranked over the whole list, before the cut to
    `wanted`, or a roster would only be ranked against itself. The roster cards' tier is this rank
    (js/surface/teams/cards.js). Plain half-PPR, so an ESPN rank is approximate. A player in
    `skip` (not playing this week) is not ranked, so everyone below him moves up."""
    best = {}
    for p in players:
        slug, pts = slugify(p.get("name") or ""), order_key(p)
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


def live_projections(raw, slugify, wanted, status=None, schedule=None, week_ranks=None):
    """LIVE_PROJECTIONS: {players: {slug -> {pts, mu, games, src, rank, of, out, done, wx, floor, ceil,
    stage, rank_pts, unlined_backup, pts_before_unlined}}, meta:
    {scoring, through}} or None when ff-jarvis has not written the file. Two players on the same
    slug keep the model source over a line-only fallback, same tie-break as build.py's
    _stock_by_slug(). A player Sleeper lists as not playing (`status`, OUT_INJURY) keeps his row
    with `out` set to the code, `pts` null and no rank: the page says OUT rather than a number he
    will not score. A player whose projected game is a later week (`slate`) keeps his row the same
    way with `done` set to "played" or "bye": his card says so rather than next week's number.

    `week_ranks` (design/week_ranks.py) is ff-jarvis's list file; given, `rank` and `of` come from its lists.

    `meta` carries the producer's own header so the modal can say whose projection it is showing
    and on what scoring, rather than printing a number with no owner."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    gone = unavailable(status, slugify)
    _, done = slate(players, slugify, schedule)
    # With ff-jarvis's week_ranks the card's rank is the Ranks page's (ledger #23): the same list, so they never
    # disagree. A player past a list's depth then has none; the old rank over every projected player stays the fallback.
    ranks = (week_ranks_module.position_ranks(week_ranks, slugify) if week_ranks
             else position_ranks(players, slugify, set(gone) | set(done)))
    out = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if slug not in wanted or p.get("pts") is None:
            continue
        prev = out.get(slug)
        if prev is None or (p.get("src") == "model" and prev.get("src") != "model"):
            rank, of = ranks.get(slug, (None, None))
            out[slug] = {"pts": None if slug in gone or slug in done else p.get("pts"), "mu": p.get("mu"),
                        "games": p.get("games"), "src": p.get("src"), "rank": rank, "of": of,
                        "out": gone.get(slug), "done": done.get(slug),
                        # {adj, cond}: points ff-jarvis already moved for this game's weather
                        # (its weather_adjust, METHODOLOGY 12.53), null when none applied.
                        "wx": p.get("wx"),
                        # The 10th and 90th percentile outcome in half-PPR points, given he plays
                        # (ff-jarvis model/market/ranges.py, 2026-10-05): a description, never a
                        # price, and never computed here. Null with no points (out, played, bye) and
                        # for a file or position without a band.
                        "floor": None if slug in gone or slug in done else p.get("floor"),
                        "ceil": None if slug in gone or slug in done else p.get("ceil"),
                        # "early" (no prop line posted for his game yet) | "lined" (lines posted for his game; his own blended if he has one) |
                        # null (a bye, or a feed from before ff-jarvis said which). Absent is never an error.
                        "stage": p.get("stage"),
                        # Running backs only (ff-jarvis METHODOLOGY 12.86 and 12.87, 2026-10-05), null
                        # elsewhere and with no points. `rank_pts`: the books' implied points, which order
                        # backs and are never shown (they read ~0.5 high). `unlined_backup`: the books priced
                        # a teammate, not him, so `pts` is already cut to 30% of `pts_before_unlined`.
                        "rank_pts": None if slug in gone or slug in done else p.get("rank_pts"),
                        "unlined_backup": (p.get("unlined_backup") or None) if slug not in gone and slug not in done else None,
                        "pts_before_unlined": None if slug in gone or slug in done else p.get("pts_before_unlined")}
    if not out:
        return None
    meta = {k: (raw or {}).get(k) for k in ("scoring", "through", "generated", "stage")}
    return {"players": out, "meta": meta}
