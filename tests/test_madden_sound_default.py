"""Sound is on when the film plays (David, 2026-11-06): the first Play turns it on unless the viewer already chose."""
import pytest
from playwright.sync_api import expect

from pages.madden_waivers import WaiversFilm


@pytest.mark.journey
def test_the_first_play_turns_the_sound_on(browser):
    with WaiversFilm(browser, 390, 844) as film:
        film.load()
        film.page.locator('[data-play]').click()
        expect(film.page.locator('[data-sound]')).to_have_attribute('aria-pressed', 'true')


@pytest.mark.journey
def test_a_viewer_who_turned_the_sound_off_before_play_keeps_it_off(browser):
    with WaiversFilm(browser, 390, 844) as film:
        film.load()
        sound = film.page.locator('[data-sound]')
        sound.click()
        expect(sound).to_have_attribute('aria-pressed', 'true')
        sound.click()
        expect(sound).to_have_attribute('aria-pressed', 'false')
        film.page.locator('[data-play]').click()
        expect(sound).to_have_attribute('aria-pressed', 'false')
