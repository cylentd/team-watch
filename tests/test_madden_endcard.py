"""The ending zooms to black, then presents a large centered Team Watch identity."""
import pytest

from test_madden_chapter2 import node
from test_madden_chapter5 import camera
from pages.madden_endcard import EndcardFilm


BLACK_PRECEDES_THE_LOGO_AND_THE_FINAL_CHORD_STAYS_AT_92_077_SCRIPT = ("""
const ident = await import(base + '/film-ident.mjs');
if (!ident.endcardPose) return null;
return [91.4, 91.7, 91.927, 92.077, 97.9].map(time => ident.endcardPose(time));""")

CAMERA_CONTINUES_FORWARD_INTO_BLACK_THEN_HOLDS_SCRIPT = ("""
const rows = [91.577, 91.827, 92.077, 97.9].map(time => {
  const shot = view(filmMoment(time), ctx);
  return {position: shot.position.toArray(), target: shot.target.toArray(), distance: shot.position.distanceTo(shot.target)};
});
return rows;""")


def test_black_precedes_the_logo_and_the_final_chord_stays_at_92_077():
    result = node(BLACK_PRECEDES_THE_LOGO_AND_THE_FINAL_CHORD_STAYS_AT_92_077_SCRIPT)
    assert result is not None
    assert result[0] == {'active': False, 'black': 0, 'logo': 0}
    assert 0 < result[1]['black'] < 1 and result[1]['logo'] == 0
    assert result[2]['black'] == 1 and result[2]['logo'] == 0
    assert result[3] == result[4] == {'active': True, 'black': 1, 'logo': 1}


@pytest.mark.parametrize('mobile', [False, True])
def test_camera_continues_forward_into_black_then_holds(mobile):
    result = camera(mobile, CAMERA_CONTINUES_FORWARD_INTO_BLACK_THEN_HOLDS_SCRIPT)
    assert result[0]['distance'] > result[1]['distance'] > result[2]['distance']
    assert result[2]['distance'] < result[0]['distance'] * .25
    assert result[2] == result[3]


@pytest.fixture(scope='module', params=[(360, 800, False), (390, 844, False), (690, 829, False), (1440, 900, False), (390, 844, True)])
def endcard_film(browser, request):
    film = EndcardFilm(browser, *request.param[:2], reduced=request.param[2])
    with film:
        film.load()
        yield film


@pytest.mark.journey
def test_logo_is_large_and_centered_on_black(endcard_film):
    endcard_film.seek(93)
    card = endcard_film.endcard()
    assert card['active'] and card['black'] == 1 and card['color'] == 'rgb(0, 0, 0)'
    assert card['opacity'] == pytest.approx(1) and card['within']
    assert card['width'] >= .65 and card['height'] >= .25
    assert card['center'] == pytest.approx([.5, .5], abs=.02)
    assert endcard_film.errors == []


@pytest.mark.journey
def test_black_completes_before_logo_and_reverse_seek_restores_the_film(endcard_film):
    endcard_film.seek(91.8)
    assert endcard_film.endcard()['opacity'] == 0
    endcard_film.seek(91.95)
    card = endcard_film.endcard()
    assert card['active'] and card['black'] == 1 and card['opacity'] < 1
    endcard_film.seek(90.5)
    card = endcard_film.endcard()
    assert not card['active'] and card['black'] == 0
    assert endcard_film.errors == []
