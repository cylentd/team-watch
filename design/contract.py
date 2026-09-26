"""The shape each injected data block must have, checked where the data enters the page.

build.py injects seven `const LIVE_*` blocks. The JS reads fixed field names off them (see
src/js/data/*.js); a field renamed or dropped on the Python side used to show up as a blank
panel or a console error on the deployed page. Now it fails the build.

The lists below are the fields the JS dereferences (top-level keys, then the keys read off each
row). A block may be None -- that is "source not available", and the page falls back to its
sample -- but a block that is present must be whole. Null values are fine; absent keys are not.
"""

# A league's `status` is fa | waiver | rostered | mine | unknown -- no value is enforced here:
# "unknown" (the scrape could not tell) is a real answer, and the card says so rather than
# guessing FA (data/waiver.js waiverListed). A league's `lane` is why that league's screen listed
# him (usage, role, open, insure, starter, injured), null where it did not (waiver.py _set_lane).
WAIVER_ROW = ["n", "slug", "pos", "team", "opp", "home", "tier", "weeks", "injury", "injury_note",
              "practice", "news_latest", "news_count", "leagues", "summary"]
# One league's view of a candidate (waiver.py `_league`). `verdict` and `drop` may be null; when
# either is an object the card reads every key below. `tier` is that league's own tier (added
# 2026-09-23); a packet from before it reads null there and the card falls back to the row's
# top-level `tier`, which ff-jarvis keeps as the best of the per-league ones.
WAIVER_LEAGUE = ["status", "clears", "need", "tier", "lane", "verdict", "drop"]

# ff-jarvis's wire_watch (design/wire_watch.py), the Breaking rail. Per league a list of events;
# every event carries WIRE_EVENT and its kind's own keys. wire_watch.py cuts to exactly these and
# never fills a required one, so a field the producer dropped fails here by name. `headline`,
# `clears`, `practice`, `note` and the `over` of a need-drop may be null.
WIRE_EVENT = ["kind", "at", "key", "name", "pos", "team", "headline"]
WIRE_KIND = {
    "path": ["status", "clears", "because", "verdict"],
    "drop": ["by", "status", "clears", "verdict"],
    "status": ["from", "to", "practice", "note", "mine"],
    "adds": ["count"],
}
WIRE_BECAUSE = ["key", "name", "status", "practice", "note"]
# A drop's verdict: kind bench|need; `start` true with a `slot` when he would start there (the
# kind stays "bench"). An event's `status` may be "unknown", which the rail says as such.
WIRE_VERDICT = ["kind", "start", "slot", "over", "over_key", "margin"]
# Of the lists above, the keys a producer may leave out (wire_watch.py writes them as null).
WIRE_OPTIONAL = {"headline", "clears", "practice", "note", "over", "over_key", "start", "slot"}
# Keys only one kind may leave out. A path's `verdict` (2026-09-23) is a drop's verdict shape,
# what claiming the opened player does for my roster; a producer from before it sends none.
# A drop's verdict stays required.
WIRE_KIND_OPTIONAL = {"path": {"verdict"}}
# Each kind's sub-objects and their keys; one listed in WIRE_KIND_OPTIONAL may be null.
WIRE_SUBS = {"path": {"because": WIRE_BECAUSE, "verdict": WIRE_VERDICT}, "drop": {"verdict": WIRE_VERDICT}}
WAIVER_VERDICT = ["kind", "over", "slot", "margin"]
WAIVER_DROP = ["name", "pos", "pts"]
WAIVER_META = ["label", "faab_left", "faab_budget", "clears", "needs"]

