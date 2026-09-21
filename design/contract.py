"""The shape each injected data block must have, checked where the data enters the page.

build.py injects seven `const LIVE_*` blocks. The JS reads fixed field names off them (see
src/js/data/*.js); a field renamed or dropped on the Python side used to show up as a blank
panel or a console error on the deployed page. Now it fails the build.

The lists below are the fields the JS dereferences (top-level keys, then the keys read off each
row). A block may be None -- that is "source not available", and the page falls back to its
sample -- but a block that is present must be whole. Null values are fine; absent keys are not.
"""

WAIVER_ROW = ["n", "slug", "pos", "team", "pts", "availability", "opp", "home", "lane", "work", "role_pts",
              "edge", "snap", "tgt", "car", "starts", "vacated", "gain", "share_pct", "promoted", "upgrade",
              "stash_reason"]

CONTRACT = {
    "LIVE_ESPN": {
        "keys": ["name", "league", "updated", "roster"],
        "rows": ("roster", ["n", "pos", "team", "slot", "slug", "status"]),
    },
    "LIVE_YAHOO": {
        "keys": ["name", "league", "updated", "roster"],
        "rows": ("roster", ["n", "pos", "team", "slug"]),
    },
    "LIVE_FEED": {
        "keys": ["generated", "steps", "usage_ready", "pool_size", "fetched"],
    },
    "LIVE_NEWS": {
        "keys": ["items"],
        "rows": ("items", ["id", "title", "desc", "impact", "team", "categories", "link", "when", "kind"]),
    },
    # Live reads kickoff times to decide whether it may poll at all. A row missing one would look
    # like a game that never starts, and the gate would sit idle straight through it.
    "LIVE_SCHEDULE": {
        "keys": ["games"],
        "rows": ("games", ["home", "away", "kickoff"]),
    },
    "LIVE_PROPS": {
        "keys": ["fetched", "events", "books", "players", "windows", "days", "model", "props", "wrcb", "logs"],
        "rows": ("props", ["n", "slug", "pos", "team", "mkt", "game", "commence", "kick", "line",
                           "book", "books", "mine", "win"]),
        # logs[slug] = {g: [[year, week, opp], ...], v: {MKT: [value per game]}} -- gamelog.js
        # indexes both, so a log missing either is a crash on expand, not a blank chart.
        "map": ("logs", ["g", "v"]),
    },
    "LIVE_DFS_YAHOO": {
        "keys": ["fetched", "modeled", "lined", "players"],
        "rows": ("players", ["n", "pos", "team", "sal", "proj", "src", "status", "slug", "game"]),
    },
    # ff-jarvis's data/player_profiles.json, keyed by slug. `next` and `red_zone` may be null (a
    # bye; a QB); when either is an object, the profile JS reads every key below, so a partial one
    # is a crash or a blank block on open.
    "LIVE_PROFILES": {
        "keys": ["generated", "season", "through_week", "players"],
        "map": ("players", ["n", "pos", "team", "usage", "coverage", "red_zone", "next"]),
        "nested": [
            ("players", "next", ["week", "opp", "home", "zones", "man_pct", "man_pct_league",
                                 "man_season", "dc_same", "rz", "factor", "tested", "method"]),
            ("players", "red_zone", ["targets", "target_share", "team_targets",
                                     "carries", "carry_share", "team_carries"]),
        ],
    },
    # ff-jarvis's model.market.market_stock, feed block `market.stock`, keyed by the producer's
    # norm_name -- build.py's load_market_stock() re-keys it by slug (profileFor()'s key) before
    # injection, so the shape below is what the JS actually sees. Step 4 (METHODOLOGY 12.46)
    # failed its backtest, so `backtested` is false and the page shows numbers only -- no verdict
    # words. A "model" row (no market priced) still carries every key, with the d_*/z/rank fields
    # null; only `pts` (from player_projections.json) is real.
    "LIVE_MARKET_STOCK": {
        "keys": ["generated", "at", "backtested", "trial", "players"],
        "map": ("players", ["name", "pos", "team", "src", "game", "markets", "pts", "role_pts",
                            "prev_at", "d_pts", "d_role_pts", "sector", "z", "rank", "d_rank",
                            "no_market"]),
    },
    # design/signals.py: one row per player on my rosters, keyed by slug. `series` is watch.json's
    # weekly snap share (None for a missed week); `verdict` is null when watch has no row for him.
    # design/waiver.py, from ff-jarvis's model.season.waiver_packet. Each league's rows share one
    # shape (waiver.py `_row`); a null sub-object (starts, vacated, promoted, upgrade) means that
    # lane or list does not apply to him.
    "LIVE_WAIVER": {
        "keys": ["date", "week", "clears", "leagues"],
        "map": ("leagues", ["team", "type", "budget_left", "lineup_unknown", "wire", "adds", "stash", "drops"]),
        "map_rows": [("leagues", sub, WAIVER_ROW) for sub in ("wire", "adds", "stash", "drops")],
    },
    # design/pool.py, from watch.json's league-wide pool. dSnap/dShare/luck are null until a
    # player has two weeks; the page plots only rows that have them.
    "LIVE_POOL": {
        "keys": ["through_week", "generated", "trended", "players"],
        "rows": ("players", ["n", "slug", "pos", "team", "snaps", "dSnap", "share", "dShare", "opp", "rz",
                             "ppg", "luck", "v", "why", "leagues", "mine"]),
    },
    # design/usage.py, from ff-jarvis's model.season.usage weekly grid. `cols` is the header
    # contract itself -- the JS builds its table from it rather than hardcoding seven labels per
    # position -- so a row whose `v`/`p` lack a column id renders an empty cell, not a crash.
    "LIVE_USAGE": {
        "keys": ["season", "weeks", "through", "generated", "rankBy", "cols", "rows"],
        "rows": ("rows", ["n", "slug", "pos", "team", "wk", "q", "v", "p"]),
    },
    "LIVE_SIGNALS": {
        "keys": ["through_week", "ready", "players"],
        "map": ("players", ["series", "verdict", "why", "news", "hot"]),
    },
}


