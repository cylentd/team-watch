"""The profile modal's bio strip: age, height, weight, years pro, depth chart slot (ff-jarvis's
sleeper_status.json, model.clients.sleeper) plus real NFL draft capital, bye week, and each
league's fantasy draft pick (ff-jarvis's pedigree.json, model.season.pedigree) -- both keyed by
norm_name, joined on that key, re-keyed by slug like build.py's _stock_by_slug() so
profileFor()'s lookup covers this too instead of a second join.

Cut to the `wanted` slug set (the same one build.py already computes for headshots): the page
only ever opens a profile for a player it can show a row for, and Sleeper carries ~800 skill
players a season -- most of whom never appear on this page.

Self-contained like pool.py/usage.py: the status map, the draft/bye/fantasy-draft block and
slugify come in as arguments.
"""


def report(pedigree):
    """build.py's one-line summary of LIVE_PEDIGREE."""
    return f"Pedigree: {len(pedigree['players'])} players" if pedigree else "Pedigree: none, so no bio strip"


def live_pedigree(status, draft, slugify, wanted):
    """LIVE_PEDIGREE: {players: {slug -> {...}}} or None when Sleeper has nothing loaded at all.
    `draft` is ff-jarvis's pedigree.json as a whole ({draft, bye, fantasy_draft}, each keyed by
    norm_name except `bye`, keyed by team) -- optional, since it needs a first
    `model.season.pedigree` run that a fresh ff-jarvis checkout may not have yet. A player Sleeper
    has no record for (a very deep rookie) is simply absent from the map; the modal's bio strip
    renders whatever piece of this it has."""
    if not status:
        return None
    d = draft or {}
    nfl_draft, bye, fantasy = d.get("draft") or {}, d.get("bye") or {}, d.get("fantasy_draft") or {}
    out = {}
    for key, rec in status.items():
        slug = slugify(rec.get("name") or "")
        if slug not in wanted or slug in out:
            continue
        nd = nfl_draft.get(key) or {}
        out[slug] = {"age": rec.get("age"), "height": rec.get("height"), "weight": rec.get("weight"),
                     "years_exp": rec.get("years_exp"), "depth": rec.get("depth"),
                     "depth_pos": rec.get("depth_pos"),
                     "draft_number": nd.get("draft_number"), "entry_year": nd.get("entry_year"),
                     "rookie_year": nd.get("rookie_year"),
                     "bye": bye.get(rec.get("team")),
                     "fantasy_draft": fantasy.get(key)}
    return {"players": out} if out else None
