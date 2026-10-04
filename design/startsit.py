"""LIVE_STARTSIT: the Takes view (Players > Takes, leaf `matchups`), from three ff-jarvis files.

- `startsit_calls.json` (model.season.startsit_calls): per position our START calls outside the
  obvious starters and our SIT calls on players usually started, each with its signed reasons.
  The page lists them across positions as one list, higher and lower than the experts. The page shows exactly what ff-jarvis froze, so the view and the graded record agree.
- `pl_startsit.json` (model.clients.pitcherlist): Pitcher List's six calls, the benchmark. Kept only
  when it is the same week as ours; last week's column is not this week's.
- `grades/<season>-w<week>.json` (model.season.grade): `startsit_record`, the season so far, from
  the newest graded week that has one.

- `startsit_review.json` (model.season.startsit_review, from week 4): Claude's read of the newest
  graded v2 week, shown under that week's takes.

Amendment 2 (2026-09-29): each take has a `tier`; a take type the pause rule has paused leaves the
list for `shadow`, and `rule` says which and why; the record gains `splits`.

Self-contained like the other cuts: the loaded files and slugify come in as arguments.
"""

POS = ("QB", "RB", "WR", "TE")


def _home(r):
    """ff-jarvis's `game` is "AWAY @ HOME" in the props feed's raw codes (JAC, not JAX), so the
    team is placed by whichever side is not its opponent."""
    away, _, home = (r.get("game") or "").partition(" @ ")
    return away.strip() == r.get("opp") or home.strip() == r.get("team")


def _call(r, tag, slugify):
    # gap: ff-jarvis's gap_n, the rank gap in units of the position's own threshold, so one list
    # can order takes across positions. Null on calls written before 2026-09-29.
    return {"tag": tag, "n": r["name"], "slug": slugify(r["name"]), "pos": r["pos"], "team": r["team"],
            "opp": r["opp"], "home": _home(r), "pts": r["pts"], "rank": r["rank"], "ecr": r.get("ecr"),
            "gap": r.get("gap_n"),
            "own": r.get("own"), "why": [{"k": w[0], "t": w[2]} for w in r.get("why") or []],
            "but": [w[2] for w in r.get("but") or []],
            # v2 (METHODOLOGY 12.64 + Amendment 1, from week 4): the reasons pointing the same way
            # (role, mx, script, door); a take with none is a gut call, graded all the same.
            "reasons": [{"k": w["k"], "t": w["text"]} for w in r.get("reasons") or []],
            "backed": bool(r.get("reasons")),
            # Amendment 2 (2026-09-29): lean / solid / strong from gap_n. Null from an older producer.
            "tier": r.get("tier")}


def _pl(c, slugify):
    return {"call": c["call"].lower(), "pos": c["pos"], "n": c["player"], "slug": slugify(c["player"]),
            "team": c["team"], "opp": c["opp"], "home": bool(c.get("home")), "rationale": c.get("rationale") or ""}


def _record(grade, since):
    """`since`: the first week v2 counts, from the calls file's own rules (ff-jarvis startsit_v2.SINCE)."""
    rec = (grade or {}).get("startsit_record")
    if not rec or not rec.get("weeks"):
        return None
    side = lambda s: {"n": s.get("n", 0), "score": s.get("score"), "score_no_dnp": s.get("score_no_dnp")}
    # FantasyPros (2026-09-29) is graded on our takes: each one is a disagreement, so FantasyPros made
    # the other call. Null in a grade file written before ff-jarvis graded that side.
    fp = rec.get("fantasypros")
    v2 = _v2(rec)
    # The record restarts at week 4 (David, 2026-09-30): no strip until a v2 week is graded, and Pitcher
    # List over the same weeks (ff-jarvis `pitcherlist_v2`). Weeks 1-3 stay in the grade files.
    if v2 is None:
        return None
    pl = rec.get("pitcherlist_v2")
    return {"through": grade["week"], "weeks": [w for w in rec["weeks"] if w >= since],
            "ours": side(rec.get("ours") or {}),
            "pl": side(pl) if pl and pl.get("n") else None, "fp": side(fp) if fp else None, "v2": v2,
            "splits": _splits(rec)}


SPLITS = (("by_call", ("START", "SIT")), ("by_pos", POS), ("by_tier", ("lean", "solid", "strong")))


def _splits(rec):
    """The record split by call, position and tier (Amendment 2), ours beside FantasyPros on the same
    takes: v2's clean set, the population of the bars above them. None from a grade file written
    before the splits."""
    s = (rec.get("splits") or {}).get("v2")
    if not s:
        return None
    cell = lambda c: {k: ((c or {}).get("clean") or {}).get(k) for k in ("n", "ours", "fp")}
    return {"set": "v2",
            **{grp: [{"k": k, **cell((s.get(grp) or {}).get(k))} for k in keys] for grp, keys in SPLITS}}


def _rule(calls):
    """The pause rule's state as the calls were written (Amendment 2): the take types it has paused,
    each with the numbers that paused it (the history entry; the type's own n restarts with its shadow
    window). None from a producer written before the rule."""
    rule = (calls.get("v2") or {}).get("rule")
    if not rule:
        return None
    paused = []
    for t in rule.get("types") or []:
        if t.get("status") != "paused":
            continue
        ev = next((h for h in reversed(t.get("history") or []) if h.get("status") == "paused"), t)
        call, _, pos = t["type"].partition("-")
        paused.append({"type": t["type"], "tag": call.lower(), "pos": pos, "n": ev.get("n"),
                       "ours": ev.get("ours"), "fp": ev.get("fp"), "since": t.get("since_week")})
    return {"min_n": (rule.get("rules") or {}).get("min_n"), "paused": paused}


