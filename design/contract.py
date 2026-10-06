"""The shape each injected data block must have, checked where the data enters the page.

The JS reads fixed field names off each `const LIVE_*` block build.py injects; a field renamed or
dropped on the Python side used to show up as a blank panel on the deployed page. Now it fails the
build. The lists below are the fields the JS dereferences (top-level keys, then the keys read off
each row). A block may be None ("source not available"), but a block that is present must be
whole. Null values are fine; absent keys are not.
"""
import contract_checks   # design/contract_checks.py: the rules that read a spec
import leagues
import startsit_board   # design/startsit_board.py: LIVE_SSB's nested shape check
import startsit_v3      # design/startsit_v3.py: LIVE_SS3's nested shape check
import teams            # design/teams.py: LIVE_TEAMS's nested shape check
import yt_clips         # design/yt_clips.py: LIVE_CLIPS's nested shape check
import player_names     # design/player_names.py: LIVE_NAMES's nested shape check
import slips            # design/slips.py: the optional tier, side and vacated fields
import trade_offers     # design/trade_offers.py: TRADE_OFFERS's nested shape check
from contract_checks import WIRE_EVENT, WIRE_KIND, WIRE_KIND_OPTIONAL, WIRE_OPTIONAL, WIRE_SUBS  # noqa: F401  re-exported for wire_watch.py

# A league's `status` is fa | waiver | rostered | mine | unknown -- no value is enforced here: "unknown"
# (the scrape could not tell) is a real answer, and the card says so rather than guessing FA (data/waiver.js
# waiverListed). A league's `lane` is why its screen listed him (usage, role, open, insure, starter, injured), else null.
# design/ranks.py: one row of Players > Ranks. `home`, `kick`, `inj`, `mu`, `mx` and `mxp` may be
# null; `mx` (the points the defense adds or takes, ff-jarvis `matchup.pts`) and `mxp` (the part of
# it already in `pts`, `matchup.priced`) are null for every WR.
RANK_ROW = ["slug", "n", "pos", "team", "opp", "home", "kick", "inj", "mu", "mx", "mxp", "pts", "floor", "ceil",
            "rank_pts", "unlined_backup", "pts_before_unlined", "rank", "tier"]
# `rank_pts`, `unlined_backup` and `pts_before_unlined` (2026-10-05, ff-jarvis METHODOLOGY 12.86 and 12.87)
# are optional in the file: ranks.py and projections.py always write them, null on a file from before them,
# on any non-RB and on a back the books priced fully. Only a back has a number.
WAIVER_ROW = ["n", "slug", "pos", "team", "opp", "home", "tier", "weeks", "injury", "injury_note",
              "practice", "news_latest", "news_count", "leagues", "summary"]
# One league's view of a candidate (waiver.py `_league`). `verdict` and `drop` may be null; when
# either is an object the card reads every key below. `tier` is that league's own tier (added
# 2026-09-23); a packet from before it reads null there and the card falls back to the row's
# top-level `tier`, which ff-jarvis keeps as the best of the per-league ones.
WAIVER_LEAGUE = ["status", "clears", "need", "tier", "lane", "verdict", "drop"]
# design/recap.py: a player's day, and a kicker's or a defense's (`slug` null for a defense).
RECAP_ROW = ["n", "slug", "pos", "team", "game_id", "actual", "proj", "diff", "line",
             "pass_td", "rush_td", "rec_td", "ret_td"]
RECAP_KD = ["n", "slug", "pos", "team", "game_id", "actual", "box"]

