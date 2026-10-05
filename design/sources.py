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

import leagues                 # design/leagues.py: David's leagues and their ff-jarvis file names

ROOT =pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent

# The three input roots. Each can be pointed elsewhere by env var so a build can run against a
# pinned snapshot (the regression suite) instead of whatever ff-jarvis holds right now.
# Since fix 3 (2026-09-29) the ff-jarvis jobs write into their own checkout, not the main one; the
# page reads it once ff-jarvis's scripts/move-jobs-data.py has left its marker. The same path as
# ff-jarvis's model.JOBS_DATA (tests/test_sources_behind.py checks the two agree).
JOBS_DATA = pathlib.Path.home() / ".ff-jarvis-history" / "data"
FF_JARVIS_DATA = JOBS_DATA if (JOBS_DATA / ".jobs-data").exists() else pathlib.Path("C:/Users/David/Github/ff-jarvis/data")
DWR = pathlib.Path(os.environ.get("TEAM_WATCH_DATA", FF_JARVIS_DATA))
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
WEATHER_BACKTEST = DWR / "weather_backtest.json"
ROUTES = DWR / "routes_run.json"


def ff_jarvis_behind():
    """How many commits the ff-jarvis checkout DWR lives in is behind its origin/main, as of its last
    fetch; None when DWR is not a checkout's data/ (the test fixtures) or git cannot say.
    Why (2026-09-29): landed ff-jarvis data (the 2018 Records lineups) sat on origin while the main
    checkout, which the jobs write into, could not fast-forward; the page built from the old copy.
    build.py warns on it and scripts/land.ps1 refuses it. The fix is ff-jarvis's scripts/sync-main.py."""
    import subprocess
    repo = DWR.parent
    if not (repo / ".git").exists():
        return None
    r = subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD..origin/main"],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    return int(out) if r.returncode == 0 and out.isdigit() else None


def warn_if_stale():
    """build.py's last line: say so when this build came from a stale ff-jarvis checkout."""
    behind = ff_jarvis_behind()
    if behind:
        print(f"WARNING: built from an ff-jarvis checkout {behind} commit(s) behind origin/main; "
              f"run python {DWR.parent / 'scripts' / 'sync-main.py'} and rebuild")


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


def load_kickers():
    """norm_name -> Sleeper id for every rostered kicker (sleeper_status.json `kickers`, 2026-09-28),
    feed first, the file as a fallback; {} before ff-jarvis writes it."""
    try:
        block = (json.loads(FEED.read_text(encoding="utf-8")).get("status") or {}).get("data") or {}
        if block.get("kickers"):
            return block["kickers"]
    except (OSError, json.JSONDecodeError):
        pass
    d = read_first(SLEEPER_STATUS) or {}
    return d.get("kickers") or {}


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


def load_weather_history(days=8):
    """The last `days` files of ff-jarvis's history kind `weather` (one per date, every forecast fetch),
    as rows. design/wx_kicked.py keeps the last forecast before each kickoff; eight days covers a week
    from Thursday night to Monday night."""
    rows = []
    for path in sorted((DWR / "history" / "weather").glob("*.jsonl"))[-days:]:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_weather_backtest():
    """ff-jarvis's weather backtest (model/season/weather_backtest.py), the file only: it is
    rerun by hand, not by the scheduled refresh, so no feed block carries it. None when absent;
    design/wx_history.py cuts it to what the Weather view prints."""
    return read_first(WEATHER_BACKTEST)


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


def load_defense():
    """{form, injured, fetched} for the leg sheet's matchup line: the feed block `defense` first,
    else ff-jarvis's defense_form.json (points allowed by position) and sleeper_defense.json (hurt
    defenders) read directly. Either half may be None; design/defense.py cuts both."""
    block = feed_block(("defense",), "form")
    if block:
        return block
    form, hurt = read_first(DWR / "defense_form.json"), read_first(DWR / "sleeper_defense.json")
    return {"form": form, "injured": hurt, "fetched": None} if form or hurt else None


def load_startsit():
    """Our calls file (model.season.startsit_calls), None when ff-jarvis has not written it. The view
    reads only its per-position best spot (the board's lead); the calls themselves are v3's."""
    return read_first(DWR / "startsit_calls.json")


def load_startsit_v3():
    """Start/Sit v3 (model.season.startsit_v3, METHODOLOGY 12.75): SMASH, bold START and SIT, and their
    record. The feed's `startsit_v3` first (the block itself, or wrapped in `data` like the others),
    else ff-jarvis's startsit_v3.json. None before ff-jarvis writes it; design/startsit_v3.py then
    builds the empty week."""
    try:
        d = (json.loads(FEED.read_text(encoding="utf-8")) or {}).get("startsit_v3") or {}
    except (OSError, json.JSONDecodeError):
        d = {}
    d = d.get("data") if isinstance(d.get("data"), dict) else d
    return d if d.get("week") else read_first(DWR / "startsit_v3.json")


