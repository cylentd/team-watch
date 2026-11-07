"""Chapter 2, the trade tracker: where Aura's three September trades stand through Week 8 and his
record without them (storyboard docs/madden-film-chapter2.md, approved 2026-11-05)."""
import json
from pathlib import Path

import pytest

from midseason_trades import deal_series, no_trade_results, short_name, story_of, check_actuals

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / 'showcase/madden-curse/edition.json'
AURA = 6


def player(name, pts, proj, pos='WR'):
    return {'name': name, 'pos': pos, 'pts': pts, 'proj': proj, 'nfl': 'AAA'}


def box(week, home, away, a, b, bench_a=(), bench_b=()):
    return {'week': week, 'home': home, 'away': away, 'bench': {'a': list(bench_a), 'b': list(bench_b)},
            'slots': [{'slot': 'WR', 'a': a, 'b': b}]}


# Team 1 got X from team 2 for Y. In Week 2 each side's traded-in starter is swapped for the player
# the team sent away (projected higher than its bench), so the 10-6 game turns into 6-10.
TRADES = [{'when': '2026-09-10T09:00-04:00', 'sides': [
    {'team': 1, 'players': [{'name': 'X', 'pos': 'WR'}]}, {'team': 2, 'players': [{'name': 'Y', 'pos': 'WR'}]}]}]
BOXES = {'weeks': {
    '1': [box(1, 1, 2, player('P', 7, 7), player('Q', 5, 5))],
    '2': [box(2, 1, 2, player('X', 10, 8), player('Y', 6, 9), [player('B', 3, 4)], [player('C', 2, 1)])]}}
GAMES = [{'week': 1, 'home': 1, 'away': 2, 'hp': 7, 'ap': 5}, {'week': 2, 'home': 1, 'away': 2, 'hp': 10, 'ap': 6}]


def test_the_no_trade_lineup_swaps_a_traded_in_starter_for_the_player_the_team_sent_away():
    results = no_trade_results(BOXES, TRADES, {}, weeks=(1, 2))
    assert results == {1: {1: (7, 7), 2: (5, 5)}, 2: {1: (10, 6), 2: (6, 10)}}


def test_a_story_counts_both_records_and_lists_the_games_the_trades_flipped():
    results = no_trade_results(BOXES, TRADES, {}, weeks=(1, 2))
    story = story_of(results, GAMES, 1)
    assert story['record'] == {'actual': '2-0', 'noTrades': '1-1'}
    assert story['flips'] == [{'week': 2, 'opponent': 2, 'actual': [10, 6], 'noTrades': [6, 10]}]


def test_a_recomputed_score_that_disagrees_with_yahoo_fails_loudly():
    results = no_trade_results(BOXES, TRADES, {}, weeks=(1, 2))
    games = [GAMES[0], dict(GAMES[1], hp=10.2)]
    with pytest.raises(ValueError, match='Week 2'):
        check_actuals(results, games)


def test_a_week_with_no_box_scores_fails_loudly():
    with pytest.raises(ValueError, match='Week 3'):
        no_trade_results(BOXES, TRADES, {}, weeks=(1, 2, 3))


def test_names_are_first_initial_and_surname_and_a_defense_is_the_team_d_st():
    assert short_name({'name': "Ja'Marr Chase", 'pos': 'WR'}) == 'J. Chase'
    assert short_name({'name': 'Deebo Samuel Sr.', 'pos': 'WR'}) == 'D. Samuel'
    assert short_name({'name': 'A.J. Brown', 'pos': 'WR'}) == 'A.J. Brown'
    assert short_name({'name': 'Rams', 'pos': 'DEF'}) == 'Rams D/ST'


def fake_verdicts(margin_by_cut):  # shape: allow injected verdict boundary reproduces the existing trade formula contract
    """Stands in for ff-jarvis verdicts(): the cutoff rides in as the 'points' the series hands over."""
    def verdicts(trades, seasons_games, points_for, current):
        cut = points_for(2026)
        sides = [{'team': 3, 'tree': 10.0 + margin_by_cut[cut], 'players': [{'name': 'Ja\'Marr Chase', 'pos': 'WR', 'par_reg': 5.0}]},
                 {'team': 6, 'tree': 10.0, 'players': [{'name': 'Stefon Diggs', 'pos': 'WR', 'par_reg': 2.0},
                                                       {'name': 'Parker Washington', 'pos': 'WR', 'par_reg': 0.0}]}]
        return [{'when': trades['seasons']['2026']['trades'][0]['when'], 'sides': sides, 'margin': abs(margin_by_cut[cut])}]
    return verdicts


def test_a_deal_series_signs_each_week_by_the_partner_and_names_the_leader():
    trades = {'seasons': {'2026': {'trades': [{'when': '2026-09-15T09:26-04:00', 'sides': []}]}}}
    games = [{'week': week} for week in (1, 2, 3)]
    verdicts = fake_verdicts({2: 3.8, 3: -0.6})
    deals = deal_series(trades, games, lambda cut: cut, verdicts, AURA, through=3)
    assert deals == [{'when': '2026-09-15', 'partner': 3, 'sent': ['J. Chase'], 'got': ['S. Diggs', 'P. Washington'],
                      'leader': 6, 'lead': 0.6,
                      'weekly': [{'week': 2, 'leader': 3, 'lead': 3.8}, {'week': 3, 'leader': 6, 'lead': -0.6}]}]


@pytest.fixture(scope='module')
def block():
    return json.loads(EDITION.read_text(encoding='utf-8'))['trades']


def test_the_export_leads_each_deal_at_week_8(block):
    assert (block['through'], block['team']) == (8, AURA)
    deals = [(deal['when'], deal['partner'], deal['leader'], deal['lead']) for deal in block['deals']]
    assert deals == [('2026-09-15', 3, 3, 17.9), ('2026-09-16', 12, 12, 63.7), ('2026-09-18', 5, 5, 4.5)]


def test_the_export_names_what_each_deal_moved(block):
    chase = block['deals'][0]
    assert (chase['sent'], chase['got']) == (['J. Chase'], ['S. Diggs', 'P. Washington'])
    assert 'Rams D/ST' in block['deals'][2]['got']


def test_the_chase_deal_changes_hands_twice_before_it_ends_at_17_9(block):
    weekly = [(row['week'], row['leader'], row['lead']) for row in block['deals'][0]['weekly']]
    assert weekly == [(2, 3, 3.8), (3, 3, 13.5), (4, 3, 11.8), (5, 3, 1.9), (6, 6, -4.6), (7, 6, -0.6), (8, 3, 17.9)]


def test_the_export_says_aura_is_3_5_and_would_be_5_3_with_no_trades(block):
    assert block['record'] == {'actual': '3-5', 'noTrades': '5-3'}


def test_the_export_lists_the_two_games_the_trades_lost_him(block):
    assert block['flips'] == [
        {'week': 2, 'opponent': 10, 'actual': [112.06, 114.24], 'noTrades': [131.66, 114.24]},
        {'week': 7, 'opponent': 8, 'actual': [84.64, 94.32], 'noTrades': [104.78, 94.32]}]
