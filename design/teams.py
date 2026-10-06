"""LIVE_TEAMS: League > Teams (leaf `teams`, 2026-10-05), the League board.

One row per team in a league, one column per position (QB, RB, WR, TE, FLX): the sum of this week's
projected points of the team's starters there, in its best legal lineup. FLX is what the league's flex
slots take, the best RB/WR/TE left after every position's own slots are filled. A team's bench keeps
its projections for the roster sheet, and the page marks a "spare starter" where a bench player beats
the league's usual weakest starter at his position.

The lineup rule is ff-jarvis's (`model.season.leagues`, `counts` and `fills`), kept here and not
imported: team-watch reads ff-jarvis's files, never its code, and nothing else in this repo imports
model.*. Dedicated slots take the top players at their position, then the flex slots take the best
of what is left, which is the optimum when a flex is open to several positions.

Starting slots come from the data, never from a table here: ESPN's roster file has `starters`;
Yahoo's and AYO's do not, so the count is the most players any team has in a slot (W/R/T is flex).
Left out: K, D/ST, IR, and anyone Sleeper lists as not playing (design/projections.py OUT_INJURY).
A player with no projection counts 0. Self-contained like the other cuts: the loaded files and
slugify come in as arguments.
"""
from collections import Counter
from statistics import median

from projections import slate, unavailable

POS = ("QB", "RB", "WR", "TE")
FLEX_POS = ("RB", "WR", "TE")
COLS = POS + ("FLX",)
FLEX_SLOTS = ("FLEX", "W/R/T")          # ESPN's name, Yahoo's name
OUT_SLOTS = ("IR", "OUT")


def slots(d):
    """{QB: 1, RB: 2, WR: 2, TE: 1, FLEX: 2} for a league's roster file, or {} when it names none."""
    raw = d.get("starters")
    if not raw:
        raw = Counter()
        for rows in d["detail"].values():
            for slot, n in Counter(r.get("slot") for r in rows).items():
                raw[slot] = max(raw[slot], n)
    out = {}
    for slot, n in raw.items():
        key = "FLEX" if slot in FLEX_SLOTS else slot
        if key in POS or key == "FLEX":
            out[key] = out.get(key, 0) + n
    return out if any(out.get(p) for p in POS) else {}


def _by_points(rows):
    return sorted(rows, key=lambda r: (-r["pts"], r["n"]))


def best_lineup(players, slot_counts):
    """(lineup, bench) for one team. `players` is [{n, pos, pts}]; the lineup is [{slot, n, pos, pts}]
    in QB, RB, WR, TE, FLX order, the bench the rest by points."""
    lineup, used = [], set()
    for pos in POS:
        mine = _by_points([p for p in players if p["pos"] == pos])
        for p in mine[:slot_counts.get(pos, 0)]:
            lineup.append({"slot": pos, **p})
            used.add(p["n"])
    left = _by_points([p for p in players if p["pos"] in FLEX_POS and p["n"] not in used])
    for p in left[:slot_counts.get("FLEX", 0)]:
        lineup.append({"slot": "FLX", **p})
        used.add(p["n"])
    return lineup, _by_points([p for p in players if p["n"] not in used])


def _sum(rows, slot):
    return round(sum(r["pts"] for r in rows if r["slot"] == slot), 1)


def _weakest(lineup, pos):
    """His lowest-projected starter at `pos`, the flex slots counted, or None with no starter there."""
    pts = [r["pts"] for r in lineup if r["pos"] == pos]
    return min(pts) if pts else None


def _floors(lineups):
    """pos -> the median team's weakest starter there: what a bench player has to beat to be spare."""
    out = {}
    for pos in POS:
        low = [w for w in (_weakest(lu, pos) for lu in lineups) if w is not None]
        if low:
            out[pos] = median(low)
    return out


def _points(proj, slugify, status, schedule):
    """(week, slug -> points, slugs not playing). `week` is the one the file speaks for (`slate`), the
    board's label; a player whose projected game is a later week (on a bye that week) counts 0, the way
    LIVE_PROJECTIONS gives him no number; the model's row wins a duplicate."""
    players = (proj or {}).get("players") or []
    week, done = slate(players, slugify, schedule)
    pts = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if not slug or (slug in pts and p.get("src") != "model"):
            continue
        pts[slug] = 0 if slug in done else (p.get("pts") or 0)
    return week, pts, set(unavailable(status, slugify))


def _byes(schedule):
    """A function NFL team -> True when it has no game in the page week; always False with no week or no
    games in it (a schedule that does not name the week cannot say a team is idle)."""
    week = (schedule or {}).get("week")
    alias = (schedule or {}).get("alias") or {}
    playing = {t for g in (schedule or {}).get("games") or [] if g.get("week") == week
               for t in (g.get("home"), g.get("away"))}
    return lambda team: bool(week is not None and playing and team and alias.get(team, team) not in playing)


