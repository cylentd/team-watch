"""LIVE_KDST: each club's D/ST and K points per played game (2026-10-07), from ff-jarvis's gamelog_kdst.json
(kdst-gamelog), read from the jobs data dir only; it is not in the feed.

    {generated, season, through_week, teams: {TEAM: [{week, opp, home, dst_espn, dst_yahoo, k_yahoo, k_ayo, kickers}]}}

Final games only; a bye has no row. The Roster's K and D/ST cards draw these as the same points bars as a player,
the league's scoring picking the key (data/kdst.js). The page computes nothing: this cut passes the file through,
None when there is none, and the backs keep their facts.
"""
import sources

TOP = ("generated", "season", "through_week", "teams")
ROW = ("week", "opp", "home", "dst_espn", "dst_yahoo", "k_yahoo", "k_ayo", "kickers")


def load_kdst():
    """The ff-jarvis file, None when absent. Lives here, not in sources.py, which is at its line budget."""
    return sources.read_first(sources.DWR / "gamelog_kdst.json")


def live_kdst(raw):
    if not raw or not raw.get("teams"):
        return None
    return {k: raw.get(k) for k in TOP}


def problems(obj):
    """Missing fields of a LIVE_KDST row as `LIVE_KDST['ARI'][0].k_ayo`, for contract.py."""
    return [f"LIVE_KDST[{team!r}][{i}].{k}" for team, rows in ((obj or {}).get("teams") or {}).items()
            for i, row in enumerate(rows) for k in ROW if k not in row]


def report(block):
    if not block:
        return "K/D/ST bars: no gamelog_kdst.json, so the backs keep their facts"
    return f"K/D/ST bars: {len(block['teams'])} clubs through week {block['through_week']}"
