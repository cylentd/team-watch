"""LIVE_RECAP: This week > Recap (2026-10-05, storyboard option C), from ff-jarvis's weekly recap file.

Everything here is league-wide and public: the games with Claude's Preview call and its grade, the
Preview record, the top three at QB, RB, WR and TE plus K and DST, who smashed and who busted
against the projection, who left hurt, the touchdown leaders, and the week's top scorer for the banner.

PRIVATE FIELDS NEVER CROSS. The recap file also holds a `leagues` block (David's lineups) and, on every
player, `rostered` and `slot`. Rows here are built from a whitelist of fields, so none of the three can
get in; tests/test_recap_data.py pins it.

WHICH WEEK. The newest file with at least half its games final (the Digest banner's rule, so Monday
morning shows Sunday, not the Friday after one Thursday game); with none, the newest file.

OLD FILES. Weeks 1-3 were written before ff-jarvis added `games`, `preview_record`, `k_dst`,
`left_hurt`, each player's TD split and `line`. The block always has every key: what a file lacks is
[] (lists), None (preview_record, top's line) or, for `games`, the file's own `slate` of finals.
Smashed and Busts are ff-jarvis's `smashed` and `busts_shown` (the Digest's own picks, since
2026-10-05), never the file's older `busts` cut; an old file has neither, so both are [].

THE LINE. A player's `line` is ff-jarvis's structured box line, passed through as it is. The page words
it with the Digest's JS (`dgStatLine`, `dgTopLine`, `dgBoxPills`, surface/digest/), not a second copy here.
"""
from digest import _left      # the Digest's cut of a left-hurt row: slug, injury tag, "exits early"

POS = ("QB", "RB", "WR", "TE")
TOP = 3                    # per position, and for K and DST
SMASH_CAP = 5              # display caps only: who smashed and who busted is ff-jarvis's pick (played_facts),
BUST_CAP = 10              # the same lists the Digest showed
HURT_CAP = 10
TD_CAP = 30
TD_KINDS = ("pass_td", "rush_td", "rec_td", "ret_td")
# What a player row carries. `rostered` and `slot` are absent on purpose.
ROW_FIELDS = ("pos", "team", "game_id", "actual", "proj", "diff", "line", *TD_KINDS)
PICK_FIELDS = ("winner", "score", "win_pct", "ats_side", "ats_conf", "total_call", "total_conf",
               "spread_home", "total_line", "headline", "frozen", "su_hit", "ats_hit", "total_hit")
RECORD_FIELDS = ("n", "su", "ats", "ats_pass", "total", "by_conf")


def _counts(r):
    """(games final, games in the week) from a recap file, old shape or new."""
    games = r.get("games")
    if games:
        return sum(1 for g in games if g.get("final")), len(games)
    done = len(r.get("slate") or [])
    return done, done + len(r.get("pending") or [])


def pick_week(files):
    """The newest recap with half its games final, else the newest; None without any file."""
    newest = None
    for r in files:
        newest = newest or r
        done, total = _counts(r)
        if total and done * 2 >= total:
            return r
    return newest


def _row(r, slugify):
    return {"n": r["name"], "slug": slugify(r["name"]), **{k: r.get(k) for k in ROW_FIELDS}}


def _tds(r):
    return sum(r.get(k) or 0 for k in TD_KINDS)


def _kd(r, slugify):
    """A kicker or a defense: a defense's name is its team code and has no face, so no slug."""
    return {"n": r["name"], "slug": slugify(r["name"]) if r.get("pos") == "K" else None,
            **{k: r.get(k) for k in ("pos", "team", "game_id", "actual", "box")}}


def _game(g):
    p = g.get("preview")
    return {"game_id": g["game_id"], "kickoff": g.get("kickoff"), "away": g["away"], "home": g["home"],
            "away_pts": g.get("away_pts"), "home_pts": g.get("home_pts"), "final": bool(g.get("final")),
            "preview": {k: p.get(k) for k in PICK_FIELDS} if p else None}


def _games(r):
    """Every game of the week; an old file has only its finals, as `slate`."""
    if r.get("games"):
        return [_game(g) for g in r["games"]]
    return [_game({**s, "final": True}) for s in sorted(r.get("slate") or [], key=lambda s: s["game_id"])]


def live_recap(files, slugify):
    """None when ff-jarvis has written no recap file: the view then says so."""
    r = pick_week(files)
    if not r or "week" not in r:
        return None
    players = [p for p in r.get("players") or [] if p.get("key") and p.get("name")]
    by_key = {p["key"]: p for p in players}
    row = lambda keys: [_row(by_key[k], slugify) for k in keys if k in by_key]
    stood = r.get("standouts") or {}
    stars = [k for pos in POS for k in (stood.get(pos) or [])[:TOP]]
    scored = [p for p in players if p.get("actual") is not None]
    top = max(scored, key=lambda p: (p["actual"], p["key"]), default=None)
    kd = r.get("k_dst") or {}
    tds = sorted((p for p in players if _tds(p)), key=lambda p: (-_tds(p), -(p.get("actual") or 0), p["key"]))
    done, total = _counts(r)
    rec = r.get("preview_record")
    return {
        "season": r.get("season"), "week": r["week"], "asof": r.get("asof"), "complete": bool(r.get("complete")),
        "n_games": total, "n_final": done, "games": _games(r),
        "preview_record": {k: rec.get(k) for k in RECORD_FIELDS} if rec else None,
        "top": _row(top, slugify) if top else None,
        "stars": row(stars),
        "k": [_kd(x, slugify) for x in (kd.get("K") or [])[:TOP]],
        "dst": [_kd(x, slugify) for x in (kd.get("DST") or [])[:TOP]],
        "smashed": row((r.get("smashed") or [])[:SMASH_CAP]),
        "busts": row((r.get("busts_shown") or [])[:BUST_CAP]),
        "tds": [{**_row(p, slugify), "td": _tds(p)} for p in tds[:TD_CAP]],
        "left_hurt": [_left(x, slugify) for x in (r.get("left_hurt") or [])[:HURT_CAP] if x.get("name")],
    }


def report(block):
    if not block:
        return "Recap: no recap file, so the view says so"
    return (f"Recap: week {block['week']}, {block['n_final']}/{block['n_games']} games final, "
            f"{len(block['stars'])} stars, {len(block['tds'])} TD scorers, {len(block['left_hurt'])} left hurt, "
            f"{'Preview record' if block['preview_record'] else 'no Preview record'}")
