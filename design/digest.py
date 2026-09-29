"""LIVE_DIGEST: the Digest view (This week, the front page), from ff-jarvis's data/weekly_digest.json.

ff-jarvis builds the packet (model.season.weekly_digest; the contract is weekly_digest_schema.py
there) and the morning Discord post renders the same file. This module only cuts it for the page:
a slug for every player, UTC stamps as Pacific wall-clock words, each headline's news kind from
team-watch's own design/news.py, and the nested sections flattened into lists the contract can
check. It picks nothing and computes no model number: the lead, every rank and every order are
the packet's.

Self-contained like the other cuts: the loaded packet and slugify come in as arguments.
"""
import datetime as dt

from news import news_kind, news_player
from slate import LOCAL_TZ, UTC

POS = ("QB", "RB", "WR", "TE")


def _local(stamp):
    """A UTC stamp ("YYYY-MM-DD HH:MM:SS" or ISO with a T) on David's clock, or None."""
    try:
        t = dt.datetime.fromisoformat(str(stamp).replace(" ", "T"))
    except ValueError:
        return None
    return (t.replace(tzinfo=UTC) if t.tzinfo is None else t).astimezone(LOCAL_TZ)


def _clock(t):
    return f"{t.hour % 12 or 12}:{t:%M} {t:%p}"


def _kick(stamp):
    """"Sun 5:20 PM", Pacific: the kickoff as the lead and the rows say it."""
    t = _local(stamp)
    return f"{t:%a} {_clock(t)}" if t else None


def _player(r, slugify, *keys):
    return {"n": r["name"], "slug": slugify(r["name"]), **{k: r.get(k) for k in keys}}


def _ko(stamp):
    """The kickoff as ISO UTC with a Z, which Date.parse reads: the page drops a row at this
    instant, live, so a tab left open never shows a pre-game fact about a game in progress."""
    t = _local(stamp)
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None


def kicks(schedule, week):
    """team -> this week's kickoff (ISO UTC), in both dialects: the packet speaks nflverse (LA, WAS),
    the schedule ESPN (LAR, WSH) and ships the alias between them."""
    if not schedule:
        return {}
    back = {espn: nfl for nfl, espn in (schedule.get("alias") or {}).items()}
    out = {}
    for g in schedule.get("games") or []:
        if g.get("week") == week:
            for team in (g["home"], g["away"]):
                out[team] = out[back.get(team, team)] = g["kickoff"]
    return out


def next_kick(schedule, team, since):
    """The team's first kickoff (ISO UTC) after `since` ("YYYY-MM-DD HH:MM:SS" UTC, the game a starters
    row is measured from), in either dialect; None without a schedule or a game after it."""
    if not schedule or not since:
        return None
    alias = schedule.get("alias") or {}
    names = {team, alias.get(team, team)}
    after = dt.datetime.fromisoformat(since.replace(" ", "T")).replace(tzinfo=UTC)
    ks = [g["kickoff"] for g in schedule.get("games") or [] if names & {g["home"], g["away"]}
          and dt.datetime.fromisoformat(g["kickoff"].replace("Z", "+00:00")) > after]
    return min(ks) if ks else None


def _game(g):
    return {"away": g["away"], "home": g["home"], "kick": _kick(g.get("kickoff")), "ko": _ko(g.get("kickoff"))} if g else None


def _wx(g):
    return {"away": g["away"], "home": g["home"], "kick": _kick(g.get("kickoff")), "ko": _ko(g.get("kickoff")),
            "temp_f": g.get("temp_f"), "wind_mph": g.get("wind_mph") or 0, "precip_pct": g.get("precip_pct") or 0,
            "short": g.get("short"), "lead": bool(g.get("lead")), "bar": g.get("bar") or "wind"}


def _asof(stamp):
    """The packet's asof (Pacific wall clock already) as the page says it: "Mon 5:58 AM"."""
    try:
        t = dt.datetime.fromisoformat(str(stamp).replace(" ", "T"))
    except ValueError:
        return None
    return f"{t:%a} {_clock(t)}"


