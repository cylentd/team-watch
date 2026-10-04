"""LIVE_SSB: what Start / Sit's picker and matchup board read (This week > Start / Sit, leaf `matchups`).

    {week, fp: {slug: {ecr, pos}}, board: {POS: {avg, n, best, worst}}, out: {slug: [{n, pos, s}]}}

- `fp`: FantasyPros' position rank for every player in ff-jarvis's `expert_ranks.json` (`pos_rank`
  "WR14" -> ecr 14, `pos` the file's `player_position_id`), keyed by the page's slug. Kickers and
  defenses are in the file, so they are here. No file, or a file whose `week` is not the board's: {}.
- `board`: per position, the matchups of the page's week. Each game gives two rows, an offense
  (`team`) and the defense it faces (`opp`), with the points that defense allows a game at the
  position (`pts`) and its rank (32 = most allowed). `best` is the four most allowed, `worst` the
  four fewest; `avg` is the league's average allowed, `n` the games the most-played defense has.
  A team with no game this week (a bye) has no row. Team codes are the projections' (LA, WAS), the
  same as LIVE_RANKS and defense_form.json; the schedule says LAR and WSH, which `alias` undoes.
- `out`: for each QB/RB/WR/TE in LIVE_RANKS, the same-team QB/RB/WR/TE teammates who are Out, IR or
  Doubtful this week (Sleeper's latest status over LIVE_PREVIEW's per-game `inj`), most-used first, at most MAX_OUT. A teammate
  whose usage is under MIN_AVG points, or unknown, is a deep backup and left out. Usage is his
  recorded average, else his projected points when he is still ranked (a Doubtful has no average).
  `n` is the full name ("Jalen Coker"; the page shortens it); `s` is Out, IR or Doubtful.

Nothing here computes a model number: every figure is one ff-jarvis wrote. Self-contained like the
other cuts: the raw blocks and slugify come in as arguments, and `problems` is the shape check
contract.py runs on the result.
"""
import re

from projections import OUT_INJURY

POS = ("QB", "RB", "WR", "TE")
MATES = POS     # a starting QB out moves his receivers most (QB added 2026-10-03: J. Daniels, week 4)
SITS = {"out": "Out", "ir": "IR", "d": "Doubtful"}   # LIVE_PREVIEW's `s` codes that will not play
MIN_AVG = 5.0    # half-PPR points a game below which a teammate is a deep backup, not a reason
SHOW = 4         # rows in each of a position's best and worst lists
MAX_OUT = 3      # teammates named for one player


def _fp(raw, slugify, week):
    """FantasyPros' ranks by slug, or {} when the file is not `week`'s (it carries its own `week`)."""
    out = {}
    if not raw or week is None or raw.get("week") != week:
        return out
    for p in raw.get("players") or []:
        name, pos = p.get("player_name"), p.get("player_position_id")
        m = re.search(r"(\d+)$", str(p.get("pos_rank") or ""))
        if not name or not pos or not m:
            continue
        slug, ecr = slugify(name), int(m.group(1))
        if slug not in out or ecr < out[slug]["ecr"]:
            out[slug] = {"ecr": ecr, "pos": pos}
    return out


def _games(schedule):
    """(the page's week, [(home, away)] of that week in the projections' team codes)."""
    week = (schedule or {}).get("week")
    back = {v: k for k, v in ((schedule or {}).get("alias") or {}).items()}
    return week, [(back.get(g["home"], g["home"]), back.get(g["away"], g["away"]))
                  for g in (schedule or {}).get("games") or [] if week is not None and g.get("week") == week]


def _board(defense, games):
    form = (defense or {}).get("form") or {}
    teams = form.get("teams") or {}
    league = (form.get("league") or {}).get("current") or {}
    played = max(((t.get("current") or {}).get("games") or 0 for t in teams.values()), default=0)
    out = {}
    for pos in POS:
        rows = []
        for home, away in games:
            for offense, defender in ((away, home), (home, away)):
                v = (((teams.get(defender) or {}).get("current") or {}).get("pos") or {}).get(pos) or {}
                if v.get("pts_pg") is not None and v.get("rank") is not None:
                    rows.append({"team": offense, "opp": defender, "pts": v["pts_pg"], "rank": v["rank"]})
        if rows and league.get(pos) is not None:
            out[pos] = {"avg": league[pos], "n": played,
                        "best": sorted(rows, key=lambda r: (-r["pts"], r["team"]))[:SHOW],
                        "worst": sorted(rows, key=lambda r: (r["pts"], r["team"]))[:SHOW]}
    return out


