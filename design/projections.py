"""The profile modal's projection-vs-actual line: ff-jarvis's `model.market.projections`
(next-game half-PPR points, already loaded for DFS by sources.load_player_proj()), re-keyed by
slug and cut to the `wanted` set, same reason pedigree.py and gamelog.py give.

Self-contained like the other profile-data cuts: the raw block and slugify come in as arguments.
"""
import datetime
from collections import Counter

from slate import EASTERN


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


def _monday(kick):
    """Is this kickoff (ISO, Z) on a Monday in Eastern time, the league's own clock? Monday night is
    00:15 UTC the next day."""
    when = datetime.datetime.fromisoformat(kick.replace("Z", "+00:00"))
    return when.astimezone(EASTERN).weekday() == 0


def slate(players, slugify, schedule):
    """(week, off): the week this file speaks for, and slug -> "played" | "bye" for every player
    whose projected game is a later week (2026-09-26).

    The file projects each player's NEXT game, so once a Thursday game is over, that team's rows
    are next week's. Ranked beside everyone else's this-week number, Bijan Robinson led the week-3
    RBs for a game he had already played. The week is the one most rows fall in; a team with a
    game in it has played it, a team without one is on a bye. No schedule: (None, {}).

    Week N holds while one of its games, Monday night apart, is still a team's next game (2026-10-05):
    the noon Sunday run, after the 1 PM ET games, has most rows on N+1 while the 4 PM games and Sunday
    night are still to play, and the page flipped to N+1 for them. Monday night alone does not hold the
    week, so Monday says N+1. The file's own rows say what is still to play: no build clock."""
    weeks, by_slug, ahead = Counter(), {}, set()
    for p in players:
        slug = slugify(p.get("name") or "")
        if not slug:
            continue
        kick = kick_iso(p)
        wk = _week_of(kick, p.get("team"), schedule)
        by_slug[slug] = (wk, p.get("team"))
        if wk is not None:
            weeks[wk] += 1
            if not _monday(kick):
                ahead.add(wk)
    if not weeks:
        return None, {}
    week = min(weeks.most_common(1)[0][0], min(ahead, default=weeks.most_common(1)[0][0]))
    alias = (schedule or {}).get("alias") or {}
    playing = {t for g in schedule.get("games") or [] if g.get("week") == week for t in (g.get("home"), g.get("away"))}
    return week, {slug: ("played" if alias.get(team, team) in playing else "bye")
                  for slug, (wk, team) in by_slug.items() if wk is not None and wk > week}


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


def live_projections(raw, slugify, wanted, status=None, schedule=None):
    """LIVE_PROJECTIONS: {players: {slug -> {pts, mu, games, src, rank, of, out, done, wx, floor, ceil,
    stage, rank_pts, unlined_backup, pts_before_unlined}}, meta:
    {scoring, through}} or None when ff-jarvis has not written the file. Two players on the same
    slug keep the model source over a line-only fallback, same tie-break as build.py's
    _stock_by_slug(). A player Sleeper lists as not playing (`status`, OUT_INJURY) keeps his row
    with `out` set to the code, `pts` null and no rank: the page says OUT rather than a number he
    will not score. A player whose projected game is a later week (`slate`) keeps his row the same
    way with `done` set to "played" or "bye": his card says so rather than next week's number.

    `meta` carries the producer's own header so the modal can say whose projection it is showing
    and on what scoring, rather than printing a number with no owner."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    gone = unavailable(status, slugify)
    _, done = slate(players, slugify, schedule)
    ranks = position_ranks(players, slugify, set(gone) | set(done))
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
