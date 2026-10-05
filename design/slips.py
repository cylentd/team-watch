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


def claude_props(raw):
    """LIVE_CLAUDE_PROPS: Claude's calls (ff-jarvis claude_props.json, 2026-10-05) cut to what the page
    matches on: {week, asof, calls: {slug: [{mkt, line, side, why}]}}. The page finds a call by player,
    market and the exact line value shown, so a call carries no confidence, model side or chance. A call
    with no name, market or numeric line is dropped. None without the file or without a usable call."""
    calls = {}
    for c in (raw or {}).get("calls") or []:
        who = c.get("name") or c.get("key")
        if not who or not c.get("market") or isinstance(c.get("line"), bool) or not isinstance(c.get("line"), (int, float)):
            continue
        calls.setdefault(slugify(who), []).append(
            {"mkt": c["market"], "line": c["line"], "side": c.get("side"), "why": str(c.get("why") or "")[:120]})
    return {"week": raw.get("week"), "asof": raw.get("asof"), "calls": calls} if calls else None


def problems_claude(obj):
    """Each call has a known side and a why; an unknown side word fails the build, as a tier word does."""
    return [f"LIVE_CLAUDE_PROPS.calls[{s!r}][{i}].{f}" for s, rows in ((obj or {}).get("calls") or {}).items()
            for i, c in enumerate(rows) for f, ok in (("side", c.get("side") in SIDES), ("why", "why" in c)) if not ok]


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


def claude_record(raw):
    """LIVE_CLAUDE_RECORD (2026-10-05): how Claude's frozen prop calls have done against the model's on the same
    lines (ff-jarvis claude_props.json `record`, METHODOLOGY 12.84), cut to the second row of the record strip.
    Only the record is injected, never the calls: {season, week, through_week, agree, alone}. `week` is the
    file's week (the one Claude is calling now). `agree` is Claude's {w, l, push, void} where he took the model's
    side, `alone` his where he took the other (`disagree.claude`); both and `through_week` are null until a game is
    graded. None without the file (or without its week), and the page draws no Claude row."""
    if not isinstance(raw, dict) or raw.get("week") is None:
        return None
    rec = raw.get("record") or {}
    weeks = rec.get("weeks") or []

    def tally(t):
        return {k: t.get(k, 0) for k in ("w", "l", "push", "void")} if isinstance(t, dict) else None
    return {"season": raw.get("season"), "week": raw["week"], "through_week": weeks[-1].get("week") if weeks else None,
            "agree": tally(rec.get("agree")), "alone": tally((rec.get("disagree") or {}).get("claude"))}


def problems_claude_record(obj):
    """A tally that is there has its wins and losses, and the two come together."""
    out = [f"LIVE_CLAUDE_RECORD.{k}.{f}" for k in ("agree", "alone") if (obj or {}).get(k) for f in ("w", "l") if f not in obj[k]]
    if ((obj or {}).get("agree") is None) != ((obj or {}).get("alone") is None):
        out.append("LIVE_CLAUDE_RECORD.agree and .alone are both there or both null")
    return out


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