def _read(doc, grade):
    """Claude's weekly review (startsit_review), kept only when it reads the graded week the page
    shows: a review of an older week under this week's takes would describe the wrong list."""
    if not doc or not doc.get("note") or (doc.get("season"), doc.get("week")) != (grade.get("season"), grade["week"]):
        return None
    def watch(w):
        call, _, pos = w["type"].partition("-")
        c = w.get("clean") or {}
        return {"type": w["type"], "tag": call.lower(), "pos": pos, "text": w.get("text") or "",
                "status": w.get("status"), "n": c.get("n"), "ours": c.get("ours"), "fp": c.get("fp")}
    return {"note": doc["note"], "patterns": list(doc.get("patterns") or []),
            "watch": [watch(w) for w in doc.get("watch") or []], "model": doc.get("model")}


def _v2(rec):
    """The v2 record (week 4 on), or None until a v2 week is graded. `clean` leaves out the takes an
    injury decided (ruled out after the call, or left early and on the injury report), David's
    'that's just bad luck'; `backed` and `gut` split the takes by whether a reason came with them."""
    ours, fp = rec.get("ours_v2") or {}, rec.get("fantasypros_v2") or {}
    if not ours.get("n"):
        return None
    ns = lambda s: {"n": (s or {}).get("n", 0), "score": (s or {}).get("score")}
    causes = ours.get("causes") or {}
    return {"ours": {**ns(ours), "clean": ns(ours.get("clean")), "backed": ns(ours.get("backed")),
                     "gut": ns(ours.get("gut")), "causes": {k: causes.get(k, 0) for k in ("injury", "role", "td", "read")}},
            "fp": {**ns(fp), "clean": ns(fp.get("clean"))}}


def _review(grade, slugify, doc=None):
    """Last graded week's v2 takes, each with its result and, for a miss, why: the page's 'learn
    from it' list, and Claude's read of it (`read`, null until written). None before a v2 week is
    graded."""
    rows = (((grade or {}).get("startsit") or {}).get("ours_v2") or {}).get("calls") or []
    if not rows:
        return None
    return {"week": grade["week"], "read": _read(doc, grade), "rows": [
        {"n": r["name"], "slug": slugify(r["name"]), "pos": r["pos"], "team": r.get("team"),
         "call": (r.get("call") or "").lower(), "score": r.get("score"), "cause": r.get("cause"),
         "note": r.get("cause_note"), "backed": bool(r.get("backed")), "finish": r.get("finish")}
        for r in rows]}


def live_startsit(calls, pl, grade, slugify, review=None):
    """None when ff-jarvis has written no calls: the view then says so instead of guessing.
    `review` is Claude's weekly review (startsit_review.json), None before one is written."""
    if not calls or "positions" not in calls:
        return None
    rows, shadow, best = [], [], []
    for pos in POS:
        d = calls["positions"].get(pos) or {}
        # The best spot is not a take (not graded): the starter with the softest matchup at his
        # position, the Digest's Matchups card. Back on Start / Sit's board since 2026-10-03.
        if d.get("best"):
            b = d["best"]
            best.append({"n": b["name"], "slug": slugify(b["name"]), "pos": b["pos"], "team": b["team"],
                         "opp": b["opp"], "home": _home(b), "pts": b["pts"],
                         "why": [w[2] for w in b.get("why") or []]})
        # A row of a paused take type (Amendment 2) is a shadow call: still graded, not a take.
        for tag in ("start", "sit"):
            for r in d.get(tag) or []:
                (shadow if r.get("paused") else rows).append(_call(r, tag, slugify))
    same_week = pl and pl.get("week") == calls["week"]
    # The week of the FantasyPros ranks the calls were measured against. Behind `week` (Tuesday,
    # before Wednesday's 8 AM fetch) there is nobody to disagree with, and the view says so.
    experts = (calls.get("inputs") or {}).get("expert_week")
    since = (((calls.get("v2") or {}).get("rules") or {}).get("since") or {}).get("week") or 0
    return {"week": calls["week"], "experts_week": experts, "generated": calls.get("generated"), "calls": rows,
            "shadow": shadow, "best": best, "rule": _rule(calls),
            "pl": [_pl(c, slugify) for c in pl["calls"]] if same_week else [],
            "article": pl.get("article") if same_week else None, "record": _record(grade, since),
            "review": _review(grade, slugify, review)}


def report(block):
    if not block:
        return "Matchups: no startsit_calls.json, so the view says so"
    n = {t: sum(r["tag"] == t for r in block["calls"]) for t in ("start", "sit")}
    rec = block["record"]
    paused = ", ".join(p["type"] for p in (block["rule"] or {}).get("paused") or [])
    return (f"Matchups: week {block['week']}, {n['start']} start, {n['sit']} sit, "
            + (f"{len(block['shadow'])} shadow (paused: {paused}), " if paused else "")
            + f"Pitcher List {len(block['pl'])}, "
            + (f"record through week {rec['through']}" if rec else "no graded week yet"))