def _results(r, slugify):
    """The week so far: finals, the recap's standouts (per position, its order) and busts."""
    r = r or {}
    # `line`: his box score from ff-jarvis's play-by-play (2026-09-29), null until it publishes; the
    # lead banner calls the top score from it.
    row = lambda x: {**_player(x, slugify, "pos", "team", "actual", "proj", "diff"), "why": _why(x.get("why")),
                     "line": x.get("line")}
    return {"finals": [{k: g.get(k) for k in ("away", "home", "away_pts", "home_pts")} for g in r.get("games") or []],
            "pending": len(r.get("pending") or []),
            "stars": [row(x) for pos in POS for x in (r.get("top") or {}).get(pos) or []],
            "smashed": [row(x) for x in r.get("smashed") or []],
            "busts": [row(x) for x in r.get("busts") or []],
            "left": [_left(x, slugify) for x in r.get("left_hurt") or []]}


def _rest(headline, name):
    """A headline without his name at its front: after the injury tag when there is one ("Baker
    Mayfield (thumb) exits early" -> "exits early"), else past his name, suffix and all ("Travis
    Etienne Jr. exits early" -> "exits early"), so a row that already names him never says it twice."""
    h = (headline or "").strip()
    if "(" in h and ")" in h:
        return h.split(")", 1)[1].strip()
    base = (name or "").replace(" Jr.", "")
    lead = next((n for n in (base + " Jr.", base) if base and h.startswith(n)), "")
    return h[len(lead):].strip() if lead else h


def _why(w):
    """The producer's reason, rounded as the row says it: {kind, luck, expected, stat, share, delta}.
    The rule that picked it is ff-jarvis's (weekly_digest_played.why_of); the page only words it."""
    w = w or {}
    rnd = lambda v: None if v is None else round(v)
    return {"kind": w.get("kind") or "earned", "luck": rnd(w.get("luck")), "expected": rnd(w.get("expected")),
            "stat": w.get("stat"), "share": rnd(w.get("share")), "delta": rnd(w.get("delta"))}


def _tag(h):
    return h[h.find("(") + 1:h.find(")")] if "(" in h and ")" in h else None


def _left(x, slugify):
    """"Baker Mayfield (thumb) exits early Sunday" -> injury "thumb"; an untagged headline has none.
    His newest headline since, when there is one, is the fresher word: its tag wins ("(quad)" the
    next day over "(thigh)" in-game) and its words are `later` ("suffers season-ending torn ACL")."""
    h, u = (x.get("headline") or "").strip(), (x.get("update") or "").strip()
    return {**_player(x, slugify, "pos", "team", "proj", "actual"), "injury": _tag(u) or _tag(h),
            "rest": _rest(h, x["name"]), "later": _rest(u, x["name"]) if u else None}


def _news(it):
    """The headline split at its injury tag: "Jaylen Wright (stinger/foot) doubtful to play Sunday"
    reads as name "Jaylen Wright" and rest "doubtful to play Sunday". A headline with no tag keeps
    its words whole in `rest` and has no name."""
    headline = it.get("headline") or ""
    name, slugs = news_player(headline)
    n = it.get("name") or name
    t = _local(it.get("created"))
    return {"when": _clock(t) if t else None, "headline": headline, "kind": news_kind({"title": headline}),
            "n": n, "rest": _rest(headline, n), "slugs": slugs}


def _starter(r, slugify, schedule):
    """A new #1 on Sleeper's depth chart or a player on a new team (ff-jarvis weekly_digest_starters):
    `over` is the #1 he replaced, `from` his old team, `day` the weekday it happened ("Tue"), `ko` the
    team's next kickoff after the game it is measured from (`since`), when the page drops it."""
    o = r.get("over")
    day = dt.date.fromisoformat(r["changed"]).strftime("%a") if r.get("changed") else None
    return {**_player(r, slugify, "pos", "team", "proj", "from", "depth"), "day": day,
            "ko": next_kick(schedule, r.get("team"), r.get("since")),
            "over": {"n": o["name"], "slug": slugify(o["name"]), "status": o.get("status")} if o else None}


