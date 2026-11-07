"""Broadcast chart frames and a recent-form comparison from the edition window."""
RECENT_WEEKS = 2
CHASE_GAP = 1
TOP_OFFENSES = 3


def _form(team):
    recent, baseline = team["weeks"][-RECENT_WEEKS:], team["weeks"][:-RECENT_WEEKS]
    old = sum(week["points"] for week in baseline) / len(baseline)
    new = sum(week["points"] for week in recent) / len(recent)
    return {"id": team["id"], "baseline": round(old, 2), "recent": round(new, 2),
            "change": round(new - old, 2), "baseline_weeks": len(baseline), "recent_weeks": len(recent),
            "wins": sum(week["result"] == "W" for week in recent),
            "losses": sum(week["result"] == "L" for week in recent),
            "ties": sum(week["result"] == "T" for week in recent)}


def film_data(teams):
    maximum = max(team["pf"] for team in teams)
    lead = max(team["w"] + team["t"] / 2 for team in teams)
    leaders = [team["id"] for team in teams if team["w"] + team["t"] / 2 == lead]
    chase = [team["id"] for team in teams if 0 < lead - team["w"] - team["t"] / 2 <= CHASE_GAP]
    frames = []
    for index in range(len(teams[0]["weeks"])):
        scores = [{"id": team["id"], "total": round(sum(week["points"] for week in team["weeks"][:index + 1]), 2)}
                  for team in teams]
        scores.sort(key=lambda score: (-score["total"], score["id"]))
        frames.append({"week": index + 1, "teams": [dict(score, place=place, share=score["total"] / maximum if maximum else 0)
                                                    for place, score in enumerate(scores)]})
    forms = [_form(team) for team in teams]
    top = sorted((team["pf"] for team in teams), reverse=True)[:TOP_OFFENSES]
    return {"leaders": leaders, "chase": chase, "crowd": len(leaders) + len(chase),
            "top_count": len(top), "top_gap": round(top[0] - top[-1], 2),
            "max_total": maximum, "frames": frames,
            "surge": max(forms, key=lambda form: (form["change"], -form["id"]))}
