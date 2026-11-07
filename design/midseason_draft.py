"""Chapter 1 of the midseason film, Draft Receipts: what every Madden Curse pick cost and returned.

Rule A (David, 2026-11-03): a week's position rank is the player's place among every QB, RB, WR or
TE that week in nflverse half-PPR. A smash week is a top-6 QB/TE or top-12 RB/WR week; a bust week
is outside QB/TE 18 or RB/WR 36. A pick's price is the order his position went in the draft (the
40th receiver taken is WR40); his finish is his season-total rank through the edition's week; value
is price minus finish, so missed games count as zeros on purpose. K and DEF picks carry no value.
"""
from constants_midseason import INJURY_RECEIPT_GAMES, ISO_DATE_LENGTH, RECEPTION_POINTS, SEASON_START_MONTH

import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from _espn import slugify  # noqa: E402

SMASH = {'QB': 6, 'TE': 6, 'RB': 12, 'WR': 12}
BUST = {'QB': 18, 'TE': 18, 'RB': 36, 'WR': 36}
THROUGH = 8
SEASON = 2026
BENCH_SLOTS = frozenset(('BN', 'Bench', 'IR', 'IR+'))
# The draft file keeps the name a team had on draft night; team 6 drafted as this, now OBJ - AuraFarming.
DRAFT_ALIAS = {'Le-Chase-Godwin Curse': 6}
# nflverse rows carry the name a player played under then (ff-jarvis model.season.trade_verdicts.ALIAS).
NAME_ALIAS = {'hollywood brown': 'marquise brown', 'nyheim millerhines': 'nyheim hines'}
SUFFIX = re.compile(r'\b(jr|sr|ii|iii|iv|v)\b\.?$')
BEATS = ('steal', 'traded', 'sleeper', 'curse', 'injury')
DAYS_PER_WEEK = 7
CENTS = 2   # half-PPR points move in tenths and halves, so cents never merge two real scores


def norm(name):
    """ff-jarvis's player key (model.common.data.norm_name), so draft, points and moves agree."""
    key = SUFFIX.sub('', re.sub(r"[.'\-]", '', str(name).lower()).strip()).strip()
    key = re.sub(r'\s+', ' ', key)
    return NAME_ALIAS.get(key, key)


