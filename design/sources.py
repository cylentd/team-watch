"""Every read of an ff-jarvis file or feed block. build.py orchestrates the build; this is the
adapter that knows where the data lives -- feed-first (what the scheduled refresh last saw),
the ff-jarvis file directly as a fallback, same two-tier pattern on every one of them. Split out
of build.py to keep the two concerns (reading ff-jarvis, assembling the page) in separate files
instead of one growing past its budget.

A function that reshapes what it reads for the page (re-keys, joins, drops rows) stays in
build.py and calls these readers -- this file returns parsed JSON, nothing more.
"""
import json
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent

# The three input roots. Each can be pointed elsewhere by env var so a build can run against a
# pinned snapshot (the regression suite) instead of whatever ff-jarvis holds right now.
DWR = pathlib.Path(os.environ.get("TEAM_WATCH_DATA", "C:/Users/David/Github/ff-jarvis/data"))
FEED = pathlib.Path(os.environ.get("TEAM_WATCH_FEED", REPO / "data" / "feed.json"))
ESPN_ROSTERS = DWR / "espn_rosters.json"
YAHOO_ROSTERS = DWR / "league_rosters.json"
BP_PROPS = DWR / "bettingpros_props.json"
SLEEPER_STATUS = DWR / "sleeper_status.json"
DFS_POOL = DWR / "dfs_pool.json"
PLAYER_PROJ = DWR / "player_projections.json"
GAMELOG_WEEKLY = DWR / "gamelog_weekly.json"
PEDIGREE = DWR / "pedigree.json"
WEATHER = DWR / "weather.json"
ROUTES = DWR / "routes_run.json"


def load_status():
    """norm_name -> Sleeper record (ff-jarvis's model.clients.sleeper), the canonical injury/depth
    read every feature should prefer over deriving its own. Feed-first (what the scheduled refresh
    saw), the ff-jarvis file directly as a fallback -- the same two-tier pattern load_props_raw()
    and load_model_raw() already use below."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = (d.get("status") or {}).get("data")
        if block and block.get("players"):
            return block["players"]
    except (OSError, json.JSONDecodeError):
        pass
    if SLEEPER_STATUS.exists():
        try:
            return json.loads(SLEEPER_STATUS.read_text(encoding="utf-8")).get("players", {})
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def load_props_raw():
    """The BettingPros pull, preferring the feed (`market.props_bp`) so the page shows what the
    scheduled refresh saw. A feed older than the props step lacks the block; then the file the
    props client wrote is read directly, the same way the rosters are."""
    feed = FEED
    try:
        d = json.loads(feed.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("props_bp") or {}).get("data")
        if block and block.get("props"):
            return block, "feed.json"
    except (OSError, json.JSONDecodeError):
        pass
    if BP_PROPS.exists():
        try:
            return json.loads(BP_PROPS.read_text(encoding="utf-8")), "ff-jarvis/data"
        except (OSError, json.JSONDecodeError):
            return None, None
    return None, None


def load_model_raw():
    """P(over) per priced line from ff-jarvis's `model.market.props_model`, feed first, file second,
    the same way the lines themselves are read. A hand re-price between refreshes leaves the file
    newer than the feed's copy, so when both exist the later `generated` wins."""
    found = []
    try:
        d = json.loads(FEED.read_text(encoding="utf-8"))
        block = ((d.get("market") or {}).get("props_model") or {}).get("data")
        if block and block.get("lines"):
            found.append(block)
    except (OSError, json.JSONDecodeError):
        pass
    # The copy kept beside the feed. The ff-jarvis checkout can sit on another branch
    # (two sessions share it), and the refresh then rewrites the feed without the model block.
    for path in (DWR / "props_model.json", REPO / "data" / "props_model.json"):
        if path.exists():
            try:
                found.append(json.loads(path.read_text(encoding="utf-8")))
                break
            except (OSError, json.JSONDecodeError):
                continue
    return max(found, key=lambda m: m.get("generated") or "") if found else None


