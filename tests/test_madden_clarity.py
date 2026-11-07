import pytest
from playwright.sync_api import expect

from pages.madden_clarity import ClarityFilm


@pytest.fixture(scope='module', params=[(390, 844), (768, 690), (900, 700), (1440, 900)])
def clarity_film(browser, request):
    film = ClarityFilm(browser, *request.param)
    with film:
        film.load()
        yield film


def test_love_and_par_label_fit_the_fold_and_existing_views(clarity_film):
    clarity_film.seek(57.7)
    expect(clarity_film.page.locator('[data-waivers-sub]')).to_have_text('Ranked by points over replacement (PAR).')
    boxes = clarity_film.pickup_frame()
    assert len(boxes) == 11
    assert all(box['visible'] and box['inside'] for box in boxes), boxes


@pytest.mark.parametrize('seconds, expected', [(59.2, 'The defense experiment.'), (67.2, 'Lamarley: the tight-end switch.'), (71.2, 'Lamarley: the tight-end switch.')])
def test_lineup_headlines_identify_the_scene_without_repeating_the_props(clarity_film, seconds, expected):
    clarity_film.seek(seconds)
    detail = clarity_film.page.locator('[data-lineup-outcome]')
    expect(detail).to_be_visible()
    expect(detail).to_have_text(expected)
    box = detail.bounding_box()
    assert box['x'] >= 0 and box['x'] + box['width'] <= clarity_film.width
    assert box['y'] >= 0 and box['y'] + box['height'] <= clarity_film.height


def test_actual_labels_use_leaderboard_places_not_win_loss(browser):
    film = ClarityFilm(browser, 390, 844)
    with film:
        film.load()
        receipts = film.textures()
        actual = [text for text in receipts['draws'] if text.endswith(' ACTUAL')]
        assert actual == [f'#{place} ACTUAL' for place in [1, 2, 6, 3, 8, 7, 4, 5, 9, 10, 11, 12]]
        assert '#6 actual' in receipts['draws'] and '#3 power' in receipts['draws']


def test_lime_stamps_render_dark_ink_in_both_chapters(browser):
    film = ClarityFilm(browser, 390, 844)
    with film:
        film.load()
        ink = film.textures()['ink']
        assert len(ink) == 3
        assert all(sample['dark'] > 100 and sample['white'] == 0 for sample in ink), ink
