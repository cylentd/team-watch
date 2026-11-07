from contextlib import contextmanager

import pytest
from playwright.sync_api import expect
from component import mount
from pages.madden_headline import headline_page  # noqa: F401 -- re-exported: four Madden test files import it from here

from test_madden_stage_polish import stage_result
from test_trophy_room import local_file


BOARD_HEADLINE_WAITS_FOR_THE_FULL_REVEAL_SCRIPT = ("""
const {filmPlan, filmMoment} = await import(base + '/film.mjs');
const {at} = await import(base + '/timing.mjs');
const board = filmPlan().beats[0], reveal = board.start + at('board', 'stand');
return {flyby: filmMoment(board.start + 2).headline, before: filmMoment(reveal - .01).headline,
  at: filmMoment(reveal).headline, age: filmMoment(reveal + .25).headlineAge,
  reduced: filmMoment(board.start + 1, true).headline};
""")

BOARD_HAS_TWO_SECONDS_OF_READING_AFTER_THE_ENTRANCE_SCRIPT = ("""
const {filmPlan} = await import(base + '/film.mjs');
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
return {read: ESTABLISH.hold - .5, duration: filmPlan().duration};
""")

MUSIC_KEEPS_THE_ORIGINAL_POST_BOARD_HITS_AFTER_THE_EXTRA_BAR_SCRIPT = ("""
const {ONSETS, filmTime} = await import(base + '/music-onsets.mjs');
return ONSETS.map(filmTime);
""")


def test_board_headline_waits_for_the_full_reveal():
    result = stage_result(BOARD_HEADLINE_WAITS_FOR_THE_FULL_REVEAL_SCRIPT)
    assert result['flyby'] is None and result['before'] is None
    assert result['at'] == result['reduced'] == 'board'
    assert result['age'] == pytest.approx(.25)


def test_board_has_two_seconds_of_reading_after_the_entrance():
    result = stage_result(BOARD_HAS_TWO_SECONDS_OF_READING_AFTER_THE_ENTRANCE_SCRIPT)
    assert result['read'] >= 2
    # 2026-11-05: Chapter 3's two beats, 6 s and 4 s, end the film on 60.077. ~~50.077~~ (David reapproved).
    # 2026-11-05 (David reapproved, +2 s Chapter 3): waiver-claim 8 s, the film ends on 62.077. ~~60.077~~.
    assert result['duration'] == pytest.approx(98.077)


def test_music_keeps_the_original_post_board_hits_after_the_extra_bar():
    times = stage_result(MUSIC_KEEPS_THE_ORIGINAL_POST_BOARD_HITS_AFTER_THE_EXTRA_BAR_SCRIPT)
    assert min(abs(time - 16.584) for time in times) < 1e-6


@contextmanager
def film_page(mount):
    context = mount.browser.new_context(viewport={'width': 1440, 'height': 900})
    context.route('http://trophy.test/**', local_file)
    context.route('https://**', lambda route: route.abort())
    try:
        yield context.new_page()
    finally:
        context.close()


def open_film(page):
    page.goto('http://trophy.test/?film')
    expect(page.locator('[data-play]')).to_be_enabled(timeout=60000)
    return page


def seek(page, time):
    page.locator('[data-seek]').evaluate('(element,time) => {element.step="any"; element.value=time; element.dispatchEvent(new Event("input"));}', time)


@pytest.mark.journey
def test_flyby_hides_lower_third_and_its_scrim(mount):
    with film_page(mount) as page:
        headline_page = open_film(page)
        seek(headline_page, 10)
        expect(headline_page.locator('[data-receipt]')).to_be_hidden()
        assert headline_page.locator('[data-room]').evaluate('element => getComputedStyle(element, "::after").opacity') == '0'


@pytest.mark.journey
def test_headline_and_subline_enter_in_stages_and_scrub_back_cleanly(mount):
    with film_page(mount) as page:
        headline_page = open_film(page)
        seek(headline_page, 13.084)
        head = headline_page.locator('[data-receipt-head]')
        sub = headline_page.locator('[data-receipt-sub]')
        assert float(head.evaluate('element => getComputedStyle(element).opacity')) == pytest.approx(0)
        seek(headline_page, 13.234)
        assert 0 < float(head.evaluate('element => getComputedStyle(element).opacity')) < 1
        assert float(sub.evaluate('element => getComputedStyle(element).opacity')) == pytest.approx(0)
        seek(headline_page, 13.584)
        assert float(sub.evaluate('element => getComputedStyle(element).opacity')) == pytest.approx(1)
        seek(headline_page, 10)
        expect(headline_page.locator('[data-receipt]')).to_be_hidden()
