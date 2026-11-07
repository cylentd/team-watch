"""Chapter 3 of the midseason film, Best pickups: the three players a team started who came off the wire,
ranked by the points each added over the lineup the owner would otherwise have run (docs/madden-film-chapter3.md).

Method (David, 2026-11-05), Yahoo league 75203, Weeks 1-8:
- A pickup is a player a team started that it neither drafted nor received in a 2026 trade. No K or DEF, and
  at least MIN_STARTS starts.
- For each week he started, remove him and refill his slot with the owner's best usable bench player by Yahoo's
  projection that week (eligible for the slot, projection above 0). With none usable the slot takes the waiver
  pick: the unrostered player at his position who played that week and has the best average half-PPR points in
  the weeks before (no hindsight about that week). Points added = his score minus the stand-in's.
- Every recomputed real score must match yahoo_league.json, or the build fails: the edition is frozen.
- A weekly rank is his place among every NFL player at the position that week by half-PPR points; a QB gets one
  point back per interception (Yahoo takes 1, nflverse 2), which reproduces the box scores.
Wins swung are signed per week: +1 when he won a game the stand-in would have lost, -1 the other way.
"""
from constants_midseason import ISO_DATE_LENGTH, STANDIN_PLAYER_INDEX

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from _espn import slugify  # noqa: E402
from midseason_trades import (BENCH_SLOTS, ELIGIBLE, LEAGUE_ID, SCORE_TOLERANCE, THROUGH,  # noqa: E402
                              YEAR, _key, ff_jarvis_root)

MIN_STARTS = 3              # David, 2026-11-05: fewer starts is not a story
TOP = 3                     # the chapter shows three
CENTS = 2
TENTHS = 1
INT_ADDBACK = 1             # nflverse takes 2 per interception, Yahoo 1
NO_STANDIN = 'none'
SKIP_POS = frozenset(('K', 'DEF'))
# A team's name on the day of a move (the draft file and transaction log keep old names).
NAME_ALIAS = {'Le-Chase-Godwin Curse': 6, 'Le-GM': 6}
METHOD = ('Each pickup removed from the weeks his team started him, his slot refilled by the owner\'s best '
          'bench player by Yahoo projection, else the best waiver pick; points added = his score minus the stand-in\'s.')


def check_league(season):
    if str(season.get('league_id')) != str(LEAGUE_ID):     # the file keeps it as text
        raise ValueError(f'Best pickups is for league {LEAGUE_ID}, not {season.get("league_id")}')


def _week_state(games):
    """(seen, lineups): every rostered player that week by key -> (pos, pts, proj, name), and each team's
    (starters [(slot, key)], bench [key])."""
    seen, lineups = {}, {}
    for game in games:
        for side, team in (('a', game['home']), ('b', game['away'])):
            starters, bench = [], []
            for slot in game['slots']:
                player = slot.get(side)
                if player:
                    (bench if slot['slot'] in BENCH_SLOTS else starters).append((slot['slot'], _key(player)))
            bench_players = (game.get('bench') or {}).get(side) or []
            bench += [_key(player) for player in bench_players]
            for player in [slot[side] for slot in game['slots'] if slot.get(side)] + list(bench_players):
                seen[_key(player)] = (player['pos'], player.get('pts') or 0.0, player.get('proj') or 0.0, player['name'])
            lineups[int(team)] = (starters, bench)
    return seen, lineups


def _weeks(boxes, through):
    out = {}
    for week in range(1, through + 1):
        games = boxes.get('weeks', {}).get(str(week))
        if not games:
            raise ValueError(f'Week {week} has no box scores')
        out[week] = _week_state(games)
    return out


class Wire:
    """The waiver pick: ff-jarvis's half-PPR rows (key, pos, week, pts), read without hindsight."""

    def __init__(self, rows, names=None):
        self.rows = [row for row in rows]
        self.played = {(row['key'], row['pos'], row['week']): row['pts'] for row in self.rows}
        self.names = names or {}

    def pick(self, week, pos, held):
        earlier = defaultdict(list)
        for row in self.rows:
            if row['pos'] == pos and row['week'] < week:
                earlier[row['key']].append(row['pts'])
        order = sorted(earlier, key=lambda key: (-sum(earlier[key]) / len(earlier[key]), key))
        for key in order:
            if key not in held and (key, pos, week) in self.played:
                return self.names.get(key, key), self.played[(key, pos, week)]
        return NO_STANDIN, 0.0


