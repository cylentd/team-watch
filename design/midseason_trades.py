"""Chapter 2 of the midseason film, the trade tracker: where Aura's three September trades stand
through Week 8, and his record had none of them happened (docs/madden-film-chapter2.md).

Leads are ff-jarvis's own trade_verdicts.verdicts() (the Trade history page's PAR) recomputed at each
week's cutoff; this module never reimplements the PAR formula. The no-trade record is rebuilt from
the player box scores: every trade is undone from Week 2, each team keeps its other real starters,
bench and waiver moves, and a traded-in starter's slot goes to the best eligible player left by
Yahoo's own projection that week (a player the team traded away comes back when Yahoo projected him
higher). A defense slot with no defense left gets the team's Week 1 defense. Every recomputed actual
score must match yahoo_league.json, or the build fails: the edition is frozen.
"""
from constants_midseason import ISO_DATE_LENGTH

import sys
from pathlib import Path

from midseason_draft import BENCH_SLOTS, norm

YEAR = '2026'
LEAGUE_ID = 75203
THROUGH = 8                 # the frozen edition's last week
AURA = 6                    # Yahoo team id of the team that made all three trades
FIRST_DEAL_WEEK = 2         # the first fantasy week a September trade counts in
SCORE_TOLERANCE = .05       # Yahoo shows scores to the hundredth; wider than rounding, tighter than a point
CENTS = 2
ELIGIBLE = {'QB': {'QB'}, 'RB': {'RB'}, 'WR': {'WR'}, 'TE': {'TE'}, 'W/R/T': {'RB', 'WR', 'TE'},
            'K': {'K'}, 'DEF': {'DEF'}}
DST_ALIAS = {'LAR': 'LA'}   # gamelog_kdst.json files the Rams under either code
NAME_SUFFIX = ('Jr', 'Sr', 'II', 'III', 'IV', 'V')
PC_FF_JARVIS = Path('C:/Users/David/Github/ff-jarvis')


def short_name(player):
    if player['pos'] == 'DEF':
        return f"{player['name']} D/ST"
    parts = player['name'].strip().split()
    while len(parts) > 2 and parts[-1].rstrip('.') in NAME_SUFFIX:
        parts.pop()
    first, rest = parts[0], ' '.join(parts[1:])
    return ' '.join(parts) if '.' in first else f'{first[0]}. {rest}'


def _key(player):
    return 'def:' + player['name'].lower() if player['pos'] == 'DEF' else norm(player['name'])


def _original_owners(trades):
    """key -> the team that held the player before any trade moved him."""
    owners = {}
    for trade in sorted(trades, key=lambda row: row['when']):
        teams = [int(side['team']) for side in trade['sides']]
        for side in trade['sides']:
            other = next(team for team in teams if team != int(side['team']))
            for player in side['players']:
                owners.setdefault(_key(player), other)
    return owners


def _week_state(games):
    """(seen, lineups): every rostered player that week by key, and each team's (starters, bench)."""
    seen, lineups = {}, {}
    for game in games:
        for side, team in (('a', game['home']), ('b', game['away'])):
            starters, bench = [], []
            for slot in game['slots']:
                player = slot.get(side)
                if player:
                    (bench if slot['slot'] in BENCH_SLOTS else starters).append((slot['slot'], player))
            bench += [('BN', player) for player in (game.get('bench') or {}).get(side) or []]
            for _, player in starters + bench:
                seen[_key(player)] = (player['pos'], player.get('pts') or 0.0, player.get('proj') or 0.0, player['name'])
            lineups[int(team)] = (starters, bench)
    return seen, lineups


def _dst_points(kdst, nfl, week):
    rows = kdst.get(nfl) or kdst.get(DST_ALIAS.get(nfl)) or []
    return next((row['dst_yahoo'] for row in rows if row['week'] == week), None)


def _week1_defenses(games, kdst):
    """team -> (nfl, name) of the defense it started in Week 1, checked against gamelog_kdst."""
    out = {}
    for game in games:
        for side, team in (('a', game['home']), ('b', game['away'])):
            for slot in game['slots']:
                player = slot['slot'] == 'DEF' and slot.get(side)
                if not player:
                    continue
                out[int(team)] = (player['nfl'], player['name'])
                logged = _dst_points(kdst, player['nfl'], 1)
                if logged is not None and abs(logged - (player.get('pts') or 0)) >= SCORE_TOLERANCE:
                    raise ValueError(f'Team {team} Week 1 defense: box {player.get("pts")} vs gamelog {logged}')
    return out


