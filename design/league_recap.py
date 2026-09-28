"""LIVE_LEAGUE and LIVE_LEAGUE_YAHOO: each league's week-by-week recap and history, My teams > League.

Reads ff-jarvis's model.clients.espn_league and yahoo_league files: the season file (refreshed daily,
one shape for both sites) and the history file (tracked). Every number the view shows is computed
here, so the page only picks which team is on screen and draws.

ESPN: a team is its ESPN id across seasons, named by what it is called today. Early seasons' names
are ESPN's default "Team <surname>", and the page is on a public URL, so a past name never ships.
A team that has since left the league has no id in `teams`; its records draw as a former team.
Yahoo: a new id every season and hidden managers, so the past is champions only, under that year's
name, and a default-shaped name ("Team X") is dropped the same way.

Nothing here advises anyone: results, awards and history are already public inside the league
(memory feedback_no_edge_for_leaguemates).
"""
import re

from league_back import (add_meets, add_standings, add_streaks, add_tape, book, enrich_weeks, last_places, next_grudge,
                         private_pairs, record_skip, withhold)

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
    smallest margin (by the winner), the lowest score that won and the highest that lost.
    A score award carries its proof: the opponent, its own margin `m` (negative lost) and its rank
    among the week's `of` scores; a margin award carries both scores."""
    scores = [(g["home"], g["hp"], g["away"], g["ap"]) for g in games] + [(g["away"], g["ap"], g["home"], g["hp"]) for g in games]
    won = [s for s in map(_sides, games) if s]
    if not scores:
        return {}
    row = lambda s: {"id": s[0], "v": s[1], "opp": s[2], "m": round(s[1] - s[3], 2),
                     "rank": 1 + sum(x[1] > s[1] for x in scores), "of": len(scores)}
    out = {"top": row(max(scores, key=lambda s: s[1])), "low": row(min(scores, key=lambda s: s[1]))}
    if won:
        m = lambda s: round(s[2] - s[3], 2)
        blow, close = max(won, key=m), min(won, key=m)
        luck, unluck = min(won, key=lambda s: s[2]), max(won, key=lambda s: s[3])
        edge = lambda s: {"id": s[0], "opp": s[1], "v": m(s), "p": s[2], "op": s[3]}
        out.update(blow=edge(blow), close=edge(close),
                   luck=row((luck[0], luck[2], luck[1], luck[3])), unluck=row((unluck[1], unluck[3], unluck[0], unluck[2])))
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
                out.append({"y": int(y), "id": int(tid), "name": None, "w": t["w"], "l": t["l"], "t": t["t"]})
    return out


def _streak(games, skip=frozenset()):
    """Longest run of regular-season wins inside one season: (team id, length, season)."""
    best, run = (None, 0, None), {}
    for g in games:
        if g["tier"] is not None:
            continue
        for tid, won in ((g["home"], g["winner"] == "home"), (g["away"], g["winner"] == "away")):
            if tid in skip:
                continue
            key = (g["y"], tid)
            run[key] = run.get(key, 0) + 1 if won else 0
            if run[key] > best[1]:
                best = (tid, run[key], g["y"])
    return best


def facts(games, champs, history, skip=frozenset()):
    """The all-time records, a fixed list in a fixed order (nothing rotates on its own). A manager in
    `skip` (league_back.record_skip) holds none of them; the next one down holds each instead."""
    if not games:
        return []
    side = [(g["home"], g["hp"], g) for g in games if g["home"] not in skip] + \
           [(g["away"], g["ap"], g) for g in games if g["away"] not in skip]
    hi, lo = max(side, key=lambda s: s[1]), min(side, key=lambda s: s[1])
    won = [(s, g) for g in games for s in [_sides(g)] if s and s[0] not in skip]
    blow_s, blow_g = max(won, key=lambda x: x[0][2] - x[0][3])
    out = [{"k": "high", "id": hi[0], "v": hi[1], "y": hi[2]["y"], "wk": hi[2]["week"]},
           {"k": "low", "id": lo[0], "v": lo[1], "y": lo[2]["y"], "wk": lo[2]["week"]},
           {"k": "blow", "id": blow_s[0], "opp": blow_s[1], "v": round(blow_s[2] - blow_s[3], 2),
            "y": blow_g["y"], "wk": blow_g["week"]}]
    tid, n, y = _streak(games, skip)
    if n >= 3:
        out.append({"k": "streak", "id": tid, "n": n, "y": y})
    titles = {}
    for c in champs:
        titles[c["id"]] = titles.get(c["id"], 0) + 1
    if titles and max(titles.values()) >= 2:
        most = max(titles.values())
        out.append({"k": "titles", "ids": sorted(i for i, c in titles.items() if c == most), "n": most})
    pf = [(int(t_id), t["pf"], int(y)) for y, s in history.items() for t_id, t in s["teams"].items() if int(t_id) not in skip]
    if pf:
        best = max(pf, key=lambda r: r[1])
        out.append({"k": "pf", "id": best[0], "v": best[1], "y": best[2]})
    return out