def _rescore(state, team, out, wire, week):
    """(team's week score with the `out` keys removed, {removed key: stand-in name})."""
    seen, lineups = state
    starters, bench = lineups[team]
    pool = {key for key in bench if key not in out}
    score, standins = 0.0, {}
    for slot, key in starters:
        if key not in out:
            score += seen[key][1]
            continue
        usable = sorted(k for k in pool if seen[k][0] in ELIGIBLE[slot] and seen[k][2] > 0)
        if usable:
            best = max(usable, key=lambda k: seen[k][2])
            pool.discard(best)
            standins[key], points = seen[best][STANDIN_PLAYER_INDEX], seen[best][1]
        else:
            standins[key], points = wire.pick(week, seen[key][0], set(seen))
        score += points
    return round(score, CENTS), standins


def check_actuals(weeks, games):
    """Raise when the engine, run with nobody removed, does not give Yahoo's recorded score."""
    for game in games:
        week = game['week']
        if week not in weeks:
            continue
        for team, shown in ((game['home'], game['hp']), (game['away'], game['ap'])):
            mine, _ = _rescore(weeks[week], int(team), set(), None, week)
            if abs(mine - shown) >= SCORE_TOLERANCE:
                raise ValueError(f'Week {week} team {team}: recomputed {mine} vs Yahoo {shown}')


def _team_ids(names, draft_by):
    team = names.get(draft_by, NAME_ALIAS.get(draft_by))
    if team is None:
        raise ValueError(f'Best pickups: {draft_by} is not a league team')
    return team


def _own_players(draft_picks, trades, names):
    """{(team, key)} the team drafted or received in a 2026 trade."""
    own = {(_team_ids(names, pick['drafted_by']), _key(pick)) for pick in draft_picks}
    for trade in trades:
        own |= {(int(side['team']), _key(player)) for side in trade['sides'] for player in side['players']}
    return own


def weekly_rank(rows, ints, key, pos, week):
    """(points, place) among every NFL player at `pos` that week; (0.0, None) when he has no row."""
    scores = {}
    for row in rows:
        if row['pos'] == pos and row['week'] == week:
            scores[row['key']] = round(row['pts'] + (INT_ADDBACK * ints.get((row['key'], week), 0) if pos == 'QB' else 0), CENTS)
    if key not in scores:
        return 0.0, None
    return scores[key], 1 + sum(score > scores[key] for score in scores.values())


def claim_of(moves, key, team_names):
    """(way, day) of the team's latest Yahoo add of the player."""
    adds = [move for move in moves if move.get('league') == 'yahoo' and move.get('kind') == 'add'
            and move['key'] == key and move['by'] in team_names]
    if not adds:
        raise ValueError(f'Best pickups: no add of {key} in the transaction log')
    last = max(adds, key=lambda move: move['when'])
    return last['via'], last['when'][:ISO_DATE_LENGTH]


def _result(game, team, score):
    mine, theirs = (game['hp'], game['ap']) if game['home'] == team else (game['ap'], game['hp'])
    return mine, theirs, int(mine > theirs) - int(score > theirs)


def _pickup(team, key, started, weeks, games, wire):
    """added, wins and weekly detail for one player his team started in `started` weeks."""
    added, detail = 0.0, []
    for week in started:
        score, standins = _rescore(weeks[week], team, {key}, wire, week)
        game = next(g for g in games if g['week'] == week and team in (g['home'], g['away']))
        mine, _, swing = _result(game, team, score)
        added += mine - score
        detail.append({'week': week, 'standIn': standins[key], 'swing': swing})
    return round(added, TENTHS), detail


def _find_pickups(weeks, own, games, wire):
    starts = defaultdict(list)
    for week, (seen, lineups) in weeks.items():
        for team, (starters, _) in lineups.items():
            for _, key in starters:
                if (team, key) not in own and seen[key][0] not in SKIP_POS:
                    starts[(team, key)].append(week)
    found = []
    for (team, key), started in starts.items():
        if len(started) >= MIN_STARTS:
            added, detail = _pickup(team, key, started, weeks, games, wire)
            found.append({'team': team, 'key': key, 'added': added, 'detail': detail})
    return found


