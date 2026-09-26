"""LIVE_LEAGUE: the ESPN league's week-by-week recap and all-time history, for My teams > League.

Reads ff-jarvis's model.clients.espn_league files: espn_league.json (this season, refreshed daily)
and espn_league_history.json (2014 on, tracked). Every number the view shows is computed here, so
the page only picks which team is on screen and draws.

A team is an ESPN team id across seasons, named by what it is called today. Early seasons' names
are ESPN's default "Team <surname>", and the page is on a public URL, so a past name never ships.
A team that has since left the league has no id in `teams`; its records draw as a former team.

Nothing here advises anyone: results, awards and history are already public inside the league
(memory feedback_no_edge_for_leaguemates).
"""

AWARDS = ("top", "low", "blow", "close", "luck", "unluck")


def _decided(games):
    return [g for g in games if g["winner"] and g["hp"] is not None and g["ap"] is not None]


def _sides(g):
    """(winner id, loser id, winner pts, loser pts); a tie has no winner and returns None."""
    if g["winner"] == "home":
        return g["home"], g["away"], g["hp"], g["ap"]
    if g["winner"] == "away":
        return g["away"], g["home"], g["ap"], g["hp"]
    return None


def awards(games):
    """The week's six awards over its decided games: top and bottom score, the biggest and the
    smallest margin (by the winner), the lowest score that won and the highest that lost."""
    scores = [(g["home"], g["hp"]) for g in games] + [(g["away"], g["ap"]) for g in games]
    won = [s for s in map(_sides, games) if s]
    if not scores:
        return {}
    top, low = max(scores, key=lambda s: s[1]), min(scores, key=lambda s: s[1])
    out = {"top": {"id": top[0], "v": top[1]}, "low": {"id": low[0], "v": low[1]}}
    if won:
        m = lambda s: round(s[2] - s[3], 2)
        blow, close = max(won, key=m), min(won, key=m)
        luck, unluck = min(won, key=lambda s: s[2]), max(won, key=lambda s: s[3])
        out.update(blow={"id": blow[0], "opp": blow[1], "v": m(blow)},
                   close={"id": close[0], "opp": close[1], "v": m(close)},
                   luck={"id": luck[0], "v": luck[2]}, unluck={"id": unluck[1], "v": unluck[3]})
    return out


def weeks(season):
    """This season's decided weeks, oldest first: every game and its awards."""
    by = {}
    for g in _decided(season["games"]):
        by.setdefault(g["week"], []).append(g)
    return [{"week": w, "games": [{"a": g["home"], "b": g["away"], "ap": g["hp"], "bp": g["ap"], "win": g["winner"]}
                                  for g in gs], "awards": awards(gs)}
            for w, gs in sorted(by.items())]


def _all_games(season, history):
    """Every decided game, oldest first, each tagged with its season."""
    out = []
    for y, s in sorted(history.items()) + [(str(season["season"]), season)]:
        out += [{**g, "y": int(y)} for g in _decided(s["games"])]
    return out


def head_to_head(games, ids):
    """h2h[a][b]: a's all-time record against b, the first season they met, a's biggest win over b
    and their last meeting. Only today's teams, both ways."""
    h = {a: {} for a in ids}
    for g in games:
        for me, them, mine, theirs in ((g["home"], g["away"], g["hp"], g["ap"]), (g["away"], g["home"], g["ap"], g["hp"])):
            if me not in h or them not in h:
                continue
            r = h[me].setdefault(them, {"w": 0, "l": 0, "t": 0, "since": g["y"], "big": None, "last": None})
            r["w" if mine > theirs else "l" if mine < theirs else "t"] += 1
            if mine > theirs and (not r["big"] or mine - theirs > r["big"]["v"]):
                r["big"] = {"v": round(mine - theirs, 2), "y": g["y"], "wk": g["week"]}
            r["last"] = {"y": g["y"], "wk": g["week"], "won": mine > theirs, "tie": mine == theirs}
    return {str(a): {str(b): r for b, r in row.items()} for a, row in h.items()}