class ContractError(SystemExit):
    """Raised as SystemExit so `python design/build.py` exits non-zero with the message."""


def problems(name, obj, limit=8):
    """Missing fields as `LIVE_X.key` / `LIVE_X.rows[i].key`, at most `limit` of them."""
    if obj is None:
        return []
    spec = CONTRACT[name]
    out = [f"{name}.{k}" for k in spec["keys"] if k not in obj]
    field, keys = spec.get("rows", (None, []))
    if field and isinstance(obj.get(field), list):
        for i, row in enumerate(obj[field]):
            out += [f"{name}.{field}[{i}].{k}" for k in keys if k not in row]
            if len(out) >= limit:
                break
    field, keys = spec.get("map", (None, []))
    if field and isinstance(obj.get(field), dict):
        for key, row in obj[field].items():
            out += [f"{name}.{field}[{key!r}].{k}" for k in keys if not isinstance(row, dict) or k not in row]
            if len(out) >= limit:
                break
    for field, sub, keys in spec.get("nested", []):
        if not isinstance(obj.get(field), dict):
            continue
        for key, row in obj[field].items():
            inner = row.get(sub) if isinstance(row, dict) else None
            if isinstance(inner, dict):
                out += [f"{name}.{field}[{key!r}].{sub}.{k}" for k in keys if k not in inner]
    for field, sub, keys in spec.get("map_rows", []):
        for key, row in (obj.get(field) or {}).items():
            for i, r in enumerate((row or {}).get(sub) or []):
                out += [f"{name}.{field}[{key!r}].{sub}[{i}].{k}" for k in keys if k not in r]
    return out[:limit]


def validate(name, obj):
    bad = problems(name, obj)
    if bad:
        raise ContractError(f"contract: {name} is missing " + ", ".join(bad))
