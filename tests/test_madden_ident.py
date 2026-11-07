import pytest
from playwright.sync_api import expect
from component import mount

from test_madden_stage_polish import stage_result
from test_trophy_room import local_file


BRAND_SHOWS_IN_THE_OPENING_ONLY_SCRIPT = ("""
const {identAt} = await import(base + '/film-ident.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const {at} = await import(base + '/timing.mjs');
const plan = filmPlan(), finale = plan.beats.find(beat => beat.id === 'finale');
const total = finale.start + at('finale', 'total');
return {middle: plan.beats.map(beat => identAt(beat.start + beat.duration / 2)),
  total: identAt(total), after: identAt(total + .25), end: identAt(plan.duration), opening: identAt(1)};
""")


def test_brand_shows_in_the_opening_only():
    opacity = stage_result(BRAND_SHOWS_IN_THE_OPENING_ONLY_SCRIPT)
    assert opacity['middle'] == [0] * len(opacity['middle'])
    assert opacity['total'] == 0 and opacity['after'] == 0
    assert opacity['end'] == pytest.approx(1)   # 2026-11-05 (Chapter 5): the tag returns at the end. ~~== 0~~.
    assert opacity['opening'] == pytest.approx(1)


@pytest.mark.journey
def test_brand_is_not_a_watermark_during_feature_beats(mount):
    context = mount.browser.new_context(viewport={'width': 1920, 'height': 1080})
    with context:
        context.route('http://trophy.test/**', local_file)
        context.route('https://**', lambda route: route.abort())
        page = context.new_page()
        page.goto('http://trophy.test/?film')
        for time in (20, 43.9, 49.8):
            page.locator('[data-seek]').evaluate(
                "(element, time) => {element.value = time; element.dispatchEvent(new Event('input'));}", time)
            expect(page.locator('.brand')).to_be_hidden()
        page.locator('[data-seek]').evaluate("element => {element.value = 1; element.dispatchEvent(new Event('input'));}")
        expect(page.locator('.brand')).to_be_visible()
