"""LIVE_STARTSIT: the Takes view (Players > Takes, leaf `matchups`), from three ff-jarvis files.

- `startsit_calls.json` (model.season.startsit_calls): per position our START calls outside the
  obvious starters and our SIT calls on players usually started, each with its signed reasons.
  The page lists them across positions as one list, higher and lower than the experts. The page shows exactly what ff-jarvis froze, so the view and the graded record agree.
- `pl_startsit.json` (model.clients.pitcherlist): Pitcher List's six calls, the benchmark. Kept only
  when it is the same week as ours; last week's column is not this week's.
- `grades/<season>-w<week>.json` (model.season.grade): `startsit_record`, the season so far, from
  the newest graded week that has one.

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
            "backed": bool(r.get("reasons"))}


def _pl(c, slugify):
    return {"call": c["call"].lower(), "pos": c["pos"], "n": c["player"], "slug": slugify(c["player"]),
            "team": c["team"], "opp": c["opp"], "home": bool(c.get("home")), "rationale": c.get("rationale") or ""}


def _record(grade):
    rec = (grade or {}).get("startsit_record")
    if not rec or not rec.get("weeks"):
        return None
    side = lambda s: {"n": s.get("n", 0), "score": s.get("score"), "score_no_dnp": s.get("score_no_dnp")}
    # FantasyPros (2026-09-29) is graded on our takes: each one is a disagreement, so FantasyPros made
    # the other call. Null in a grade file written before ff-jarvis graded that side.
    fp = rec.get("fantasypros")
    return {"through": grade["week"], "weeks": rec["weeks"], "ours": side(rec.get("ours") or {}),
            "pl": side(rec.get("pitcherlist") or {}), "fp": side(fp) if fp else None, "v2": _v2(rec)}


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


def _review(grade, slugify):
    """Last graded week's v2 takes, each with its result and, for a miss, why: the page's 'learn
    from it' list. None before a v2 week is graded."""
    rows = (((grade or {}).get("startsit") or {}).get("ours_v2") or {}).get("calls") or []
    if not rows:
        return None
    return {"week": grade["week"], "rows": [
        {"n": r["name"], "slug": slugify(r["name"]), "pos": r["pos"], "team": r.get("team"),
         "call": (r.get("call") or "").lower(), "score": r.get("score"), "cause": r.get("cause"),
         "note": r.get("cause_note"), "backed": bool(r.get("backed")), "finish": r.get("finish")}
        for r in rows]}


def live_startsit(calls, pl, grade, slugify):
    """None when ff-jarvis has written no calls: the view then says so instead of guessing."""
    if not calls or "positions" not in calls:
        return None
    rows = []
    for pos in POS:
        d = calls["positions"].get(pos) or {}
        # The best spot (d["best"]) is not a take: the matchup is a Ranks tag since 2026-09-29.
        rows += [_call(r, "start", slugify) for r in d.get("start") or []]
        rows += [_call(r, "sit", slugify) for r in d.get("sit") or []]
    same_week = pl and pl.get("week") == calls["week"]
    # The week of the FantasyPros ranks the calls were measured against. Behind `week` (Tuesday,
    # before Wednesday's 8 AM fetch) there is nobody to disagree with, and the view says so.
    experts = (calls.get("inputs") or {}).get("expert_week")
    return {"week": calls["week"], "experts_week": experts, "generated": calls.get("generated"), "calls": rows,
            "pl": [_pl(c, slugify) for c in pl["calls"]] if same_week else [],
            "article": pl.get("article") if same_week else None, "record": _record(grade),
            "review": _review(grade, slugify)}


def report(block):
    if not block:
        return "Matchups: no startsit_calls.json, so the view says so"
    n = {t: sum(r["tag"] == t for r in block["calls"]) for t in ("start", "sit")}
    rec = block["record"]
    return (f"Matchups: week {block['week']}, {n['start']} start, {n['sit']} sit, Pitcher List {len(block['pl'])}, "
            + (f"record through week {rec['through']}" if rec else "no graded week yet"))
