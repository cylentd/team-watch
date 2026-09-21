"""The Usage page's data: ff-jarvis's `model.season.usage` weekly grid, cut to what the page draws.

Every number is the producer's own. This file renames fields and drops rows; it computes nothing,
because a second implementation of a share or a percentile is a second thing to keep in step.

WHY THE COLUMNS COME FROM THE DATA. `usage_weekly.json` carries its own `cols` — id, header and
format, per position — so adding a column upstream does not need a matching edit here or in the JS.
Hardcoding seven headers in three places is how the RB grid ends up labelled with the WR's columns.

WHAT IS DROPPED. A player who never cleared his position's floor in any week is already gone
upstream. What goes here is the long tail below the page's own cut: the grid is a scanner, and
nobody scans 340 receivers. `KEEP` per position is a display depth, not a judgment — the drawer
and the search still reach everyone the producer kept.

Self-contained like pool.py: the grid and slugify come in as arguments.
"""
import json

# The feed's `usage` block is already watch.json (signals.load_usage reads it), so this one is
# `usage_grid`. Two different files under one key would resolve by whichever refresh wrote last.
FEED_KEY = "usage_grid"
FILE = "usage_weekly.json"


def load_grid(feed_path, dwr_path):
    """ff-jarvis's usage_weekly.json: the feed block first, then the file. None means nflverse has
    published no week yet, and the page falls back to its sample."""
    try:
        block = (json.loads(feed_path.read_text(encoding="utf-8")).get(FEED_KEY) or {}).get("data")
        if block and block.get("rows"):
            return block
    except (OSError, json.JSONDecodeError):
        pass
    path = dwr_path / FILE
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None

# How deep each position's grid runs, ranked by the sort column below. A back who is RB60 in
# carries and RB1 in nothing else is not a row anyone reads.
KEEP = {"QB": 40, "RB": 60, "WR": 80, "TE": 40}

# The column each position is ranked by when the page opens: the one that says how much work he
# got, not how well it went. Everything else the reader sorts to.
RANK_BY = {"QB": "dropbacks", "RB": "car", "WR": "tgt", "TE": "tgt"}


def report(usage):
    """build.py's one-line summary of LIVE_USAGE."""
    if not usage:
        return "Usage: no usage_weekly.json, Usage tab falls back to its sample"
    weeks = usage["weeks"]
    span = f"week {weeks[0]}" if len(weeks) == 1 else f"weeks {weeks[0]}-{weeks[-1]}"
    return (f"Usage: {len(usage['rows'])} player-weeks over {span}, "
            f"{len(usage['cols'])} position grids")


def _row(r, slugify):
    return {"n": r.get("name"), "slug": slugify(r.get("name") or ""), "pos": r.get("pos"),
            "team": r.get("team"), "wk": r.get("week"), "q": bool(r.get("q")),
            "v": r.get("v") or {}, "p": r.get("p") or {}}


def live_usage(grid, slugify):
    """LIVE_USAGE: {season, weeks, through, cols, rows} or None when ff-jarvis has no grid yet.

    `rows` is every kept player-week for every position, flat: the page filters by position and
    week itself, because a reader flicking between weeks should not wait on anything."""
    rows = (grid or {}).get("rows") or []
    cols = (grid or {}).get("cols") or {}
    if not rows or not cols:
        return None
    weeks = sorted({r["week"] for r in rows if r.get("week") is not None})
    if not weeks:
        return None

    kept = []
    for pos, spec in cols.items():
        by = RANK_BY.get(pos) or (spec[0]["id"] if spec else None)
        for wk in weeks:
            here = [r for r in rows if r.get("pos") == pos and r.get("week") == wk]
            here.sort(key=lambda r: (-(r.get("v", {}).get(by) or 0), r.get("name") or ""))
            kept += here[:KEEP.get(pos, 40)]

    return {"season": grid.get("season"), "weeks": weeks, "through": grid.get("through"),
            "generated": grid.get("generated"), "rankBy": RANK_BY,
            "cols": cols, "rows": [_row(r, slugify) for r in kept]}