def _sits(code):
    """A Sleeper injury code as Out / IR / Doubtful, or None when he plays (healthy, Questionable)."""
    if code == "IR":
        return "IR"
    return "Out" if code in OUT_INJURY else "Doubtful" if code == "Doubtful" else None


def _hurt(ranks, preview, status, slugify):
    """team -> [{slug, n, pos, s, avg}]: who will not play. The status is Sleeper's latest (the
    Saturday 8:45 pm run), which overrides the preview's, written once at midday (2026-10-03:
    McLaurin went Questionable -> Doubtful that evening); the preview still gives team and usage."""
    by = {}
    for g in (preview or {}).get("games") or []:
        for team, rows in (g.get("inj") or {}).items():
            for r in rows:
                if r.get("pos") in MATES and r.get("slug"):
                    by[r["slug"]] = {"slug": r["slug"], "n": r["n"], "pos": r["pos"], "team": team,
                                     "s": SITS.get(r.get("s")), "avg": r.get("avg")}
    if status:
        ranked = {r["slug"]: r for r in (ranks or {}).get("rows") or []}
        live = {slugify(v.get("name") or ""): v for v in status.values()}
        for slug, m in by.items():
            if slug in live:
                m["s"] = _sits(live[slug].get("injury"))
        for slug, v in live.items():
            if slug not in by and slug in ranked and _sits(v.get("injury")) and ranked[slug]["pos"] in MATES:
                r = ranked[slug]
                by[slug] = {"slug": slug, "n": r["n"], "pos": r["pos"], "team": r["team"], "s": _sits(v["injury"]), "avg": None}
    hurt = {}
    for m in by.values():
        if m["s"]:
            hurt.setdefault(m["team"], []).append(m)
    return hurt


def _out(ranks, preview, status=None, slugify=None):
    hurt = _hurt(ranks, preview, status, slugify)
    pts = {r["slug"]: r["pts"] for r in (ranks or {}).get("rows") or []}
    out = {}
    for r in (ranks or {}).get("rows") or []:
        mates = []
        for m in hurt.get(r["team"]) or []:
            use = m.get("avg") if m.get("avg") is not None else pts.get(m.get("slug"))
            if m.get("slug") != r["slug"] and use is not None and use >= MIN_AVG:
                mates.append((-use, m["slug"], {"n": m["n"], "pos": m["pos"], "s": m["s"]}))
        if mates:
            out[r["slug"]] = [m[2] for m in sorted(mates, key=lambda x: x[:2])[:MAX_OUT]]
    return out


def live_ssb(ranks, schedule, preview, defense, experts, slugify, status=None):
    """LIVE_SSB from LIVE_RANKS, LIVE_SCHEDULE, LIVE_PREVIEW, sources.load_defense()'s block, the raw
    expert_ranks.json and sources.load_status(). Always a dict with all four keys; a source that is
    missing leaves its part empty."""
    week, games = _games(schedule)
    week = week if week is not None else (ranks or {}).get("week")
    return {"week": week, "fp": _fp(experts, slugify, week), "board": _board(defense, games),
            "out": _out(ranks, preview, status, slugify)}


def report(ssb):
    """build.py's one-line summary of LIVE_SSB."""
    board = ssb["board"]
    rows = max((len(b["best"]) for b in board.values()), default=0)
    return (f"Start/Sit board: week {ssb['week']}, {len(ssb['fp'])} FantasyPros ranks, "
            f"{len(board)} positions boarded ({rows} per list), {len(ssb['out'])} players with a teammate out")


def problems(obj):
    """Missing fields of a LIVE_SSB as `LIVE_SSB.board['QB'].best[0].pts`, for contract.py (nested maps and
    lists are beyond its one-level row specs)."""
    miss = [f"LIVE_SSB.fp[{s!r}].{k}" for s, v in (obj.get("fp") or {}).items() for k in ("ecr", "pos") if k not in v]
    for pos, b in (obj.get("board") or {}).items():
        miss += [f"LIVE_SSB.board[{pos!r}].{k}" for k in ("avg", "n", "best", "worst") if k not in b]
        for side in ("best", "worst"):
            for i, row in enumerate(b.get(side) or []):
                miss += [f"LIVE_SSB.board[{pos!r}].{side}[{i}].{k}" for k in ("team", "opp", "pts", "rank") if k not in row]
    for slug, rows in (obj.get("out") or {}).items():
        for i, row in enumerate(rows):
            miss += [f"LIVE_SSB.out[{slug!r}][{i}].{k}" for k in ("n", "pos", "s") if k not in row]
    return miss
