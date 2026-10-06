"""The Yahoo League view's back page (2026-09-27, storyboard https://claude.ai/artifact/LBKkjFWgJ1rLZGrKtQ1Fn3):
what LIVE_LEAGUE_YAHOO carries on top of league_recap's recap and history.

- each week: Claude's headline and dek, and per game its punchline, 1-3 facts (`beats`), stamp, box score and both records after
  that week (ff-jarvis model.season.league_roast and model.clients.yahoo_box);
- the week's bench award: the biggest same-position bench mistake, from the box (ff-jarvis decides
  what a mistake is, `left`; nothing here re-derives it);
- per pairing, every meeting as [season, week, margin, playoff] for the tale of the tape;
- per team, the all-time record, title seasons and last-place seasons;
- the record book: a Hall of Fame and a Hall of Shame, fixed lists in a fixed order.

ESPN's league is David's work league and keeps the plain view, so none of this is built for it.
Everything here is results the league already knows (memory feedback_no_edge_for_leaguemates).
- private pairs (design/league_private.json): a pair's head-to-head leaves the page, and the series
  draws as a "classified" grudge card with both names withheld (a manager's ask, 2026-09-27).
"""
import json
import os


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


def blip_of(wk):
    """Blip's pose on every lead (2026-09-29, storyboard
    https://claude.ai/artifact/RKkFYVa7asD65uWfvLMVLU; on every lead since 2026-10-06, when the player headshot
    that replaced it went: the recap is the whole league's board, not one roster's), from the lead game's place
    in the week, first that fits:
    biggest margin and lowest score "ko", biggest margin "wince", lowest score "flatline", closest game
    "sweat", else "laugh"."""
    key = lambda g: f"{g['a']}-{g['b']}"
    margin = lambda g: abs(g["ap"] - g["bp"])
    games = wk["games"]
    big = key(max(games, key=margin))
    low = key(min(games, key=lambda g: min(g["ap"], g["bp"])))
    close = key(min(games, key=margin))
    lead = wk["lead"]
    if lead == big and lead == low:
        return "ko"
    return "wince" if lead == big else "flatline" if lead == low else "sweat" if lead == close else "laugh"


def _lead_key(wk, said):
    """The roast's lead game, or the week's biggest margin when the roast named none (weeks written
    before 2026-09-27) or skipped the week."""
    keys = {f"{g['a']}-{g['b']}" for g in wk["games"]}
    if said in keys:
        return said
    g = max(wk["games"], key=lambda g: abs(g["ap"] - g["bp"]))
    return f"{g['a']}-{g['b']}"


def enrich_weeks(weeks, box, recap):
    """league_recap.weeks() rows (every decided week, oldest first), each game with both records after
    that week, its punchline, facts, stamp and box, each week with its headline and dek (None when the roast skipped
    it), the bench award, the lead game's key and Blip's pose for it."""
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
            g.update(ar=_rec(tally[g["a"]]), br=_rec(tally[g["b"]]), punch=said.get("punch"),
                     beats=said.get("beats") or [], stamp=said.get("stamp"), box=slim_box(b) if b else None)
            for tid, m in zip((g["a"], g["b"]), g["box"]["left"] if g["box"] else ()):
                if m and (not best or m["lost"] > best["v"]):
                    best = {"id": tid, "v": m["lost"], "name": m["benched"], "bp": m["bp"], "started": m["started"], "sp": m["sp"]}
        if best:
            wk["awards"]["bench"] = best
        wk["lead"] = _lead_key(wk, r.get("lead"))
        wk["blip"] = blip_of(wk)
    return weeks


LUCK_TAG = 1.0   # wins of luck, either way, that earn a Lucky or Snakebit tag


