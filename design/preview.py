"""LIVE_PREVIEW: This week > Preview (2026-09-29), one game a screen, from ff-jarvis's
model.season.game_preview (`data/game_previews.json`, feed block `game_preview`).

Per game, the facts the card prints (the market's implied score, rain when it moves scoring, who is out)
and Claude's take (headline, lean, its score, how it sits against the market, 3-6 player calls, the risk),
cut to what the page reads. A player is named by the slug every other view uses, so a row opens his profile.
A game with no take yet (a failed write, or before the first run) keeps its facts and `take` null.
"""

RAIN = 50   # precip % at which weather moves scoring (ff-jarvis METHODOLOGY 12.53: precipitation, WR/K)


def _player(r, team, slugify):
    return {"n": r["name"], "slug": slugify(r["name"]), "pos": r["pos"], "team": team, "proj": r["proj"]}


def _take(take, names):
    if not take:
        return None
    return {"head": take["headline"], "lean": take["lean"], "vs": take["vs_market"], "risk": take["risk"],
            "pick": take["pick"],
            "players": [{**names[p["key"]], "call": p["call"], "why": p["why"]} for p in take["players"] if p["key"] in names]}


def _game(g, slugify):
    f = g["facts"]
    names = {r["key"]: _player(r, t, slugify) for t, side in f["teams"].items() for r in side["players"]}
    line = f.get("line") or {}
    rain = (f.get("weather") or {}).get("precip_pct")
    return {"key": f["key"], "home": f["home"], "away": f["away"], "kickoff": f["kickoff"],
            "implied": line.get("implied"), "fav": line.get("favorite"), "by": line.get("by"), "total": line.get("total"),
            "rain": rain if rain is not None and rain >= RAIN else None,
            "out": [{"n": m["name"], "slug": slugify(m["name"]), "pos": m["pos"], "team": t, "inj": m["injury"]}
                    for t, side in f["teams"].items() for m in side["missing"]],
            "take": _take(g.get("take"), names)}


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
