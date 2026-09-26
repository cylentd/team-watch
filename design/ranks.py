"""LIVE_RANKS: this week's ranking at each position, and a FLEX ranking, each split into tiers
(2026-09-26). Players > Ranks draws it (js/surface/ranks/).

The rank is the one the roster cards already use (projections.position_ranks over ff-jarvis's
`model.market.projections`, half-PPR, a player Sleeper lists as not playing left out), so a
player is the same number on his card and in the list.

Tiers are natural breaks in projected points: the split of the list into k groups that keeps
each group's points closest together (optimal 1-D k-means, exact by dynamic programming). A tier
line then marks the widest drops, the way Boris Chen's tiers do, with a fixed count per position
as his are. A plain "break where the drop is large" rule was tried on week 3 and gave WR tiers of
1, 2, 1, 1, 2 and 41: the top is sparse and the middle is dense, so no one threshold fits both.

Self-contained like the other cuts: the raw block, slugify and the out-list come in as arguments.
"""
from projections import position_ranks, unavailable

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


def live_ranks(raw, slugify, status=None):
    """LIVE_RANKS: {scoring, through, rows, flex}, or None when ff-jarvis has not written the file.
    Both are lists of {slug, n, pos, team, opp, home, pts, rank, tier}, best first: `rows` holds
    every position's list one after another, each tiered on its own; `flex` is RB/WR/TE together,
    tiered together. `rank` is the position rank (the card's), on a FLEX row too; a FLEX row's
    place is its index."""
    players = (raw or {}).get("players") or []
    if not players:
        return None
    gone = unavailable(status, slugify)
    ranks = position_ranks(players, slugify, gone)
    rows = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if slug not in ranks or p.get("pts") is None:
            continue
        prev = rows.get(slug)
        if prev is None or p["pts"] > prev["pts"]:
            rows[slug] = {"slug": slug, "n": p.get("name"), "pos": p.get("pos"), "team": p.get("team"),
                          "opp": p.get("opp"), "home": _home(p), "pts": round(p["pts"], 2),
                          "rank": ranks[slug][0], "tier": None}
    lists = {}
    for pos, (depth, k) in DEPTH.items():
        want = FLEX if pos == "FLEX" else (pos,)
        top = sorted((r for r in rows.values() if r["pos"] in want), key=lambda r: (-r["pts"], r["slug"]))[:depth]
        tiers = natural_breaks([r["pts"] for r in top], k)
        lists[pos] = [{**r, "tier": t} for r, t in zip(top, tiers)]
    return {"scoring": raw.get("scoring"), "through": raw.get("through"),
            "rows": [r for pos in DEPTH if pos != "FLEX" for r in lists[pos]], "flex": lists["FLEX"]}
