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


def _game(g):
    return {"away": g["away"], "home": g["home"], "kick": _kick(g.get("kickoff"))} if g else None


def _wx(g):
    return {"away": g["away"], "home": g["home"], "kick": _kick(g.get("kickoff")), "temp_f": g.get("temp_f"),
            "wind_mph": g.get("wind_mph") or 0, "precip_pct": g.get("precip_pct") or 0,
            "short": g.get("short"), "lead": bool(g.get("lead")), "bar": g.get("bar") or "wind"}


def _news(it):
    """The headline split at its injury tag: "Jaylen Wright (stinger/foot) doubtful to play Sunday"
    reads as name "Jaylen Wright" and rest "doubtful to play Sunday". A headline with no tag keeps
    its words whole in `rest` and has no name."""
    headline = it.get("headline") or ""
    name, slugs = news_player(headline)
    rest = headline.split(")", 1)[1].strip() if name and ")" in headline else headline
    t = _local(it.get("created"))
    return {"when": _clock(t) if t else None, "headline": headline, "kind": news_kind({"title": headline}),
            "n": it.get("name") or name, "rest": rest, "slugs": slugs}


def live_digest(p, slugify):
    """None when ff-jarvis has written no packet: the view then says so instead of guessing."""
    if not p or "week" not in p:
        return None
    m, wx, adds, stock = p.get("matchups") or {}, p.get("weather") or {}, p.get("adds") or {}, p.get("stock") or {}
    best = (m.get("best") or {})
    rec = m.get("record")
    return {
        "season": p.get("season"), "week": p["week"], "asof": p.get("asof"), "lead": p.get("lead"),
        "rules": p.get("rules"),   # ff-jarvis's thresholds, quoted by the row feet; never re-applied here
        "hurt": [{**_player(r, slugify, "pos", "team", "status", "was", "injury", "new", "rank", "rostered"),
                  "game": _game(r.get("game"))} for r in p.get("hurt") or []],
        "calls": m.get("calls") or 0,
        "record": ({"through": rec["through"], "ours": rec["ours"], "pl": rec["pl"]} if rec else None),
        "best": [_player(best[pos], slugify, "pos", "team", "opp", "home", "pts", "why") for pos in POS if best.get(pos)],
        "wx": [_wx(g) for g in wx.get("games") or []],
        "near": _wx(wx["near"]) if wx.get("near") else None,
        "adds_weeks": adds.get("weeks") or [],
        "adds": [_player(r, slugify, "pos", "team", "was", "now", "delta") for r in adds.get("rows") or []],
        "top5": [{"pos": pos, **_player(r, slugify, "team", "opp", "pts")}
                 for pos in POS for r in (p.get("top5") or {}).get(pos) or []],
        "up": [_player(r, slugify, "pos", "team", "d_pts", "pts") for r in stock.get("up") or []],
        "down": [_player(r, slugify, "pos", "team", "d_pts", "pts") for r in stock.get("down") or []],
        "gems": [_player(r, slugify, "pos", "team", "usage", "metric", "ecr", "rostered") for r in p.get("gems") or []],
        "news": [_news(it) for it in p.get("news") or []],
    }


def report(block):
    if not block:
        return "Digest: no weekly_digest.json, so the view says so"
    lead = block["lead"]
    return (f"Digest: week {block['week']} as of {block['asof']}, lead "
            + (f"{lead['rule']}[{lead['index']}]" if lead else "none")
            + f", {len(block['hurt'])} hurt, {len(block['adds'])} adds, {len(block['news'])} news")
