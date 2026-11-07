"""Export the frozen Week 8 show and the same editorial copy used by Recap."""
import json
import math
import re

from midseason import EDITION_SEASON, EDITION_WEEK, midseason_special
from midseason_draft import load_draft
from midseason_pickups import load_pickups
from midseason_trades import load_trades

BENCH_SLOTS = frozenset(('BN', 'Bench', 'IR', 'IR+'))
TEAM_COUNT = 12


def starter_totals(boxes, through=EDITION_WEEK):
    totals = {}
    for week, games in boxes.get('weeks', {}).items():
        if not 1 <= int(week) <= through:
            continue
        for game in games:
            for side, team_id in (('a', game['home']), ('b', game['away'])):
                players = totals.setdefault(int(team_id), {})
                for slot in game.get('slots', []):
                    player = slot.get(side)
                    if slot.get('slot') in BENCH_SLOTS or not player:
                        continue
                    points = player.get('pts')
                    if isinstance(points, bool) or not isinstance(points, (int, float)) or not math.isfinite(points):
                        continue
                    entry = players.setdefault(player['name'], {'name': player['name'], 'points': 0, 'starts': 0})
                    entry['points'] += points
                    entry['starts'] += 1
    for players in totals.values():
        for player in players.values():
            player['points'] = round(player['points'], 2)
    return totals


def _name(name):
    return re.sub(r'[^a-z0-9]', '', name.lower())


def showcase_edition(season, boxes, copy, manifest):
    edition = midseason_special(season)
    if not edition or not edition['final']:
        return None
    if boxes.get('season') != EDITION_SEASON:
        raise ValueError('The show requires matching 2026 player box scores')
    expected = set(range(1, TEAM_COUNT + 1))
    for week in range(1, EDITION_WEEK + 1):
        games = boxes.get('weeks', {}).get(str(week), [])
        appearances = [int(game[side]) for game in games for side in ('home', 'away')]
        if len(appearances) != TEAM_COUNT or set(appearances) != expected:
            raise ValueError('The show requires complete Weeks 1–8 player box scores')
    stats = starter_totals(boxes)
    if set(stats) != set(range(1, TEAM_COUNT + 1)):
        raise ValueError('The show requires all twelve teams in the player boxes')
    teams = []
    for item in manifest['teams']:
        team_id = item['id']
        if any(str(week) not in boxes['weeks'] for week in range(1, EDITION_WEEK + 1)):
            raise ValueError('The show requires Weeks 1–8 player box scores')
        players = list(stats[team_id].values())
        featured = next((player for player in players if _name(player['name']) == _name(item['player'])), None)
        if not featured:
            raise ValueError(f'Team {team_id} has no verified starts for its featured player')
        teams.append({'id': team_id, 'name': season['teams'][str(team_id)]['name'],
                      'avatar': f'../../avatars/yahoo/{team_id}.webp', 'motif': item['motif'],
                      'headline': copy[f'midseason.team.{team_id}.headline'],
                      'article': copy[f'midseason.team.{team_id}.report'],
                      'featured': featured, 'mvp': max(players, key=lambda player: player['points'])})
    if len(teams) != TEAM_COUNT or len({team['id'] for team in teams}) != TEAM_COUNT:
        raise ValueError('Each of the twelve teams needs exactly one show appearance')
    return {'season': EDITION_SEASON, 'through': EDITION_WEEK, 'generated': season.get('generated'),
            'title': copy['midseason.report.title'], 'intro': copy['midseason.report.intro'],
            'source': copy['midseason.report.source'], 'teams': teams}


def keep_written(written, key, fresh):
    """The edition is frozen once a block is written: moves roll out of ff-jarvis's files, and a rebuild
    from what is left rewrote the approved film's curse tour without its last stop (2026-11-06)."""
    return written.get(key) or fresh


def write_showcase(repo, data):
    season_path, boxes_path = data / 'yahoo_league.json', data / 'yahoo_league_box.json'
    if not season_path.exists() or not boxes_path.exists():
        return 'Madden show: player data unavailable'
    load = lambda path: json.loads(path.read_text(encoding='utf-8'))
    season = load(season_path)
    special = midseason_special(season)
    if not special or not special['final']:
        return 'Madden show: waiting for completed Week 8'
    manifest = load(repo / 'design/midseason_editorial.json')
    edition = showcase_edition(season, load(boxes_path), load(repo / 'design/src/content.json'), manifest)
    if edition is None:
        return 'Madden show: waiting for completed Week 8'
    target = repo / 'showcase/madden-curse/edition.json'
    written = load(target) if target.exists() else {}
    names = {team['name']: int(team_id) for team_id, team in season['teams'].items()}
    notes = []
    for key, label, build in (('draft', 'Draft Receipts', lambda: load_draft(data, manifest['draft'], names)),
                              ('trades', 'Trade tracker', lambda: load_trades(data)),
                              ('pickups', 'Best pickups', lambda: load_pickups(data))):
        block = keep_written(written, key, None) or build()
        notes.append(f"{label} {'kept' if written.get(key) else 'exported' if block else 'missing'}")
        if block:
            edition[key] = block
    target.write_text(json.dumps(edition, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    return f"Madden show: twelve verified Week 8 stories exported; {'; '.join(notes)}"
