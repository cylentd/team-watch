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
  Since 2026-09-29 (storyboard option A, confidence and record; David: "going with safe is just
  saying we go with Vegas") it also carries `win` {winner: 50-99}, `ats` {side, conf, edge} (side
  null = no edge) and `total` {call, conf}, each null on a take written before them. With the
  research pass (ff-jarvis preview-research, same day): `blind` {fav, by, total}, Claude's number
  before seeing the line, said like the line; `vs_blind`, how the final call moved from it; `notes`
  [{text, source}], source a link, "pbp" or null. Null / [] when absent.
- `market_win`: {team: win %} from the moneylines, vig removed; null without both prices.
- `base`: how favourites of this spread did 2011-2025, as whole percentages: {n, wins, covers, home};
  a pick'em has `home` (the home side's win %) and null `wins` / `covers`.

`record` (the block's own key, not a game's): Claude's graded season from ff-jarvis's
`preview_record` (design/sources.py `load_preview_record`), cut by `_record`; its `weeks` are [] until
the first week is final.
"""
import datetime

from injury import level
from slate import et_slot

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


CONF = ("lean", "solid", "strong")


def _ats(a):
    """{side, conf, edge}; a side without a known confidence, or a confidence without a side, is no edge."""
    if not a:
        return None
    side = a.get("side") or None
    conf = a.get("conf") if side and a.get("conf") in CONF else None
    return {"side": side if conf else None, "conf": conf, "edge": (a.get("edge") or None) if conf else None}


def _total(tc):
    if not tc:
        return None
    call = tc.get("call") if tc.get("call") in ("over", "under") else None
    conf = tc.get("conf") if call and tc.get("conf") in CONF else None
    return {"call": call if conf else None, "conf": conf}


def _blind(b, home, away):
    """Claude's number before seeing the line, as the line is said: {fav, by, total}. ff-jarvis's
    `margin_home` is home minus away, so above 0 the home side wins; 0 is even (fav None)."""
    if not b or b.get("margin_home") is None:
        return None
    m = b["margin_home"]
    return {"fav": home if m > 0 else away if m < 0 else None, "by": abs(m), "total": b.get("total")}


def _notes(notes):
    """Research notes, each with its source: a web link, "pbp" (play-by-play), else none."""
    def src(s):
        return s if s == "pbp" or (isinstance(s, str) and s.startswith(("https://", "http://"))) else None
    return [{"text": n["text"], "source": src(n.get("source"))} for n in notes or [] if n.get("text")]


def _take(take, names, home, away):
    if not take:
        return None
    return {"head": take["headline"], "lean": take["lean"], "vs": take["vs_market"], "risk": take["risk"],
            "pick": take["pick"], "win": take.get("win") or None, "ats": _ats(take.get("ats")),
            "total": _total(take.get("total")),
            "blind": _blind(take.get("blind"), home, away), "vs_blind": take.get("vs_blind") or None,
            "notes": _notes(take.get("notes")),
            "players": [{**names[p["key"]], "call": p["call"], "why": p["why"]} for p in take["players"] if p["key"] in names]}


def _base(b):
    """The spread's base rate as whole percentages. ff-jarvis's preview_market writes percentages to one
    decimal (0.5-3: fav_wins 54.8, fav_covers 46.5); a pick'em carries home_wins and null fav_* fields."""
    if not b or not b.get("n"):
        return None
    pct = lambda k: None if b.get(k) is None else round(b[k])
    out = {"n": b["n"], "wins": pct("fav_wins"), "covers": pct("fav_covers"), "home": pct("home_wins")}
    return out if any(out[k] is not None for k in ("wins", "covers", "home")) else None


def _slot(kickoff):
    """(slot, "1:00 PM", "Sun") for a kickoff, by its Eastern weekday and hour."""
    slot, t = et_slot(datetime.datetime.fromisoformat(kickoff.replace("Z", "+00:00")))   # slate.py: the one definition
    return slot, f"{t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}", t.strftime("%a")


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


def _s_of(code):
    """Sleeper's injury code as a row status (out / ir / d / q), None for a healthy player."""
    lv = level(code)
    return "ir" if code == "IR" else {"OUT": "out", "D": "d", "Q": "q"}.get(lv)


def _recheck(row, known, live):
    """Fresh status wins (the take is written once at midday, Sleeper runs again by evening: Start/Sit
    does the same in startsit_board._hurt, 2026-10-03). A changed row carries `changed` True (the page
    words it: copy key preview.inj.changed); a player now healthy drops out only when the take saw a real designation on him
    (a bare absence, a release or a trade, is not Sleeper's to clear). A player Sleeper does not list keeps
    the take's row."""
    if row["slug"] not in live:
        return row
    s = _s_of(live[row["slug"]])
    if s is None:
        return row if not known else None
    if s == row["s"]:
        return row
    if s in ("out", "ir") and row["s"] in ("out", "ir"):
        return {**row, "s": s}
    return {**row, "s": s, "changed": True}


def _newly_hurt(side, have, live, slugify):
    """Players the take listed healthy (or not at all) whom Sleeper now has hurt."""
    rows = []
    for p in side.get("players") or []:
        slug = slugify(p["name"])
        s = _s_of(live.get(slug))
        if s and slug not in have:
            rows.append({"n": p["name"], "slug": slug, "pos": p["pos"], "s": s, "avg": None, "changed": True})
    return rows


