"""Chapter 17 (2026-11-04): the film's frame shows only the film. The report under it (the article) stays below
the fold for the whole film, opening and every beat, and comes into view only when the reader scrolls past the
film. The draft's lower third shows only in the board beats, never in the opening."""
import pytest
from component import mount  # noqa: F401  (the shared browser fixture)

from test_trophy_room import local_file

VISIBLE = """selector => [...document.querySelectorAll(selector)].filter(el => {
  const box = el.getBoundingClientRect();
  return box.height > 0 && box.bottom > 0 && box.top < innerHeight && el.checkVisibility({visibilityProperty: true})
    && [...el.childNodes].some(node => node.nodeType === 3 && node.textContent.trim());
}).map(el => el.textContent.trim().slice(0, 40))"""
SEEK = '(el, t) => { el.step = "any"; el.value = t; el.dispatchEvent(new Event("input")); }'
TIMES = """async () => {
  const {TITLE_WORDS} = await import('./timing.mjs');
  const {OPENING} = await import('./constants.mjs');
  const {filmPlan} = await import('./film.mjs');
  const plan = filmPlan();
  return {opening: [1, ...TITLE_WORDS, OPENING.duration - .6],
    // 2026-11-05 (David reapproved): the board's lower third waits for the stand-up, so sample in the hold;
    // ~~beat.start + beat.duration / 2~~.
    beats: plan.beats.map(beat => beat.start + beat.settle + .5)};   // a beat's start is in film seconds
}"""
SIZES = [{'width': 1920, 'height': 1080}, {'width': 390, 'height': 844}]


@pytest.fixture(scope='module')
def film(mount):
    def open_at(size):
        context = mount.browser.new_context(viewport=size, reduced_motion='no-preference')
        context.route('http://trophy.test/**', local_file)
        context.route('https://**', lambda route: route.abort())
        page = context.new_page()
        page.goto('http://trophy.test/index.html?film')
        page.wait_for_selector('.room[data-phase=ready]', timeout=60000)
        return context, page
    return open_at


def shown(page, time, selector):
    page.eval_on_selector('[data-seek]', SEEK, time)
    return page.evaluate(VISIBLE, selector)


@pytest.mark.parametrize('size', SIZES)
def test_no_chapter_copy_shows_in_the_opening_frame(film, size):
    context, page = film(size)
    with context:
        times = page.evaluate(TIMES)
        assert all((shown(page, time, '[data-receipt] *, [data-report] *') == []) for time in times['opening']), [f'chapter copy in the opening at {time} s' for time in times['opening']]
        assert shown(page, times['beats'][0], '[data-receipt] *'), 'the board beat shows its lower third'


@pytest.mark.parametrize('size', SIZES)
def test_the_report_stays_below_the_film_through_every_beat_until_the_reader_scrolls(film, size):
    context, page = film(size)
    with context:
        times = page.evaluate(TIMES)
        assert all((shown(page, time, '[data-report] *') == []) for time in times['beats']), [f'the report peeks into the frame at {time} s' for time in times['beats']]
        page.evaluate("document.querySelector('[data-report]').scrollIntoView()")
        assert page.evaluate(VISIBLE, '[data-report] *'), 'scrolled past the film, the report is there to read'
