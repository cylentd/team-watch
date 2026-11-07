"""Chapter 5 receipts contract: the checked power rankings and the numbers the view derives from them."""
import pytest

from test_madden_chapter2 import node

DATA = "const {checkPower, powerValues} = await import(base + '/power-data.mjs'); const raw = JSON.parse((await import('node:fs')).readFileSync(new URL('power-receipts.json', base + '/'), 'utf8')); "
TRY = "; try {checkPower(raw); return null;} catch(error) {return {name:error.name,message:error.message};}"
LEADERS = [10, 11, 12, 3]
POWER_ORDER = [10, 11, 12, 3, 9, 5, 1, 2, 8, 6, 7, 4]


def test_the_real_receipts_pass_and_derive_the_views_numbers():
    result = node(DATA + "return powerValues(checkPower(raw));")
    assert [team['id'] for team in result['order']] == POWER_ORDER
    assert [team['id'] for team in result['four']] == LEADERS
    assert [team['id'] for team in result['upper']] == POWER_ORDER[:6]
    assert [team['id'] for team in result['lower']] == POWER_ORDER[6:]
    assert (result['feature']['id'], result['feature']['gap']) == (12, 3)
    assert result['apart'] == 1


def test_rows_carry_text_records_and_the_places():
    first = node(DATA + "return powerValues(checkPower(raw)).order;")
    assert first[0] == {'id': 10, 'name': 'Jaxon The Box', 'power': 1, 'standing': 1, 'record': '6-2',
                        'allPlay': '56-32', 'points': 954.28}
    assert (first[7]['id'], first[7]['allPlay'], first[7]['power']) == (2, '41-47', 8)


def test_a_record_with_ties_prints_the_ties():
    result = node(DATA + "raw.teams[0].record={w:5,l:2,t:1}; raw.teams[0].allPlay={w:55,l:32,t:1}; return powerValues(checkPower(raw)).order[0];")
    assert result['record'] == '5-2-1' and result['allPlay'] == '55-32-1'


def test_the_feature_is_derived_from_the_gap_not_hardcoded():
    result = node(DATA + "raw.teams.forEach(t => { if (t.id === 9) t.standing = 12; if (t.id === 4) t.standing = 8; }); "
                  "return powerValues(checkPower(raw)).feature;")
    assert (result['id'], result['gap']) == (9, 7)


@pytest.mark.parametrize('mutation', [
    "raw.teams.push({...raw.teams[0]})",
    "raw.teams[1].id=raw.teams[0].id",
    "raw.teams[0].power=13",
    "raw.teams[0].standing=0",
    "raw.teams[0].record.l=3",
    "raw.teams[0].allPlay.l=31",
    "[raw.teams[0], raw.teams[1]] = [raw.teams[1], raw.teams[0]]",
    "raw.through=9",
    "raw.comparisons=87",
    "raw.season=2025",
    "raw.league=1",
    "raw.teams[0].points='954.28'",
    "raw.teams[0].luck=null",
    "raw.teams[0].name=' '",
])
def test_receipt_contract_rejects_invalid_receipts(mutation):
    result = node(DATA + mutation + TRY)
    assert result['name'] == 'Error' and result['message'].startswith('Invalid power receipts:')
