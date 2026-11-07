import pytest
from test_madden_chapter2 import node

DATA = "const {checkLineups, lineupValues} = await import(base + '/lineups-data.mjs'); const raw = JSON.parse((await import('node:fs')).readFileSync(new URL('lineups-receipts.json', base + '/'), 'utf8')); "


def test_two_negative_starts_carry_their_actual_results():
    result = node(DATA + "return lineupValues(checkLineups(raw)).defense;")
    assert [(row['name'], row['week'], row['score']) for row in result] == [('Saints', 'W4', '−3'), ('Raiders', 'W5', '−1')]
    assert [(row['won'], row['margin']) for row in result] == [(True, '2.50'), (True, '63.30')]


def test_win_labels_change_when_the_historical_result_changes():
    result = node(DATA + "raw.defense[3].points = 70; const values = lineupValues(checkLineups(raw)); return {first: values.defense[0], outcome: values.outcome};")
    assert result['first']['won'] is False and result['first']['margin'] == '10.28'
    assert result['outcome'] == 'Won 1 negative week.'


@pytest.mark.parametrize('reduced', [False, True])
def test_win_stamps_cannot_appear_early_and_reverse_seeking_is_deterministic(reduced):
    result = node(DATA + f"const {{lineupsPose}} = await import(base + '/lineups-pose.mjs'); const cast = lineupValues(checkLineups(raw)); const at = s => lineupsPose(s, {str(reduced).lower()}, cast); const before = at(1); at(7); return {{before, again: at(1), wins: [1.99,2.2,5.99,6.2].map(s=>at(s).shieldStamps.map(mark=>mark.win.visible))}};")
    assert result['before'] == result['again']
    assert result['wins'] == [[False, False], [True, False], [True, False], [True, True]]
