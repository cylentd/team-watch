"""LIVE_SS3: Start/Sit v3 (leaf `matchups`), from ff-jarvis's `startsit_v3` block (METHODOLOGY 12.75).

SMASH, bold START and bold SIT, from our own projections alone (David, 2026-10-04: "SMASH, START,
SIT for only those we have confidence in. No coin flips."). FantasyPros and Pitcher List are never an
input: they appear only as a for-fun line of the record. The page computes nothing; this cut puts the
rows in the order the view draws them and fills every field the JS reads, so a producer that is
missing a field (a first week with no graded record, a reason with no kind) cannot blank the page.

A missing block is the empty block: no rows, a zero record. The view then says no calls are posted.
Self-contained like the other cuts: the loaded block and slugify come in as arguments.
"""

POS = ("QB", "RB", "WR", "TE")
SINCE = 5          # the first graded week (12.75), shown when the producer says nothing else
CALLS = ("START", "SIT")
KINDS = ("smash", "start", "sit")


def _count(c):
    c = c or {}
    return {k: int(c.get(k) or 0) for k in ("hit", "miss", "void")}


def _reason(r):
    """A v2 reason as ff-jarvis writes it today, {k, text}; also {kind, text_key} and {k, t}."""
    text = r.get("text") or r.get("t") or r.get("text_key") or ""
    return {"k": r.get("k") or r.get("kind") or "", "t": text}


def _who(r, slugify):
    return {"slug": r.get("slug") or slugify(r["name"]), "name": r["name"], "pos": r.get("pos"),
            "team": r.get("team"), "opp": r.get("opp"), "home": bool(r.get("home")),
            "kick": r.get("kick"), "rank": r.get("rank"), "avg_rank": r.get("avg_rank"), "pts": r.get("pts")}


def _smash(r, slugify):
    ln = r.get("line")
    return {**_who(r, slugify),
            "line": {"stat": ln["stat"], "value": ln["value"]} if ln and ln.get("value") is not None else None,
            "td_price": r.get("td_price")}


def _take(r, slugify):
    return {**_who(r, slugify), "call": str(r.get("call") or "").upper(), "line_pts": r.get("line_pts"),
            "margin_spots": r.get("margin_spots") or 0,
            "reasons": [_reason(x) for x in r.get("reasons") or []]}


def _week(w):
    return {"week": w.get("week"), **{k: {"hit": int((w.get(k) or {}).get("hit") or 0),
                                           "miss": int((w.get(k) or {}).get("miss") or 0)} for k in KINDS}}


def _record(rec, slugify):
    rec = rec or {}
    fun = rec.get("fun") or {}
    return {"since_week": rec.get("since_week") or SINCE,
            **{k: _count(rec.get(k)) for k in KINDS},
            "weeks": [_week(w) for w in rec.get("weeks") or []],
            "fun": {k: {"hit": int((fun.get(k) or {}).get("hit") or 0), "miss": int((fun.get(k) or {}).get("miss") or 0)}
                    for k in ("fantasypros", "pitcherlist")},
            "last_week": [{"slug": r.get("slug") or slugify(r["name"]), "name": r["name"], "pos": r.get("pos"),
                           "call": str(r.get("call") or "").upper(), "result": r.get("result"), "finish": r.get("finish")}
                          for r in rec.get("last_week") or []]}


def live_ss3(block, slugify, week=None):
    """The block the page reads. Always a dict with every key; None or {} reads as an empty week.

    `week` is the page week (LIVE_SCHEDULE.week). A block written for another week (this week's calls
    are not out yet, 2026-10-05: the site turns at the Monday-night final, ff-jarvis posts the next
    week's calls later) keeps its record but loses its SMASH and bold calls, so the view says no calls
    are posted rather than showing last week's under this week's title. No week passed: not judged."""
    block = block or {}
    stale = week is not None and block.get("week") is not None and block["week"] != week
    pos = {p: i for i, p in enumerate(POS)}
    smash = [] if stale else sorted((_smash(r, slugify) for r in block.get("smash") or []),
                                    key=lambda r: (pos.get(r["pos"], 9), r["rank"] or 0))
    takes = [] if stale else sorted((_take(r, slugify) for r in block.get("takes") or []
                                     if str(r.get("call")).upper() in CALLS),
                                    key=lambda r: (CALLS.index(r["call"]), -r["margin_spots"]))
    return {"week": block.get("week"), "season": block.get("season"), "smash": smash, "takes": takes,
            "record": _record(block.get("record"), slugify)}


def report(b):
    n = {c: sum(r["call"] == c for r in b["takes"]) for c in CALLS}
    rec = b["record"]
    graded = bool(rec["weeks"]) or any(sum(rec[k].values()) for k in KINDS)
    if b["week"] is None:
        return "Start/Sit v3: no startsit_v3 block, so the view says no calls are posted"
    return (f"Start/Sit v3: week {b['week']}, {len(b['smash'])} SMASH, {n['START']} START, {n['SIT']} SIT, "
            + (f"record since week {rec['since_week']} ({len(rec['weeks'])} weeks graded)" if graded
               else f"no week graded yet (counts from week {rec['since_week']})"))


def problems(obj):
    """Missing fields of a LIVE_SS3 as `LIVE_SS3.record.smash.hit`, for contract.py (a record's nested
    counts are beyond its one-level row specs)."""
    rec, miss = obj.get("record") or {}, []
    for k in KINDS:
        miss += [f"LIVE_SS3.record.{k}.{c}" for c in ("hit", "miss", "void") if c not in (rec.get(k) or {})]
    for k in ("fantasypros", "pitcherlist"):
        miss += [f"LIVE_SS3.record.fun.{k}.{c}" for c in ("hit", "miss") if c not in ((rec.get("fun") or {}).get(k) or {})]
    return miss
