"""The optional broadcast edition is validated with the league block."""
import contract_checks

MAX_PROBLEMS = 64
WEEK_KEYS = ["week", "points", "opponent", "against", "result"]
SPEC = {
    "keys": ["season", "through", "final", "target", "generated", "teams", "max_score", "overview", "film"],
    "rows": [("teams", ["id", "w", "l", "t", "pf", "pa", "average", "standing", "scoring_rank",
                         "against_rank", "allplay", "angle", "weeks", "best", "closest_win"])],
    "row_objs": [("teams", "best", WEEK_KEYS), ("teams", "closest_win", WEEK_KEYS)],
}


def problems_league(league):
    edition = league.get("midseason")
    if edition is None:
        return []
    if not isinstance(edition, dict):
        return ["midseason"]
    out = contract_checks.problems("midseason", edition, SPEC, limit=MAX_PROBLEMS)
    out += _film_problems(edition.get("film"))
    overview = edition.get("overview")
    if not isinstance(overview, dict):
        out.append("midseason.overview")
    else:
        out += [f"midseason.overview.{key}" for key in ("leader", "scorer", "points", "games", "peak") if key not in overview]
        peak = overview.get("peak")
        if not isinstance(peak, dict):
            out.append("midseason.overview.peak")
        else:
            out += [f"midseason.overview.peak.{key}" for key in ("id", "week", "points") if key not in peak]
    teams = edition.get("teams")
    if not isinstance(teams, list) or not teams:
        return out + ["midseason.teams"]
    for index, team in enumerate(teams):
        for week_index, week in enumerate(team.get("weeks") or []):
            out += [f"midseason.teams[{index}].weeks[{week_index}].{key}" for key in WEEK_KEYS if key not in week]
    return out


def _film_problems(film):
    if not isinstance(film, dict):
        return ["midseason.film"]
    spec = {"keys": ["leaders", "chase", "crowd", "frames", "max_total", "surge", "top_count", "top_gap"],
            "rows": [("frames", ["week", "teams"])],
            "objs": [("surge", ["id", "baseline", "recent", "change", "baseline_weeks", "recent_weeks", "wins", "losses", "ties"])]}
    out = contract_checks.problems("midseason.film", film, spec, limit=MAX_PROBLEMS)
    if not isinstance(film.get("surge"), dict):
        out.append("midseason.film.surge")
    if not isinstance(film.get("frames"), list) or not film["frames"]:
        return out + ["midseason.film.frames"]
    for index, frame in enumerate(film["frames"]):
        if not isinstance(frame.get("teams"), list) or not frame["teams"]:
            out.append(f"midseason.film.frames[{index}].teams")
        else:
            out += contract_checks.problems(f"midseason.film.frames[{index}]", frame,
                                            {"keys": [], "rows": ("teams", ["id", "total", "place", "share"])}, limit=MAX_PROBLEMS)
    return out