def add_standings(weeks, ids):
    """Each week row gets `table`: every team after that week in standings order (wins, then points),
    as {id, w, l, t, pf, pfr (points rank), move (places up since the week before; 0 in week 1), luck, tag}.
    `luck` is real wins minus the wins the team's points earned: each week a score earns the share of the
    other teams it outscored (ties half), so a week's top score earns a whole win and its lowest none. `tag`
    is "lucky" at LUCK_TAG wins or more, "robbed" at LUCK_TAG or more short (Luck so far, 2026-10-06; it was
    the record's place against the points rank, which tiebreaks by points left at 0 for 10 of 12 teams)."""
    tally = {i: [0, 0, 0, 0.0] for i in ids}
    earned = {i: 0.0 for i in ids}
    last = None
    for wk in weeks:
        scores = [(tid, pts) for g in wk["games"] for tid, pts in ((g["a"], g["ap"]), (g["b"], g["bp"])) if tid in tally]
        for tid, pts in scores:
            beat = sum(1 if pts > o else 0.5 if pts == o else 0 for t, o in scores if t != tid)
            earned[tid] += beat / max(len(scores) - 1, 1)
        for g in wk["games"]:
            res = {"home": (0, 1), "away": (1, 0)}.get(g["win"], (2, 2))
            for tid, r, pts in ((g["a"], res[0], g["ap"]), (g["b"], res[1], g["bp"])):
                if tid in tally:
                    tally[tid][r] += 1
                    tally[tid][3] = round(tally[tid][3] + pts, 2)
        order = sorted(ids, key=lambda i: (-(tally[i][0] + tally[i][2] / 2), -tally[i][3]))
        by_pf = sorted(ids, key=lambda i: -tally[i][3])
        rows = []
        for n, i in enumerate(order, 1):
            pfr = by_pf.index(i) + 1
            luck = round(tally[i][0] + tally[i][2] / 2 - earned[i], 1) + 0.0   # + 0.0: never a -0.0
            rows.append({"id": i, "w": tally[i][0], "l": tally[i][1], "t": tally[i][2], "pf": tally[i][3], "pfr": pfr,
                         "move": (last.index(i) + 1 - n) if last else 0, "luck": luck,
                         "tag": "lucky" if luck >= LUCK_TAG else "robbed" if luck <= -LUCK_TAG else None})
        wk["table"] = rows
        last = order
    return weeks


def next_grudge(now, h2h):
    """This week's most lopsided series between two of today's teams, {a, b} with `a` the side that
    leads it, or None when no pairing has met 3 times: the league-wide grudge the recap leads with."""
    best = None
    for g in now:
        r = (h2h.get(str(g["a"])) or {}).get(str(g["b"]))
        if not r or r["w"] + r["l"] + r["t"] < 3:
            continue
        key = (abs(r["w"] - r["l"]), r["w"] + r["l"] + r["t"])
        if not best or key > best[0]:
            best = (key, {"a": g["a"], "b": g["b"]} if r["w"] >= r["l"] else {"a": g["b"], "b": g["a"]})
    return best[1] if best else None


PRIVATE = os.path.join(os.path.dirname(__file__), "league_private.json")


def private_pairs(path=PRIVATE):
    """[(a, b)]: the Yahoo pairs a manager asked to keep off the page (design/league_private.json)."""
    if not os.path.exists(path):
        return []
    return [(p["a"], p["b"]) for p in json.load(open(path, encoding="utf-8")).get("pairs", [])]


SKIP = os.path.join(os.path.dirname(__file__), "league_record_skip.json")


def record_skip(path=SKIP, former=1000):
    """Owner ids (league_recap's FORMER + N for "former-N") of managers who hold no record on Records
    (design/league_record_skip.json). David, 2026-09-27: a manager who gave up and left pollutes the
    book; he keeps only his last place (the spoon case reads Yahoo's final places, not this)."""
    if not os.path.exists(path):
        return frozenset()
    keys = [m["key"] for m in json.load(open(path, encoding="utf-8")).get("managers", [])]
    return frozenset(former + int(k.split("-")[1]) if k.startswith("former-") else int(k) for k in keys)


def withhold(h2h, pairs):
    """Take each private pair's head-to-head out of `h2h` (both ways), so its record never ships, and
    return the pairs [[a, b]]: Records draws the row with the record blacked out rather than drop it,
    because a missing row would say more than a blacked-out one. (Until 2026-09-27 the League page
    also drew the series as a "Classified grudge" card every week; David cut it as too obvious.)"""
    out = []
    for a, b in pairs:
        (h2h.get(str(a)) or {}).pop(str(b), None)
        (h2h.get(str(b)) or {}).pop(str(a), None)
        out.append([a, b])
    return out


MEET_KIND = {"playoff": 1, "consolation": 2}


