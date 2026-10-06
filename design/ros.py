"""LIVE_ROS: rest-of-season value (2026-10-06), from ff-jarvis's ros_value.json (model.season.ros_value, METHODOLOGY 12.97).

Each QB/RB/WR/TE's expected half-PPR points from the week still to play through week 17: points a game times the games
he is expected to play. Stats > Ranks > Rest of season draws its rank by week; the profile's block draws the same.
The page computes nothing: this cut keeps the fields the page reads, in the page's names (`n` for the name, as the
other blocks), and drops the model's inputs (pace, xfp, f, att and the rest) and the weekly points of `hist`, which
the chart never shows (ROS points fall every week for everyone, so only the rank is charted).

    {season, week, through_week, last_week, generated,
     players: [{slug, n, pos, team, rank, ros_pg, ros_pts, games_left, sched_left, hist, espn}]}
    hist    [[week, rank], ...] ascending, one item for a player with no earlier week
    espn    {ros_pg, ros_pts, rank, hist}: the same on ESPN scoring, not backtested

None when ff-jarvis has written no file: the Rest of season tab is then absent and Ranks reads as it did before.
"""

import sources


def load_ros_value():
    """The ff-jarvis file (ros_value.json, METHODOLOGY 12.97): feed block `ros_value` first, the file second; None when
    neither exists. Lives here, not in sources.py, which is at its 500-line budget (tests/test_budgets.py)."""
    return sources.feed_block(("ros_value",), "players") or sources.read_first(sources.DWR / "ros_value.json")


TOP = ("season", "week", "through_week", "last_week", "generated")
PLAYER = ("slug", "pos", "team", "rank", "ros_pg", "ros_pts", "games_left", "sched_left")


def _hist(rows):
    """[week, rank] only: the file's third item, the week's points, is not charted."""
    return [[r[0], r[1]] for r in rows or []]


def _espn(e):
    e = e or {}
    return {"ros_pg": e.get("ros_pg"), "ros_pts": e.get("ros_pts"), "rank": e.get("rank"), "hist": _hist(e.get("hist"))}


def live_ros(raw):
    if not raw or not raw.get("players"):
        return None
    players = [{**{k: p.get(k) for k in PLAYER}, "n": p.get("name"), "hist": _hist(p.get("hist")), "espn": _espn(p.get("espn"))}
               for p in raw["players"]]
    return {**{k: raw.get(k) for k in TOP}, "players": players}


def report(block):
    if not block:
        return "Rest of season: none, so Ranks has no such tab"
    return f"Rest of season: {len(block['players'])} players from week {block['week']}"
