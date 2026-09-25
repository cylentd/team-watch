"""LIVE_ARCHETYPE and LIVE_TRENCHES: ff-jarvis's model.season.archetype (every player in the
season's grid, keyed by slug -- the role/style/athletic_profile envelope) and model.season.trenches
(32 teams, OL continuity and injury exposure). model/season/ARCHETYPE.md in ff-jarvis is the
contract both producers write to.

archetype.json is already keyed by slug -- the producer's own bridge join, not name-matched here
-- so this file does no re-keying, only the same wanted-slug cut pedigree.py/routes.py already
make: the page only ever opens a profile for a player it can show a row for. trenches.json is
small (32 teams) and passed through whole, the same way sources.py's load_weather() passes weather
through untouched: a team-keyed block this size needs no cut, and the non-goal is lineman-level
display, not team count.

Self-contained like wire_watch.py/usage.py: the feed path and ff-jarvis data root come in as
arguments rather than through sources.py, which reserves itself for readers that reshape nothing.
"""
import json


def _load(feed_path, dwr_path, feed_key, file_name, must):
    """The feed block at `feed_key` when it carries `must`, else the ff-jarvis file directly --
    same two-tier pattern as every other design/*.py loader (see wire_watch.load_wire)."""
    try:
        block = (json.loads(feed_path.read_text(encoding="utf-8")).get(feed_key) or {}).get("data")
        if block and block.get(must):
            return block
    except (OSError, json.JSONDecodeError):
        pass
    path = dwr_path / file_name
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None


def load_archetype(feed_path, dwr_path):
    """ff-jarvis's data/archetype.json: feed block `archetype` first, the file second."""
    return _load(feed_path, dwr_path, "archetype", "archetype.json", "players")


def load_trenches(feed_path, dwr_path):
    """ff-jarvis's data/trenches.json: feed block `trenches` first, the file second."""
    return _load(feed_path, dwr_path, "trenches", "trenches.json", "teams")


def live_archetype(archetype, wanted):
    """LIVE_ARCHETYPE: {generated, season, players: {slug -> the 13-key envelope}}, cut to the
    page's own wanted slug set -- or None when ff-jarvis has not run model.season.archetype yet.
    No re-keying: archetype.json is already keyed by slug and its envelope is exactly what
    ARCHETYPE.md's contract defines (every key present, null with a reason where the position or
    the sample has nothing to say), so passing a player's record through as-is is the whole job."""
    if not archetype or not archetype.get("players"):
        return None
    players = {slug: rec for slug, rec in archetype["players"].items() if slug in wanted}
    if not players:
        return None
    return {"generated": archetype.get("generated"), "season": archetype.get("season"), "players": players}


# The team record's own envelope (model/season/trenches.py): a count and, when it is null or
# zero for a reason worth naming, the reason beside it -- the same null-carries-its-reason rule
# ARCHETYPE.md states for role/style, applied to a team instead of a player. `ol_starters_out`
# is the before-kickoff read: the same five-most-used-linemen pool `ol_continuity` measures,
# checked against this week's Out/Doubtful designations instead of who actually played.
TEAM_FIELDS = ["ol_continuity", "ol_continuity_of", "ol_continuity_reason",
               "ol_out", "ol_out_by_status", "ol_out_reason",
               "ol_starters_out", "ol_starters_out_of", "ol_starters_out_names",
               "ol_starters_out_reason"]


def live_trenches(trenches):
    """LIVE_TRENCHES: {generated, season, week, teams: {team -> ol_continuity/ol_out and their
    reasons}}, every team passed through whole -- no wanted-slug cut needed, the same call
    sources.py's load_weather() makes for its own 32-team block. None when ff-jarvis has not run
    model.season.trenches yet."""
    if not trenches or not trenches.get("teams"):
        return None
    teams = {team: {k: rec.get(k) for k in TEAM_FIELDS} for team, rec in trenches["teams"].items()}
    return {"generated": trenches.get("generated"), "season": trenches.get("season"),
            "week": trenches.get("week"), "teams": teams}


def report_archetype(archetype):
    """build.py's one-line summary of LIVE_ARCHETYPE."""
    return (f"Archetype: {len(archetype['players'])} players"
            if archetype else "Archetype: none, so no role/style labels")


def report_trenches(trenches):
    """build.py's one-line summary of LIVE_TRENCHES."""
    return (f"Trenches: {len(trenches['teams'])} teams"
            if trenches else "Trenches: none, so no OL context")
