"""The Yahoo League view's back page (2026-09-27, storyboard https://claude.ai/artifact/LBKkjFWgJ1rLZGrKtQ1Fn3):
what LIVE_LEAGUE_YAHOO carries on top of league_recap's recap and history.

- each week: Claude's headline and dek, and per game its dig, stamp, box score and both records after
  that week (ff-jarvis model.season.league_roast and model.clients.yahoo_box);
- the week's bench award: the biggest same-position bench mistake, from the box (ff-jarvis decides
  what a mistake is, `left`; nothing here re-derives it);
- per pairing, every meeting as [season, week, margin, playoff] for the tale of the tape;
- per team, the all-time record, title seasons and last-place seasons;
- the record book: a Hall of Fame and a Hall of Shame, fixed lists in a fixed order.

ESPN's league is David's work league and keeps the plain view, so none of this is built for it.
Everything here is results the league already knows (memory feedback_no_edge_for_leaguemates).
"""


def _rec(r):
    return f"{r[0]}–{r[1]}" + (f"–{r[2]}" if r[2] else "")


def slim_box(b):
    """One game's box as the page draws it: [slot, left name, left pts, right name, right pts] per
    starter, both projected totals, and each side's bench mistake or None."""
    side = lambda p: (p["name"], p["pts"]) if p else (None, None)
    left = b.get("left") or {}
    mistake = lambda m: m and {"benched": m["benched"], "bp": m["benched_pts"], "started": m["started"],
                               "sp": m["started_pts"], "lost": m["lost"]}
    return {"slots": [[s["slot"], *side(s["a"]), *side(s["b"])] for s in b["slots"]],
            "proj": [(b.get("proj") or {}).get("a"), (b.get("proj") or {}).get("b")],
            "left": [mistake(left.get("a")), mistake(left.get("b"))]}


def enrich_weeks(weeks, box, recap):
    """league_recap.weeks() rows (every decided week, oldest first), each game with both records after
    that week, its dig, stamp and box, each week with its headline and dek (None when the roast skipped
    it) and the bench award."""
    boxes = {(int(w), g["home"], g["away"]): g for w, gs in ((box or {}).get("weeks") or {}).items() for g in gs}
    words = (recap or {}).get("weeks") or {}
    tally = {}
    for wk in weeks:
        for g in wk["games"]:
            for tid, res in ((g["a"], {"home": 0, "away": 1}.get(g["win"], 2)), (g["b"], {"away": 0, "home": 1}.get(g["win"], 2))):
                tally.setdefault(tid, [0, 0, 0])[res] += 1
        r = words.get(str(wk["week"])) or {}
        wk["head"], wk["dek"] = r.get("headline"), r.get("dek")
        best = None
        for g in wk["games"]:
            said = (r.get("games") or {}).get(f"{g['a']}-{g['b']}") or {}
            b = boxes.get((wk["week"], g["a"], g["b"]))
            g.update(ar=_rec(tally[g["a"]]), br=_rec(tally[g["b"]]), dig=said.get("dig"), stamp=said.get("stamp"),
                     box=slim_box(b) if b else None)
            for tid, m in zip((g["a"], g["b"]), g["box"]["left"] if g["box"] else ()):
                if m and (not best or m["lost"] > best["v"]):
                    best = {"id": tid, "v": m["lost"], "name": m["benched"]}
        if best:
            wk["awards"]["bench"] = best
    return weeks


def add_meets(h2h, games):
    """h2h[a][b]["m"]: every meeting of two of today's teams, oldest first, as [season, week, a's margin,
    playoff 1/0]. Consolation games count as meetings but not as playoffs."""
    for g in games:
        for me, them, mine, theirs in ((g["home"], g["away"], g["hp"], g["ap"]), (g["away"], g["home"], g["ap"], g["hp"])):
            row = h2h.get(str(me), {}).get(str(them))
            if row is not None:
                row.setdefault("m", []).append([g["y"], g["week"], round(mine - theirs, 2), int(g.get("tier") == "playoff")])
    return h2h


