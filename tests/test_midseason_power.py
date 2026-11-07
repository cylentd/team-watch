"""Chapter 5, Midseason power rankings: every team's weekly score against the other eleven (all-play),
ranked beside the real standings (storyboard docs/madden-film-chapter5.md)."""
import json
from pathlib import Path

import pytest

from league_back import add_standings
from midseason_power import load_power, power_block

DATA = Path.home() / '.ff-jarvis-history' / 'data'
LEAGUE = {'league_id': '75203', 'season': 2026}
FOUR = 4          # synthetic league size


def season(games, league_id='75203', size=FOUR):
    teams = {str(i): {'name': f'T{i}'} for i in range(1, size + 1)}
    return {'league_id': league_id, 'season': 2026, 'teams': teams, 'games': games}


def game(week, home, away, hp, ap, winner=None):
    winner = winner or ('home' if hp > ap else 'away' if ap > hp else 'tie')
    return {'week': week, 'home': home, 'away': away, 'hp': hp, 'ap': ap, 'winner': winner}


def week_one(scores):
    """Four teams, scores by id: 1v2 and 3v4."""
    a, b, c, d = scores
    return [game(1, 1, 2, a, b), game(1, 3, 4, c, d)]


def block(games, through=1):
    return power_block(season(games), through=through, teams=FOUR)


def by_id(result):
    return {team['id']: team for team in result['teams']}


def test_a_tie_counts_as_a_tie_for_both_teams_and_half_a_win_in_luck():
    teams = by_id(block(week_one((10, 10, 5, 20))))
    assert teams[1]['allPlay'] == {'w': 1, 'l': 1, 't': 1}
    assert teams[2]['allPlay'] == {'w': 1, 'l': 1, 't': 1}
    assert teams[1]['record'] == {'w': 0, 'l': 0, 't': 1}
    assert teams[1]['luck'] == 0.0          # real 0.5 wins, earned 1.5 / 3 = 0.5


def test_luck_is_real_wins_minus_the_share_the_points_earned_rounded_to_a_tenth():
    teams = by_id(block(week_one((30, 10, 20, 5))))
    assert teams[1]['luck'] == 0.0 and teams[3]['luck'] == pytest.approx(0.3)
    assert teams[2]['luck'] == pytest.approx(-0.3) and teams[4]['luck'] == 0.0
    assert str(teams[1]['luck']) == '0.0'


def test_power_orders_by_all_play_then_points_and_says_so():
    result = block(week_one((10, 10, 5, 5)))
    assert result['order'] == 'all-play wins, then points scored' and result['tieBreak'] == 'points'
    assert [team['id'] for team in result['teams']][:2] == [1, 2]
    assert result['comparisons'] == 3 and result['through'] == 1 and result['league'] == 75203


def test_standing_place_is_wins_with_ties_half_then_points():
    result = block(week_one((10, 30, 20, 5)))
    assert {team['id']: team['standing'] for team in result['teams']} == {2: 1, 3: 2, 1: 3, 4: 4}
    assert {team['id']: team['power'] for team in result['teams']} == {2: 1, 3: 2, 1: 3, 4: 4}


def test_a_week_with_no_games_is_refused():
    with pytest.raises(ValueError, match='Week 2'):
        block(week_one((1, 2, 3, 4)), through=2)


def test_a_team_twice_in_one_week_is_refused():
    with pytest.raises(ValueError, match='twice'):
        block([game(1, 1, 2, 1, 2), game(1, 1, 3, 3, 4)])


def test_a_week_with_too_few_teams_is_refused():
    with pytest.raises(ValueError, match='4 teams'):
        block([game(1, 1, 2, 1, 2)])


def test_a_non_numeric_score_is_refused():
    with pytest.raises(ValueError, match='score'):
        block([game(1, 1, 2, '10', 2, 'home'), game(1, 3, 4, 3, 4)])


def test_another_league_is_refused():
    with pytest.raises(ValueError, match='75203'):
        power_block(season(week_one((1, 2, 3, 4)), league_id='1'), through=1, teams=FOUR)


def real():
    path = DATA / 'yahoo_league.json'
    return json.loads(path.read_text(encoding='utf-8'))


def test_the_real_edition_has_88_comparisons_and_the_oracle_leaders():
    result = load_power(DATA)
    teams = result['teams']
    assert result['comparisons'] == 88 and len(teams) == 12
    assert all(sum(team['allPlay'].values()) == 88 and sum(team['record'].values()) == 8 for team in teams)
    assert [(team['id'], team['allPlay']['w'], team['allPlay']['l']) for team in teams[:4]] == [
        (10, 56, 32), (11, 55, 33), (12, 55, 33), (3, 55, 33)]
    by = by_id(result)
    assert (by[12]['standing'], by[12]['power']) == (6, 3)
    assert by[2]['power'] == 8 and (by[2]['allPlay']['w'], by[2]['allPlay']['l']) == (41, 47)
    assert teams[-1]['id'] == 4 and (teams[-1]['allPlay']['w'], teams[-1]['allPlay']['l']) == (24, 64)


def test_the_real_games_sum_is_the_points_oracle_and_games_used_are_48():
    doc = real()
    used = [g for g in doc['games'] if g['week'] <= 8]
    assert len(used) == 48
    sums = {team['id']: team['points'] for team in power_block(doc)['teams']}
    expected = {}
    for g in used:
        expected[g['home']] = round(expected.get(g['home'], 0) + g['hp'], 2)
        expected[g['away']] = round(expected.get(g['away'], 0) + g['ap'], 2)
    assert sums == {int(k): v for k, v in expected.items()}


def test_real_luck_matches_the_league_recap_method():
    doc = real()
    weeks = [{'games': [{'a': g['home'], 'b': g['away'], 'ap': g['hp'], 'bp': g['ap'], 'win': g['winner']}
                        for g in doc['games'] if g['week'] == w]} for w in range(1, 9)]
    ids = [int(i) for i in doc['teams']]
    table = add_standings(weeks, ids)[-1]['table']
    oracle = {row['id']: row['luck'] for row in table}
    assert {team['id']: team['luck'] for team in power_block(doc)['teams']} == oracle
