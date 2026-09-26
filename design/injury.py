"""LIVE_INJURY: who is hurt this week, from ff-jarvis's Sleeper status (sources.load_status()),
cut to the players the page can show (2026-09-25).

Three levels, because they ask for three different things of a lineup:
  OUT  Out, IR, PUP, Sus, NA, DNR, COV (projections.OUT_INJURY): not playing, swap him
  D    Doubtful: usually sits, swap him if you can
  Q    Questionable: usually plays, watch the news
Sleeper's own code and note ride along ("NA", "Personal") so the card can say why. The same
OUT set is what drops a player's projection and rank (projections.unavailable), so the two never
disagree."""
from projections import OUT_INJURY

LEVEL = {"Doubtful": "D", "Questionable": "Q"}


def level(code):
    """Sleeper's injury code -> "OUT" / "D" / "Q", or None for a healthy player."""
    return "OUT" if code in OUT_INJURY else LEVEL.get(code)


def live_injury(status, slugify, wanted):
    """{players: {slug -> {s, code, note}}} for every hurt player in `wanted`, or None with no
    status file. A healthy player has no row."""
    if not status:
        return None
    out = {}
    for r in status.values():
        slug, s = slugify(r.get("name") or ""), level(r.get("injury"))
        if slug in wanted and s:
            out[slug] = {"s": s, "code": r["injury"], "note": r.get("injury_note") or None}
    return {"players": out}


def report(block):
    if not block:
        return "Injuries: no Sleeper status"
    n = {k: sum(1 for v in block["players"].values() if v["s"] == k) for k in ("OUT", "D", "Q")}
    return f"Injuries: {n['OUT']} out, {n['D']} doubtful, {n['Q']} questionable on the page"