def last_places(games, season):
    """{season: the manager id with the worst finished regular season} for every past season: fewest
    wins net of losses, then fewest points."""
    by = {}
    for g in games:
        if g["y"] >= season or g.get("tier") is not None:
            continue
        for tid, pts, won in ((g["home"], g["hp"], g["winner"] == "home"), (g["away"], g["ap"], g["winner"] == "away")):
            r = by.setdefault(g["y"], {}).setdefault(tid, [0, 0.0])
            r[0] += 1 if won else -1
            r[1] += pts
    return {y: min(t, key=lambda tid: (t[tid][0], t[tid][1])) for y, t in by.items()}


def add_tape(teams, games, champs, lasts):
    """Each of today's teams gets `all` [w, l, t] over every decided game, `titles` and `lasts` (seasons)."""
    for tm in teams:
        r = [0, 0, 0]
        for g in games:
            for me, mine, theirs in ((g["home"], g["hp"], g["ap"]), (g["away"], g["ap"], g["hp"])):
                if me == tm["id"]:
                    r[0 if mine > theirs else 1 if mine < theirs else 2] += 1
        tm.update(all=r, titles=sorted(c["y"] for c in champs if c["id"] == tm["id"]),
                  lasts=sorted(y for y, tid in lasts.items() if tid == tm["id"]))
    return teams


def _streak(games, want):
    """Longest run inside one regular season of wins (want True) or losses: (id, length, season)."""
    best, run = (None, 0, None), {}
    for g in games:
        if g.get("tier") is not None:
            continue
        for tid, won in ((g["home"], g["winner"] == "home"), (g["away"], g["winner"] == "away")):
            key = (g["y"], tid)
            run[key] = run.get(key, 0) + 1 if won == want else 0
            if run[key] > best[1]:
                best = (tid, run[key], g["y"])
    return best


def book(facts, games, teams, lasts):
    """{fame, shame}: league_recap.facts() split, plus the records only the back page shows."""
    by = {f["k"]: f for f in facts}
    fame = [by[k] for k in ("high", "blow", "streak", "titles", "pf") if k in by]
    shame = [by[k] for k in ("low",) if k in by]
    ids = {t["id"] for t in teams}
    rec = [t for t in teams if sum(t["all"]) >= 20]
    pct = lambda t: (t["all"][0] + t["all"][2] / 2) / sum(t["all"])
    if rec:
        hi, lo = max(rec, key=pct), min(rec, key=pct)
        fame.append({"k": "bestrec", "id": hi["id"], "w": hi["all"][0], "l": hi["all"][1]})
    # (game, winner id, winner pts, loser id, loser pts) for every game somebody won.
    won = [(g, g["home"], g["hp"], g["away"], g["ap"]) if g["winner"] == "home" else (g, g["away"], g["ap"], g["home"], g["hp"])
           for g in games if g["winner"] in ("home", "away")]
    if won:
        g, _, _, loser, pts = max(won, key=lambda x: x[4])
        shame.append({"k": "robbed", "id": loser, "v": pts, "y": g["y"], "wk": g["week"]})
        g, winner, pts, _, _ = min(won, key=lambda x: x[2])
        shame.append({"k": "stole", "id": winner, "v": pts, "y": g["y"], "wk": g["week"]})
    tid, n, y = _streak(games, False)
    if n >= 3:
        shame.append({"k": "lstreak", "id": tid, "n": n, "y": y})
    if rec:
        shame.append({"k": "worstrec", "id": lo["id"], "w": lo["all"][0], "l": lo["all"][1]})
    count = {}
    for tid in lasts.values():
        if tid in ids:
            count[tid] = count.get(tid, 0) + 1
    if count and max(count.values()) >= 2:
        most = max(count.values())
        shame.append({"k": "lasts", "ids": sorted(i for i, c in count.items() if c == most), "n": most})
    return {"fame": fame, "shame": shame}
