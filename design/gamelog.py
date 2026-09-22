"""The profile modal's weekly-history table: ff-jarvis's `model.season.gamelog_weekly` box score
(rush/rec yards, TDs, receptions, fantasy points), one row per player-week.

Cut to the `wanted` slug set (the same one build.py already computes for headshots), same reason
pedigree.py gives: the modal only ever opens for a player the page can already show a row for, and
the source file carries every skill player in the league every week.

Self-contained like usage.py: the gamelog block and slugify come in as arguments.
"""


def report(gamelog):
    """build.py's one-line summary of LIVE_GAMELOG."""
    if not gamelog:
        return "Gamelog: no gamelog_weekly.json, profile modal shows no weekly history"
    return f"Gamelog: {len(gamelog['rows'])} player-weeks kept of {gamelog.get('total', '?')}"


def _row(r, slugify):
    return {"n": r.get("name"), "slug": slugify(r.get("name") or ""), "pos": r.get("pos"),
            "team": r.get("team"), "opp": r.get("opp"), "wk": r.get("week"),
            "pts": r.get("pts"), "car": r.get("carries"), "rush_yds": r.get("rushing_yards"),
            "rush_td": r.get("rushing_tds"), "tgt": r.get("targets"), "rec": r.get("receptions"),
            "rec_yds": r.get("receiving_yards"), "rec_td": r.get("receiving_tds"),
            "pass_yds": r.get("passing_yards"), "pass_td": r.get("passing_tds")}


def live_gamelog(gamelog, slugify, wanted):
    """LIVE_GAMELOG: {season, weeks, through, generated, rows} or None when ff-jarvis has not
    written the file yet. `rows` is flat, every kept player-week; the modal filters by slug
    itself, the same way LIVE_USAGE leaves the per-position/week split to the JS."""
    rows = (gamelog or {}).get("rows") or []
    if not rows:
        return None
    kept = [_row(r, slugify) for r in rows if slugify(r.get("name") or "") in wanted]
    if not kept:
        return None
    return {"season": gamelog.get("season"), "weeks": gamelog.get("weeks"),
            "through": gamelog.get("through"), "generated": gamelog.get("generated"),
            "total": len(rows), "rows": kept}
