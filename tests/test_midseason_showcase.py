import pytest

from midseason_showcase import keep_written, showcase_edition, starter_totals


@pytest.fixture
def sources():
    teams = range(1, 13)
    season = {'league_id': '75203', 'league': 'The Madden Curse', 'season': 2026, 'week': 9,
              'teams': {str(team): {'name': f'Team {team}'} for team in teams},
              'games': [{'week': week, 'home': team, 'away': team + 1, 'hp': 100, 'ap': 90,
                         'winner': 'home', 'tier': None} for week in range(1, 9) for team in range(1, 13, 2)]}
    boxes = {'season': 2026, 'weeks': {str(week): [
        {'home': team, 'away': team + 1, 'slots': [
            {'slot': 'QB', 'a': {'name': f'Player {team}', 'pts': 10},
             'b': {'name': f'Player {team + 1}', 'pts': 20}}]}
        for team in range(1, 13, 2)] for week in range(1, 9)}}
    manifest = {'teams': [{'id': team, 'player': f'Player {team}', 'motif': 'stamp'} for team in teams]}
    copy = {f'midseason.team.{team}.{key}': f'{key} {team}' for team in teams for key in ('headline', 'report')}
    copy.update({f'midseason.report.{key}': key for key in ('title', 'intro', 'source')})
    return season, boxes, copy, manifest


def test_export_carries_all_twelve_verified_player_stories(sources):
    edition = showcase_edition(*sources)
    assert (edition['through'], len(edition['teams'])) == (8, 12)
    assert edition['teams'][0]['featured'] == {'name': 'Player 1', 'points': 80, 'starts': 8}
    assert edition['teams'][-1]['headline'] == 'headline 12'


def test_a_partial_week_must_not_be_published(sources):
    sources[1]['weeks']['8'].pop()
    with pytest.raises(ValueError, match='complete'):
        showcase_edition(*sources)


def test_bench_points_never_become_starter_production(sources):
    sources[1]['weeks']['1'][0]['slots'].append(
        {'slot': 'BN', 'a': {'name': 'Player 1', 'pts': 999}, 'b': None})
    assert starter_totals(sources[1])[1]['Player 1']['points'] == 80


def test_a_written_block_survives_moves_rolling_out_of_the_source():
    # 2026-11-06: yahoo_transactions.json had dropped the curse card's Oct 28-30 moves, the rebuilt draft
    # block lost its last stop, and the approved film crashed before Play enabled.
    written = {'draft': {'steps': ['wire', 'cooked']}}
    assert keep_written(written, 'draft', {'steps': ['wire']}) == {'steps': ['wire', 'cooked']}
    assert keep_written(written, 'trades', {'record': '3-5'}) == {'record': '3-5'}
    assert keep_written({}, 'draft', None) is None


def test_unverified_player_is_rejected(sources):
    sources[3]['teams'][0]['player'] = 'Never started'
    with pytest.raises(ValueError, match='verified starts'):
        showcase_edition(*sources)
