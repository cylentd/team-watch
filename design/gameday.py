"""Gameday > Live (2026-09-28): every team's lineup, this week's games and each league's scoring rules,
so the page can score every matchup itself from Sleeper's live stats (storyboard
https://claude.ai/artifact/8qKDQUVxkz4F5naVPVQjhH).

Inputs are ff-jarvis's: espn_league.json / yahoo_league.json (teams, games, week, bonus, ESPN's raw
`scoring`), espn_rosters.json / league_rosters.json (`me` and each team's `detail` lineup), and
yahoo_settings.json (Yahoo's raw `scoring`). api/_scoring.py turns the raw rules into terms. A
player's Sleeper id comes from sleeper_status.json; a defense's is its team code, the way Sleeper
keys it. Nothing here scores a point: the page does (js/data/gameday/).
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "api"))
import _scoring  # noqa: E402

# Sleeper's team codes, which its schedule and stats use; ESPN and Yahoo spell three of them otherwise.
SLEEPER_TEAM = {"LA": "LAR", "WSH": "WAS", "JAC": "JAX"}
DEFENSE = ("D/ST", "DEF", "DST")
BENCH = ("BE", "BN", "IR")
# Slot order down a lineup, the way ESPN and Yahoo draw it; a slot not listed goes last.
ORDER = ("QB", "RB", "WR", "TE", "FLEX", "W/R/T", "W/R", "OP", "K", "D/ST", "DEF", "BE", "BN", "IR")


def _team(code):
    return SLEEPER_TEAM.get(code, code)


def _row(p, ids, slugify, norm):
    pos = "DEF" if p.get("pos") in DEFENSE else p.get("pos")
    team = _team(p.get("team") or "")
    sid = team if pos == "DEF" else ids.get(norm(p["name"]))
    return {"slot": p.get("slot"), "n": p["name"], "slug": slugify(p["name"]), "pos": pos, "team": team,
            "sid": sid}


def _lineup(players, ids, slugify, norm):
    rows = [_row(p, ids, slugify, norm) for p in players or []]
    rank = lambda r: ORDER.index(r["slot"]) if r["slot"] in ORDER else len(ORDER)
    return sorted(rows, key=rank)


def _league(key, season, rosters, rules, ids, slugify, norm):
    """One league's block, or None without its season or rosters file."""
    if not season or not rosters or not rosters.get("detail"):
        return None
    week = season.get("week")
    names = {str(k): t["name"] for k, t in (season.get("teams") or {}).items()}
    by_name = {v: k for k, v in names.items()}
    teams = {tid: {"name": name, "lineup": _lineup(rosters["detail"].get(name), ids, slugify, norm)}
             for tid, name in names.items()}
    games = [[str(g["away"]), str(g["home"])] for g in season.get("games") or []
             if str(g.get("week")) == str(week) and g.get("home") is not None]
    return {"key": key, "name": season.get("league"), "week": int(week) if week else None,
            "median": season.get("bonus") == "WIN_BONUS_TOP_HALF", "me": by_name.get(rosters.get("me")),
            "rules": rules, "teams": teams, "games": games}


def live_gameday(espn, espn_rosters, yahoo, yahoo_rosters, yahoo_settings, status, kickers, slugify, norm):
    """LIVE_GAMEDAY: {season, leagues [LEAGUE]}; a league without its files is left out. `status` is
    sleeper_status.json's players (skill positions), `kickers` its kicker map: together, every id."""
    ids = {**{k: (r or {}).get("sleeper_id") for k, r in (status or {}).items()}, **(kickers or {})}
    leagues = [
        _league("espn", espn, espn_rosters, _scoring.espn_rules((espn or {}).get("scoring")), ids, slugify, norm),
        _league("yahoo", yahoo, yahoo_rosters, _scoring.yahoo_rules((yahoo_settings or {}).get("scoring")),
                ids, slugify, norm),
    ]
    leagues = [lg for lg in leagues if lg]
    return {"season": (espn or yahoo or {}).get("season"), "leagues": leagues}


def report(block):
    parts = []
    for lg in block["leagues"]:
        players = [r for t in lg["teams"].values() for r in t["lineup"]]
        missing = sum(1 for r in players if not r["sid"])
        parts.append(f"{lg['key']} week {lg['week']} {len(lg['teams'])} teams, {len(lg['games'])} games, "
                     f"{len(players)} players ({missing} without a Sleeper id), "
                     f"{len(lg['rules']['off']) + len(lg['rules']['dst'])} rules"
                     + (f", unknown {lg['rules']['unknown']}" if lg["rules"]["unknown"] else "")
                     + (", median" if lg["median"] else ""))
    return "Gameday: " + ("; ".join(parts) if parts else "none")