def _teams(season, rosters, slugify, league):
    """Today's teams, keyed as the team switch keys them: David's is the league's own key ("espn",
    "yahoo"), every other one as design/mates.py keys it. w/l/t is the site's own standing (ESPN's
    counts this league's top-half bonus win each week)."""
    me = (rosters or {}).get("me")
    return [{"id": int(i), "name": t["name"], "key": league if t["name"] == me else f"{league}-{slugify(t['name'])}",
             "w": t["w"], "l": t["l"], "t": t["t"]}
            for i, t in season["teams"].items()]


def _block(season, teams, games, champs, facts_, since, scope):
    now = [{"a": g["home"], "b": g["away"]} for g in season["games"] if g["week"] == season["week"]]
    return {"league": season["league"], "season": season["season"], "week": season["week"], "since": since,
            "scope": scope, "teams": teams, "weeks": weeks(season), "now": now,
            "h2h": head_to_head(games, [t["id"] for t in teams]), "champs": champs, "facts": facts_}


def live_league(season, history, rosters, slugify):
    """LIVE_LEAGUE (ESPN), or None when ff-jarvis has not written this season's file. `rosters` is
    espn_rosters.json. Head-to-head and records run all-time: ESPN keeps a team's id every season."""
    if not season or not season.get("teams"):
        return None
    past = (history or {}).get("seasons") or {}
    games = _all_games(season, past)
    champs = champions(past)
    return _block(season, _teams(season, rosters, slugify, "espn"), games, champs, facts(games, champs, past),
                  min([int(y) for y in past] + [season["season"]]), "all")


def _past_name(name):
    """A past Yahoo team's name, or None for a site default that may carry a surname ("Team Smith")."""
    return None if not name or re.fullmatch(r"Team \S+", name.strip()) else name


FORMER = 1000   # a manager who has left: 1000 + N, never one of today's ids (1-12)


def _owner(owners, y, tid):
    """Today's team id of the manager who ran team `tid` in season `y` (ff-jarvis's owner map), 1000+N
    for a manager who has left, or a season-scoped id (y*100+tid, never joined) when the map lacks it."""
    o = (((owners or {}).get("seasons") or {}).get(str(y)) or {}).get(str(tid))
    if o is None:
        return int(y) * 100 + int(tid)
    return int(o) if not str(o).startswith("former-") else FORMER + int(str(o).split("-")[1])


def _mgr_of(managers):
    """Owner id -> the manager's display name (ff-jarvis yahoo_league_managers.json, keyed like the owner
    map): today's id, or FORMER+N for former-N. None for an unmapped team or without the file."""
    m = (managers or {}).get("managers") or {}
    def name(oid):
        if oid is None:
            return None
        return m.get(str(oid)) if oid < FORMER else m.get(f"former-{oid - FORMER}") if oid < 100000 else None
    return name


