"""LIVE_SOS: strength of schedule (2026-10-05), from ff-jarvis's sos.json (model.season.sos).

What the defenses each team faces allow each position over the next 4 weeks, the rest of the season and
the fantasy playoff weeks, rank 1 = easiest. Context, not backtested (ff-jarvis METHODOLOGY 12.11), and
the page says so with the file's own `label`. The producer's docstring is the field contract. The page
computes nothing: this cut passes the file through, None when there is none.
"""


def live_sos(raw):
    """None when ff-jarvis has written no file: the view then says so."""
    if not raw or not raw.get("teams"):
        return None
    keep = ("label", "generated", "season", "from_week", "through_week", "playoff_weeks", "last_week",
            "weights", "windows", "teams")
    return {k: raw.get(k) for k in keep}


def report(block):
    if not block:
        return "Schedule: no sos.json, so the view says so"
    return f"Schedule: {len(block['teams'])} teams from week {block['from_week']}"
