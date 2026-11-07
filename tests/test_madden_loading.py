import pytest
from playwright.sync_api import expect

from pages.madden_loading import LoadingFilm


@pytest.fixture(params=[(360, 800, False), (768, 690, False), (1440, 900, False), (390, 844, True)])
def loading_film(browser, request):
    film = LoadingFilm(browser, *request.param)
    with film:
        film.hold()
        yield film


def test_loading_replaces_controls_until_real_readiness(loading_film):
    expect(loading_film.loader()).to_be_visible()
    expect(loading_film.loader()).to_contain_text("Getting the film ready.")
    for controls in loading_film.inactive_controls().all():
        expect(controls).to_be_hidden()
    metrics = loading_film.loading_metrics()
    assert metrics["inside"] and metrics["blocked"] and metrics["busy"] == "true", metrics
    assert metrics["animation"] == ("none" if loading_film.reduced else "loading-signal")
    loading_film.release()
    expect(loading_film.play_button()).to_be_enabled(timeout=30000)
    expect(loading_film.loader()).to_be_hidden()
    expect(loading_film.phase()).to_have_attribute("aria-busy", "false")
    assert not loading_film.errors


def test_failed_load_replaces_spinner_with_existing_fallback(loading_film):
    loading_film.release(fail=True)
    expect(loading_film.phase()).to_have_attribute("data-phase", "fallback")
    expect(loading_film.loader()).to_be_hidden()
    expect(loading_film.phase()).to_have_attribute("aria-busy", "false")
    expect(loading_film.play_button()).to_be_disabled()
    assert not loading_film.errors