def _fill_hole(slot, pool, seen, week, team, standin):
    candidates = sorted(key for key in pool if seen[key][0] in ELIGIBLE[slot])
    if candidates:
        best = max(candidates, key=lambda key: seen[key][2])
        pool.discard(best)
        return best
    if slot != 'DEF' or standin is None:
        raise ValueError(f'Week {week} team {team}: nobody left for {slot}')
    seen[f'standin:{team}'] = ('DEF', standin, 0.0, 'Week 1 defense')
    return f'standin:{team}'


def _team_score(team, week, starters, bench, seen, owners, standin_of):
    """(actual, no-trade) for one team-week."""
    projected = lambda key: seen[key][2]
    pool = {_key(player) for _, player in bench if _key(player) not in owners}
    pool |= {key for key in owners if owners[key] == team and key in seen}
    lineup, holes = [], []
    for slot, player in starters:
        key = _key(player)
        if key in owners and owners[key] != team:
            holes.append(slot)      # he came by trade: his slot goes to someone the team still has
        else:
            lineup.append([slot, key])
    for slot in holes:
        lineup.append([slot, _fill_hole(slot, pool, seen, week, team, standin_of(team))])
    kept = [key for key in pool if key in owners and owners[key] == team]
    for key in sorted(kept, key=lambda key: (-projected(key), key)):
        spots = [i for i, (slot, held) in enumerate(lineup) if seen[key][0] in ELIGIBLE[slot] and projected(held) < projected(key)]
        if spots:
            i = min(spots, key=lambda i: projected(lineup[i][1]))
            pool.add(lineup[i][1])
            lineup[i][1] = key
            pool.discard(key)
    actual = round(sum(player.get('pts') or 0 for _, player in starters), CENTS)
    return actual, round(sum(seen[key][1] for _, key in lineup), CENTS)


def no_trade_results(boxes, trades, kdst, weeks=None):
    """{week: {team: (actual, noTrades)}} for the weeks given (Week 1 is before any trade counts)."""
    weeks = tuple(weeks or range(1, THROUGH + 1))
    owners = _original_owners(trades)
    if not boxes.get('weeks', {}).get('1'):
        raise ValueError('Week 1 has no box scores')
    week1 = _week1_defenses(boxes['weeks']['1'], kdst)
    out = {}
    for week in weeks:
        games = boxes.get('weeks', {}).get(str(week))
        if not games:
            raise ValueError(f'Week {week} has no box scores')
        seen, lineups = _week_state(games)

        def standin_of(team, week=week):
            return _dst_points(kdst, week1[team][0], week) if team in week1 else None
        out[week] = {}
        for team, (starters, bench) in lineups.items():
            if week < FIRST_DEAL_WEEK:
                actual = round(sum(player.get('pts') or 0 for _, player in starters), CENTS)
                out[week][team] = (actual, actual)
            else:
                out[week][team] = _team_score(team, week, starters, bench, seen, owners, standin_of)
    return out


def check_actuals(results, games):
    """Raise when a recomputed actual score is not the one Yahoo recorded."""
    for game in games:
        week = game['week']
        if week not in results:
            continue
        for team, shown in ((game['home'], game['hp']), (game['away'], game['ap'])):
            mine = results[week].get(team)
            if mine is None or abs(mine[0] - shown) >= SCORE_TOLERANCE:
                raise ValueError(f'Week {week} team {team}: recomputed {mine and mine[0]} vs Yahoo {shown}')


def story_of(results, games, team):
    """One team's record as played and with no trades, and the games the trades turned."""
    record, flips = {'actual': [0, 0], 'noTrades': [0, 0]}, []
    for game in sorted(games, key=lambda row: row['week']):
        week = game['week']
        if week not in results or team not in (game['home'], game['away']):
            continue
        opponent = game['away'] if game['home'] == team else game['home']
        actual = [results[week][team][0], results[week][opponent][0]]
        notrade = [results[week][team][1], results[week][opponent][1]]
        won, would = actual[0] > actual[1], notrade[0] > notrade[1]
        record['actual'][0 if won else 1] += 1
        record['noTrades'][0 if would else 1] += 1
        if won != would:
            flips.append({'week': week, 'opponent': opponent, 'actual': actual, 'noTrades': notrade})
    return {'record': {kind: f'{w}-{l}' for kind, (w, l) in record.items()}, 'flips': flips}


