"""LIVE_LINES: each team's implied points for its next game, from the game lines Yahoo's DFS lobby
carries (ff-jarvis's model.clients.dfs, sources.load_dfs_pool()). The defense support card on the
roster leads with the opponent's number: a defense scores when the other offense doesn't.

Implied points are the total split by the spread: total/2 - spread/2, the spread signed from that
team's side (a 3.5-point favourite is -3.5). Book lines, not our model: a price, never a verdict.
Self-contained like projections.py: the raw pool and the team-code fix come in as arguments.
"""


def live_lines(pool, team_fix):
    """{teams: {TEAM -> {implied, opp, spread, total}}} or None when no game in the pool is priced."""
    games = (pool or {}).get("games") or {}
    teams = {}
    for key, g in games.items():
        odds = (g or {}).get("odds") or {}
        total, home_spread, away_spread = odds.get("overUnder"), odds.get("homeSpread"), odds.get("awaySpread")
        if "@" not in key or total is None or home_spread is None or away_spread is None:
            continue
        away, home = (team_fix.get(t, t) for t in key.split("@", 1))
        teams[home] = {"implied": round(total / 2 - home_spread / 2, 1), "opp": away,
                       "spread": home_spread, "total": total}
        teams[away] = {"implied": round(total / 2 - away_spread / 2, 1), "opp": home,
                       "spread": away_spread, "total": total}
    return {"teams": teams} if teams else None


def report(lines):
    """build.py's one-line summary of LIVE_LINES."""
    return f"Lines: {len(lines['teams'])} teams priced" if lines else "Lines: none, so no implied points"