def add_meets(h2h, games):
    """h2h[a][b]["m"]: every meeting of two of today's teams, oldest first, as [season, week, a's margin,
    kind]: MEET_KIND, 0 regular season, 1 playoff, 2 consolation. Every kind counts in the series; Records'
    sheet splits the record by kind (2026-09-27, David: Lateef and Theo's 16 read as a mistake until
    the 2 playoff games were visible). Until then the flag was playoff 1/0, consolation folded into 0."""
    for g in games:
        for me, them, mine, theirs in ((g["home"], g["away"], g["hp"], g["ap"]), (g["away"], g["home"], g["ap"], g["hp"])):
            row = h2h.get(str(me), {}).get(str(them))
            if row is not None:
                row.setdefault("m", []).append([g["y"], g["week"], round(mine - theirs, 2), MEET_KIND.get(g.get("tier"), 0)])
    return h2h


def last_places(games, season, finals=None):
    """{season: the manager id who finished last} for every past season. `finals` ({season: id}, Yahoo's
    own final place, which counts the consolation bracket) wins where it exists; a season without it
    falls back to the worst regular season: fewest wins net of losses, then fewest points. The two
    disagree (2019: the worst record was not last), so the fallback is only for a season Yahoo's
    standings could not be read for."""
    by = {}
    for g in games:
        if g["y"] >= season or g.get("tier") is not None:
            continue
        for tid, pts, won in ((g["home"], g["hp"], g["winner"] == "home"), (g["away"], g["ap"], g["winner"] == "away")):
            r = by.setdefault(g["y"], {}).setdefault(tid, [0, 0.0])
            r[0] += 1 if won else -1
            r[1] += pts
    return {y: min(t, key=lambda tid: (t[tid][0], t[tid][1])) for y, t in by.items()} | dict(finals or {})


def add_streaks(weeks, games, ids):
    """Each week's `streaks`: every one of today's teams' run going into the next week, counted across
    seasons and playoffs, as {id, n, w (1 a win streak, 0 a losing one), y, wk (where it began)}, longest
    first. A tie ends a run and starts none."""
    order = sorted((g for g in games if g.get("winner")), key=lambda g: (g["y"], g["week"]))
    now = order[-1]["y"] if order else None
    for wk in weeks:
        run = {}
        for g in order:
            if g["y"] == now and g["week"] > wk["week"]:
                break
            for tid, side in ((g["home"], "home"), (g["away"], "away")):
                if tid not in ids:
                    continue
                if g["winner"] == "tie":
                    run.pop(tid, None)
                    continue
                won = int(g["winner"] == side)
                r = run.get(tid)
                run[tid] = {"id": tid, "n": r["n"] + 1, "w": won, "y": r["y"], "wk": r["wk"]} if r and r["w"] == won \
                    else {"id": tid, "n": 1, "w": won, "y": g["y"], "wk": g["week"]}
        wk["streaks"] = sorted(run.values(), key=lambda r: (-r["n"], r["id"]))
    return weeks


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


def _streak(games, want, skip=frozenset()):
    """Longest run inside one regular season of wins (want True) or losses: (id, length, season)."""
    best, run = (None, 0, None), {}
    for g in games:
        if g.get("tier") is not None:
            continue
        for tid, won in ((g["home"], g["winner"] == "home"), (g["away"], g["winner"] == "away")):
            if tid in skip:
                continue
            key = (g["y"], tid)
            run[key] = run.get(key, 0) + 1 if won == want else 0
            if run[key] > best[1]:
                best = (tid, run[key], g["y"])
    return best


def book(facts, games, teams, lasts, skip=frozenset()):
    """{fame, shame}: league_recap.facts() split, plus the records only the back page shows. A manager
    in `skip` (record_skip) holds none of the records added here either."""
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
    lost_by = [x for x in won if x[3] not in skip]
    won_by = [x for x in won if x[1] not in skip]
    if lost_by:
        g, _, _, loser, pts = max(lost_by, key=lambda x: x[4])
        shame.append({"k": "robbed", "id": loser, "v": pts, "y": g["y"], "wk": g["week"]})
    if won_by:
        g, winner, pts, _, _ = min(won_by, key=lambda x: x[2])
        shame.append({"k": "stole", "id": winner, "v": pts, "y": g["y"], "wk": g["week"]})
    tid, n, y = _streak(games, False, skip)
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