def deal_series(trades, games, points_upto, verdicts, team, through=THROUGH):
    """Each trade of `team`, oldest first: who leads it at the last cutoff and week by week.
    `verdicts` is ff-jarvis's trade_verdicts.verdicts; `points_upto(week)` the points through that week.
    A weekly lead is signed from the partner's side: positive when the partner leads."""
    only = {'seasons': {YEAR: trades['seasons'][YEAR]}}
    rows = {}
    for cut in range(FIRST_DEAL_WEEK, through + 1):
        cut_games = [game for game in games if game['week'] <= cut]
        for row in verdicts(only, {YEAR: cut_games}, lambda _year, cut=cut: points_upto(cut), YEAR):
            rows.setdefault(row['when'], []).append((cut, row))
    return [_deal(series, team, through) for _, series in sorted(rows.items())]


def _deal(series, team, through):
    cut, final = series[-1]
    if cut != through:
        raise ValueError(f'Trade {final["when"]} has no verdict at Week {through}')
    mine = next(side for side in final['sides'] if side['team'] == team)
    theirs = next(side for side in final['sides'] if side['team'] != team)
    partner = theirs['team']
    by_par = lambda side: [short_name(p) for p in sorted(side['players'], key=lambda p: -p['par_reg'])]
    weekly = []
    for week, row in series:
        leader = max(row['sides'], key=lambda side: side['tree'])['team']
        weekly.append({'week': week, 'leader': leader, 'lead': row['margin'] if leader == partner else -row['margin']})
    return {'when': final['when'][:ISO_DATE_LENGTH], 'partner': partner, 'sent': by_par(theirs),
            'got': by_par(mine), 'leader': weekly[-1]['leader'], 'lead': final['margin'], 'weekly': weekly}


def trades_block(season, boxes, trades_doc, kdst, points_upto, verdicts, through=THROUGH, team=AURA):
    games = [game for game in season['games'] if game['week'] <= through]
    season_trades = trades_doc['seasons'][YEAR]['trades']
    results = no_trade_results(boxes, season_trades, kdst, weeks=range(1, through + 1))
    check_actuals(results, games)
    story = story_of(results, games, team)
    return {'through': through, 'team': team, **story,
            'deals': deal_series(trades_doc, games, points_upto, verdicts, team, through)}


def ff_jarvis_root(repo=None):
    """ff-jarvis beside this checkout, or beside the main one above a .claude/worktrees one (yt_channels.py's search)."""
    here = Path(repo or Path(__file__).resolve().parents[1])
    found = (parent / 'ff-jarvis' for parent in here.parents)
    return next((path for path in found if (path / 'model' / 'season').is_dir()), PC_FF_JARVIS)


def _verdict_tools(root):
    """(verdicts, load_points) from ff-jarvis's model.season.trade_verdicts; its code, read-only, as the Trade
    history page runs it. The path is added only while importing so ff-jarvis's `model` cannot shadow ours."""
    sys.path.insert(0, str(root))
    try:
        from model.season import trade_verdicts  # noqa: PLC0415
    finally:
        sys.path.remove(str(root))
    return trade_verdicts.verdicts, trade_verdicts.load_points


def load_trades(data, root=None):
    """The chapter's block from ff-jarvis's files, or None when one is missing."""
    import json  # noqa: PLC0415
    data = Path(data)
    files = [data / name for name in ('yahoo_league.json', 'yahoo_league_box.json', 'yahoo_league_trades.json', 'gamelog_kdst.json')]
    root = Path(root) if root else ff_jarvis_root()
    if not all(path.exists() for path in files) or not (root / 'model' / 'season' / 'trade_verdicts.py').exists():
        return None
    season, boxes, trades_doc, kdst = (json.loads(path.read_text(encoding='utf-8')) for path in files)
    if str(season.get('league_id')) != str(LEAGUE_ID):     # the file keeps it as text
        raise ValueError(f'Trade tracker is for league {LEAGUE_ID}, not {season.get("league_id")}')
    verdicts, load_points = _verdict_tools(root)
    points = load_points(int(YEAR))
    return trades_block(season, boxes, trades_doc, kdst['teams'],
                        lambda cut: points[points.week <= cut], verdicts)
