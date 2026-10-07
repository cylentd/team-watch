"""LIVE_SOS: strength of schedule (2026-10-05), from ff-jarvis's sos.json (model.season.sos).

What the defenses each team faces allow each position over the next 4 weeks, the rest of the season and
the fantasy playoff weeks, rank 1 = easiest. Context, not backtested (ff-jarvis METHODOLOGY 12.11), and
the page says so with the file's own `label`. The producer's docstring is the field contract. The page
computes nothing: this cut passes the file through, None when there is none.

Since 2026-10-06 a team also has a `K` row (kicker points a game against the opponents' defenses, from play-by-play,
`pts_pg` null with none cached), the file's `k` note ({scoring, prior_season, prior_used, note}) passes through, and
`source` is cut to `k_play_by_play`, the files the K numbers came from. The page draws K rows only for a team that has one.

Since 2026-10-06 `k_allowed` ({TEAM: {pts_pg, games, rank}}) is this season's Yahoo kicker points a game each defense
allowed, rank 32 = most; it passes through, None when the file has none (the Defenses card then draws no K row).
"""

K_ALLOWED_KEYS = ("pts_pg", "games", "rank")
K_KEYS = ("games", "pts_pg", "current", "prior", "avg_def_rank", "rank")


def live_sos(raw):
    """None when ff-jarvis has written no file: the view then says so."""
    if not raw or not raw.get("teams"):
        return None
    keep = ("label", "generated", "season", "from_week", "through_week", "playoff_weeks", "last_week",
            "weights", "windows", "teams", "k", "k_allowed")
    src = raw.get("source") or {}
    return {**{k: raw.get(k) for k in keep},
            "source": {"k_play_by_play": src["k_play_by_play"]} if "k_play_by_play" in src else None}


def problems(block):
    """K (2026-10-06) is a position beside QB, RB, WR and TE: when a team carries a `K` row, each of the file's windows
    has its numbers, null ones included (a kicker with no cached play-by-play). A file with no K at all is fine."""
    out = []
    for team, entry in ((block or {}).get("teams") or {}).items():
        if not isinstance(entry, dict) or "K" not in entry:
            continue
        for win in (block.get("windows") or {}):
            row = (entry["K"] or {}).get(win)
            if not isinstance(row, dict):
                out.append(f"LIVE_SOS.teams[{team!r}].K.{win}")
                continue
            out += [f"LIVE_SOS.teams[{team!r}].K.{win}.{k}" for k in K_KEYS if k not in row]
    for team, row in ((block or {}).get("k_allowed") or {}).items():
        out += [f"LIVE_SOS.k_allowed[{team!r}].{k}" for k in K_ALLOWED_KEYS if not isinstance(row, dict) or k not in row]
    return out


def report(block):
    if not block:
        return "Schedule: no sos.json, so the view says so"
    return f"Schedule: {len(block['teams'])} teams from week {block['from_week']}"
