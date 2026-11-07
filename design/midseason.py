"""Madden Curse's broadcast edition: preview after seven complete weeks, final through eight.

The league ID scopes the feature to Madden Curse. Scores and records are rebuilt from the
same complete rounds, not live standings. Later weeks can never rewrite this edition.
"""
import math
from midseason_film import film_data

MADDEN_CURSE_ID = "75203"
EDITION_SEASON = 2026
PREVIEW_WEEK = 7
EDITION_WEEK = 8
TOP_SCORERS = 3


def _score(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _rounds(season, ids):
    complete = []
    for week in range(1, EDITION_WEEK + 1):
        games = [game for game in season.get("games", []) if game.get("week") == week]
        played = [team for game in games for team in (game.get("home"), game.get("away"))]
        finals = all(game.get("winner") in ("home", "away", "tie")
                     and _score(game.get("hp")) and _score(game.get("ap")) for game in games)
        if sorted(played) != sorted(ids) or not finals:
            break
        complete.append(games)
    return complete


def _team(team_id, rounds):
    weeks, allplay = [], [0, 0, 0]
    for games in rounds:
        scores = [game[key] for game in games for key in ("hp", "ap")]
        game = next(game for game in games if team_id in (game["home"], game["away"]))
        home = team_id == game["home"]
        points, against = (game["hp"], game["ap"]) if home else (game["ap"], game["hp"])
        result = "W" if points > against else "L" if points < against else "T"
        weeks.append({"week": game["week"], "points": points, "opponent": game["away"] if home else game["home"],
                      "against": against, "result": result})
        allplay[0] += sum(points > score for score in scores)
        allplay[1] += sum(points < score for score in scores)
        allplay[2] += sum(points == score for score in scores) - 1
    wins = [week for week in weeks if week["result"] == "W"]
    return {"id": team_id, "w": len(wins), "l": sum(week["result"] == "L" for week in weeks),
            "t": sum(week["result"] == "T" for week in weeks), "pf": round(sum(week["points"] for week in weeks), 2),
            "pa": round(sum(week["against"] for week in weeks), 2), "weeks": weeks, "allplay": allplay,
            "best": max(weeks, key=lambda week: week["points"]),
            "closest_win": min(wins, key=lambda week: week["points"] - week["against"]) if wins else None}


def _angle(team, count):
    if team["standing"] == 1 and team["scoring_rank"] == 1:
        return "leader"
    if team["scoring_rank"] <= min(TOP_SCORERS, count // 2) and team["standing"] > team["scoring_rank"]:
        return "darkhorse"
    if team["against_rank"] == 1:
        return "gauntlet"
    if team["w"] >= team["l"] and team["scoring_rank"] > count / 2:
        return "survivor"
    if team["w"] >= team["l"]:
        return "contender"
    return "comeback"


def _overview(teams, rounds):
    peak = max(({"id": team["id"], "week": week["week"], "points": week["points"]}
                for team in teams for week in team["weeks"]),
               key=lambda item: (item["points"], -item["week"], -item["id"]))
    return {"leader": teams[0]["id"], "scorer": min(teams, key=lambda team: (team["scoring_rank"], team["id"]))["id"],
            "points": round(sum(team["pf"] for team in teams), 2),
            "games": sum(len(games) for games in rounds), "peak": peak}


def midseason_special(season):
    if not season or str(season.get("league_id")) != MADDEN_CURSE_ID or season.get("season") != EDITION_SEASON:
        return None
    ids = [int(team_id) for team_id in season.get("teams", {})]
    if len(ids) < 2:
        return None
    rounds = _rounds(season, ids)
    if len(rounds) < PREVIEW_WEEK:
        return None
    teams = [_team(team_id, rounds) for team_id in ids]
    teams.sort(key=lambda team: (-(team["w"] + team["t"] / 2), -team["pf"], team["id"]))
    for team in teams:
        standing_key = (team["w"] + team["t"] / 2, team["pf"])
        team["standing"] = 1 + sum((other["w"] + other["t"] / 2, other["pf"]) > standing_key for other in teams)
        team["scoring_rank"] = 1 + sum(other["pf"] > team["pf"] for other in teams)
        team["against_rank"] = 1 + sum(other["pa"] > team["pa"] for other in teams)
        team["angle"] = _angle(team, len(teams))
        team["average"] = round(team["pf"] / len(rounds), 2)
    return {"season": season["season"], "through": len(rounds), "final": len(rounds) == EDITION_WEEK,
            "target": EDITION_WEEK, "generated": season.get("generated"), "teams": teams,
            "overview": _overview(teams, rounds),
            "film": film_data(teams),
            "max_score": max(week["points"] for team in teams for week in team["weeks"])}
