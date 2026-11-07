"""Chapter 3, Best pickups: the three players a team started who came off the wire, and the points each
added over the lineup the owner would otherwise have run (storyboard docs/madden-film-chapter3.md,
method approved by David 2026-11-05)."""
import json
from pathlib import Path

import pytest

from midseason_pickups import check_league, claim_of, pickups_block, weekly_rank

ROOT = Path(__file__).resolve().parents[1]
EDITION = ROOT / 'showcase/madden-curse/edition.json'
SEASON = {'teams': {'1': {'name': 'Ones'}, '2': {'name': 'Twos'}}}


def player(name, pos, pts, proj=0.0):
    return {'name': name, 'pos': pos, 'pts': pts, 'proj': proj, 'nfl': 'AAA'}


def box(week, slots, bench_a=()):  # shape: allow synthetic box-score builder keeps input schema separate from the oracle
    return {'week': week, 'home': 1, 'away': 2, 'bench': {'a': list(bench_a), 'b': []},
            'slots': [{'slot': slot, 'a': a, 'b': b} for slot, a, b in slots]}


def one_week(week, rival, bench=(player('Ben Bench', 'WR', 5, 4),)):  # shape: allow synthetic season builder documents acquisition/start provenance
    """Team 1: pickup 10 + kicker 4 + a flex 6 = 20. Team 2 scores `rival` + 3 from its kicker."""
    flex = player('Sam Short', 'WR', 6) if week < 3 else player('Dee Drafted', 'WR', 6)
    slots = [('WR', player('Pat Pickup', 'WR', 10), player('Quin Rival', 'WR', rival)),
             ('K', player('Kay Kicker', 'K', 4), player('Kit Kicker', 'K', 3)),
             ('W/R/T', flex, None)]
    return box(week, slots, bench)


def boxes(rivals=(9, 14, 9), bench=(player('Ben Bench', 'WR', 5, 4),)):
    return {'weeks': {str(w): [one_week(w, rivals[w - 1], bench)] for w in (1, 2, 3)}}


GAMES = [{'week': w, 'home': 1, 'away': 2, 'hp': 20, 'ap': rival + 3} for w, rival in ((1, 9), (2, 14), (3, 9))]
SEASON_ROWS = dict(SEASON, games=GAMES)
DRAFT = [{'name': name, 'pos': 'WR', 'drafted_by': team} for name, team in
         (('Ben Bench', 'Ones'), ('Dee Drafted', 'Ones'), ('Quin Rival', 'Twos'))] + \
        [{'name': 'Kit Kicker', 'pos': 'K', 'drafted_by': 'Twos'}]
POINTS = [{'key': key, 'pos': 'WR', 'week': w, 'pts': pts}
          for w in (1, 2, 3) for key, pts in (('pat pickup', 10.0), ('top dog', 12.0), ('low man', 8.0))]
MOVES = [{'league': 'yahoo', 'kind': 'add', 'via': 'waiver', 'key': 'pat pickup', 'by': 'Ones',
          'when': '2026-09-23T01:14-07:00'}]


def block(**over):
    args = dict(season=SEASON_ROWS, boxes=boxes(), draft_picks=DRAFT, trades=[], point_rows=POINTS,
                moves=MOVES, through=3)
    return pickups_block(**dict(args, **over))


def test_a_pickup_is_scored_against_the_bench_player_the_owner_would_have_started():
    top = block()['top']
    assert [(row['name'], row['pos'], row['starts'], row['added']) for row in top] == [('Pat Pickup', 'WR', 3, 15.0)]
    assert [week['standIn'] for week in top[0]['weeks']] == ['Ben Bench'] * 3


def test_a_win_he_swung_counts_and_a_kicker_or_a_two_start_player_is_left_out():
    top = block()['top']
    assert [row['name'] for row in top] == ['Pat Pickup']       # Kay (K) and Sam (2 starts) are out
    assert (top[0]['rank'], top[0]['wins'], top[0]['team'], top[0]['teamName']) == (1, 1, 1, 'Ones')
    assert [week['swing'] for week in top[0]['weeks']] == [0, 1, 0]


def test_each_week_carries_his_points_and_his_place_among_the_position():
    weeks = block()['top'][0]['weeks']
    assert [(week['week'], week['pts'], week['rank']) for week in weeks] == [(1, 10.0, 2), (2, 10.0, 2), (3, 10.0, 2)]


