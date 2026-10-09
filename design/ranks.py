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
from week_ranks import load_week_ranks   # noqa: F401  (build.py loads the file through here)

# How deep each list goes, and how many tiers it is split into.
DEPTH = {"QB": (32, 8), "RB": (60, 12), "WR": (72, 14), "TE": (32, 8), "FLEX": (100, 16)}
FLEX = ("RB", "WR", "TE")
SCORING_WORD = {"half": "half-PPR"}   # week_ranks says "half"; the heading says the scoring the way the projections do
FALLBACK_WORDS = "Ranks: week_ranks missing, so the old cut (natural breaks of our projections)"


def report(ranks):
    """build.py's one-line summary of LIVE_RANKS, naming where its order came from."""
    if not ranks:
        return "Ranks: none, so no Ranks view"
    lists = {pos: [r for r in ranks["rows"] if r["pos"] == pos] for pos in DEPTH if pos != "FLEX"}
    lists["FLEX"] = ranks["flex"]
    head = "Ranks: week_ranks" if ranks.get("from") == "week_ranks" else FALLBACK_WORDS
    return head + " · " + " · ".join(f"{pos} {len(rs)} in {max((r['tier'] for r in rs), default=0)} tiers" for pos, rs in lists.items())


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


def _matchup(p, key="pts"):
    """The points this week's defense adds or takes against an average one: ff-jarvis's calibrated
    `matchup.pts` (2026-09-29), QB/RB/TE only (the WR effect tests null, so a WR has none), and with
    key="priced" the part of it already inside `pts` (METHODOLOGY 12.61 kept the projection's own
    pricing: the full effect made its MAE worse). Null when ff-jarvis wrote none. The page decides
    what is big enough to show."""
    v = (p.get("matchup") or {}).get(key)
    return round(v, 1) if isinstance(v, (int, float)) and p.get("pos") != "WR" else None


def live_ranks(raw, slugify, status=None, schedule=None, week_ranks=None):
    """LIVE_RANKS: {scoring, week, off, from, rows, flex}. With ff-jarvis's week_ranks (design/week_ranks.py) the lists
    are theirs (`from` "week_ranks", ledger #23, 2026-10-08); without the file it is the old cut from the projections
    (`from` "projections", None when ff-jarvis has not written those either), kept as the fallback."""
    players = (raw or {}).get("players") or []
    if week_ranks:
        return _from_lists(week_ranks, players, slugify)
    return _from_projections(raw, slugify, status, schedule)


def _from_projections(raw, slugify, status=None, schedule=None):
    """The old cut: {scoring, week, off, from, rows, flex}, or None when ff-jarvis has not written the file.
    Both lists hold {slug, n, pos, team, opp, home, kick, inj, mu, mx, mxp, pts, floor, ceil, rank, tier}, best
    first (`floor` and `ceil`: ff-jarvis's 10th and 90th percentile outcome, null without a band, never computed
    here). Every position, running backs too, orders and tiers by `pts` (ledger #96, 2026-10-09; a back followed the
    books' `rank_pts` until then, with a "No line" flag, ff-jarvis METHODOLOGY 12.86 and 12.87).
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
            rows[slug] = _row(p, slug)
    off = sorted({rows[s]["team"] for s in done if s in rows})
    live = [r for r in rows.values() if r["slug"] not in done]
    lists, place = {}, {}
    for pos, (depth, k) in DEPTH.items():
        want = FLEX if pos == "FLEX" else (pos,)
        ordered = sorted((r for r in live if r["pos"] in want), key=lambda r: (-r["pts"], r["slug"]))
        if pos != "FLEX":
            place.update({r["slug"]: i + 1 for i, r in enumerate(ordered)})
        top = ordered[:depth]
        lists[pos] = [{**r, "tier": t} for r, t in zip(top, natural_breaks([r["pts"] for r in top], k))]
    for rs in lists.values():
        for r in rs:
            r["rank"] = place[r["slug"]]
    return {"scoring": raw.get("scoring"), "week": week, "off": off, "from": "projections",
            "rows": [r for pos in DEPTH if pos != "FLEX" for r in lists[pos]], "flex": lists["FLEX"]}


def _row(p, slug):
    """One list row from a projections player (a dict with nothing in it when ff-jarvis's projections do not hold him)."""
    return {"slug": slug, "n": p.get("name"), "pos": p.get("pos"), "team": p.get("team"),
            "opp": p.get("opp"), "home": _home(p), "kick": kick_iso(p), "inj": INJ.get(p.get("injury")),
            "mu": _makeup(p.get("mu"), p.get("pos")), "mx": _matchup(p), "mxp": _matchup(p, "priced"),
            "pts": round(p["pts"], 2) if p.get("pts") is not None else None,
            "shown": round(p["pts"], 2) if p.get("pts") is not None else None, "floor": p.get("floor"), "ceil": p.get("ceil"),
            "rank": None, "tier": None}


def _from_lists(doc, players, slugify):
    """LIVE_RANKS from ff-jarvis's week_ranks lists, drawn as the producer ships them (ledger #98, 2026-10-09; David chose
    "our own rank and tiers" on 2026-10-08, and ff-jarvis #88 now orders and tiers each list on our `pts`, frozen at
    kickoff). The lists say who is in each one, his game and kickoff, his `rank` and `tier`. The number is the projection
    every other view prints (his projections row's `pts`, else the list's own), printed as `shown`. A position row's
    `rank` is the list's, so a card's rank is the one drawn here; a FLEX row takes his place at his own position. `val`,
    `src` and `rank_pts` (the books' price, in no order) stay behind. What only the projections hold (home,
    injury tag, the points' makeup, the matchup, the band) is read off his projections row by slug, null when he has none."""
    wk = doc["weekly"]
    held = {}
    for p in players:
        slug = slugify(p.get("name") or "")
        if slug and p.get("pts") is not None and (slug not in held or p["pts"] > held[slug]["pts"]):
            held[slug] = p
    place, lists = {}, {}
    for pos, (_, k) in DEPTH.items():   # QB RB WR TE first, FLEX last: a FLEX row's rank is his place at his own position
        rows = []
        for r in wk["lists"][pos]:
            slug = slugify(r["name"])
            mine = held.get(slug)
            pts = round(mine["pts"] if mine else r["pts"], 2)
            rows.append({**_row(mine or {}, slug), "n": r["name"], "pos": r["pos"], "team": r["team"], "opp": r["opp"],
                         "kick": r["kickoff"], "pts": pts, "shown": pts,
                         "rank": r["rank"], "tier": r["tier"]})
        if pos == "FLEX":
            for row in rows:
                row["rank"] = place.get(row["slug"])
        else:
            place.update({row["slug"]: row["rank"] for row in rows})
        lists[pos] = rows
    return {"scoring": SCORING_WORD.get(wk["scoring"], wk["scoring"]), "week": wk["week"], "off": sorted(wk["off"]), "from": "week_ranks",
            "rows": [r for pos in DEPTH if pos != "FLEX" for r in lists[pos]], "flex": lists["FLEX"]}


def ranks_places(block):
    """slug -> (rank, of): his place in his position's list as Ranks draws it and the list's length, the roster cards' rank.
    None for the old cut (no week_ranks file), whose cards keep projections.position_ranks, ordered the same way."""
    if not block or block.get("from") != "week_ranks":
        return None
    out = {}
    for pos in DEPTH:
        rows = [r for r in block["rows"] if r["pos"] == pos]
        out.update({r["slug"]: (r["rank"], len(rows)) for r in rows})
    return out
