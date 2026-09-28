"""LIVE_DEFENSE: each defense's points allowed by position and its starters who will not play, for
the leg sheet's matchup line (surface/parlay/legsheet.js).

Two ff-jarvis files feed it, `defense_form.json` (points allowed per game and rank, this season and
last) and `sleeper_defense.json` (every hurt defender, Sleeper's depth and status), read by
sources.load_defense(). This file renames nothing and computes nothing: it re-keys both by the
page's team spelling (nflverse writes LA, the page LAR) and keeps only what the page draws.

A starter is Sleeper's depth 1. "Will not play" is every status but Questionable: a doubtful
defender sits about as often as an out one, and injSits (ui/player.js) reads it the same way.
"""

SITS = {"IR", "Out", "Doubtful", "PUP", "Sus", "COV", "NA"}


def _form(side):
    """{pos: {pts_pg, rank}} of one season, or None."""
    pos = (side or {}).get("pos")
    return {k: {"pts_pg": v.get("pts_pg"), "rank": v.get("rank")} for k, v in pos.items()} if pos else None


def live_defense(block, fix):
    """{form: {team: {current, prior}}, out: {team: [{name, pos, injury}]}, fetched} or None.

    `block` is {form, injured, fetched} as sources.load_defense returns it; `fix` maps a team
    spelling to the page's (build.TEAM_FIX). Rank 1 allows the fewest points."""
    form = ((block or {}).get("form") or {}).get("teams") or {}
    hurt = ((block or {}).get("injured") or {}).get("teams") or {}
    if not form and not hurt:
        return None
    out = {}
    for team, rows in hurt.items():
        sits = [{"name": r.get("name"), "pos": r.get("pos"), "injury": r.get("injury")}
                for r in rows or [] if r.get("depth") == 1 and r.get("injury") in SITS]
        if sits:
            out[fix.get(team, team)] = sits
    return {"form": {fix.get(t, t): {"current": _form(v.get("current")), "prior": _form(v.get("prior"))}
                     for t, v in form.items()},
            "out": out,
            "fetched": (block or {}).get("fetched") or ((block or {}).get("form") or {}).get("generated")}


def report(d):
    """build.py's one-line summary of LIVE_DEFENSE."""
    if not d:
        return "Defense: no defense_form/sleeper_defense, the leg sheet's matchup line is opp_f only"
    return f"Defense: {len(d['form'])} teams' form, {sum(len(v) for v in d['out'].values())} starters out"
