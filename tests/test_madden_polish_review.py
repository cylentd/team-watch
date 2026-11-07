import pytest
from playwright.sync_api import expect
from component import mount

from test_madden_stage_polish import stage_result
from test_madden_rev8 import CAMERA
from test_trophy_room import local_file


ZOOM_HAS_NO_WHITE_OVERLAY_SCRIPT = ("""
const {flareAt} = await import(base + '/film-zoom.mjs');
return [7.1, 7.4, 7.58, 7.7, 7.9].map(flareAt);
""")

LIGHT_POOL_FOLLOWS_THE_FLYBY_AND_SETTLES_TO_A_READABLE_BOARD_SCRIPT = ("""
const module = await import(base + '/draft-establish.mjs');
const {pathLight: light} = await import(base + '/draft-path-light.mjs');
const samples = [1, 3].map(time => {
  const point = module.passLook(time, false);
  return {near: light(point.x, point.along, time, false), far: light(point.x + 5, point.along, time, false)};
});
return {samples, held: light(0, 0, 6, false)};
""")

FULL_BOARD_HOLDS_FOR_ONE_SECOND_BEFORE_TRAVEL_SCRIPT = ("""
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const board = filmPlan().beats[0], start = board.start + ESTABLISH.stand[1];
const frames = [0, .25, .75, .999].map(offset => view(filmMoment(start + offset), ctx));
return frames.slice(1).map(frame => frame.position.distanceTo(frames[0].position));
""")

TITLE_TAGLINE_AND_IDENT_USE_THE_SITE_BRAND_WITHOUT_OVERLAP_SCRIPT = ("""async () => {
const {TITLE_DROP} = await import('/film-title-drop.mjs');
const tag = document.querySelector('.tagline').getBoundingClientRect();
const canvas = document.querySelector('canvas').getBoundingClientRect();
const brand = document.querySelector('.brand');
return {font: TITLE_DROP.font?.family, tagTop: tag.top, tagRight: tag.right, height: canvas.height,
  family: getComputedStyle(brand).fontFamily, background: getComputedStyle(brand).backgroundColor};
}""")


def test_zoom_has_no_white_overlay():
    values = stage_result(ZOOM_HAS_NO_WHITE_OVERLAY_SCRIPT)
    # 2026-11-05 (David reapproved): only the short flash at the cut (7.584 s), capped at 0.6
    # (test_madden_colored_path.py); ~~no white at all, [0] * 5~~.
    assert [values[0], values[1], values[4]] == [0, 0, 0]
    assert all(0 < value <= .6 for value in values[2:4])


# 2026-11-05 (David reapproved): rule 19, the camera never stands still; it drifts slowly through the full board's
# hold instead of ~~holding still for one second~~ (distances [0, 0, 0]).
def test_full_board_holds_for_one_second_before_travel():
    result = stage_result(CAMERA.replace('MOBILE', 'false') + FULL_BOARD_HOLDS_FOR_ONE_SECOND_BEFORE_TRAVEL_SCRIPT)
    assert all(later > earlier for earlier, later in zip([0, *result], result)), result   # moving every sample
    assert result[-1] < 1, result                                                          # slowly


def test_light_pool_follows_the_flyby_and_settles_to_a_readable_board():
    result = stage_result(LIGHT_POOL_FOLLOWS_THE_FLYBY_AND_SETTLES_TO_A_READABLE_BOARD_SCRIPT)
    assert all(sample['near'] > sample['far'] + .4 for sample in result['samples'])
    # 2026-11-05 (David reapproved, polish note 1): unlit cards sit dark (test_madden_flyby_polish.py, <= .34);
    # ~~far >= .35~~.
    assert all(sample['far'] <= .34 for sample in result['samples'])
    assert result['held'] == pytest.approx(1)


@pytest.mark.journey
@pytest.mark.parametrize('width', [360, 1280, 1440, 1920])
def test_title_tagline_and_ident_use_the_site_brand_without_overlap(mount, width):
    context = mount.browser.new_context(viewport={'width': width, 'height': 900})
    with context:
        context.route('http://trophy.test/**', local_file)
        context.route('https://**', lambda route: route.abort())
        page = context.new_page()
        page.goto('http://trophy.test/?film')
        expect(page.locator('[data-play]')).to_be_enabled(timeout=60000)
        page.locator('[data-seek]').evaluate("element => {element.value = 6.3; element.dispatchEvent(new Event('input'));}")
        result = page.evaluate(TITLE_TAGLINE_AND_IDENT_USE_THE_SITE_BRAND_WITHOUT_OVERLAP_SCRIPT)
        assert 'Bricolage Grotesque' in (result['font'] or '')
        assert 'Bricolage Grotesque' in result['family']
        assert result['background'] == 'rgba(0, 0, 0, 0)'
        assert result['tagTop'] >= result['height'] * .86
        assert result['tagRight'] <= width
        expect(page.locator('.brand .slashes')).to_be_visible()
