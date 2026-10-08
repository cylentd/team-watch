"""DFS covers the Sunday main slate only (David, 2026-10-08): Yahoo's contest holds the Sunday early and
afternoon games, none of Thursday, Sunday night or Monday. build.live_dfs_yahoo cuts the pool here, so the
pool table, the lineup builder and every lineup it shows read the same rows.

ff-jarvis puts `slate_window` on each pool row (commit 3fb052f, `model.clients.dfs.slate_window`, the one
copy of the rule). A pool saved before then has no key: the row's game kickoff in the schedule stands in,
cut the same way. The page never computes a model number; this only decides which Yahoo rows are in the contest.
"""
import datetime as dt

import contract
from schedule import TO_ESPN
from slate import LOCAL_TZ, UTC

# The window names ff-jarvis writes. A value outside this set fails the build; null is a row with no kickoff.
WINDOWS = ("thu", "early", "afternoon", "night", "mnf", "other")
MAIN_SLATE = ("early", "afternoon")        # the contest's games, David 2026-10-08
SUNDAY = 6                                 # datetime.weekday()
NIGHT_FROM_HOUR = 17                       # Sunday 17:00 PT, ff-jarvis dfs.NIGHT_FROM_HOUR: the 8:20 pm ET game


def _canon(code, team_fix):
    code = team_fix.get(code, code)
    return TO_ESPN.get(code, code)


def _kickoffs(schedule, team_fix):
    """{frozenset({away, home}): kickoff datetime} for the page week's games (every game when no week)."""
    week = (schedule or {}).get("week")
    out = {}
    for g in (schedule or {}).get("games") or []:
        if week is not None and g.get("week") not in (None, week):
            continue
        out[frozenset((_canon(g["away"], team_fix), _canon(g["home"], team_fix)))] = dt.datetime.fromisoformat(
            g["kickoff"].replace("Z", "+00:00")).astimezone(UTC)
    return out


def _in_main_slate_by_kickoff(when):
    local = when.astimezone(LOCAL_TZ)
    return local.weekday() == SUNDAY and local.hour < NIGHT_FROM_HOUR


def _keep(row, kickoffs, team_fix):
    """True or False when the row's window is known, None when it cannot be."""
    window = row.get("slate_window")
    if window is not None:
        if window not in WINDOWS:
            raise contract.ContractError(
                f"contract: dfs pool row {row.get('name')!r} has slate_window {window!r}, expected one of {', '.join(WINDOWS)}")
        return window in MAIN_SLATE
    away, _, home = (row.get("game") or "").partition("@")
    when = kickoffs.get(frozenset((_canon(away, team_fix), _canon(home, team_fix))))
    return None if when is None else _in_main_slate_by_kickoff(when)


def main_slate(pool, schedule, team_fix):
    """The pool with only the main slate's rows. A row whose window is unknown (no key and no schedule game,
    or a null key) stays, so a missing schedule never blanks the page. No pool is no pool. The input is not changed."""
    if not pool:
        return pool
    kickoffs = _kickoffs(schedule, team_fix)
    players = [r for r in pool["players"] if _keep(r, kickoffs, team_fix) is not False]
    return {**pool, "players": players}