CONTRACT = {
    "LIVE_ESPN": {
        "keys": ["name", "league", "updated", "roster"],
        "rows": ("roster", ["n", "pos", "team", "slot", "slug", "status"]),
    },
    "LIVE_YAHOO": {
        "keys": ["name", "league", "updated", "roster"],
        "rows": ("roster", ["n", "pos", "team", "slot", "slug"]),
    },
    "LIVE_FEED": {
        "keys": ["generated", "steps", "usage_ready", "pool_size", "fetched"],
    },
    "LIVE_NEWS": {
        "keys": ["items"],
        "rows": ("items", ["id", "title", "desc", "impact", "team", "categories", "link", "when", "kind"]),
    },
    # Live reads kickoff times to decide whether it may poll at all. A row missing one would look
    # like a game that never starts, and the gate would sit idle straight through it. The drive
    # strip reads `week` and `espn` off the same rows to turn "this club, this week" into the
    # event id /api/game wants; `espn` may be null (an older history row), and the strip then has
    # no game to open rather than a wrong one.
    "LIVE_SCHEDULE": {
        "keys": ["games", "alias"],
        "rows": ("games", ["id", "home", "away", "kickoff", "week", "espn"]),
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
                                     "carries", "carry_share", "team_carries", "others"]),
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
    # design/waiver.py, from ff-jarvis's model.season.waiver_packet: one card row per candidate
    # (`players`), and `leagues_meta` per league, in the order the cards draw their league rows.
    # `summary` and `news_latest` may be null; a row's `leagues` map is checked by `waiver_leagues`.
    "LIVE_WAIVER": {
        "keys": ["date", "week", "clears", "leagues_meta", "players"],
        "rows": ("players", WAIVER_ROW),
        "map": ("leagues_meta", WAIVER_META),
        "row_objs": [("players", "summary", ["text", "src"])],
        "row_maps": [("players", "leagues", WAIVER_LEAGUE,
                      {"verdict": WAIVER_VERDICT, "drop": WAIVER_DROP})],
    },
    # design/wire_watch.py, the Breaking rail: {asof, leagues: {key: {events}}}, checked per
    # event by `_wire_events` (the kind decides the keys).
    "LIVE_WIRE": {
        "keys": ["asof", "leagues"],
        "wire_events": True,
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
    # `sheet` is the profile modal's stat sheet, from ff-jarvis's model.season.sheet: `axes` is the
    # axis contract per position (the JS draws from it rather than hardcoding six labels three
    # times) and `rows` is one season-to-date row per player. Every player the producer kept is in
    # `rows`, not only the page's own display cut, because the modal ranks a player against his
    # whole position and dropping the tail would move everyone's rank.
    "LIVE_USAGE": {
        "keys": ["season", "weeks", "through", "generated", "rankBy", "cols", "sheet", "rows"],
        "rows": ("rows", ["n", "slug", "pos", "team", "wk", "q", "v", "p"]),
        "sub_rows": [("sheet", "rows", ["n", "slug", "pos", "team", "g", "v"])],
    },
    "LIVE_SIGNALS": {
        "keys": ["through_week", "ready", "players"],
        "map": ("players", ["series", "verdict", "why", "news", "hot"]),
    },
    # design/pedigree.py, from ff-jarvis's sleeper_status.json, cut to the players the page can
    # show. Every field may be null (Sleeper carries no bio for some deep rookies); the key
    # itself is missing only for a player the page cannot draw a headshot for either.
    "LIVE_PEDIGREE": {
        "keys": ["players"],
        "map": ("players", ["age", "height", "weight", "years_exp", "depth", "depth_pos",
                            "draft_number", "draft_round", "draft_slot", "entry_year", "rookie_year",
                            "bye", "fantasy_draft"]),
    },
    # design/gamelog.py, from ff-jarvis's model.season.gamelog_weekly box score, cut to the
    # players the page can show. The profile modal's weekly-history table.
    "LIVE_GAMELOG": {
        "keys": ["season", "weeks", "through", "generated", "rows"],
        "rows": ("rows", ["n", "slug", "pos", "team", "opp", "wk", "pts", "car", "rush_yds",
                          "rush_td", "tgt", "rec", "rec_yds", "rec_td", "pass_yds", "pass_td"]),
    },
    # design/projections.py, from ff-jarvis's model.market.projections, cut to the players the
    # page can show. `mu` is the component means (PASS/RUSH/TD/...), read as-is off the source.
    "LIVE_PROJECTIONS": {
        "keys": ["players"],
        "map": ("players", ["pts", "mu", "games", "src", "rank", "of", "out"]),
    },
    # design/injury.py, from ff-jarvis's Sleeper status: every hurt player the page can show, `s`
    # OUT / D / Q. `note` may be null (Sleeper gives no reason for some).
    "LIVE_INJURY": {
        "keys": ["players"],
        "map": ("players", ["s", "code", "note"]),
    },
    # ff-jarvis's model.clients.weather (National Weather Service), passed straight through, keyed
    # by team. `roof` is the only key guaranteed present -- a dome has nothing else, and an
    # outdoor/retractable team missing a live forecast (a miss the client already prints and
    # skips) has only that too.
    "LIVE_WEATHER": {
        "keys": ["generated", "teams"],
        "map": ("teams", ["roof"]),
    },
    # design/lines.py: each team's implied points from the DFS lobby's game lines. The roster's
    # defense card reads the opponent's; kicker and defense cards read `opp`.
    "LIVE_LINES": {
        "keys": ["teams"],
        "map": ("teams", ["implied", "opp", "spread", "total"]),
    },
    # design/routes.py, from ff-jarvis's model.clients.routes (heatradar.app): routes run and
    # yards per route run, season to date, cut to the players the page can show. The profile
    # sheet's YPRR axis for a receiver; `yprr` may be null under the source's route floor.
    "LIVE_ROUTES": {
        "keys": ["fetched", "week", "players"],
        "map": ("players", ["n", "pos", "team", "routes", "yprr", "tprr", "target_share"]),
    },
    # design/archetype.py, from ff-jarvis's model.season.archetype (model/season/ARCHETYPE.md is
    # the contract), cut to the players the page can show. Every player carries every key: a
    # position with nothing to say for `role` or `style` emits null there and the reason in
    # `role_null`/`style_null`, never an absent field, so exactly one of each pair is non-null.
    # `athletic_profile` may itself be null (no combine record at all) or a dict with any drill
    # null (a skipped one). `flags` is always a list, `[]` when empty.
    "LIVE_ARCHETYPE": {
        "keys": ["generated", "season", "players"],
        "map": ("players", ["name", "pos", "team", "gsis_id", "role", "role_null", "role_evidence",
                            "style", "style_null", "style_floor", "style_evidence",
                            "athletic_profile", "flags"]),
    },
    # design/archetype.py, from ff-jarvis's model.season.trenches, every team passed through
    # whole (32 rows, no wanted-slug cut). `ol_continuity` and `ol_out` may be null/0 for a
    # reason named in the matching `_reason` field; `ol_out_by_status` is a count per status,
    # `{}` when nobody is out. `ol_starters_out` is the same five-most-used pool checked against
    # Out/Doubtful only -- the before-kickoff signal `ol_continuity` cannot give until after the
    # game; `ol_starters_out_names` lists the affected linemen, `ol_starters_out_reason` names
    # why it is null.
    "LIVE_TRENCHES": {
        "keys": ["generated", "season", "week", "teams"],
        "map": ("teams", ["ol_continuity", "ol_continuity_of", "ol_continuity_reason",
                          "ol_out", "ol_out_by_status", "ol_out_reason",
                          "ol_starters_out", "ol_starters_out_of", "ol_starters_out_names",
                          "ol_starters_out_reason"]),
    },
}


