"""LIVE_PREVIEW: This week > Preview, from ff-jarvis's model.season.game_preview
(`data/game_previews.json`, feed block `game_preview`). Rebuilt 2026-09-29 as a slate and a dossier
(storyboard option A): the slate lists every game by kickoff window, a tap opens the game's research.

Per game, cut to what the page reads:
- `slot`, `et`, `day`: the kickoff window (Thu night, Sun morning, Sun 1:00, Sun late, Sun night, Mon
  night, else a weekday) and the kickoff in Eastern time, which is how the league schedules.
- `line`: the favourite and by how much, never a signed spread ("ARI by 1.5"); `open` the same for the
  first line seen, null when ff-jarvis has none.
- `matchup`: keyed by the offense; ff-jarvis's `defense_faced` under a team is the defense that team's
  offense faces (rank 1 = gives up the fewest).
- `wx`, `inj`, `rest`, `travel`, `site`: facts as given, null (or empty) when the producer has none.
- `flags`: at most two reasons to open the game, by priority (FLAG_ORDER).
- `take`: Claude's call (headline, lean, its score, how it sits against the market, the player calls,
  the risk), null before the first write. A player is named by the slug every other view uses.
"""
import datetime
import zoneinfo

ET = zoneinfo.ZoneInfo("America/New_York")
RAIN = 50       # precip % at which weather moves scoring (ff-jarvis METHODOLOGY 12.53: precipitation, WR/K)
WIND = 15       # mph, the backtest's wind threshold (12.53: QB, WR, TE, K)
MOVED = 3       # points the spread must move, favourite unchanged, to flag the game
KEY_AVG = 10    # points a game that make a missing player a reason to open the game
FLAG_ORDER = ["upset", "moved", "wx", "out", "short"]
COVERED = {"dome", "closed"}
INJ = {"Out": "out", "IR": "ir", "Doubtful": "d", "Questionable": "q"}
INJ_ORDER = {"out": 0, "ir": 0, "d": 1, "q": 2}


def _player(r, team, slugify):
    return {"n": r["name"], "slug": slugify(r["name"]), "pos": r["pos"], "team": team, "proj": r["proj"]}


def _take(take, names):
    if not take:
        return None
    return {"head": take["headline"], "lean": take["lean"], "vs": take["vs_market"], "risk": take["risk"],
            "pick": take["pick"],
            "players": [{**names[p["key"]], "call": p["call"], "why": p["why"]} for p in take["players"] if p["key"] in names]}


def _slot(kickoff):
    """(slot, "1:00 PM", "Sun") for a kickoff, by its Eastern weekday and hour."""
    t = datetime.datetime.fromisoformat(kickoff.replace("Z", "+00:00")).astimezone(ET)
    day, h = t.strftime("%a"), t.hour
    slot = {"Thu": "thu", "Mon": "mon"}.get(day) or (day == "Sun" and (
        "sunam" if h < 13 else "sun1" if h < 16 else "sunlate" if h < 19 else "sunnight")) or "day"
    return slot, f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if h < 12 else 'PM'}", day


def _fav(spread_home, home, away):
    """(favourite, by) from the home spread: below 0 the home side is favoured; 0 is even (None, 0)."""
    if spread_home is None:
        return None, None
    return (home if spread_home < 0 else away if spread_home > 0 else None), abs(spread_home)


def _line(line, home, away):
    if not line or line.get("spread_home") is None:
        return None
    fav, by = _fav(line["spread_home"], home, away)
    first = line.get("first_seen") or None
    opened = None
    if first and first.get("spread_home") is not None:
        ofav, oby = _fav(first["spread_home"], home, away)
        opened = {"fav": ofav, "by": oby, "total": first.get("total")}
    return {"fav": fav, "by": by, "total": line.get("total"), "implied": line.get("implied"), "open": opened,
            "move": None if first is None or first.get("spread_home") is None
            else round(abs(line["spread_home"] - first["spread_home"]), 1)}


def _wx(w):
    if not w:
        return None
    return {"roof": w.get("roof"), "temp": w.get("temp_f"), "wind": w.get("wind_mph"),
            "precip": w.get("precip_pct"), "sky": w.get("sky")}