def champions(history):
    """One row per finished season, newest first. `final` 1 is the title; a season still being
    played has none yet."""
    out = []
    for y, s in sorted(history.items(), reverse=True):
        for tid, t in s["teams"].items():
            if t["final"] == 1:
                out.append({"y": int(y), "id": int(tid), "w": t["w"], "l": t["l"], "t": t["t"]})
    return out


def _streak(games):
    """Longest run of regular-season wins inside one season: (team id, length, season)."""
    best, run = (None, 0, None), {}
    for g in games:
        if g["tier"] is not None:
            continue
        for tid, won in ((g["home"], g["winner"] == "home"), (g["away"], g["winner"] == "away")):
            key = (g["y"], tid)
            run[key] = run.get(key, 0) + 1 if won else 0
            if run[key] > best[1]:
                best = (tid, run[key], g["y"])
    return best


def facts(games, champs, history):
    """The all-time records, a fixed list in a fixed order (nothing rotates on its own)."""
    if not games:
        return []
    side = [(g["home"], g["hp"], g) for g in games] + [(g["away"], g["ap"], g) for g in games]
    hi, lo = max(side, key=lambda s: s[1]), min(side, key=lambda s: s[1])
    won = [(s, g) for g in games for s in [_sides(g)] if s]
    blow_s, blow_g = max(won, key=lambda x: x[0][2] - x[0][3])
    out = [{"k": "high", "id": hi[0], "v": hi[1], "y": hi[2]["y"], "wk": hi[2]["week"]},
           {"k": "low", "id": lo[0], "v": lo[1], "y": lo[2]["y"], "wk": lo[2]["week"]},
           {"k": "blow", "id": blow_s[0], "opp": blow_s[1], "v": round(blow_s[2] - blow_s[3], 2),
            "y": blow_g["y"], "wk": blow_g["week"]}]
    tid, n, y = _streak(games)
    if n >= 3:
        out.append({"k": "streak", "id": tid, "n": n, "y": y})
    titles = {}
    for c in champs:
        titles[c["id"]] = titles.get(c["id"], 0) + 1
    if titles and max(titles.values()) >= 2:
        most = max(titles.values())
        out.append({"k": "titles", "ids": sorted(i for i, c in titles.items() if c == most), "n": most})
    pf = [(int(t_id), t["pf"], int(y)) for y, s in history.items() for t_id, t in s["teams"].items()]
    if pf:
        best = max(pf, key=lambda r: r[1])
        out.append({"k": "pf", "id": best[0], "v": best[1], "y": best[2]})
    return out


def live_league(season, history, rosters, slugify):
    """LIVE_LEAGUE, or None when ff-jarvis has not written this season's file. `rosters` is
    espn_rosters.json (its `me` names David's team, keyed "espn" on the page; every other team
    is keyed as design/mates.py keys it)."""
    if not season or not season.get("teams"):
        return None
    past = (history or {}).get("seasons") or {}
    me = (rosters or {}).get("me")
    # w/l/t is ESPN's own standing, which counts this league's top-half bonus win each week.
    teams = [{"id": int(i), "name": t["name"], "key": "espn" if t["name"] == me else f"espn-{slugify(t['name'])}",
              "w": t["w"], "l": t["l"], "t": t["t"]}
             for i, t in season["teams"].items()]
    games = _all_games(season, past)
    champs = champions(past)
    now = [{"a": g["home"], "b": g["away"]} for g in season["games"] if g["week"] == season["week"]]
    return {"league": season["league"], "season": season["season"], "week": season["week"],
            "since": min([int(y) for y in past] + [season["season"]]), "teams": teams,
            "weeks": weeks(season), "now": now, "h2h": head_to_head(games, [t["id"] for t in teams]),
            "champs": champs, "facts": facts(games, champs, past)}


def report(league):
    if not league:
        return "League: none (ff-jarvis espn_league.json missing)"
    return (f"League: {league['league']} {league['season']}, {len(league['weeks'])} weeks decided, "
            f"{len(league['champs'])} champions since {league['since']}")
