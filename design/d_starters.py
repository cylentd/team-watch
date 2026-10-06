"""LIVE_D_STARTERS: which defenses are missing starters this week (2026-10-06), from ff-jarvis's d_starters block
(`model.season.d_starters`, METHODOLOGY 12.93's exploratory run). Drawn in two places, both a plain fact:
Preview's chips (one per defense with a starter out) and the profile's matchup note for the defense he faces.
**It moves no projection, rank, order or call**, and the page says the lead is unproven.

The producer writes `games: [{game_id, kickoff, away: TEAM, home: TEAM}]`; this cut re-keys it by defense, in the
page's team spelling (nflverse writes LA, the page LAR; `signals.TEAM_ALIAS`, the one table), and sends that alias so
the page can look a defense up by either spelling. It computes nothing: counts, shares and statuses are the file's.

    {asof, season, week, source, rules: {starters, missing, units, share, evidence}, alias,
     teams: {TEAM: {team, opp, n_starters, n_missing, front7_missing, secondary_missing, share,
                    players: [{name, pos, unit: front7|secondary|null, status, snap_share}]}}}

`players` holds only the missing starters, most snaps first. A defense with no game before this week has null
counts and no players: the page draws nothing for it, which is not the same as none missing.
"""
from signals import TEAM_ALIAS
from sources import DWR, feed_block, read_first

TEAM_KEYS = ("team", "opp", "n_starters", "n_missing", "front7_missing", "secondary_missing", "share", "players")
PLAYER_KEYS = ("name", "pos", "unit", "status", "snap_share")
UNITS = ("front7", "secondary", None)
PASS = ("asof", "season", "week", "source", "rules")


def load_d_starters():
    """ff-jarvis's d_starters block: feed block `d_starters` first (null in a feed from before the step), then
    `d_starters.json`; None when neither exists. Kept here, not in sources.py, which is at its line budget."""
    return feed_block(("d_starters",), "games") or read_first(DWR / "d_starters.json")


def _page(code):
    return TEAM_ALIAS.get(code, code)


def _team(rec):
    out = {k: rec.get(k) for k in TEAM_KEYS}
    out["team"], out["opp"] = _page(rec.get("team")), _page(rec.get("opp"))
    out["players"] = [{k: p.get(k) for k in PLAYER_KEYS} for p in rec.get("players") or []]
    return out


def live_d_starters(raw):
    """The block, or None when ff-jarvis has written no file or a week with no game."""
    if not raw or not raw.get("games"):
        return None
    teams = {}
    for g in raw["games"]:
        for side in (g.get("away"), g.get("home")):
            if isinstance(side, dict) and side.get("team"):
                teams[_page(side["team"])] = _team(side)
    if not teams:
        return None
    return {**{k: raw.get(k) for k in PASS}, "alias": dict(TEAM_ALIAS), "teams": teams}


def problems(block):
    """The nested shape `contract.py` cannot say with a row spec: each player's keys and unit."""
    out = []
    for team, rec in ((block or {}).get("teams") or {}).items():
        for i, p in enumerate(rec.get("players") or []):
            out += [f"LIVE_D_STARTERS.teams[{team!r}].players[{i}].{k}" for k in PLAYER_KEYS if k not in p]
            if p.get("unit") not in UNITS:
                out.append(f"LIVE_D_STARTERS.teams[{team!r}].players[{i}].unit {p['unit']!r}")
    return out


def report(block):
    if not block:
        return "Defenders out: no d_starters block, so no chips and no profile note"
    short = sum(1 for r in block["teams"].values() if r["n_missing"])
    return f"Defenders out: week {block['week']}, {len(block['teams'])} defenses, {short} with a starter out"
