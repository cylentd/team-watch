"""LIVE_DST: D/ST and K streaming numbers (2026-10-05), from ff-jarvis's dst_projections.json
(model.market.dst, METHODOLOGY 12.85).

Every team's D/ST points on each league's scoring and K points (Yahoo leagues only), this week and the
next 3, with who rosters it per league and a `streamer` flag. The producer's docstring is the field
contract. The page computes nothing: this cut passes the file through, None when there is none.
"""


def live_dst(raw):
    """None when ff-jarvis has written no file: the board then says so."""
    if not raw or not raw.get("teams"):
        return None
    return {k: raw.get(k) for k in ("generated", "season", "weeks", "source", "leagues", "rules", "teams")}


def report(block):
    if not block:
        return "D/ST + K: no dst_projections.json, so the board says so"
    return f"D/ST + K: {len(block['teams'])} teams, weeks {block['weeks']}"