def test_with_no_usable_bench_player_the_stand_in_is_the_best_free_agent_by_earlier_average():
    top = block(boxes=boxes(bench=()), names={'top dog': 'Top Dog'})['top'][0]
    # week 1 has no earlier weeks, so nobody qualifies and the slot scores 0; weeks 2 and 3 take the
    # unrostered WR with the best earlier average (12.0), who scores 12 against Pat's 10
    assert [week['standIn'] for week in top['weeks']] == ['none', 'Top Dog', 'Top Dog']
    assert top['added'] == 10 - 2 - 2


def test_a_recomputed_score_that_disagrees_with_yahoo_fails_loudly():
    games = [GAMES[0], dict(GAMES[1], hp=20.2), GAMES[2]]
    with pytest.raises(ValueError, match='Week 2'):
        block(season=dict(SEASON, games=games))


def test_a_week_with_no_box_scores_fails_loudly():
    with pytest.raises(ValueError, match='Week 4'):
        block(through=4)


def test_the_wrong_league_fails_loudly():
    with pytest.raises(ValueError, match='75203'):
        check_league({'league_id': '1'})
    check_league({'league_id': '75203'})


def test_a_player_the_team_received_in_a_trade_is_not_a_pickup():
    trade = {'when': '2026-09-10T09:00-04:00', 'sides': [
        {'team': 1, 'players': [{'name': 'Pat Pickup', 'pos': 'WR'}]}, {'team': 2, 'players': []}]}
    assert block(trades=[trade])['top'] == []


def test_a_qb_rank_adds_back_one_point_per_interception():
    rows = [{'key': 'ann a', 'pos': 'QB', 'week': 3, 'pts': 20.0}, {'key': 'bo b', 'pos': 'QB', 'week': 3, 'pts': 19.0}]
    assert weekly_rank(rows, {('bo b', 3): 3}, 'bo b', 'QB', 3) == (22.0, 1)
    assert weekly_rank(rows, {}, 'bo b', 'QB', 3) == (19.0, 2)


def test_a_claim_is_the_teams_latest_add_of_him_with_its_way_and_day():
    moves = MOVES + [dict(MOVES[0], by='Twos', when='2026-09-30T01:00-07:00'), dict(MOVES[0], kind='drop')]
    assert claim_of(moves, 'pat pickup', {'Ones'}) == ('waiver', '2026-09-23')
    with pytest.raises(ValueError, match='pat pickup'):
        claim_of([], 'pat pickup', {'Ones'})


@pytest.fixture(scope='module')
def export():
    return json.loads(EDITION.read_text(encoding='utf-8'))['pickups']


def test_the_export_names_the_three_best_pickups_by_points_added(export):
    assert [row['teamName'].split()[0] for row in export['top']] == ['Sausage', 'OBJ', 'Am']
    rows = [(row['name'], row['pos'], row['team'], row['via'], row['when'], row['starts'], row['added'])
            for row in export['top']]
    assert export['through'] == 8
    assert rows == [('Jordan Love', 'QB', 12, 'waiver', '2026-09-23', 6, 40.5),
                    ('Emanuel Wilson', 'RB', 6, 'fa', '2026-09-25', 6, 25.7),
                    ('Dalton Schultz', 'TE', 2, 'fa', '2026-09-18', 3, 20.4)]


def test_love_started_six_weeks_and_ranked_between_qb6_and_qb17(export):
    weeks = [(week['week'], week['pts'], week['rank']) for week in export['top'][0]['weeks']]
    assert weeks == [(3, 19.5, 16), (4, 14.1, 17), (5, 25.3, 8), (6, 21.2, 6), (7, 18.0, 13), (8, 22.5, 6)]


def test_the_export_records_the_wins_each_pickup_swung(export):
    assert [row['wins'] for row in export['top']] == [-1, 1, 0]
    assert export['top'][0]['weeks'][1]['swing'] == -1 and export['top'][1]['weeks'][2]['swing'] == 1


def test_each_pickup_has_a_headshot_slug_that_exists(export):
    slugs = [row['slug'] for row in export['top']]
    assert slugs == ['jordan-love', 'emanuel-wilson', 'dalton-schultz']
    assert all((ROOT / 'heads/lg' / f'{slug}.webp').exists() for slug in slugs)
