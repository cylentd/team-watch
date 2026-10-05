"""LIVE_STARTSIT: each position's best spot, the lead of Start/Sit's matchup board (leaf `matchups`).

From ff-jarvis's `startsit_calls.json` (model.season.startsit_calls): per position the starter with
the softest matchup (`best`), with its signed reasons. A best spot is not a call and is not graded.
The calls themselves (SMASH, bold START and SIT) are Start/Sit v3's (design/startsit_v3.py); the v2
takes, Pitcher List's column and the v2 record left this view on 2026-10-04.

Self-contained like the other cuts: the loaded file and slugify come in as arguments.
"""

POS = ("QB", "RB", "WR", "TE")


def _home(r):
    """ff-jarvis's `game` is "AWAY @ HOME" in the props feed's raw codes (JAC, not JAX), so the
    team is placed by whichever side is not its opponent."""
    away, _, home = (r.get("game") or "").partition(" @ ")
    return away.strip() == r.get("opp") or home.strip() == r.get("team")


def live_startsit(calls, slugify):
    """None when ff-jarvis has written no calls file: the board then draws without a best spot."""
    if not calls or "positions" not in calls:
        return None
    best = []
    for pos in POS:
        b = (calls["positions"].get(pos) or {}).get("best")
        if b:
            best.append({"n": b["name"], "slug": slugify(b["name"]), "pos": b["pos"], "team": b["team"],
                         "opp": b["opp"], "home": _home(b), "pts": b["pts"],
                         "why": [w[2] for w in b.get("why") or []]})
    return {"week": calls["week"], "generated": calls.get("generated"), "best": best}


def report(block):
    if not block:
        return "Best spots: no startsit_calls.json, so the board has none"
    return f"Best spots: week {block['week']}, {len(block['best'])} positions"