def live_league_yahoo(season, history, owners, rosters, slugify, box=None, recap=None, managers=None):
    """LIVE_LEAGUE_YAHOO, or None. Yahoo re-ids every team each season and hides managers from the
    cookie, so past teams join today's through `owners` (ff-jarvis yahoo_league_owners.json, no names).
    With every past season mapped, head-to-head and titles run all-time (`scope` "all"); without, this
    season only. A past team keeps the name it had that year (`name`); `id` says who it is today.
    `rosters` is league_rosters.json; `box` and `recap` are ff-jarvis's box scores and weekly roast,
    and the back page (design/league_back.py) draws without either. `managers` names each manager
    (`mgr` on teams, champions and records) for Records, which files a record under its manager."""
    if not season or not season.get("teams"):
        return None
    mgr = _mgr_of(managers)
    pods = (history or {}).get("seasons") or {}
    mapped = all(str(y) in ((owners or {}).get("seasons") or {}) for y, s in pods.items() if s.get("games"))
    champs = []
    for y, s in sorted(pods.items(), reverse=True):
        if s.get("podium"):
            oid = _owner(owners, y, s["podium"][0]["id"])
            champs.append({"y": int(y), "id": oid if oid < FORMER else None, "name": _past_name(s["podium"][0]["name"]),
                           "w": None, "l": None, "t": None, "mgr": mgr(oid)})
    now = _all_games(season, {})
    past, names, totals = _yahoo_past(pods, owners)
    everything = sorted(past + now, key=lambda g: (g["y"], g["week"]))
    skip = record_skip(former=FORMER)
    fx = _named(facts(everything, [c for c in champs if c["id"]] if mapped else [], totals, skip), names, mgr)
    games = everything if mapped else now
    teams = [{**t, "mgr": mgr(t["id"])} for t in _teams(season, rosters, slugify, "yahoo")]
    block = _block(season, teams, games, champs, fx,
                   min([int(y) for y in pods] + [season["season"]]), "all" if mapped else "season")
    enrich_weeks(block["weeks"], box, recap, slugify)
    add_standings(block["weeks"], [t["id"] for t in block["teams"]])
    add_meets(block["h2h"], games)
    ids = {t["id"] for t in block["teams"]}
    add_streaks(block["weeks"], games, ids)
    block["withheld"] = withhold(block["h2h"], private_pairs())
    block["grudge"] = next_grudge(block["now"], block["h2h"])
    finals = _yahoo_finals(pods, owners) if mapped else {}
    lasts = last_places(games, season["season"], finals)
    block["spoons"] = [{"y": y, "id": oid if oid < FORMER else None, "name": names.get((y, oid)), "mgr": mgr(oid),
                        "final": y in finals} for y, oid in sorted(lasts.items(), reverse=True)] if mapped else []
    add_tape(block["teams"], games, champs, lasts)
    b = book(fx, games, block["teams"], lasts, skip)
    block["book"] = {k: _named(v, names, mgr) for k, v in b.items()}
    return block


def _yahoo_past(pods, owners):
    """Past Yahoo seasons' games with each team as its manager's id (_owner), each (season, id)'s name
    that year, and each season's regular-season points in facts()'s history shape."""
    games, names, totals = [], {}, {}
    for y, s in pods.items():
        oid = lambda tid: _owner(owners, y, tid)
        for g in s.get("games") or []:
            games.append({**g, "home": oid(g["home"]), "away": oid(g["away"]), "y": int(y)})
        names.update({(int(y), oid(tid)): _past_name(n) for tid, n in (s.get("names") or {}).items()})
        pf = {}
        for g in s.get("games") or []:
            if g["tier"] is None:
                for tid, pts in ((g["home"], g["hp"]), (g["away"], g["ap"])):
                    pf[oid(tid)] = round(pf.get(oid(tid), 0) + pts, 2)
        if pf:
            totals[y] = {"teams": {str(k): {"pf": v} for k, v in pf.items()}}
    return games, names, totals


def _yahoo_finals(pods, owners):
    """{season: the owner id Yahoo placed last}, from each season's `final` (ff-jarvis yahoo_league
    finals: that season's team id -> final place, consolation bracket counted)."""
    out = {}
    for y, s in pods.items():
        f = s.get("final") or {}
        if f:
            out[int(y)] = _owner(owners, y, max(f, key=lambda tid: f[tid]))
    return out


def _named(fx, names, mgr=None):
    """A fact from a past season names the team as it was that year (`name`, `oppname`) and, given
    `mgr`, its manager (`mgr`, `oppmgr`, `mgrs` for a list of ids), which a former manager keeps too;
    its `id` stays when it is one of today's teams (the page adds "now ..."), and is dropped for a
    manager who has left or an unmapped team. A fact may pass through twice (facts, then the book):
    a name, once set, stays."""
    for f in fx:
        for key, label, who in (("id", "name", "mgr"), ("opp", "oppname", "oppmgr")):
            if f.get(key) is not None and "y" in f and (f["y"], f[key]) in names:
                f[label] = names[(f["y"], f[key])]
            if mgr and f.get(key) is not None and not f.get(who) and mgr(f[key]):
                f[who] = mgr(f[key])
            if f.get(key) is not None and f[key] >= FORMER:
                f[key] = None
        if mgr and f.get("ids") and "mgrs" not in f and any(map(mgr, f["ids"])):
            f["mgrs"] = [mgr(i) for i in f["ids"]]
    return fx


def report(league, site="ESPN"):
    if not league:
        return f"League ({site}): none (ff-jarvis {site.lower()}_league.json missing)"
    return (f"League ({site}): {league['league']} {league['season']}, {len(league['weeks'])} weeks decided, "
            f"{len(league['champs'])} champions since {league['since']}")
