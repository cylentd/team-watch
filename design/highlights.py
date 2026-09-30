"""LIVE_HIGHLIGHTS: Players > Highlights (leaf `highlights`, 2026-09-29), from ff-jarvis's highlights.json.

Two lines per Players view (Ranks, Leaders, Role, Grid), written by Claude from candidates ff-jarvis's
code found in each view's own data, every number checked against its candidate (ff-jarvis
model.season.highlights). Storyboard https://claude.ai/artifact/W5ty9RzT4XWSRfSjtdKEAk, option A.
The page computes nothing: this cut keeps the views in the order the tab draws them and the fields
it reads. Worth knowing on the Digest shows each view's first line.

Self-contained like the other cuts: the loaded file comes in as an argument. The slugs are already
team-watch's (ff-jarvis mirrors slugify, pinned by its test_mirrors).
"""

# The tab's order and each view's leaf, the one table both the tab and Worth knowing read.
VIEWS = (("ranks", "ranks"), ("leaders", "board"), ("role", "movers"), ("grid", "usage"))
FIELDS = ("slug", "n", "pos", "team", "num", "line")


def _row(r):
    """The row the page reads, plus `kind` ("ranks.jump"): the candidate id's first two parts, ff-jarvis's
    contract (`view.kind.key`). The page words the number's unit from it (2026-09-30, the Reel)."""
    row = {k: r.get(k) for k in FIELDS}
    row["kind"] = ".".join((r.get("id") or "").split(".")[:2])
    return row


def live_highlights(raw):
    """None when ff-jarvis has written no packet: the tab then says so."""
    views = (raw or {}).get("views") or {}
    out = []
    for view, leaf in VIEWS:
        rows = [_row(r) for r in views.get(view) or [] if r.get("line")]
        if rows:
            out.append({"view": view, "leaf": leaf, "rows": rows})
    if not out:
        return None
    return {"season": raw.get("season"), "week": raw.get("week"), "generated": raw.get("generated"), "views": out}


def report(block):
    if not block:
        return "Highlights: no highlights.json, so the tab says so"
    n = sum(len(v["rows"]) for v in block["views"])
    return f"Highlights: week {block['week']}, {n} lines over {len(block['views'])} views"