def feed_block(keys, must):
    """The `data` of the feed block at `keys` (a path of nested keys) when it carries `must`."""
    try:
        d = json.loads(FEED.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for k in keys:
        d = (d or {}).get(k)
    block = (d or {}).get("data")
    return block if block and block.get(must) else None


def read_first(*paths):
    """The first of `paths` that exists and parses as JSON, else None."""
    for path in paths:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
    return None


def load_player_proj():
    """Half-PPR points for every player from ff-jarvis's `model.market.projections`, feed block
    first (`projections`), then the file, same two-tier pattern as the other live reads. A feed
    written before that step existed has no block, and an ff-jarvis checkout on another branch
    may have no file: then nothing is modelled and every DFS row falls back to Yahoo's FPPG,
    which the header says out loud."""
    return (feed_block(("projections",), "players")
            or read_first(PLAYER_PROJ, REPO / "data" / "player_projections.json"))


def load_wrcb():
    """RotoBaller's WR/CB column for the week, feed first then the ff-jarvis file."""
    return feed_block(("market", "wrcb"), "records") or read_first(DWR / "wrcb.json")


def load_profiles():
    """Per-player profile (usage by zone, coverage split, red zone, next opponent) from ff-jarvis's
    data/player_profiles.json, feed block `profiles` first. None renders no chips and a quiet
    "no profile yet" panel."""
    return feed_block(("profiles",), "players") or read_first(DWR / "player_profiles.json")


def load_gamelog_weekly():
    """Per-player-week box score (rush/rec yards, TDs, receptions, fantasy points) from ff-jarvis's
    model.season.gamelog_weekly, feed block `gamelog` first, the file second -- same two-tier
    pattern as load_profiles(). The profile modal's weekly-history table reads this."""
    return feed_block(("gamelog",), "rows") or read_first(GAMELOG_WEEKLY)


def load_draft_pedigree():
    """Real NFL draft capital, bye week, and each league's fantasy draft picks, from ff-jarvis's
    model.season.pedigree, feed block `pedigree` first, the file second -- same two-tier pattern
    as load_gamelog_weekly()."""
    return feed_block(("pedigree",), "draft") or read_first(PEDIGREE)


def load_weather():
    """Game-day forecast per stadium from ff-jarvis's model.clients.weather (National Weather
    Service), feed block `weather` first, the file second -- same two-tier pattern as
    load_gamelog_weekly(). No `wanted`-slug cut: it is keyed by team, already small (32 rows).
    Passed straight through -- no reshaping, so no dedicated design/weather.py transform."""
    return feed_block(("weather",), "teams") or read_first(WEATHER)


def load_routes():
    """Routes run and yards per route run, season to date, from ff-jarvis's model.clients.routes
    (heatradar.app), feed block `routes` first, the file second. design/routes.py cuts it to
    the page's players for the profile sheet's YPRR axis."""
    return feed_block(("routes",), "players") or read_first(ROUTES)


def load_dfs_pool():
    """Yahoo's own contest salary export, imported into ff-jarvis by `python -m model.clients.dfs
    import <csv>` -- deliberately manual, per that module's own docstring: an automated Yahoo
    scrape is a decision to ask about, not build quietly. Feed-first, the ff-jarvis file directly
    as a fallback, same two-tier pattern as load_status()/load_props_raw()."""
    return feed_block(("market", "dfs"), "players") or read_first(DFS_POOL)


def load_recap(season, week):
    """ff-jarvis's weekly recap (model.season.recap): per player `actual` and pregame `proj`,
    half-PPR, keyed by norm_name. No DST or K rows. None when the week has none yet."""
    return read_first(DWR / "recap" / f"{season}-w{week:02d}.json")


def load_status_asof(day):
    """norm_name -> the newest Sleeper status row ff-jarvis recorded on or before `day`
    (YYYY-MM-DD, history kind `status`): load_status() as it stood that morning."""
    out = {}
    for path in sorted((DWR / "history" / "status").glob("*.jsonl")):
        if path.stem > day:
            break
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("key"):
                out[row["key"]] = row
    return out


def load_dfs_history(season, week):
    """Every Yahoo DFS pool row ff-jarvis recorded for one week (history kind `dfs`, since
    2026-09-25; week 1 was backfilled, week 2 was never saved). Oldest first."""
    rows = []
    for path in sorted((DWR / "history" / "dfs").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("season") == season and row.get("week") == week:
                rows.append(row)
    return rows
