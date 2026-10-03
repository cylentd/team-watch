"""The Slips research board's data (2026-10-03), cut out of build.py to keep it in budget: LIVE_REASONS
from ff-jarvis's slip_reasons.json, and the markets the model does not price (Longest reception).
tests/test_slip_reasons.py pins both."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "api"))
from _espn import slugify  # noqa: E402  (the one build.py names its rows with)

# Longest reception is shown with its line and his own mean longest catch, and no P(over): no pick,
# confidence, edge or stale check, and never a "no role" tag.
UNPRICED = {"LONG"}


def null_prices(p):
    """A row of an unpriced market: every price key is there and null, on the row and on each book,
    so a reader tests a value and never a missing key."""
    p.update(model=None, edge=None, pick=None, conf=None)
    for x in p["books"].values():
        x.update(model=None, pick=None, conf=None)


def carry_mean(p, r, team_fix):
    """What ff-jarvis's model row adds to an unpriced line: his mean (last 8 games) and the defense."""
    p["mu"], p["games"] = r.get("mu"), r.get("games")
    if r.get("opp_f"):
        p["opp"], p["opp_f"] = team_fix.get(r.get("opp"), r.get("opp")), r["opp_f"]


def live_reasons(raw, props):
    """LIVE_REASONS: {slug: {why, work, tags}}, ff-jarvis's keys (already team-watch slugs, pinned on its
    side) cut to the players with a line on this page. `{}` without the file, so the board draws every
    row with no why instead of failing."""
    # A player with no headshot has no `slug` on his row; the page names him by slugify(name) then.
    have = {p.get("slug") or slugify(p["n"]) for p in (props or {}).get("props", [])}
    return {s: r for s, r in ((raw or {}).get("players") or {}).items() if s in have}


def report(reasons):
    if not reasons:
        return "Reasons: none (no slip_reasons.json, or no player in it has a line), the Slips board draws without a why"
    return f"Reasons: {len(reasons)} players with a line this week"