def load_expert_ranks():
    """FantasyPros' consensus position rank for every player this week (ff-jarvis's expert_ranks.json:
    `player_name`, `player_position_id`, `pos_rank` "WR14"). The file only, no feed block; None when it
    is missing. design/startsit_board.py cuts it into LIVE_SSB.fp."""
    return read_first(DWR / "expert_ranks.json")


def load_digest():
    """The league-wide week packet (model.season.weekly_digest), feed block `weekly_digest` first,
    the file second. design/digest.py cuts it for the Digest view; None when neither exists."""
    return feed_block(("weekly_digest",), "week") or read_first(DWR / "weekly_digest.json")


def load_digest_headline():
    """Claude's pick of the best story while no game is on (model.season.digest_headline, 2026-10-04):
    feed block `digest_headline` first, the file second. design/digest.py cuts it into
    LIVE_DIGEST.story; None when neither exists."""
    return feed_block(("digest_headline",), "week") or read_first(DWR / "digest_headline.json")


def load_highlights():
    """Players > Highlights: two Claude-written, number-checked lines per Players view
    (model.season.highlights, 2026-09-29), feed block `highlights` first, the file second. None when
    neither exists."""
    return feed_block(("highlights",), "views") or read_first(DWR / "highlights.json")


def load_role_board():
    """Each player's season so far: what his work is worth against what he scored, and last
    season's same gap (model.season.role_board, 2026-09-29), feed block `role_board` first, the
    file second. design/role.py cuts it for Players > Role; None when neither exists."""
    return feed_block(("role_board",), "players") or read_first(DWR / "role_board.json")


def load_slip_reasons():
    """Why each player with a line this week is worth a look (model.market.slip_reasons, 2026-10-03):
    a one-line `why`, the work behind it and tags, keyed by slug. Feed block `slip_reasons` first, the
    file second. build.py cuts it into LIVE_REASONS for the Slips board; None when neither exists."""
    return feed_block(("slip_reasons",), "players") or read_first(DWR / "slip_reasons.json")


def load_game_preview():
    """Each game of the week's facts and Claude's take (model.season.game_preview), feed block
    `game_preview` first, the file second. design/preview.py cuts it for This week > Preview."""
    return feed_block(("game_preview",), "games") or read_first(DWR / "game_previews.json")


def load_preview_record():
    """Claude's graded previews (every take against the final score, the spread and the market's win %),
    feed block `preview_record` first, the file second. design/preview.py cuts it into LIVE_PREVIEW.record;
    None when neither exists. `weeks` is [] until the first previewed week is final."""
    return feed_block(("preview_record",), "season") or read_first(DWR / "preview_record.json")


def load_league():
    """(this season, every past season) of the ESPN league, from ff-jarvis's model.clients.espn_league.
    Files only: neither is a feed block. design/league_recap.py cuts them for My teams > League."""
    return read_first(DWR / "espn_league.json"), read_first(DWR / "espn_league_history.json")


def league_path(key, kind):
    """One league's ff-jarvis data file (design/leagues.py names it), read or not."""
    return DWR / leagues.file(key, kind)


def load_league_yahoo(key="yahoo"):
    """(this season, past seasons, owner map) of a Yahoo league, from ff-jarvis's model.clients.yahoo_league.
    The owner map joins a past team to today's team of the same manager; it holds no names."""
    return tuple(read_first(league_path(key, k)) for k in ("league", "league_history", "league_owners"))


def load_league_back(key="yahoo"):
    """(box scores, weekly roast, manager names) of a Yahoo league for its back page and Records, from
    ff-jarvis's model.clients.yahoo_box, model.season.league_roast and data/yahoo_league_managers.json (first
    names, David's call for Records, 2026-09-27). Any may be missing; the pages draw without them."""
    return tuple(read_first(league_path(key, k)) for k in ("league_box", "league_recap", "league_managers"))


def load_case_rosters(key="yahoo"):
    """Each Yahoo season's champion and last-place team as their final lineups (ff-jarvis
    data/yahoo_case_rosters.json, 2026-09-28), for Records' two cases. None without it; the cases draw
    without it, their slots just do not open."""
    return read_first(league_path(key, "case_rosters"))


def load_trades(key="yahoo"):
    """ff-jarvis's trade verdicts (model.season.trade_verdicts): every Yahoo trade 2018 on, who won it by
    points above replacement, the games and playoff spots it decided, curses. A file, not a feed block."""
    return read_first(league_path(key, "trade_verdicts"))


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


if __name__ == "__main__":
    # scripts/land.ps1: `python design/sources.py --fetch` fetches the ff-jarvis checkout, then prints
    # how far behind it is and where it is; "None" when DWR is not a checkout.
    import subprocess
    import sys
    if "--fetch" in sys.argv and (DWR.parent / ".git").exists():
        subprocess.run(["git", "-C", str(DWR.parent), "fetch", "--quiet", "origin", "main"])
    print(ff_jarvis_behind(), DWR.parent)