def _inj(teams, slugify, status=None):
    """Per team, who is out (Out/IR, with his average) then doubtful and questionable, worst first.
    With Sleeper's `status`, each row is re-checked against it (see `_recheck`)."""
    live = {slugify(v.get("name") or ""): v.get("injury") for v in (status or {}).values()}
    out = {}
    for t, side in teams.items():
        rows = [({"n": m["name"], "slug": slugify(m["name"]), "pos": m["pos"], "s": INJ.get(m.get("injury"), "out"),
                  "avg": m.get("avg")}, m.get("injury") in INJ) for m in side.get("missing") or []]
        rows += [({"n": p["name"], "slug": slugify(p["name"]), "pos": p["pos"], "s": INJ[p["injury"]], "avg": None}, True)
                 for p in side.get("players") or [] if p.get("injury") in ("Doubtful", "Questionable")]
        rows = [r for r in (_recheck(r, known, live) for r, known in rows) if r]
        rows += _newly_hurt(side, {r["slug"] for r in rows}, live, slugify)
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


def _game(g, slugify, status=None):
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
           "inj": _inj(teams, slugify, status),
           "rest": _per_team(teams, "rest", _rest),
           "travel": _per_team(teams, "travel", _travel),
           "site": {"stadium": site.get("stadium"), "neutral": bool(site.get("neutral"))} if site else None,
           "market_win": (f.get("line") or {}).get("market_win") or None,
           "base": _base((f.get("line") or {}).get("base")),
           "take": _take(g.get("take"), names, f["home"], f["away"])}
    out["flags"] = _flags(out)
    return out


def _closer(games):
    """(games where Claude's win % scored closer to the result than the market's, games both were scored)."""
    both = [g for g in games if g.get("brier_claude") is not None and g.get("brier_market") is not None]
    return sum(1 for g in both if g["brier_claude"] < g["brier_market"]), len(both)


def _favs(games):
    """(games Claude picked the favourite to win, games that had one)."""
    had = [g for g in games if g.get("fav_pick") is not None]
    return sum(1 for g in had if g["fav_pick"]), len(had)


def _record_game(g):
    return {"away": g["away"], "home": g["home"], "pick": g.get("pick"), "side": g.get("ats_side"),
            "conf": g.get("ats_conf"), "spread_home": g.get("spread_home"), "result": g.get("result"),
            "hit": g.get("ats_hit")}


def _record_week(w):
    games = w.get("games") or []
    closer, graded = _closer(games)
    fav, fav_of = _favs(games)
    return {"week": w["week"], "n": w.get("n") or len(games), "ats": w["ats"],
            "strong": (w.get("by_conf") or {}).get("strong"), "closer": closer, "graded": graded,
            "fav": fav, "fav_of": fav_of, "games": [_record_game(g) for g in games]}


def _record_blind(b):
    """The blind number's own record: {n, ats, mae_blind, mae_market} (margin error in points), None
    before it has a graded game."""
    if not b or not b.get("n"):
        return None
    mae = b.get("margin_mae") or {}
    return {"n": b["n"], "ats": b.get("ats"), "mae_blind": mae.get("blind"), "mae_market": mae.get("market")}


def _record(raw):
    """Claude's season against the spread: the totals, win % closer than the market's on N of M, and each
    graded week newest first with its games. None without the file; `weeks` [] before the first final week."""
    if not raw:
        return None
    weeks = sorted(raw.get("weeks") or [], key=lambda w: w["week"])
    games = [g for w in weeks for g in w.get("games") or []]
    tot = raw.get("totals") or {}
    closer, graded = _closer(games)
    fav, fav_of = _favs(games)
    covered = sum(1 for g in games if g.get("fav_covered"))
    return {"season": raw.get("season"), "through": raw.get("through_week"), "n": tot.get("n") or 0,
            "ats": tot.get("ats"), "by_conf": tot.get("by_conf") or {}, "closer": closer, "graded": graded,
            "fav": fav, "fav_of": fav_of, "covered": covered, "blind": _record_blind(tot.get("blind")),
            "weeks": [_record_week(w) for w in reversed(weeks)]}


def live_preview(raw, slugify, record=None, status=None):
    """`status` is sources.load_status() (Sleeper's latest): each game's `inj` is re-checked against it,
    so the dossier never says a player is out on the strength of a midday take alone."""
    if not raw or not raw.get("games"):
        return None
    games = sorted((_game(g, slugify, status) for g in raw["games"].values()), key=lambda g: (g["kickoff"], g["key"]))
    return {"season": raw.get("season"), "week": raw.get("week"), "asof": raw.get("asof"), "games": games,
            "record": _record(record)}


def report(block):
    if not block:
        return "Preview: no game_previews.json, so the view says so"
    taken = sum(1 for g in block["games"] if g["take"])
    rec = block.get("record")
    graded = f"record {rec['ats']} vs spread through week {rec['through']}" if rec and rec["weeks"] else "no graded week yet"
    return f"Preview: week {block['week']}, {len(block['games'])} games, {taken} with a take, {graded}, as of {block['asof']}"
