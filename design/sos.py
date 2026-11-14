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

Since 2026-11-14 `defense_recent` ({DEF: {games, QB|RB|WR|TE: {last3_pts_pg, season_pts_pg, trend}}}, RB adding
last3_rush_yds_pg, season_rush_yds_pg, rush_trend) and `recent` ({games, trend_margin_pts, trend_margin_rush_yds, note})
pass through, None from a file written before ff-jarvis's defense form (o3-defense-form). Schedule and Preview read them
in data/defform.js. Context only: form failed as a price (ff-jarvis METHODOLOGY 12.73).
"""

K_ALLOWED_KEYS = ("pts_pg", "games", "rank")
K_KEYS = ("games", "pts_pg", "current", "prior", "avg_def_rank", "rank")
FORM_POS = ("QB", "RB", "WR", "TE")
FORM_KEYS = ("last3_pts_pg", "season_pts_pg", "trend")
FORM_RUSH_KEYS = ("last3_rush_yds_pg", "season_rush_yds_pg", "rush_trend")   # RB only
FORM_TRENDS = ("up", "down", None)                                            # "up": the defense allowed more lately


def live_sos(raw):
    """None when ff-jarvis has written no file: the view then says so."""
    if not raw or not raw.get("teams"):
        return None
    keep = ("label", "generated", "season", "from_week", "through_week", "playoff_weeks", "last_week",
            "weights", "windows", "teams", "k", "k_allowed", "defense_recent", "recent")
    src = raw.get("source") or {}
    return {**{k: raw.get(k) for k in keep},
            "source": {"k_play_by_play": src["k_play_by_play"]} if "k_play_by_play" in src else None}


def problems(block):
    """The `label` must be a non-blank string: it is the Schedule's "context only" mark and an untested number must say
    so (PRODUCT.md), so a missing one fails the build. K (2026-10-06) is a position beside QB, RB, WR and TE: when a team carries a `K` row, each of the file's windows
    has its numbers, null ones included (a kicker with no cached play-by-play). A file with no K at all is fine."""
    out = []
    label = (block or {}).get("label")
    if block and not (isinstance(label, str) and label.strip()):
        out.append("LIVE_SOS.label")   # the page's only "context only" mark (data/sos.js reads it); no label, no build (2026-11-01)
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


def problems_form(block):
    """`defense_recent` is optional; when sent, every position the page reads carries the fields data/defform.js
    reads (null allowed: fewer than 3 games), and a trend is "up", "down" or null. An unknown word fails the build
    rather than drawing an arrow the copy has no words for."""
    out = []
    for team, entry in ((block or {}).get("defense_recent") or {}).items():
        for pos in FORM_POS:
            row = entry.get(pos) if isinstance(entry, dict) else None
            if not isinstance(row, dict):
                out.append(f"LIVE_SOS.defense_recent[{team!r}].{pos}")
                continue
            keys = FORM_KEYS + (FORM_RUSH_KEYS if pos == "RB" else ())
            out += [f"LIVE_SOS.defense_recent[{team!r}].{pos}.{k}" for k in keys if k not in row]
            out += [f"LIVE_SOS.defense_recent[{team!r}].{pos}.{k}" for k in ("trend", "rush_trend")
                    if k in row and k in keys and row[k] not in FORM_TRENDS]
    return out


def report(block):
    if not block:
        return "Schedule: no sos.json, so the view says so"
    return f"Schedule: {len(block['teams'])} teams from week {block['from_week']}"