def _tonight(t, slugify):
    """Tonight's standalone game(s), as ff-jarvis cut them (weekly_digest_tonight): every player gets
    a slug, `next_up` names who he replaces by name, the kickoff comes as words and as ISO UTC."""
    games = []
    for g in (t or {}).get("games") or []:
        out = [{**_player(r, slugify, "pos", "team", "status", "injury")} for r in g.get("out") or []]
        names = {r["key"]: r["name"] for r in g.get("out") or []}
        games.append({"away": g["away"], "home": g["home"], "kick": _kick(g.get("kickoff")), "ko": _ko(g.get("kickoff")),
                      "wx": {k: (g.get("wx") or {}).get(k) for k in ("roof", "temp_f", "wind_mph", "precip_pct", "short")},
                      "out": out,
                      "next_up": [{**_player(r, slugify, "pos", "team", "pts"), "for": names.get(r["for"])}
                                  for r in g.get("next_up") or []],
                      "groups": [{k: r.get(k) for k in ("team", "group", "d_pts")} for r in g.get("groups") or []],
                      "moved": [_player(r, slugify, "pos", "team", "d_pts") for r in g.get("moved") or []],
                      "tcalls": [_player(r, slugify, "pos", "team", "pts", "call") for r in g.get("calls") or []],
                      "projected": [_player(r, slugify, "pos", "team", "pts") for r in g.get("projected") or []]})
    return {"tonight": games, "tonight_last": bool((t or {}).get("last"))}


def live_digest(p, slugify, schedule=None):
    """None when ff-jarvis has written no packet: the view then says so instead of guessing.
    `schedule` is LIVE_SCHEDULE, for each best-spot and top-5 row's kickoff (`ko`)."""
    if not p or "week" not in p:
        return None
    m, wx, adds, stock = p.get("matchups") or {}, p.get("weather") or {}, p.get("adds") or {}, p.get("stock") or {}
    best = (m.get("best") or {})
    rec = m.get("record")
    ko = kicks(schedule, p["week"])
    return {
        "season": p.get("season"), "week": p["week"], "asof": p.get("asof"), "asof_words": _asof(p.get("asof")),
        "lead": p.get("lead"),
        "rules": p.get("rules"),   # ff-jarvis's thresholds, quoted by the row feet; never re-applied here
        "hurt": [{**_player(r, slugify, "pos", "team", "status", "was", "injury", "new", "rank", "rostered"),
                  "game": _game(r.get("game"))} for r in p.get("hurt") or []],
        "calls": m.get("calls") or 0,
        "record": ({"through": rec["through"], "ours": rec["ours"], "pl": rec["pl"]} if rec else None),
        "best": [{**_player(best[pos], slugify, "pos", "team", "opp", "home", "pts", "why"), "ko": ko.get(best[pos]["team"])}
                 for pos in POS if best.get(pos)],
        "wx": [_wx(g) for g in wx.get("games") or []],
        "near": _wx(wx["near"]) if wx.get("near") else None,
        # Sleeper's adds over the last `adds_hours` since 2026-09-28; "espn" is the fallback cut
        # (ESPN % rostered, week over week), and a packet from before that date has no source.
        "adds_source": adds.get("source") or "espn", "adds_hours": adds.get("hours"),
        "adds_weeks": adds.get("weeks") or [],
        "adds": [_player(r, slugify, "pos", "team", "count", "was", "now", "delta") for r in adds.get("rows") or []],
        "top5": [{"pos": pos, **_player(r, slugify, "team", "opp", "pts"), "ko": ko.get(r["team"])}
                 for pos in POS for r in (p.get("top5") or {}).get(pos) or []],
        **_results(p.get("results"), slugify),
        **_tonight(p.get("tonight"), slugify),
        "up": [_player(r, slugify, "pos", "team", "d_pts", "pts") for r in stock.get("up") or []],
        "down": [_player(r, slugify, "pos", "team", "d_pts", "pts") for r in stock.get("down") or []],
        "gems": [_player(r, slugify, "pos", "team", "usage", "metric", "ecr", "rostered") for r in p.get("gems") or []],
        "news": [_news(it) for it in p.get("news") or []],
        # Since 2026-09-29; a packet from before has no `starters` and the row says nothing new.
        "starters": [_starter(r, slugify, schedule) for r in p.get("starters") or []],
    }


def report(block):
    if not block:
        return "Digest: no weekly_digest.json, so the view says so"
    lead = block["lead"]
    return (f"Digest: week {block['week']} as of {block['asof']}, lead "
            + (f"{lead['rule']}[{lead['index']}]" if lead else "none")
            + f", {len(block['hurt'])} hurt, {len(block['adds'])} adds, {len(block['news'])} news"
            + f", {len(block['finals'])} final")
