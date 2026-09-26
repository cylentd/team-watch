"""LIVE_RANKS: this week's ranking at each position, and a FLEX ranking, each split into tiers
(2026-09-26). Players > Ranks draws it (js/surface/ranks/).

The points are ff-jarvis's `model.market.projections` (half-PPR); a player Sleeper lists as not
playing is left out, as the roster cards leave him out. The rank is his place in this week's list,
so it can differ from his card's while a Thursday team's week-4 number still sits in the file.

Tiers are natural breaks in projected points: the split of the list into k groups that keeps
each group's points closest together (optimal 1-D k-means, exact by dynamic programming). A tier
line then marks the widest drops, the way Boris Chen's tiers do, with a fixed count per position
as his are. A plain "break where the drop is large" rule was tried on week 3 and gave WR tiers of
1, 2, 1, 1, 2 and 41: the top is sparse and the middle is dense, so no one threshold fits both.

Self-contained like the other cuts: the raw block, slugify and the out-list come in as arguments.
"""
from projections import kick_iso, slate, unavailable

# How deep each list goes, and how many tiers it is split into.
DEPTH = {"QB": (32, 8), "RB": (60, 12), "WR": (72, 14), "TE": (32, 8), "FLEX": (100, 16)}
FLEX = ("RB", "WR", "TE")


def report(ranks):
    """build.py's one-line summary of LIVE_RANKS."""
    if not ranks:
        return "Ranks: none, so no Ranks view"
    lists = {pos: [r for r in ranks["rows"] if r["pos"] == pos] for pos in DEPTH if pos != "FLEX"}
    lists["FLEX"] = ranks["flex"]
    return "Ranks: " + " · ".join(f"{pos} {len(rs)} in {max((r['tier'] for r in rs), default=0)} tiers" for pos, rs in lists.items())


def natural_breaks(xs, k):
    """Tier (1-based) per value of `xs`, sorted high to low, splitting it into at most k groups
    with the least total squared distance from each group's mean. O(k·n²); n is at most 100."""
    n = len(xs)
    k = max(1, min(k, n))
    if not n:
        return []
    s1, s2 = [0.0], [0.0]
    for x in xs:
        s1.append(s1[-1] + x)
        s2.append(s2[-1] + x * x)

    def cost(i, j):  # the spread of xs[i:j]
        s, m = s1[j] - s1[i], j - i
        return (s2[j] - s2[i]) - s * s / m

    inf = float("inf")
    best = [[inf] * (n + 1) for _ in range(k + 1)]
    cut = [[0] * (n + 1) for _ in range(k + 1)]
    best[0][0] = 0.0
    for t in range(1, k + 1):
        for j in range(t, n + 1):
            for i in range(t - 1, j):
                c = best[t - 1][i] + cost(i, j)
                if c < best[t][j]:
                    best[t][j], cut[t][j] = c, i
    tiers, j = [0] * n, n
    for t in range(k, 0, -1):
        i = cut[t][j]
        for q in range(i, j):
            tiers[q] = t
        j = i
    return tiers


def _home(p):
    """True at home, False away, None when the game string does not say ("LAC @ BUF")."""
    game, team = p.get("game") or "", p.get("team") or ""
    if "@" not in game or not team:
        return None
    away, home = (x.strip() for x in game.split("@", 1))
    return True if home == team else False if away == team else None


INJ = {"Questionable": "Q", "Doubtful": "D"}   # the ones who still play often enough to rank


def _makeup(mu, pos):
    """What the points are made of, as the producer's own means: passing and rushing yards for a
    QB (his TD mean is rushing only, so it is left off), else rushing and receiving yards,
    catches and touchdowns. Rounded for reading; null when the producer gave none."""
    mu = mu or {}
    keys = ("PASS", "RUSH") if pos == "QB" else ("RUSH", "REC", "RECS", "TD")
    out = {k: round(mu[k], 1) for k in keys if isinstance(mu.get(k), (int, float))}
    return out or None


def live_ranks(raw, slugify, status=None, schedule=None):
    """LIVE_RANKS: {scoring, week, off, rows, flex}, or None when ff-jarvis has not written the file.
    Both lists hold {slug, n, pos, team, opp, home, kick, inj, mu, pts, rank, tier}, best first:
    `rows` is every position's list one after another, each tiered on its own; `flex` is RB/WR/TE
    together, tiered together. `rank` is the place at the position in this week's list, on a FLEX
    row too; a FLEX row's own place is its index.

    One week only (projections.slate, the same cut the roster cards take): a team whose next game
    is a later week -- a Thursday game already played, a bye -- is left off and named in `off`."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    gone = unavailable(status, slugify)
    week, done = slate(players, slugify, schedule)
    rows = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if not slug or slug in gone or p.get("pts") is None or p.get("pos") not in ("QB", "RB", "WR", "TE"):
            continue
        prev = rows.get(slug)
        if prev is None or p["pts"] > prev["pts"]:
            rows[slug] = {"slug": slug, "n": p.get("name"), "pos": p.get("pos"), "team": p.get("team"),
                          "opp": p.get("opp"), "home": _home(p), "kick": kick_iso(p), "inj": INJ.get(p.get("injury")),
                          "mu": _makeup(p.get("mu"), p.get("pos")), "pts": round(p["pts"], 2), "rank": None, "tier": None}
    off = sorted({rows[s]["team"] for s in done if s in rows})
    live = [r for r in rows.values() if r["slug"] not in done]
    lists, place = {}, {}
    for pos, (depth, k) in DEPTH.items():
        want = FLEX if pos == "FLEX" else (pos,)
        ordered = sorted((r for r in live if r["pos"] in want), key=lambda r: (-r["pts"], r["slug"]))
        if pos != "FLEX":
            place.update({r["slug"]: i + 1 for i, r in enumerate(ordered)})
        top = ordered[:depth]
        tiers = natural_breaks([r["pts"] for r in top], k)
        lists[pos] = [{**r, "tier": t} for r, t in zip(top, tiers)]
    for rs in lists.values():
        for r in rs:
            r["rank"] = place[r["slug"]]
    return {"scoring": raw.get("scoring"), "week": week, "off": off,
            "rows": [r for pos in DEPTH if pos != "FLEX" for r in lists[pos]], "flex": lists["FLEX"]}