def _players(rows, pts, gone, slugify, bye=None):
    """A team's rows -> [{n, pos, pts, team, bye}] of the players who can start: QB/RB/WR/TE, not on IR, not
    out. `team` is his NFL club as the roster file spells it; `bye` says that club has no game in the page
    week (the page draws BYE for such a player, a dash for any other with no points)."""
    out = []
    for r in rows:
        slug = slugify(r["name"])
        if r["pos"] in POS and r.get("slot") not in OUT_SLOTS and slug not in gone:
            team = r.get("team") or ""
            out.append({"n": r["name"], "pos": r["pos"], "pts": round(pts.get(slug, 0), 1),
                        "team": team, "bye": bool(bye(team)) if bye else False})
    return out


def _record(season):
    """team name -> (w, l, t) from the league file's standings."""
    return {t["name"]: (t.get("w"), t.get("l"), t.get("t")) for t in ((season or {}).get("teams") or {}).values()}


def live_league(key, roster, season, pts, gone, slugify, bye=None):
    """One league's board, or None when its roster file is missing or names no starting slots."""
    counts = slots(roster) if roster else {}
    if not counts:
        return None
    rec = _record(season)
    cut = {name: best_lineup(_players(rows, pts, gone, slugify, bye), counts) for name, rows in roster["detail"].items()}
    floor = _floors([lu for lu, _ in cut.values()])
    teams = []
    for name, (lineup, bench) in cut.items():
        cols = {c: _sum(lineup, c) for c in COLS}
        w, l, t = rec.get(name, (None, None, None))
        teams.append({"key": key if name == roster.get("me") else f"{key}-{slugify(name)}", "name": name,
                      "w": w, "l": l, "t": t, "tot": round(sum(cols.values()), 1), "cols": cols,
                      "spare": [p for p in POS if p in floor and any(b["pos"] == p and b["pts"] > floor[p] for b in bench)],
                      "lineup": lineup, "bench": bench})
    teams.sort(key=lambda x: (-x["tot"], x["name"].lower()))
    return {"key": key, "name": roster.get("league") or key, "slots": counts,
            "median": {c: round(median(x["cols"][c] for x in teams), 1) for c in COLS}, "teams": teams}


def live_teams(inputs, proj, slugify, status=None, schedule=None):
    """LIVE_TEAMS: {week, leagues: [league, ...]} for `inputs`, [(league key, roster file, this season's league
    file)] in the order the League switch lists them, or None when no league has a board. A league with no
    roster file is left out, and the page says so under its chip. `week` is the projections' week, null
    with no schedule; the page labels the board with it, never with the page's own week."""
    week, pts, gone = _points(proj, slugify, status, schedule)
    bye = _byes(schedule)
    made = [live_league(k, r, s, pts, gone, slugify, bye) for k, r, s in inputs]
    made = [m for m in made if m and m["teams"]]
    return {"week": week, "leagues": made} if made else None


def add_teams(blocks, report, slugify):
    """Adds LIVE_TEAMS to `blocks` and its summary line to `report`, both in place (build.py's one line)."""
    import leagues
    from myteams import roster_file, roster_path
    from sources import load_league, load_league_yahoo, load_player_proj, load_status, ESPN_ROSTERS
    inputs = [(k, roster_file(roster_path(k)), load_league_yahoo(k)[0]) for k in leagues.YAHOO]
    inputs.append(("espn", roster_file(ESPN_ROSTERS), load_league()[0]))
    blocks["LIVE_TEAMS"] = live_teams(inputs, load_player_proj(), slugify, load_status(), blocks["LIVE_SCHEDULE"])
    report.append(report_line(blocks["LIVE_TEAMS"]))


def report_line(block):
    if not block:
        return "Teams: no league has a roster file with starting slots, so the view says so"
    return "Teams: " + ", ".join(f"{lg['key']} {len(lg['teams'])}" for lg in block["leagues"])


TEAM_KEYS = ("key", "name", "w", "l", "t", "tot", "cols", "spare", "lineup", "bench")


def problems(obj):
    """Missing fields of a LIVE_TEAMS team as `LIVE_TEAMS.leagues[0].teams[1].cols`, for contract.py (a
    row spec is one level, and a team's lineup rows sit one deeper)."""
    miss = []
    for i, lg in enumerate(obj.get("leagues") or []):
        miss += [f"LIVE_TEAMS.leagues[{i}].median.{c}" for c in COLS if c not in (lg.get("median") or {})]
        for j, tm in enumerate(lg.get("teams") or []):
            at = f"LIVE_TEAMS.leagues[{i}].teams[{j}]"
            miss += [f"{at}.{k}" for k in TEAM_KEYS if k not in tm]
            miss += [f"{at}.cols.{c}" for c in COLS if c not in (tm.get("cols") or {})]
            for part, keys in (("lineup", ("slot", "n", "pos", "pts", "team", "bye")),
                              ("bench", ("n", "pos", "pts", "team", "bye"))):
                for r, row in enumerate(tm.get(part) or []):
                    miss += [f"{at}.{part}[{r}].{k}" for k in keys if k not in row]
    return miss