def _inj(teams, slugify):
    """Per team, who is out (Out/IR, with his average) then doubtful and questionable, worst first."""
    out = {}
    for t, side in teams.items():
        rows = [{"n": m["name"], "slug": slugify(m["name"]), "pos": m["pos"], "s": INJ.get(m.get("injury"), "out"),
                 "avg": m.get("avg")} for m in side.get("missing") or []]
        rows += [{"n": p["name"], "slug": slugify(p["name"]), "pos": p["pos"], "s": INJ[p["injury"]], "avg": None}
                 for p in side.get("players") or [] if p.get("injury") in ("Doubtful", "Questionable")]
        out[t] = sorted(rows, key=lambda r: (INJ_ORDER[r["s"]], -(r["avg"] or 0)))
    return out


def _per_team(teams, key, cut):
    got = {t: cut(side[key]) for t, side in teams.items() if side.get(key)}
    return got or None


def _rest(r):
    return {"days": r.get("days"), "short": bool(r.get("short_week")), "bye": bool(r.get("off_bye"))}


def _travel(tr):
    return {"zones": tr.get("zones") or 0, "body": tr.get("body_kickoff"), "miles": tr.get("miles")}


def _matchup(teams):
    got = {t: {"games": d["games"], "epa": d.get("pass_epa_rank"),
               "pos": {p: {"pts": v["pts_pg"], "rank": v["rank"]} for p, v in d["pos"].items()}}
           for t, side in teams.items() if (d := side.get("defense_faced"))}
    return got or None


def _flags(g):
    """Why a reader would open this game, at most two, in FLAG_ORDER."""
    got, line, take, wx = [], g["line"], g["take"], g["wx"]
    if take and line and line["fav"] and take["pick"]["winner"] != line["fav"]:
        got.append({"k": "upset"})
    if line and line["open"]:
        flip = line["open"]["fav"] is not None and line["fav"] is not None and line["open"]["fav"] != line["fav"]
        if flip or (line["move"] or 0) >= MOVED:
            got.append({"k": "moved", "flip": flip, "by": line["move"]})
    if wx and wx["roof"] not in COVERED:
        if (wx["precip"] or 0) >= RAIN:
            got.append({"k": "wx", "rain": wx["precip"]})
        elif (wx["wind"] or 0) >= WIND:
            got.append({"k": "wx", "wind": wx["wind"]})
    outs = [r for rows in g["inj"].values() for r in rows if r["s"] in ("out", "ir") and (r["avg"] or 0) >= KEY_AVG]
    if outs:
        top = max(outs, key=lambda r: r["avg"])
        got.append({"k": "out", "n": top["n"], "slug": top["slug"]})
    short = [t for t, r in (g["rest"] or {}).items() if r["short"]]
    if short:
        got.append({"k": "short", "teams": sorted(short)})
    return sorted(got, key=lambda f: FLAG_ORDER.index(f["k"]))[:2]


def _game(g, slugify):
    f = g["facts"]
    teams = f["teams"]
    names = {r["key"]: _player(r, t, slugify) for t, side in teams.items() for r in side["players"]}
    slot, et, day = _slot(f["kickoff"])
    site = f.get("site") or None
    out = {"key": f["key"], "home": f["home"], "away": f["away"], "kickoff": f["kickoff"],
           "slot": slot, "et": et, "day": day,
           "line": _line(f.get("line"), f["home"], f["away"]),
           "matchup": _matchup(teams),
           "wx": _wx(f.get("weather")),
           "inj": _inj(teams, slugify),
           "rest": _per_team(teams, "rest", _rest),
           "travel": _per_team(teams, "travel", _travel),
           "site": {"stadium": site.get("stadium"), "neutral": bool(site.get("neutral"))} if site else None,
           "take": _take(g.get("take"), names)}
    out["flags"] = _flags(out)
    return out


def live_preview(raw, slugify):
    if not raw or not raw.get("games"):
        return None
    games = sorted((_game(g, slugify) for g in raw["games"].values()), key=lambda g: (g["kickoff"], g["key"]))
    return {"season": raw.get("season"), "week": raw.get("week"), "asof": raw.get("asof"), "games": games}


def report(block):
    if not block:
        return "Preview: no game_previews.json, so the view says so"
    taken = sum(1 for g in block["games"] if g["take"])
    return f"Preview: week {block['week']}, {len(block['games'])} games, {taken} with a take, as of {block['asof']}"