def pickups_block(season, boxes, draft_picks, trades, point_rows, moves, ints=None, names=None, through=THROUGH):
    """The chapter's block. `point_rows` are ff-jarvis's half-PPR rows as dicts (key, pos, week, pts); `ints`
    {(key, week): interceptions} for QB ranks; `names` {key: display name} for waiver stand-ins."""
    ints = ints or {}
    games = [game for game in season['games'] if game['week'] <= through]
    weeks = _weeks(boxes, through)
    check_actuals(weeks, games)
    team_of = {team['name']: int(team_id) for team_id, team in season['teams'].items()}
    own = _own_players(draft_picks, trades, team_of)
    found = _find_pickups(weeks, own, games, Wire(point_rows, names))
    top = sorted(found, key=lambda row: (-row['added'], row['key']))[:TOP]
    return {'through': through, 'method': METHOD,
            'top': [_entry(rank, row, weeks, season, point_rows, ints, moves) for rank, row in enumerate(top, 1)]}


def _entry(rank, row, weeks, season, point_rows, ints, moves):
    team, key = row['team'], row['key']
    pos, _, _, name = weeks[row['detail'][0]['week']][0][key]
    team_name = season['teams'][str(team)]['name']
    aliases = {alias for alias, owner in NAME_ALIAS.items() if owner == team}
    via, when = claim_of(moves, key, {team_name} | aliases)
    detail = []
    for item in row['detail']:
        pts, place = weekly_rank(point_rows, ints, key, pos, item['week'])
        detail.append({'week': item['week'], 'pts': round(pts, TENTHS), 'rank': place,
                       'standIn': item['standIn'], 'swing': item['swing']})
    return {'rank': rank, 'name': name, 'slug': slugify(name), 'pos': pos, 'team': team, 'teamName': team_name,
            'via': via, 'when': when, 'starts': len(detail), 'added': row['added'],
            'wins': sum(item['swing'] for item in detail), 'weeks': detail}


def _ff_tools(root):
    """(load_points, key, CACHE) from ff-jarvis, imported read-only; the path is added only while importing so
    its `model` cannot shadow ours."""
    sys.path.insert(0, str(root))
    try:
        from model import CACHE  # noqa: PLC0415
        from model.season import trade_verdicts  # noqa: PLC0415
    finally:
        sys.path.remove(str(root))
    return trade_verdicts.load_points, trade_verdicts.key, CACHE


def _moves(data):
    import json  # noqa: PLC0415
    lines = (line for path in sorted((data / 'history' / 'transactions').glob('*.jsonl'))
             for line in path.read_text(encoding='utf-8').splitlines() if line.strip())
    return [json.loads(line) for line in lines]


def _nflverse_extras(cache, tv_key):
    """({(key, week): interceptions}, {key: display name}) from the weekly stats file load_points reads."""
    import pandas as pd  # noqa: PLC0415
    raw = pd.read_parquet(Path(cache) / f'spw_{YEAR}.parquet',
                          columns=['player_display_name', 'position', 'week', 'season_type', 'passing_interceptions'])
    raw = raw[raw.season_type == 'REG']
    names = {tv_key(name): name for name in raw.player_display_name}
    qbs = raw[raw.position == 'QB']
    ints = {(tv_key(row.player_display_name), int(row.week)): int(row.passing_interceptions or 0) for row in qbs.itertuples()}
    return ints, names


def load_pickups(data, root=None):
    """The chapter's block from ff-jarvis's files, or None when one is missing."""
    import json  # noqa: PLC0415
    data = Path(data)
    files = [data / name for name in ('yahoo_league.json', 'yahoo_league_box.json', 'yahoo_draft.json', 'yahoo_league_trades.json')]
    root = Path(root) if root else ff_jarvis_root()
    if not all(path.exists() for path in files) or not (data / 'history' / 'transactions').is_dir() \
            or not (root / 'model' / 'season' / 'trade_verdicts.py').exists():
        return None
    season, boxes, draft, trades_doc = (json.loads(path.read_text(encoding='utf-8')) for path in files)
    check_league(season)
    load_points, tv_key, cache = _ff_tools(root)
    frame = load_points(int(YEAR))
    rows = [{'key': row.key, 'pos': row.pos, 'week': int(row.week), 'pts': float(row.pts)} for row in frame.itertuples()]
    ints, names = _nflverse_extras(cache, tv_key)
    return pickups_block(season, boxes, draft['picks'], trades_doc['seasons'][YEAR]['trades'], rows, _moves(data),
                         ints=ints, names=names)
