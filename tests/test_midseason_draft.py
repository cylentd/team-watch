"""Chapter 1, Draft Receipts: every number the film shows comes from the draft, the weekly
half-PPR points and the league's moves, by Rule A (David, 2026-11-03)."""
import json
from pathlib import Path

import pytest

from midseason_draft import check_claims, pick_receipts, player_path, team_values

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / 'showcase/madden-curse/edition.json'
NAMES = {'Alpha': 1, 'Beta': 2}


def pick(overall, name, pos, team, rnd=1):
    return {'overall': overall, 'round': rnd, 'pick': overall, 'name': name, 'key': name.lower(),
            'pos': pos, 'drafted_by': team}


def week_rows(week, pos, players):
    """players: [(key, points)], best first."""
    return [{'key': key, 'pos': pos, 'week': week, 'pts': pts} for key, pts in players]


def wr_field(week, star_points):
    """'star' plus 40 filler receivers; the star's points decide his weekly rank."""
    filler = [(f'filler {n}', 40 - n * .5) for n in range(40)]
    return week_rows(week, 'WR', sorted(filler + [('star', star_points)], key=lambda row: -row[1]))


def test_price_is_the_order_a_position_was_drafted_and_value_is_price_minus_finish():
    picks = [pick(1, 'First', 'WR', 'Alpha'), pick(2, 'Star', 'WR', 'Beta')]
    rows = week_rows(1, 'WR', [('star', 30), ('first', 2)])
    receipts = {r['name']: r for r in pick_receipts(picks, rows, NAMES)}
    assert (receipts['Star']['price'], receipts['Star']['finish'], receipts['Star']['value']) == (2, 1, 1)
    assert (receipts['First']['price'], receipts['First']['finish'], receipts['First']['value']) == (1, 2, -1)


def test_a_week_is_smash_inside_the_top_twelve_and_bust_outside_thirty_six():
    rows = wr_field(1, 39.9) + wr_field(2, 30) + wr_field(3, -1)
    receipt = pick_receipts([pick(1, 'Star', 'WR', 'Alpha')], rows, NAMES, through=3)[0]
    assert receipt['weeks'] == ['smash', 'solid', 'bust']
    assert (receipt['smash'], receipt['bust'], receipt['games']) == (1, 1, 3)


def test_missed_weeks_score_zero_and_kickers_carry_no_value():
    picks = [pick(1, 'Star', 'WR', 'Alpha'), pick(2, 'Leg', 'K', 'Beta')]
    rows = week_rows(1, 'WR', [('star', 9)]) + week_rows(2, 'WR', [('other', 1)])
    star, leg = pick_receipts(picks, rows, NAMES, through=2)
    assert star['weeks'] == ['smash', 'out'] and star['games'] == 1
    assert leg['value'] is None and leg['weeks'] == []


def test_a_tie_shares_the_better_place_even_when_float_sums_split_it():
    picks = [pick(1, 'Tie', 'TE', 'Alpha')]
    rows = week_rows(1, 'TE', [('other', 36.00000000000001)]) + week_rows(2, 'TE', [('tie', 36.0)])
    assert pick_receipts(picks, rows, NAMES, through=2)[0]['finish'] == 1


def test_team_value_sums_its_picks_and_unscored_picks_count_zero():
    receipts = [{'team': 1, 'value': 5}, {'team': 1, 'value': None}, {'team': 2, 'value': -3}]
    assert team_values(receipts) == {1: 5, 2: -3}


def test_an_unknown_drafting_team_fails_the_build():
    with pytest.raises(ValueError, match='Nobody'):
        pick_receipts([pick(1, 'Star', 'WR', 'Nobody')], [], NAMES)


BOXES = {'weeks': {
    '1': [{'home': 1, 'away': 2, 'slots': [{'slot': 'WR', 'a': {'name': 'Star', 'pts': 6.3}, 'b': None}], 'bench': {}}],
    '2': [{'home': 1, 'away': 2, 'slots': [], 'bench': {'a': [{'name': 'Star', 'pts': 4.0}]}}],
    '3': [{'home': 1, 'away': 2, 'slots': [], 'bench': {}}],
    '4': [{'home': 1, 'away': 2, 'slots': [{'slot': 'WR', 'a': None, 'b': {'name': 'Star', 'pts': 0.0}}], 'bench': {}}],
}}
MOVES = [{'kind': 'add', 'key': 'star', 'by': 'Alpha', 'when': '2026-09-29T09:02-07:00'},
         {'kind': 'drop', 'key': 'star', 'by': 'Alpha', 'when': '2026-09-29T17:52-07:00'},
         {'kind': 'add', 'key': 'star', 'by': 'Beta', 'when': '2026-09-30T12:56-07:00'}]


