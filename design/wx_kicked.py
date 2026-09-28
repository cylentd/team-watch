"""LIVE_WEATHER["kicked"]: each stadium's last forecast before each of its recent kickoffs.

LIVE_WEATHER's `teams` rows hold each stadium's NEXT home kickoff, so the morning after a game its row
is already next week's, and Weather used to drop the game to a one-line "Played" list. David wanted the
games kept, dimmed (2026-09-27), so the view needs the forecast it showed before kickoff. ff-jarvis
appends every fetch to history kind `weather` ({team, kickoff, as_of, roof, temp_f, wind_mph,
precip_pct, short}); this keeps, per team and kickoff, the last row fetched before that kickoff, in
the `teams` row's own shape (`wind` as "13 mph"), so the page reads both the same way.
"""
from datetime import datetime


def _t(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def kicked(rows):
    """{team: [forecast row, one per kickoff, oldest first]} from history `weather` rows. A row fetched
    after its own kickoff is not a forecast and is skipped."""
    best = {}
    for r in rows:
        if not r.get("kickoff") or not r.get("as_of") or r.get("roof") == "dome":
            continue
        if _t(r["as_of"]) >= _t(r["kickoff"]):
            continue
        key = (r["team"], r["kickoff"])
        if key not in best or _t(r["as_of"]) > _t(best[key]["as_of"]):
            best[key] = r
    out = {}
    for (team, _), r in sorted(best.items(), key=lambda kv: _t(kv[0][1])):
        out.setdefault(team, []).append({
            "roof": r.get("roof"), "kickoff": r["kickoff"], "as_of": r["as_of"], "temp_f": r.get("temp_f"),
            "wind": f"{r['wind_mph']} mph" if r.get("wind_mph") is not None else None,
            "short": r.get("short"), "precip_pct": r.get("precip_pct")})
    return out
