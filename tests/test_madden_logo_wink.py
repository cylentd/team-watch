"""One 0.3-second wink, half a second after the closing logo lands."""
import pytest

from test_madden_chapter2 import node
from pages.madden_logo_wink import LogoWinkFilm


WINK_HAPPENS_ONCE_AND_REDUCED_MOTION_KEEPS_THE_SMUG_FACE_SCRIPT = ("""
const ident = await import(base + '/film-ident.mjs');
if (!ident.winkAt) return null;
const times = [1, 91.8, 92.577, 92.652, 92.727, 92.802, 92.877, 97.9];
return {normal: times.map(time => ident.winkAt(time)), reduced: times.map(time => ident.winkAt(time, true))};""")


def test_wink_happens_once_and_reduced_motion_keeps_the_smug_face():
    result = node(WINK_HAPPENS_ONCE_AND_REDUCED_MOTION_KEEPS_THE_SMUG_FACE_SCRIPT)
    assert result is not None
    assert result['normal'] == pytest.approx([0, 0, 0, .5, 1, .5, 0, 0], abs=1e-8)
    assert result['reduced'] == [0] * 8


@pytest.fixture(params=[(390, 844, False), (1440, 900, False), (390, 844, True)])
def wink_film(browser, request):
    width, height, reduced = request.param
    film = LogoWinkFilm(browser, width, height, reduced=reduced)
    with film:
        film.load()
        yield film, reduced


@pytest.mark.journey
def test_only_one_eye_winks_and_seeking_restores_it(wink_film):
    film, reduced = wink_film
    rows = film.faces_at([92.5, 92.727, 92.95, 92.727, 92.5])
    assert rows[1]['eyes'][0] == pytest.approx(rows[0]['eyes'][0] * (1 if reduced else .08), rel=.02)
    assert all(row['eyes'][1] == pytest.approx(rows[0]['eyes'][1]) for row in rows)
    assert rows[0] == rows[2] == rows[4] and rows[1] == rows[3]
    assert all(row['word'] == rows[0]['word'] and row['mark'] == rows[0]['mark'] for row in rows)
    assert film.errors == []
