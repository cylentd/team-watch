import pytest

from pages.madden_power import PowerFilm


@pytest.mark.journey
def test_the_live_finale_borrows_the_opening_trophy_and_rewinds(browser):
    film = PowerFilm(browser, 390, 844)
    with film:
        film.load()
        observed = []
        for time in [89.5, 81, 89.5]:
            film.seek(time)
            observed.append(film.page.evaluate('''async () => (await import('./power-set.mjs')).powerReadout()'''))
        assert observed == [{'bound': True, 'visible': True}, {'bound': True, 'visible': False}, {'bound': True, 'visible': True}]
        assert film.errors == []
