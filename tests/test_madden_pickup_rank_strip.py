"""Love shows position ranks, not duplicate weekly scores, in the shorter cut."""
import pytest

from component import mount
from pages.madden_waivers import WaiversFilm


@pytest.mark.parametrize('width,height', [(360, 800), (768, 690), (1440, 900)])
def test_love_week_strip_is_rank_only_and_fits(mount, width, height):
    film = WaiversFilm(mount.browser, width, height)
    with film:
        film.load()
        film.seek(57.8)
        strip = film.page.locator('[data-waivers-weeks]')
        assert strip.locator('[data-week-points]').count() == 0
        assert strip.locator('[data-week-rank]').all_text_contents() == ['QB16', 'QB17', 'QB8', 'QB6', 'QB13', 'QB6']
        assert strip.is_visible()
        assert strip.bounding_box()['y'] + strip.bounding_box()['height'] <= height
