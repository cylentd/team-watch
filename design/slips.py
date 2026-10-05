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


TIERS = ("none", "slight", "confident", "very")
SIDES = ("higher", "lower")
VACATED_KEYS = ("name", "last", "status", "work")


def priced(x, r):
    """Put ff-jarvis's model row `r` on a PROPS row or one of its books `x`: the chance in percent, and,
    when the producer sent them (prop-tiers, 2026-10-05), the model's `side` and `tier` for that exact
    line. The tier's cutoffs live only in ff-jarvis; the page never computes one from the chance. A TD,
    an unpriced or an Out row carries neither (null), so the key is left off and the page draws no tier."""
    x["model"] = round(r["p_over"] * 100)
    if r.get("tier") is not None:
        x["tier"], x["side"] = r["tier"], r.get("side")


def props_record(raw):
    """LIVE_PROPS_RECORD: the graded record of each tier (ff-jarvis props_record.json, 2026-10-05), cut to
    what the strip reads: {season, through_week, tiers: {slight, confident, very: {w, l, push, void}}}.
    None without the file or without a graded tier."""
    tiers = (raw or {}).get("tiers")
    if not isinstance(tiers, dict) or not all(isinstance(tiers.get(k), dict) for k in TIERS[1:]):
        return None
    return {"season": raw.get("season"), "through_week": raw.get("through_week"), "tiers": {k: tiers[k] for k in TIERS[1:]}}


def problems_props(obj):
    """Optional `tier`/`side` on a PROPS row or its books: when sent, a known word."""
    out = []
    for i, p in enumerate((obj or {}).get("props") or []):
        for where, x in [("", p)] + [(f".books[{b!r}]", v) for b, v in (p.get("books") or {}).items()]:
            if x.get("tier") is not None and x["tier"] not in TIERS:
                out.append(f"LIVE_PROPS.props[{i}]{where}.tier")
            if x.get("side") is not None and x["side"] not in SIDES:
                out.append(f"LIVE_PROPS.props[{i}]{where}.side")
    return out


def problems_reasons(obj):
    """Optional `vacated` on a reason: a list, each teammate with all four keys."""
    out = []
    for slug, r in (obj or {}).items():
        v = r.get("vacated") if isinstance(r, dict) else None
        if v is None:
            continue
        if not isinstance(v, list):
            out.append(f"LIVE_REASONS[{slug!r}].vacated")
            continue
        out += [f"LIVE_REASONS[{slug!r}].vacated[{i}].{k}" for i, e in enumerate(v) for k in VACATED_KEYS if k not in e]
    return out


def problems_record(obj):
    """Each tier of the record has its wins and losses."""
    return [f"LIVE_PROPS_RECORD.tiers[{k!r}].{f}" for k in TIERS[1:] for f in ("w", "l") if f not in (obj or {}).get("tiers", {}).get(k, {})]


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
