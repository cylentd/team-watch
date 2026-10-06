"""LIVE_ACCURACY: the accuracy receipts (2026-10-05), from ff-jarvis's accuracy.json (model.season.accuracy).

Ours vs FantasyPros on the players both projected, per week and position, copied by ff-jarvis from its
grade files, plus season to date with the scorecard's 95% CI. The producer's docstring is the field
contract. The page computes nothing: this cut passes the file through, None when there is none.
"""


def live_accuracy(raw):
    """None when ff-jarvis has written no file: the page then says so."""
    if not raw or not raw.get("weeks"):
        return None
    return {k: raw.get(k) for k in ("season", "generated", "rules", "weeks", "missing_weeks", "season_to_date")}


def report(block):
    if not block:
        return "Accuracy: no accuracy.json, so the page says so"
    return f"Accuracy: weeks {[w['week'] for w in block['weeks']]}, season to date {'yes' if block['season_to_date'] else 'not yet'}"