def fantasy_week(when, season=SEASON):
    """The fantasy week a move counts in: weeks open the Tuesday after Labor Day, and a move counts
    from the day after it (ff-jarvis trade_verdicts.trade_week, the rule the Trades page uses)."""
    first = datetime.date(season, SEASON_START_MONTH, 1)
    labor = first + datetime.timedelta(days=(DAYS_PER_WEEK - first.weekday()) % DAYS_PER_WEEK)
    day = datetime.date.fromisoformat(when[:ISO_DATE_LENGTH]) + datetime.timedelta(days=1)
    return max(1, 1 + (day - labor - datetime.timedelta(days=1)).days // DAYS_PER_WEEK)


def _team(name, names):
    team = names.get(name, DRAFT_ALIAS.get(name))
    if team is None:
        raise ValueError(f'Draft Receipts: {name} is not a league team')
    return team


def _ranks(scores):
    """{item: points} -> {item: competition rank}, ties share the better place. Points are rounded to
    the cent first: float sums split true ties (Ferguson's 36.0 vs Tremble's 36.00000000000001 TE
    totals through Week 8 put Honey Bijan at -109 instead of -108, 2026-11-03)."""
    rounded = {item: round(points, CENTS) for item, points in scores.items()}
    ordered = sorted(rounded.values(), reverse=True)
    return {item: ordered.index(points) + 1 for item, points in rounded.items()}


def pick_receipts(picks, rows, names, through=THROUGH):
    rows = [row for row in rows if row['week'] <= through and row['pos'] in SMASH]
    weekly, totals = defaultdict(dict), defaultdict(float)
    for row in rows:
        weekly[(row['week'], row['pos'])][row['key']] = row['pts']
        totals[(row['key'], row['pos'])] += row['pts']
    week_rank = {(week, pos, key): rank for (week, pos), scores in weekly.items()
                 for key, rank in _ranks(scores).items()}
    finish = {}
    for pos in SMASH:
        finish.update({(key, pos): rank for key, rank in _ranks(
            {key: pts for (key, kind), pts in totals.items() if kind == pos}).items()})
    taken, out = defaultdict(int), []
    for item in sorted(picks, key=lambda row: row['overall']):
        pos, key = item['pos'], norm(item.get('key') or item['name'])
        receipt = {'overall': item['overall'], 'round': item['round'], 'team': _team(item['drafted_by'], names),
                   'name': item['name'], 'slug': slugify(item['name']), 'pos': pos,
                   'price': None, 'finish': None, 'value': None, 'points': None,
                   'games': 0, 'smash': 0, 'bust': 0, 'weeks': []}
        if pos in SMASH:
            taken[pos] += 1
            ranks = [week_rank.get((week, pos, key)) for week in range(1, through + 1)]
            receipt['weeks'] = ['out' if rank is None else 'smash' if rank <= SMASH[pos]
                                else 'bust' if rank > BUST[pos] else 'solid' for rank in ranks]
            place = finish.get((key, pos))
            receipt.update(price=taken[pos], finish=place, value=None if place is None else taken[pos] - place,
                           points=round(totals.get((key, pos), 0.0), 1), games=sum(r is not None for r in ranks),
                           smash=receipt['weeks'].count('smash'), bust=receipt['weeks'].count('bust'))
        out.append(receipt)
    return out


def team_values(receipts):
    values = defaultdict(int)
    for receipt in receipts:
        values[receipt['team']] += receipt['value'] or 0
    return dict(values)


def _box_events(key, boxes, through):
    for week in range(1, through + 1):
        for game in boxes['weeks'].get(str(week), []):
            for side, team in (('a', game['home']), ('b', game['away'])):
                for slot in game.get('slots', []):
                    player = slot.get(side)
                    if player and norm(player['name']) == key:
                        kind = 'bench' if slot.get('slot') in BENCH_SLOTS else 'start'
                        yield (week, 1, ''), {'kind': kind, 'team': int(team), 'week': week, 'pts': player.get('pts')}
                for player in (game.get('bench') or {}).get(side) or []:
                    if norm(player['name']) == key:
                        yield (week, 1, ''), {'kind': 'bench', 'team': int(team), 'week': week, 'pts': player.get('pts')}


def player_path(name, boxes, moves, trades, names, through=THROUGH):
    """One player's season as steps: lineup and bench stretches, adds, drops and trades, in order.
    A drop the moves file no longer holds is inferred when a team adds him while another holds him."""
    key, events = norm(name), []
    events += list(_box_events(key, boxes, through))
    events += [((fantasy_week(move['when']), 0, move['when']), {'kind': move['kind'], 'team': _team(move['by'], names),
               'when': move['when']}) for move in moves if norm(move.get('key') or move['name']) == key
               and move['kind'] in ('add', 'drop') and fantasy_week(move['when']) <= through]
    for trade in trades:
        sides = trade['sides']
        for index, side in enumerate(sides):
            if any(norm(player['name']) == key for player in side['players']) and len(sides) == 2:
                week = fantasy_week(trade['when'])
                if week <= through:
                    events.append(((week, 0, trade['when']), {'kind': 'trade', 'team': int(side['team']),
                                   'from': int(sides[1 - index]['team']), 'week': week}))
    steps, holder = [], None
    for _, event in sorted(events, key=lambda pair: pair[0]):
        kind, team = event['kind'], event['team']
        if kind in ('start', 'bench'):
            last = steps[-1] if steps else None
            if last and last['kind'] == kind and last['team'] == team:
                last['weeks'].append(event['week']); last['points'].append(event['pts'])
            else:
                steps.append({'kind': kind, 'team': team, 'weeks': [event['week']], 'points': [event['pts']]})
            holder = team
            continue
        if kind == 'add' and holder is not None:
            steps.append({'kind': 'drop', 'team': holder, 'inferred': True})
        steps.append(event)
        holder = None if kind == 'drop' else team
    return steps


def check_claims(draft):
    """The headlines say these things; a rebuild that makes one false fails instead of lying."""
    above = [team['id'] for team in draft['teams'] if team['value'] > 0]
    if len(above) != 1:
        raise ValueError('Draft Receipts claims one only team beat its draft')
    beats, picks = draft['beats'], {row['overall']: row for row in draft['picks']}
    receipt = lambda beat: picks[beats[beat]['overall']]
    if 'sleeper' in beats and receipt('sleeper')['bust']:
        raise ValueError('Draft Receipts claims the round-8 back had zero busts')
    if 'injury' in beats and ('ACL' not in beats['injury']['injury']['note'] or receipt('injury')['games'] != INJURY_RECEIPT_GAMES):
        raise ValueError('Draft Receipts claims three games and a torn ACL')
    if 'traded' in beats and not any(step['kind'] == 'trade' for step in beats['traded']['path']):
        raise ValueError('Draft Receipts claims the round-2 receiver was traded')
    if 'curse' in beats and any(step['kind'] == 'trade' for step in beats['curse']['path']):
        raise ValueError('Draft Receipts claims the curse needed no trade')
    return draft


def draft_chapter(picks, rows, boxes, moves, trades, status, names, manifest, through=THROUGH):
    receipts = pick_receipts(picks, rows, names, through)
    order = {row['team']: row['overall'] - 1 for row in receipts if row['round'] == 1}
    for row in receipts:
        row['column'] = order[row['team']]
    values = team_values(receipts)
    found = {norm(row['name']): row for row in receipts}
    chosen = {beat: found[norm(manifest[beat])] for beat in BEATS}
    paths = {beat: player_path(chosen[beat]['name'], boxes, moves, trades, names, through) for beat in ('traded', 'curse')}
    injury = status.get(norm(chosen['injury']['name'])) or {}
    beats = {beat: {'overall': chosen[beat]['overall']} for beat in BEATS}
    beats['traded']['path'], beats['curse']['path'] = paths['traded'], paths['curse']
    beats['injury']['injury'] = {'status': injury.get('injury'), 'note': injury.get('injury_note') or ''}
    best = max(values, key=values.get)
    beats['finale'] = {'team': best}
    teams = [{'id': team, 'column': column, 'value': values[team]} for team, column in sorted(order.items(), key=lambda kv: kv[1])]
    return check_claims({'through': through, 'rule': {'smash': SMASH, 'bust': BUST},
                         'teams': teams, 'picks': receipts, 'beats': beats})


def load_points(data, season=SEASON):
    """nflverse weekly rows -> [{key, pos, week, pts}] in half-PPR (ff-jarvis common.data.half_ppr:
    standard points plus half a point a catch), regular season only."""
    import pandas as pd  # noqa: PLC0415  (build-side only; Vercel functions never import this)
    frame = pd.read_parquet(Path(data) / 'cache' / f'spw_{season}.parquet', columns=[
        'player_display_name', 'position', 'week', 'season_type', 'fantasy_points', 'receptions'])
    frame = frame[(frame.season_type == 'REG') & frame.position.isin(list(SMASH))]
    return [{'key': norm(name), 'pos': pos, 'week': int(week), 'pts': float(points) + RECEPTION_POINTS * float(catches or 0)}
            for name, pos, week, _, points, catches in frame.itertuples(index=False)]


def load_draft(data, manifest, names):
    """The chapter's block from ff-jarvis's files, or None when one is missing."""
    data = Path(data)
    paths = [data / name for name in ('yahoo_draft.json', 'yahoo_league_box.json', 'yahoo_transactions.json',
                                      'yahoo_league_trades.json', 'sleeper_status.json')]
    if not all(path.exists() for path in paths) or not (data / 'cache' / f'spw_{SEASON}.parquet').exists():
        return None
    draft, boxes, moves, trades, status = (json.loads(path.read_text(encoding='utf-8')) for path in paths)
    season_trades = (trades.get('seasons', {}).get(str(SEASON)) or {}).get('trades', [])
    return draft_chapter(draft['picks'], load_points(data), boxes, moves['transactions'], season_trades,
                         status['players'], names, manifest)