LEAGUE_SPEC = {
    "keys": ["league", "season", "week", "since", "scope", "teams", "weeks", "now", "h2h", "champs", "facts"],
    "rows": [("teams", ["id", "name", "key", "w", "l", "t"]),
             ("weeks", ["week", "games", "awards"]),
             ("now", ["a", "b"]),
             ("champs", ["y", "id", "name", "w", "l", "t"]),
             ("facts", ["k"])],
}
# The Yahoo back page (design/league_back.py) reads more: each team's record, titles and last places, each week's
# headline and dek (null when the roast skipped it), the book, and `history` (a past-seasons file was read).
LEAGUE_YAHOO_SPEC = {
    "keys": LEAGUE_SPEC["keys"] + ["book", "grudge", "withheld", "spoons", "history"],
    "rows": [("teams", ["id", "name", "key", "w", "l", "t", "all", "titles", "lasts"]),
             ("weeks", ["week", "games", "awards", "head", "dek", "table", "lead", "blip", "streaks"]),
             ("spoons", ["y", "id", "name", "mgr", "final"])] + LEAGUE_SPEC["rows"][2:],
}
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
    # design/mates.py: every other team in both leagues, rows in LIVE_ESPN / LIVE_YAHOO's shape.
    "LIVE_MATES": {
        "keys": ["teams"],
        "rows": ("teams", ["key", "league", "name", "roster"]),
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
        "keys": ["games", "alias", "week"],
        "rows": ("games", ["id", "home", "away", "kickoff", "week", "final", "espn"]),
    },
    "LIVE_PROPS": {
        "keys": ["fetched", "events", "books", "players", "windows", "days", "model", "props", "wrcb", "logs"],
        "rows": ("props", ["n", "slug", "pos", "team", "mkt", "game", "commence", "kick", "line",
                           "book", "books", "mine", "win"]),
        # logs[slug] = {g: [[year, week, opp], ...], v: {MKT: [value per game]}} -- the leg sheet
        # (parlay/legdata.js) indexes both, so a log missing either is a crash on open, not a blank
        # chart. `u` (ff-jarvis, 2026-09-27) is optional: per-game usage arrays aligned with `g`,
        # ints or null; when present it carries every key below.
        "map": ("logs", ["g", "v"]),
        "nested": [("logs", "u", ["tgt", "car", "snap", "team_tgt", "rz_tgt", "rz_car", "gl_car", "team_rz"])],
        # A row and each of its books may carry `tier` (none|slight|confident|very) and `side` (2026-10-05):
        # optional, absent means no pick drawn; when sent they must be a known word (slips.problems_props).
        "checks": [slips.problems_props],
    },
    # design/defense.py: per team the points allowed by position (this season and last, rank 1 the
    # fewest) and its starters who will not play. The whole block is optional (None without either
    # ff-jarvis file); `current` or `prior` may be null for a team with no games in that season.
    "LIVE_DEFENSE": {
        "keys": ["form", "out", "fetched"],
        "map": ("form", ["current", "prior"]),
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
        "sub_rows": [("sheet", "rows", ["n", "slug", "pos", "team", "g", "v", "s"])],
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
        "map": ("players", ["pts", "mu", "games", "src", "rank", "of", "out", "done", "wx", "floor", "ceil",
                            "rank_pts", "unlined_backup", "pts_before_unlined"]),
    },
    # design/ranks.py: Players > Ranks. Every position's list in `rows`, RB/WR/TE together in
    # `flex`, each tiered by natural breaks, one week only: `week` is null with no schedule, and
    # `off` lists the teams whose next game is a later week (a Thursday game already played, a bye).
    "LIVE_RANKS": {
        "keys": ["scoring", "week", "off", "rows", "flex"],
        "rows": [("rows", RANK_ROW), ("flex", RANK_ROW)],
    },
    # design/signed.py: page players who finished top 3 at their position in the last completed
    # week. The card's autograph.
    "LIVE_SIGNED": {
        "keys": ["wk", "players"],
        "map": ("players", ["rank", "pts"]),
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
    # `kicked` (design/wx_kicked.py, 2026-09-27): per team, the last forecast before each recent
    # kickoff, so a game already played keeps its forecast on Weather, dimmed.
    "LIVE_WEATHER": {
        "keys": ["generated", "teams", "kicked"],
        "map": ("teams", ["roof"]),
    },
    # design/wx_history.py: ff-jarvis's weather backtest, one summary per condition. `inproj`
    # ({yes, no, kickers}) and `since` are null without the projections' weather_adjust block.
    # `matters` rows carry pos and mean; `tested` lists every position with a cell.
    "LIVE_WX_HISTORY": {
        "keys": ["seasons", "thresholds", "since", "conditions"],
        "map": ("conditions", ["matters", "tested", "inproj"]),
    },
    # design/wx_hits.py: per team, the top QB, two WRs and TE by projected points, not-playing
    # skipped, each with `wx` ({adj, cond}) or null. Weather's "Who it hits"; never a roster.
    "LIVE_WX_HITS": {
        "keys": ["teams"],
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
    # design/startsit.py, each position's best spot, the lead of Start/Sit's matchup board (leaf `matchups`); null without ff-jarvis's calls file.
    "LIVE_STARTSIT": {
        "keys": ["week", "generated", "best"],
        "rows": [("best", ["n", "slug", "pos", "team", "opp", "home", "pts", "why"])],
    },
    # design/startsit_v3.py, Start/Sit's SMASH list, bold calls and record (2026-10-04). Always a dict: no block from ff-jarvis is an empty week
    # (`week` null, no rows, a zero record). A SMASH row's `line` and `td_price` may be null (no book prices him); a take's `reasons` may be [].
    # `record` counts from `since_week`; `weeks` is [] until one is graded; the nested counts are checked by its `problems`.
    "LIVE_SS3": {
        "keys": ["week", "season", "smash", "takes", "record"],
        "rows": [("smash", ["slug", "name", "pos", "team", "opp", "home", "kick", "rank", "pts", "avg_rank", "line", "td_price"]),
                 ("takes", ["slug", "name", "pos", "team", "opp", "home", "kick", "rank", "pts", "avg_rank", "call", "line_pts", "margin_spots", "reasons"])],
        "objs": [("record", ["since_week", "smash", "start", "sit", "weeks", "fun", "last_week"])],
        "sub_rows": [("record", "last_week", ["slug", "name", "pos", "call", "result", "finish"])],
        "checks": [startsit_v3.problems],
    },
    # design/recap.py, This week > Recap (2026-10-05). Always whole: a recap file from before ff-jarvis added `games`,
    # `preview_record`, `k_dst`, `left_hurt`, the TD split and `line` gives [] / null for them (`games` falls back to the
    # file's finals, a game's `preview` is null, a row's TD fields and `line` null), never an absent key. `top` is null
    # with no scorer. A row never carries `rostered`, `slot` or the file's `leagues` (tests/test_recap_data.py).
    "LIVE_RECAP": {
        "keys": ["season", "week", "asof", "complete", "n_games", "n_final", "games", "preview_record", "top", "stars",
                 "k", "dst", "smashed", "busts", "tds", "left_hurt"],
        "rows": [("games", ["game_id", "kickoff", "away", "home", "away_pts", "home_pts", "final", "preview"]),
                 ("stars", RECAP_ROW), ("smashed", RECAP_ROW), ("busts", RECAP_ROW), ("tds", RECAP_ROW + ["td"]),
                 ("k", RECAP_KD), ("dst", RECAP_KD),
                 ("left_hurt", ["n", "slug", "pos", "team", "proj", "actual", "injury", "rest", "later"])],
        "row_objs": [("games", "preview", ["winner", "score", "win_pct", "ats_side", "ats_conf", "total_call",
                                           "total_conf", "spread_home", "total_line", "headline", "frozen",
                                           "su_hit", "ats_hit", "total_hit"])],
        "objs": [("preview_record", ["n", "su", "ats", "ats_pass", "total", "by_conf"]), ("top", RECAP_ROW)],
    },
    # design/role.py, Players > Role (leaf `movers`). A row's `prev` is null when he played under 4
    # games last season; `work` values may be null where ff-jarvis had no number.
    "LIVE_ROLE": {"keys": ["season", "through", "min_games", "rows"],
                  "rows": [("rows", ["slug", "n", "pos", "team", "g", "xfp", "pts", "gap", "td", "work", "prev"])]},
    # design/teams.py, League > Teams (leaf `teams`, 2026-10-05). A league has its slot counts, its column medians
    # and its teams; a team's record (`w`, `l`, `t`) is null with no standings. The nested shapes are checked by `problems`.
    # `week` is the projections' week, the board's label (null with no schedule).
    "LIVE_TEAMS": {"keys": ["week", "leagues"], "rows": [("leagues", ["key", "name", "slots", "median", "teams"])],
                   "checks": [teams.problems]},
    # design/trade_offers.py, League > Trades, the Trade finder (v2 since 2026-10-06). Not an injected block: a file written
    # beside the page (`trade_offers.json`) that the finder fetches on first open. Owner lists, offers and players are checked by `problems`.
    "TRADE_OFFERS": {"keys": ["updated", "season", "leagues"], "checks": [trade_offers.problems]},
    # design/startsit_board.py, the Start / Sit picker and board (2026-10-03): `fp` {slug: {ecr, pos}}, `board` {POS: {avg, n, best, worst}}
    # (rows {team, opp, pts, rank}), `out` {slug: [{n, pos, s}]}; each part may be empty. The nested shapes are checked by its `problems`.
    "LIVE_SSB": {"keys": ["week", "fp", "board", "out"], "checks": [startsit_board.problems]},
    # design/highlights.py, Players > Highlights (2026-09-29); a view's rows are pinned in tests/test_highlights.py.
    "LIVE_HIGHLIGHTS": {"keys": ["season", "week", "generated", "views"], "rows": [("views", ["view", "leaf", "rows"])]},
    # design/yt_clips.py, official YouTube clips (2026-10-05): `players` {slug: [{id, title, kind, secs, embed, shape}]}, `games` {team: {id, title, secs, embed, shape}}; null without ff-jarvis's file. Nested shapes are checked by its `problems`.
    "LIVE_CLIPS": {"keys": ["week", "players", "games", "alias"], "checks": [yt_clips.problems]},
    # design/player_names.py, jersey numbers and nicknames for the clip matcher (2026-10-05): the block IS the map {slug: {n, t, k}}; null without ff-jarvis's file.
    "LIVE_NAMES": {"keys": [], "checks": [player_names.problems]},
    # design/slips.py (2026-10-03): the block IS the map; `{}` without the file. A reason may carry `vacated`
    # (2026-10-05, optional): [{name, last, status, work}], a teammate out whose work he inherits.
    "LIVE_REASONS": {"keys": [], "map": (".", ["why", "work", "tags"]), "checks": [slips.problems_reasons]},
    # design/slips.py (2026-10-05): the tiers' graded record, the strip at the top of Slips. None without ff-jarvis's file.
    "LIVE_PROPS_RECORD": {"keys": ["season", "through_week", "tiers"], "checks": [slips.problems_record]},
    # design/accuracy.py, design/dst.py, design/sos.py (2026-10-05): each passes its ff-jarvis file through, None without
    # it; the producers' docstrings hold the nested shapes.
    "LIVE_ACCURACY": {"keys": ["season", "generated", "weeks", "season_to_date"], "rows": [("weeks", ["week", "model", "by_pos"])]},
    "LIVE_DST": {"keys": ["season", "weeks", "source", "leagues", "rules", "teams"], "rows": [("teams", ["team", "rostered", "weeks"])]},
    "LIVE_SOS": {"keys": ["label", "season", "from_week", "playoff_weeks", "windows", "teams"]},
    # design/slips.py (2026-10-05): Claude's calls on prop lines, {slug: [{mkt, line, side, why}]}. Optional: None without
    # ff-jarvis's file, and a line with no call draws no badge.
    "LIVE_CLAUDE_PROPS": {"keys": ["week", "asof", "calls"], "checks": [slips.problems_claude]},
    # design/preview.py, This week > Preview (slate and dossier, 2026-09-29). A game's `take` is null
    # before Claude has written it; `line`, `matchup`, `wx`, `rest`, `travel`, `site` are null when
    # ff-jarvis has none (the row is not drawn), a line's `fav` null at even and `open` null with no
    # first line. `inj` is {team: [{n, slug, pos, s, avg}]} and `flags` [{k, ...}], pinned in
    # tests/test_preview.py since a row spec is one level.
    # Confidence and record (2026-09-29): a game's `market_win` and `base`, and a take's `win`, `ats` and
    # `total`, are null from a producer written before them; `ats.side` null is no edge. The research pass
    # adds a take's `blind` and `vs_blind` (null) and `notes` ([]), and the record's `blind` (null before
    # it has a graded game); their shapes are pinned in tests/test_preview.py. `record` is null
    # without ff-jarvis's preview_record and its `weeks` [] before the first final week; a week's games
    # are pinned in tests/test_preview.py.
    "LIVE_PREVIEW": {
        "keys": ["season", "week", "asof", "games", "record"],
        "rows": [("games", ["key", "home", "away", "kickoff", "slot", "et", "day", "line", "matchup", "wx",
                            "inj", "rest", "travel", "site", "flags", "market_win", "base", "take"])],
        "row_objs": [("games", "line", ["fav", "by", "total", "implied", "open", "move"]),
                     ("games", "wx", ["roof", "temp", "wind", "precip", "sky"]),
                     ("games", "site", ["stadium", "neutral"]),
                     ("games", "base", ["n", "wins", "covers", "home"]),
                     ("games", "take", ["head", "lean", "vs", "risk", "pick", "win", "ats", "total", "blind",
                                        "vs_blind", "notes", "players"])],
        "objs": [("record", ["season", "through", "n", "su", "ats", "total", "by_conf", "closer", "graded", "fav",
                             "fav_of", "covered", "blind", "weeks"])],
        "sub_rows": [("record", "weeks", ["week", "n", "su", "ats", "total", "strong", "closer", "graded", "fav",
                                          "fav_of", "games"])],
        "row_maps": [("games", "matchup", ["games", "epa", "pos"], {}),
                     ("games", "rest", ["days", "short", "bye"], {}),
                     ("games", "travel", ["zones", "body", "miles"], {})],
    },
    # design/digest.py, the Digest view (This week). `lead`, `record` and `near` may be null, and a
    # hurt row's `game`; `rank`, `rostered`, `injury`, `was`, `why`, `opp`, `temp_f`, `short`,
    # `when`, a headline's `n` and `ko` (a kickoff the schedule lacks) may be null too, and an add's `count`
    # (espn) or `was`/`now`/`delta` (sleeper, `now` when the experts do not have him), and `adds_hours` (espn).
    # Every list may be empty: that is "nothing new". The week's results (finals, stars, smashed, busts,
    # left) left the packet on 2026-10-05 for LIVE_RECAP.
    "LIVE_DIGEST": {
        "keys": ["season", "week", "asof", "asof_words", "lead", "story", "rules", "hurt", "calls", "record", "best", "wx",
                 "near", "adds_source", "adds_hours", "adds_weeks", "adds", "top5", "up", "down", "gems", "news",
                 "tonight", "tonight_last", "starters"],
        "rows": [("hurt", ["n", "slug", "pos", "team", "status", "was", "injury", "new", "rank", "rostered", "game"]),
                 ("best", ["n", "slug", "pos", "team", "opp", "home", "pts", "why", "ko"]),
                 ("wx", ["away", "home", "kick", "ko", "temp_f", "wind_mph", "precip_pct", "short", "lead", "bar"]),
                 ("adds", ["n", "slug", "pos", "team", "count", "was", "now", "delta"]),
                 ("top5", ["pos", "n", "slug", "team", "opp", "pts", "ko"]),
                 ("up", ["n", "slug", "pos", "team", "d_pts", "pts"]),
                 ("down", ["n", "slug", "pos", "team", "d_pts", "pts"]),
                 ("gems", ["n", "slug", "pos", "team", "usage", "metric", "ecr", "rostered"]),
                 ("news", ["when", "headline", "kind", "n", "rest", "slugs", "link"]),
                 # `over` (a team move alone), `from` (a new #1 alone), `proj`, `depth`, `day` and `ko` may be null.
                 ("starters", ["n", "slug", "pos", "team", "proj", "from", "depth", "day", "ko", "over"]),
                 # A Tonight card's game; its lists (out, next_up, groups, moved, tcalls, projected)
                 # are pinned field by field in tests/test_digest.py, since a row spec is one level.
                 ("tonight", ["away", "home", "kick", "ko", "wx", "out", "next_up", "groups", "moved", "tcalls",
                              "projected"])],
        "row_objs": [("hurt", "game", ["away", "home", "kick", "ko"]),
                     ("starters", "over", ["n", "slug", "status"]),
                     ("tonight", "wx", ["roof", "temp_f", "wind_mph", "precip_pct", "short"])],
        # Claude's pick of the story between games (2026-10-04): null, else head, fact, kind and asof are
        # all there; `club` and `player` ({n, slug, pos, team}) may be null.
        "objs": [("story", ["head", "fact", "kind", "asof", "club", "player"])],
    },
    # design/league_recap.py: each league's recap and history, My teams > League. `h2h` is
    # {team id: {opponent id: record}}, all-time or this season only by `scope`; each week's
    # `awards` may lack the winner-only four in a week of ties. A fact carries `k` and its kind's own
    # keys (surface/league/history.js). A champion has an `id` (ESPN) or a past `name` (Yahoo).
    # design/gameday.py, This week > Live. A league's `me` may be null (my team not found by name) and
    # no view reads it as the reader's team (the reader's is found by a team's `key`);
    # `teams` is {id: {key, name, lineup [{slot, n, slug, pos, team, sid}]}} (`key` pinned in
    # tests/test_gameday.py) and a row's `sid` may be null
    # (no Sleeper id: he scores nothing). The lineup rows are pinned in tests/test_gameday.py.
    "LIVE_GAMEDAY": {
        "keys": ["season", "leagues"],
        "rows": [("leagues", ["key", "name", "week", "median", "me", "rules", "teams", "games"])],
    },
    "LIVE_LEAGUE": LEAGUE_SPEC,
    "LIVE_LEAGUE_YAHOO": LEAGUE_YAHOO_SPEC,
    # design/league_trades.py: League > Trades. A trade's `win`/`lose` side is {m, got, slugs, tree, par,
    # after, via}, pinned in tests/test_league_trades.py since a row spec is one level; each `decided` line is
    # {k, m, seed, without}; a curse's `moves` are {season, week, from, to, lost, margin, open}.
    "LIVE_TRADES": {
        "keys": ["since", "through", "n", "names", "ranking", "trades", "heists", "decided", "curses"],
        "rows": [("ranking", ["m", "trades", "won", "lost", "per_trade", "lo", "hi", "shrunk", "few"]),
                 ("trades", ["id", "season", "week", "open", "margin", "win", "lose", "held", "decided"]),
                 ("curses", ["player", "surname", "kind", "n", "slug", "moves"])],
    },
}
# Every other Yahoo league's blocks (design/leagues.py blocks(); AYO since 2026-09-29) are the first one's shape.
CONTRACT.update({b: CONTRACT[a] for key in leagues.YAHOO for a, b in zip(leagues.blocks("yahoo"), leagues.blocks(key))})

# design/claude_record.py (2026-10-05): Claude's hit rate where he took the model's side and where he did not, the second
# row of the Slips record strip. None without ff-jarvis's file; `agree` and `alone` are null before a game is graded.
CONTRACT["LIVE_CLAUDE_RECORD"] = {"keys": ["season", "week", "through_week", "agree", "alone"], "checks": [slips.problems_claude_record]}


class ContractError(SystemExit):
    """Raised as SystemExit so `python design/build.py` exits non-zero with the message."""


def problems(name, obj, limit=8):
    """Missing fields as `LIVE_X.key` / `LIVE_X.rows[i].key`, at most `limit` of them (the rules: contract_checks.py)."""
    return contract_checks.problems(name, obj, CONTRACT[name], limit) if obj is not None else []


def validate(name, obj):
    bad = problems(name, obj)
    if bad:
        raise ContractError(f"contract: {name} is missing " + ", ".join(bad))
