"""ff-jarvis's week_ranks.json (feed block `week_ranks`; METHODOLOGY 12.116/12.117; ledger #23, 2026-10-08): our rank and
tier at each position and FLEX, cut upstream. Stats > Ranks draws its order, rank and tier from these lists
(design/ranks.py) and the roster cards' rank reads the same ones (projections.live_projections).

    {v, generated, weekly: {season, week, scoring: "half", w, src_by_pos, tier_method, off: [team],
                            lists: {QB|RB|WR|TE|FLEX|K|DST: [row]}}, ros}
    row  {key, name, pos, team, opp, kickoff, rank, tier, val, pts, src, rank_pts}   (rank_pts: v2 only)

`val` is the list's order key and `src` says whose number it is: the page shows neither (David, 2026-10-08: readers
see one rank). `pts` is our projection. v2 (ff-jarvis 9ef94b4, 2026-10-08) adds `rank_pts`, the half-PPR number the
list is ordered and tiered by (QB/RB/TE the books' price where priced, else ours; FLEX its blend twin; WR points, but
the list is ordered by the blended rank, so `rank_pts` can step up down it). Ranks shows that number
(design/ranks.py); a v1 file without it shows `pts`. `val` is not points everywhere: never shown. Out players are already dropped and a row freezes at its kickoff. K and
D/ST rows are team-level; the K and D/ST tabs keep reading `dst_projections` (LIVE_DST). `ros` is ignored here.

Shape-checked where it enters: a malformed file fails the build, not the page. None when no file exists.
"""
import math

import sources

VERSIONS = (1, 2)
SCORING = "half"
POSITIONS = ("QB", "RB", "WR", "TE")
LISTS = POSITIONS + ("FLEX", "K", "DST")
TOP = ("v", "generated", "weekly")
WEEKLY = ("season", "week", "scoring", "off", "lists")
ROW = {"key", "name", "pos", "team", "opp", "kickoff", "rank", "tier", "val", "pts", "src"}
ROW_BY_VERSION = {1: ROW, 2: ROW | {"rank_pts"}}
LIMIT = 8   # problems reported at most


def load_week_ranks():
    """The file: feed block `week_ranks` first, `week_ranks.json` second; None when neither exists. A file that
    is there but malformed raises SystemExit naming the first wrong field (the producer checks before it writes,
    so this is a different file than it wrote). Lives here, not in sources.py, which is at its line budget."""
    doc = sources.feed_block(("week_ranks",), "weekly") or sources.read_first(sources.DWR / "week_ranks.json")
    if doc is None:
        return None
    bad = problems(doc)
    if bad:
        raise SystemExit("week_ranks.json: " + "; ".join(bad))
    return doc


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _list_problems(rows, where, fields):
    """rank 1..n, tier from 1 stepping 0 or 1, `val` non-increasing, unique keys, every field of the version present
    (v2: `rank_pts` a number, in no order, since only `rank` orders the list)."""
    bad, seen, tier, val = [], set(), 0, math.inf
    for i, r in enumerate(rows):
        at = f"{where}[{i}]"
        if not isinstance(r, dict) or set(r) != fields:
            bad.append(f"{at}: keys {sorted(r) if isinstance(r, dict) else type(r).__name__}, expected {sorted(fields)}")
            return bad
        if not _num(r["pts"]):
            bad.append(f"{at}.pts: {r['pts']!r} is not a number")
        if "rank_pts" in fields and not _num(r["rank_pts"]):
            bad.append(f"{at}.rank_pts: {r['rank_pts']!r} is not a number")
        if r["rank"] != i + 1:
            bad.append(f"{at}.rank: {r['rank']!r}, expected {i + 1}")
        if r["tier"] not in (tier, tier + 1) or r["tier"] < 1:
            bad.append(f"{at}.tier: {r['tier']!r} after {tier}")
        if not _num(r["val"]) or r["val"] > val:
            bad.append(f"{at}.val: {r['val']!r} is not a number at or below the row above")
        if r["key"] in seen:
            bad.append(f"{at}.key: duplicate {r['key']!r}")
        seen.add(r["key"])
        tier, val = r["tier"], r["val"] if _num(r["val"]) else val
    return bad


def problems(doc):
    """What is wrong with a week_ranks file, as `weekly.lists.RB[1].rank: why`, at most LIMIT of them; [] when whole."""
    if not isinstance(doc, dict) or any(k not in doc for k in TOP):
        return ["week_ranks: needs " + ", ".join(TOP)]
    if doc["v"] not in VERSIONS:
        return [f"v: {doc['v']!r}, expected " + " or ".join(map(str, VERSIONS))]
    wk = doc["weekly"]
    if not isinstance(wk, dict) or any(k not in wk for k in WEEKLY):
        return ["weekly: needs " + ", ".join(WEEKLY)]
    if wk["scoring"] != SCORING:
        return [f"weekly.scoring: {wk['scoring']!r}, expected {SCORING!r}"]
    bad = []
    for name in LISTS:
        rows = wk["lists"].get(name) if isinstance(wk["lists"], dict) else None
        if not isinstance(rows, list):
            bad.append(f"weekly.lists.{name}: missing")
            continue
        bad += _list_problems(rows, f"weekly.lists.{name}", ROW_BY_VERSION[doc["v"]])
    return bad[:LIMIT]


def position_ranks(doc, slugify):
    """slug -> (rank, of): his place in his position's list and the list's length (the roster cards' rank). A player
    the lists do not hold is not ranked: the cards would otherwise show a number the Ranks page does not."""
    out = {}
    for pos in POSITIONS:
        rows = doc["weekly"]["lists"][pos]
        out.update({slugify(r["name"]): (r["rank"], len(rows)) for r in rows})
    return out
