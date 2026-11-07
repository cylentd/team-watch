import pytest
from test_madden_chapter2 import node
from test_madden_defense_story import DATA
from pages.madden_defense_cards import DefenseCardsFilm


def test_defense_copy_labels_the_start_and_points_without_repeating_manager():
    result = node("return (await import(base + '/lineups-copy.mjs')).LINEUPS_COPY;")
    assert result['defense'] == 'The defense experiment.'
    assert result['defenseWin'] == 'Still won.'
    assert result['outcomeBoth'] == 'Won both weeks.'
    assert result['defenseCard']['started'] == 'STARTED · WEEK {week}'
    assert result['defenseCard']['points'] == '{score} PTS'


def test_retired_defense_card_does_not_return_for_the_payoff():
    result = node(DATA + "const {lineupsPose} = await import(base + '/lineups-pose.mjs'); const cast = lineupValues(checkLineups(raw)); return [5,6.5,7.5].map(s => lineupsPose(s,false,cast).shields.map(p => p.visible));")
    assert result == [[False, True], [False, True], [False, True]]


@pytest.mark.parametrize('size', [(360,800), (690,829), (1440,900)])
@pytest.mark.journey
def test_defense_cards_show_one_identity_and_explicit_scores(browser, size):  # shape: allow single browser trace verifies two card entrances retain identity and explicit scores
    film = DefenseCardsFilm(browser, *size)
    with film:
        film.load()
        film.seek(59.5)
        assert {'SAINTS', 'STARTED · WEEK 4', '−3 PTS'} <= set(film.shown_text())
        assert 'GIBBS' not in film.shown_text() and 'DEF' not in film.shown_text()
        assert film.identity() == {'text': 'Gibbs', 'loaded': True, 'visible': True, 'inside': True}
        film.seek(62.9)
        assert {'RAIDERS', 'STARTED · WEEK 5', '−1 PTS'} <= set(film.shown_text())
        assert 'SAINTS' not in film.shown_text()
        film.seek(64.8)
        assert film.headline()['text'] == 'Won both weeks.'
        assert next(item for item in film.readout()['objects'] if item['text'] == 'Blip')['inside']
        film.seek(59.5)
        assert '−1 PTS' not in film.shown_text()
        assert film.errors == []

@pytest.mark.journey
def test_power_decals_use_depth_bias_without_writing_transparent_depth(browser):
    film = DefenseCardsFilm(browser, 360, 800)
    with film:
        film.load()
        materials = film.power_layers()
        assert len(materials) == 5
        assert all(not material['write'] and material['bias'] for material in materials)


@pytest.mark.parametrize('logo', ['saints', 'raiders'])
@pytest.mark.journey
def test_missing_defense_logo_prevents_play(browser, logo):
    film = DefenseCardsFilm(browser, 360, 800)
    with film:
        readout = film.fail_portrait(f'**/assets/{logo}.webp')
        assert not readout['ready']
        assert readout['disposed'] == 1
