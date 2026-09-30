"""League > Trades: ff-jarvis's trade verdicts (model.season.trade_verdicts) cut to what the page draws.

Storyboard https://claude.ai/artifact/EhbDwDUZ7ERb2iNfAqaKjn (2026-09-28). The numbers are ff-jarvis's;
nothing here computes a verdict. It names managers (yahoo_league_managers.json, the key Records uses),
shortens player names to initials, drops a manager Records keeps out of the book (league_record_skip.json)
from the ranking, and orders the lists the page shows. Copy stays in content.json: a trade's "decided"
lines ship as {k, m, seed, without}, and the JS words them.
"""
import json
import os

import leagues

SKIP =os.path.join(os.path.dirname(__file__), "league_record_skip.json")
FEW = 4          # fewer trades than this and a manager's row is dimmed: too few to rank fairly
HEISTS = 3
SUFFIX = ("Jr.", "Jr", "Sr.", "Sr", "II", "III", "IV", "V")


def skip_keys(path=SKIP):
    if not os.path.exists(path):
        return frozenset()
    return frozenset(m["key"] for m in json.load(open(path, encoding="utf-8")).get("managers", []))


def short(name):
    """ "Ja'Marr Chase" -> "J. Chase" (initials rule); a defense ("Bills") stays whole."""
    parts = name.split()
    return name if len(parts) < 2 else f"{parts[0][0]}. {' '.join(parts[1:])}"


def surname(name):
    parts = [p for p in name.split() if p not in SUFFIX]
    return parts[-1] if parts else name


def _side(s, slugify=None):
    return {"m": str(s["manager"]), "got": [short(p["name"]) for p in s["players"]],
            "slugs": [slugify(p["name"]) if slugify else None for p in s["players"]], "tree": s["tree"],
            "par": s["par"], "after": s["after"], "via": [short(x["player"]) for x in s.get("via", [])]}


def _decided(t):
    """What the trade decided, as data: the title, then each playoff spot or bye it moved."""
    out = [{"k": "title", "m": str(t["won_title"]), "seed": None, "without": None}] if t.get("won_title") else []
    p = t.get("playoffs") or {}
    n, byes = p.get("n", 6), p.get("byes", 2)
    for m, c in (p.get("changed") or {}).items():
        a, b = c["seed"], c["without"]
        k = "in" if a <= n < b else "out" if b <= n < a else "bye" if a <= byes < b else "nobye" if b <= byes < a else None
        if k:
            out.append({"k": k, "m": str(m), "seed": a, "without": b})
    return out


def _trade(i, t, slugify=None):
    a, b = t["sides"]
    win, lose = (a, b) if a["tree"] >= b["tree"] else (b, a)
    hw, hl = (a, b) if a["par"] >= b["par"] else (b, a)
    return {"id": i, "season": t["season"], "week": t["week"], "open": t["open"], "margin": t["margin"],
            "win": _side(win, slugify), "lose": _side(lose, slugify),
            "held": {"win": str(hw["manager"]), "margin": round(hw["par"] - hl["par"], 1)},
            "decided": _decided(t)}


def live_trades(verdicts, managers, skip=None, slugify=None, key="yahoo"):
    """The LIVE_TRADES block (or another Yahoo league's, by `key`, which picks its record-skip file), or
    None without the verdicts file. `slugify` names each traded and cursed player's headshot
    (heads/<slug>.webp); the page draws initials when there is none."""
    if not verdicts or not verdicts.get("trades"):
        return None
    skip = skip_keys(leagues.skip_file(key)) if skip is None else skip
    names = (managers or {}).get("managers", {})
    trades = [_trade(i, t, slugify) for i, t in enumerate(verdicts["trades"])]
    closed = [t for t in trades if not t["open"]]
    ranking = [{"m": k, **{f: s[f] for f in ("trades", "won", "lost", "per_trade", "lo", "hi", "shrunk")},
                "few": s["trades"] < FEW}
               for k, s in verdicts.get("managers", {}).items() if k not in skip]
    ranking.sort(key=lambda r: -r["shrunk"])
    decided = sorted((t for t in closed if t["decided"]),
                     key=lambda t: (not any(d["k"] == "title" for d in t["decided"]), -t["season"], -t["margin"]))
    curses = [{"player": short(c["player"]), "surname": surname(c["player"]), "kind": c["kind"], "n": c["n"],
               "slug": slugify(c["player"]) if slugify else None,
               "moves": [{"season": m["season"], "week": m["week"], "from": str(m["from"]), "to": str(m["to"]),
                          "lost": m["sender_lost"], "margin": m["margin"], "open": m["open"]} for m in c["moves"]]}
              for c in verdicts.get("curses", [])]
    seasons = [t["season"] for t in closed]
    return {"since": min(seasons) if seasons else None, "through": max(seasons) if seasons else None,
            "n": len(closed), "names": {k: v for k, v in names.items()},
            "ranking": ranking, "trades": trades,
            "heists": [t["id"] for t in sorted(closed, key=lambda t: -t["margin"])[:HEISTS]],
            "decided": [t["id"] for t in decided], "curses": curses}


def report(block, key="yahoo"):
    head = "Trades" if key == "yahoo" else f"Trades ({key})"
    if not block:
        return f"{head}: none (no ff-jarvis {leagues.file(key, 'trade_verdicts')})"
    return (f"{head}: {len(block['trades'])} trades, {block['n']} closed {block['since']}-{block['through']}, "
            f"{len(block['ranking'])} managers ranked, {len(block['curses'])} curses")