def test_a_player_path_reads_lineups_benches_and_moves_in_order():
    steps = player_path('Star', BOXES, MOVES, [], NAMES, through=4)
    assert [step['kind'] for step in steps] == ['start', 'bench', 'drop', 'add', 'drop', 'add', 'start']
    assert steps[0] == {'kind': 'start', 'team': 1, 'weeks': [1], 'points': [6.3]}
    assert steps[2] == {'kind': 'drop', 'team': 1, 'inferred': True}
    assert steps[3]['when'] == '2026-09-29T09:02-07:00' and steps[-1]['team'] == 2


def test_a_trade_moves_the_player_to_the_side_that_received_him():
    trades = [{'when': '2026-09-18T14:39-04:00', 'sides': [
        {'team': 1, 'players': [{'name': 'Other'}]}, {'team': 2, 'players': [{'name': 'Star'}]}]}]
    steps = player_path('Star', BOXES, [], trades, NAMES, through=2)
    assert steps[1] == {'kind': 'trade', 'team': 2, 'from': 1, 'week': 2}


@pytest.fixture(scope='module')
def draft():
    return json.loads(EDITION.read_text(encoding='utf-8'))['draft']


def featured(draft, beat):
    overall = draft['beats'][beat]['overall']
    return next(row for row in draft['picks'] if row['overall'] == overall)


@pytest.fixture
def export_carries_the_main_threads_verified_week_8_numbers(draft):
    golden = featured(draft, 'steal')
    brown = featured(draft, 'traded')
    hubbard = featured(draft, 'sleeper')
    achane = featured(draft, 'injury')
    return golden, brown, hubbard, achane


def test_the_export_carries_the_main_threads_verified_week_8_numbers_1(export_carries_the_main_threads_verified_week_8_numbers):
    golden, brown, hubbard, achane = export_carries_the_main_threads_verified_week_8_numbers
    assert (golden['overall'], golden['team'], golden['price'], golden['finish']) == (96, 5, 40, 7)
    assert (golden['points'], golden['games'], golden['smash'], golden['bust']) == (110.0, 8, 4, 0)
    assert (brown['overall'], brown['price'], brown['finish'], brown['games']) == (24, 10, 111, 3)
    assert (hubbard['overall'], hubbard['team'], hubbard['price'], hubbard['finish']) == (86, 4, 33, 12)


def test_the_export_carries_the_main_threads_verified_week_8_numbers_2(export_carries_the_main_threads_verified_week_8_numbers, draft):
    golden, brown, hubbard, achane = export_carries_the_main_threads_verified_week_8_numbers
    assert (hubbard['smash'], hubbard['bust']) == (6, 0)
    assert (achane['overall'], achane['team'], achane['price'], achane['finish'], achane['games']) == (13, 9, 8, 63, 3)
    assert draft['beats']['injury']['injury'] == {'status': 'IR', 'note': 'Knee - ACL'}


def test_the_export_ranks_every_teams_draft_and_only_romo_beat_his(draft):
    values = {team['id']: team['value'] for team in draft['teams']}
    # Honey -108 and Gibbs -138, one better than first reported: float sums had split two true ties
    # (Ferguson and Tremble at 36.0 TE points among them); tied players now share the better place.
    assert values == {1: 41, 10: -14, 12: -19, 11: -76, 6: -81, 9: -93, 3: -104,
                      7: -108, 8: -123, 5: -138, 4: -201, 2: -243}
    assert draft['beats']['finale']['team'] == 1


def test_the_export_follows_brown_to_aura_and_godwin_through_three_teams(draft):
    brown = draft['beats']['traded']['path']
    assert {'kind': 'trade', 'team': 6, 'from': 5, 'week': 2} in brown
    assert [step['points'] for step in brown if step['kind'] == 'start' and step['team'] == 6] == [[4.2, 6.3]]
    godwin = draft['beats']['curse']['path']
    assert [(step['kind'], step['team']) for step in godwin] == [
        ('start', 3), ('bench', 3), ('drop', 3), ('add', 3), ('drop', 3), ('add', 2), ('start', 2)]
    assert godwin[0]['points'] == [6.3, 7.3] and godwin[-1] == {'kind': 'start', 'team': 2, 'weeks': [8], 'points': [0.0]}


def test_the_finale_claim_needs_exactly_one_team_above_zero():
    with pytest.raises(ValueError, match='only team'):
        check_claims({'teams': [{'id': 1, 'value': 3}, {'id': 2, 'value': 4}], 'beats': {}, 'picks': []})
