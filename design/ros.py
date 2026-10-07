"""LIVE_ROS: rest-of-season value (2026-10-06), from ff-jarvis's ros_value.json (model.season.ros_value, METHODOLOGY 12.97).

Each QB/RB/WR/TE's expected half-PPR points from the week still to play through week 17: points a game times the games
he is expected to play. Stats > Ranks > Rest of season draws its rank by week; the profile's block draws the same.
The page computes nothing: this cut keeps the fields the page reads, in the page's names (`n` for the name, as the
other blocks), and drops the model's inputs (pace, xfp, f, att and the rest) and the weekly points of `hist`, which
the chart never shows (ROS points fall every week for everyone, so only the rank is charted).

    {season, week, through_week, last_week, generated,
     po_weeks, fp,
     players: [{slug, n, pos, team, rank, ros_pg, ros_pts, games_left, sched_left, hist, espn, po_rank, po_pts, po_games, fp}]}
    hist    [[week, rank], ...] ascending, one item for a player with no earlier week
    espn    {ros_pg, ros_pts, rank, hist}: the same on ESPN scoring, not backtested
    po_*    (2026-10-07, METHODOLOGY 12.109) the fantasy playoff weeks still to play, half-PPR: his rank among his position,
            points, games. Same points a game as the rest of season (12.109 failed), so only games and byes differ.
            po_weeks [15, 16, 17] is null when the file has none, and the page then has no Playoffs toggle.
    fp      block: {experts, updated} of ff-jarvis's ros_compare; player: {rank, gap, pts}, FantasyPros' ROS consensus
            position rank, theirs less ours, and their points. Every player the compare file joins (its `players` list; an
            older file's biggest gaps only) carries one; null for the rest and the page draws nothing. Display only.

None when ff-jarvis has written no file: the Rest of season tab is then absent and Ranks reads as it did before.
"""

import sources


def load_ros_value():
    """The ff-jarvis file (ros_value.json, METHODOLOGY 12.97): feed block `ros_value` first, the file second; None when
    neither exists. Lives here, not in sources.py, which is at its 500-line budget (tests/test_budgets.py)."""
    return sources.feed_block(("ros_value",), "players") or sources.read_first(sources.DWR / "ros_value.json")


def load_ros_compare():
    """ff-jarvis's FantasyPros comparison (ros_compare.json): feed block `ros_compare` first, the file second; None when
    neither exists. Display only: it moves no number."""
    return sources.feed_block(("ros_compare",), "positions") or sources.read_first(sources.DWR / "ros_compare.json")


TOP = ("season", "week", "through_week", "last_week", "generated")
PLAYER = ("slug", "pos", "team", "rank", "ros_pg", "ros_pts", "games_left", "sched_left", "po_rank", "po_pts", "po_games")


def _hist(rows):
    """[week, rank] only: the file's third item, the week's points, is not charted."""
    return [[r[0], r[1]] for r in rows or []]


def _espn(e):
    e = e or {}
    return {"ros_pg": e.get("ros_pg"), "ros_pts": e.get("ros_pts"), "rank": e.get("rank"), "hist": _hist(e.get("hist"))}


def _fp_rows(compare):
    """{(position, name key): the compare row} over every position's lists; {} without a file."""
    rows = {}
    for pos, v in ((compare or {}).get("positions") or {}).items():
        # `players` lists every joined player; an older file has only the biggest gaps each way
        for r in v.get("players") or (v.get("higher") or []) + (v.get("lower") or []):
            rows[(pos, r.get("key"))] = r
    return rows


def _fp(p, rows):
    """FantasyPros' position rank for him, its points, and the gap (theirs less ours, ours as the page shows it: the
    compare file is written earlier in the day than the value file, so its own gap can be a spot off). None when
    FantasyPros has no row for him in the file."""
    r = rows.get((p.get("pos"), p.get("key")))
    if not r or r.get("fp_pos_rank") is None or p.get("rank") is None:
        return None
    return {"rank": r["fp_pos_rank"], "gap": r["fp_pos_rank"] - p["rank"], "pts": r.get("fp_pts")}


def live_ros(raw, compare=None):
    if not raw or not raw.get("players"):
        return None
    rows = _fp_rows(compare)
    players = [{**{k: p.get(k) for k in PLAYER}, "n": p.get("name"), "hist": _hist(p.get("hist")), "espn": _espn(p.get("espn")),
                "fp": _fp(p, rows)} for p in raw["players"]]
    weeks = ((raw.get("rules") or {}).get("playoffs") or {}).get("weeks")
    fp = {"experts": compare.get("experts"), "updated": compare.get("fp_last_updated")} if rows else None
    return {**{k: raw.get(k) for k in TOP}, "players": players,
            "po_weeks": weeks if any(p["po_rank"] is not None for p in players) else None, "fp": fp}


def report(block):
    if not block:
        return "Rest of season: none, so Ranks has no such tab"
    return f"Rest of season: {len(block['players'])} players from week {block['week']}"