class ContractError(SystemExit):
    """Raised as SystemExit so `python design/build.py` exits non-zero with the message."""


def _row_specs(spec):
    """`rows` is one (field, keys) pair, or a list of them for a block with two row lists."""
    if not spec:
        return []
    return list(spec) if isinstance(spec[0], (list, tuple)) else [spec]


def problems(name, obj, limit=8):
    """Missing fields as `LIVE_X.key` / `LIVE_X.rows[i].key`, at most `limit` of them."""
    if obj is None:
        return []
    spec = CONTRACT[name]
    out = [f"{name}.{k}" for k in spec["keys"] if k not in obj]
    for field, keys in _row_specs(spec.get("rows")):
        if field and isinstance(obj.get(field), list):
            for i, row in enumerate(obj[field]):
                out += [f"{name}.{field}[{i}].{k}" for k in keys if k not in row]
                if len(out) >= limit:
                    break
    for field, sub, keys in spec.get("sub_rows", []):
        inner = (obj.get(field) or {}).get(sub)
        if isinstance(inner, list):
            for i, row in enumerate(inner):
                out += [f"{name}.{field}.{sub}[{i}].{k}" for k in keys if k not in row]
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
    out += _row_children(name, obj, spec)
    if spec.get("wire_events"):
        out += _wire_events(name, obj)
    return out[:limit]


def _wire_events(name, obj):
    """Each league's `events`, each event by its kind, and the kind's one sub-object."""
    out = []
    for lg, block in (obj.get("leagues") or {}).items():
        at = f"{name}.leagues[{lg!r}]"
        if not isinstance(block, dict) or not isinstance(block.get("events"), list):
            out.append(f"{at}.events")
            continue
        for i, e in enumerate(block["events"]):
            here = f"{at}.events[{i}]"
            kind = e.get("kind")
            if kind not in WIRE_KIND:
                out.append(f"{here}.kind")
                continue
            out += [f"{here}.{k}" for k in WIRE_EVENT + WIRE_KIND[kind] if k not in e]
            for sub, keys in WIRE_SUBS.get(kind, {}).items():
                if isinstance(e.get(sub), dict):
                    out += [f"{here}.{sub}.{k}" for k in keys if k not in e[sub]]
                elif sub in e and not (e[sub] is None and sub in WIRE_KIND_OPTIONAL.get(kind, ())):
                    out.append(f"{here}.{sub}")
    return out


def _row_children(name, obj, spec):
    """Objects hanging off each row: `row_objs` is a nullable sub-object whose keys must all be
    there when it is present; `row_maps` is a {key: object} map per row, each object checked,
    and its own nullable sub-objects with it."""
    out = []
    for field, sub, keys in spec.get("row_objs", []):
        for i, row in enumerate(obj.get(field) or []):
            inner = row.get(sub)
            if isinstance(inner, dict):
                out += [f"{name}.{field}[{i}].{sub}.{k}" for k in keys if k not in inner]
    for field, sub, keys, children in spec.get("row_maps", []):
        for i, row in enumerate(obj.get(field) or []):
            for key, inner in (row.get(sub) or {}).items():
                at = f"{name}.{field}[{i}].{sub}[{key!r}]"
                out += [f"{at}.{k}" for k in keys if not isinstance(inner, dict) or k not in inner]
                for child, ckeys in children.items():
                    c = inner.get(child) if isinstance(inner, dict) else None
                    if isinstance(c, dict):
                        out += [f"{at}.{child}.{k}" for k in ckeys if k not in c]
    return out


def validate(name, obj):
    bad = problems(name, obj)
    if bad:
        raise ContractError(f"contract: {name} is missing " + ", ".join(bad))
