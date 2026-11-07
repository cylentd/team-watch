"""Chapter 17, David's title notes (2026-11-04): a much bigger burst on every word's landing, the title in Team
Watch's own palette, and the hand-over as a zoom into the trophy's ball. All pure functions of film time, in
Node. The frame's corners are tested in the browser (test_madden_stage_fill.py)."""
import math

import pytest

from test_madden_stage_polish import stage_result

REV15_SPARKS = 72      # the burst before these notes (film-impact.mjs, revision 15)


SPARK_FALLS_UNDER_GRAVITY_AND_BOUNCES_ONCE_ON_THE_FLOOR_SCRIPT = ("""
const {sparkHeight} = await import(base + '/film-impact.mjs');
return Array.from({length: 400}, (_, index) => sparkHeight(index / 200, .7));
""")

RING_OF_EMBERS_LINGERS_A_SECOND_AND_A_HALF_SCRIPT = ("""
const {IMPACT, embersAt} = await import(base + '/film-impact.mjs');
return {life: IMPACT.embers.life, early: embersAt(.2), late: embersAt(1.4), gone: embersAt(1.51), before: embersAt(-.01)};
""")

DEBRIS_CHIPS_FLY_IN_EACH_WORDS_OWN_MATERIAL_SCRIPT = ("""
const {IMPACT} = await import(base + '/film-impact.mjs');
const {TITLE_DROP} = await import(base + '/film-title-drop.mjs');
return {chips: IMPACT.chips, tones: TITLE_DROP.hits.map(hit => hit.tone)};
""")

TITLE_WEARS_TEAM_WATCH_INK_AND_LIME_WITH_THE_LOGOS_RED_MARK_SCRIPT = ("""
const {TITLE_DROP} = await import(base + '/film-title-drop.mjs');
const {PALETTE} = await import(base + '/constants.mjs');
return {look: TITLE_DROP.look, depth: TITLE_DROP.depth, layers: TITLE_DROP.layers, ink: PALETTE.ink, lime: PALETTE.brandLime,
  red: PALETTE.mark};
""")

CURSES_HIT_LIGHTS_A_LIME_RIM_ON_THE_TROPHY_THAT_SETTLES_AND_STAYS_SCRIPT = ("""
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const {rimAmount} = await import(base + '/film-title-drop.mjs');
const at = TITLE_WORDS[TITLE_WORDS.length - 1];
return {before: rimAmount(at - .01), peak: Math.max(...[0, .1, .2, .3, .4].map(age => rimAmount(at + age))), held: rimAmount(at + 2)};
""")

HANDOVER_DOLLIES_STRAIGHT_INTO_THE_BALL_TO_A_NEAR_WHITE_FLARE_ON_THE_GUITAR_SCRIPT = ("""
const {OPENING} = await import(base + '/constants.mjs');
const {HANDOVER, handoverCamera, flareAt, zoomAmount} = await import(base + '/film-zoom.mjs');
const {sceneChanges} = await import(base + '/film.mjs');
const start = new THREE.Vector3(3.4, 3.1, 8.6), aim = new THREE.Vector3(0, 1.9, 0), ball = new THREE.Vector3(0, 3.68, 0);
const step = 1 / 30, samples = [];
for (let time = HANDOVER.from; time <= OPENING.duration + 1e-9; time += step) {
  const {position, target} = handoverCamera(time, start, aim, ball);
  samples.push({time, distance: position.distanceTo(ball), position: position.toArray(), target: target.toArray()});
}
return {samples, from: HANDOVER.from, duration: OPENING.duration, flare: HANDOVER.flare, fade: HANDOVER.fade,
  before: flareAt(HANDOVER.from - .01), atStart: flareAt(HANDOVER.from), atGuitar: flareAt(OPENING.duration),
  after: flareAt(OPENING.duration + HANDOVER.fade + .01), zoomBefore: zoomAmount(HANDOVER.from - .1),
  zoomEarly: zoomAmount(HANDOVER.from + .1), zoomEnd: zoomAmount(OPENING.duration), change: sceneChanges()[0], start: start.toArray()};
""")

SHEET_WHOSE_HANDOVER_IS_MISSING_OR_STARTS_AFTER_THE_BOARD_FAILS_AT_LOAD_SCRIPT = ("""
const {checkTiming} = await import(base + '/timing.mjs');
const beat = {id: 'board', duration: 4, hold: 1, events: []};
const opening = handover => ({titleWords: [1, 2, 3], duration: 7, ...(handover && {handover})});
return [opening(null), opening({from: 7.5, flare: .9, fade: .3})].map(open => {
  try { checkTiming({beats: [beat], opening: open}); return 'passed'; } catch (error) { return error.message; } });
""")


def got(script):
    return stage_result(script)


def test_each_landing_throws_three_to_five_times_the_sparks_with_the_phone_capped():
    sparks = got("const {IMPACT} = await import(base + '/film-impact.mjs'); return IMPACT.sparks;")
    assert 3 * REV15_SPARKS <= sparks['count'] <= 5 * REV15_SPARKS
    assert sparks['phone'] < sparks['count'] and sparks['phone'] <= 2 * REV15_SPARKS, 'a phone holds frame rate'
    assert sparks['trail'] > 0, 'every spark draws a trail'


def test_a_spark_falls_under_gravity_and_bounces_once_on_the_floor():
    path = got(SPARK_FALLS_UNDER_GRAVITY_AND_BOUNCES_ONCE_ON_THE_FLOOR_SCRIPT)
    assert path[0] >= 0 and max(path) > 0
    # Flights: runs of samples clear of the floor. A sample rarely lands on the contact instant itself.
    clear, flights = 1e-3, []
    for height in path:
        if height > clear and (not flights or flights[-1][-1] <= clear):
            flights.append([])
        if flights:
            flights[-1].append(height)
    peaks = [max(flight) for flight in flights]
    assert len(peaks) == 2, 'flies, bounces once, and rests'
    assert 0 < peaks[1] < peaks[0] / 2
    assert path[-1] == 0, 'rests on the floor'


def test_a_ring_of_embers_lingers_a_second_and_a_half():
    embers = got(RING_OF_EMBERS_LINGERS_A_SECOND_AND_A_HALF_SCRIPT)
    assert embers['life'] == pytest.approx(1.5)
    assert embers['before'] is None and embers['gone'] is None
    assert embers['early']['opacity'] > embers['late']['opacity'] > 0


def test_curse_alone_throws_a_second_larger_ring_and_a_floor_wide_ember_carpet():
    hits = got("const {TITLE_DROP} = await import(base + '/film-title-drop.mjs'); return TITLE_DROP.hits;")
    *earlier, last = hits
    assert last['second'] > last['ring'] and last['carpet']
    assert all(not hit['second'] and not hit['carpet'] for hit in earlier)


def test_debris_chips_fly_in_each_words_own_material():
    chips = got(DEBRIS_CHIPS_FLY_IN_EACH_WORDS_OWN_MATERIAL_SCRIPT)
    assert chips['chips']['count'] >= 8 and chips['chips']['phone'] <= chips['chips']['count']
    assert chips['tones'] == ['ink', 'ink', 'lime']


def test_the_title_wears_team_watch_ink_and_lime_with_the_logos_red_mark():
    look = got(TITLE_WEARS_TEAM_WATCH_INK_AND_LIME_WITH_THE_LOGOS_RED_MARK_SCRIPT)
    assert (look['ink'], look['lime'], look['red']) == (0xf3f1ea, 0xc8ff2e, 0xc62e38)   # design/src/css/base/tokens.css, the logo
    assert look['look']['tracking'] < 0, 'tighter than the face sets itself'
    # 2026-11-05 (David reapproved): the red slash before THE is gone (ch17, David: "it reads as out of place");
    # ~~look.mark.width > 0~~.
    assert 'mark' not in look['look'], 'no red slash before THE'
    assert look['depth'] >= .45 and look['layers'] >= 14, 'a deeper extrusion'


def test_curses_hit_lights_a_lime_rim_on_the_trophy_that_settles_and_stays():
    rim = got(CURSES_HIT_LIGHTS_A_LIME_RIM_ON_THE_TROPHY_THAT_SETTLES_AND_STAYS_SCRIPT)
    assert rim['before'] == 0 and rim['peak'] == pytest.approx(1, abs=.05)
    assert 0 < rim['held'] < rim['peak']


@pytest.fixture
def handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar():
    zoom = got(HANDOVER_DOLLIES_STRAIGHT_INTO_THE_BALL_TO_A_NEAR_WHITE_FLARE_ON_THE_GUITAR_SCRIPT)
    distances = [sample['distance'] for sample in zoom['samples']]
    start, end = zoom['samples'][0]['position'], zoom['samples'][-1]['position']
    length = math.dist(start, end)
    line = [(b - a) / length for a, b in zip(start, end)]
    return zoom, distances, start, end, length, line


def test_the_handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar_1(handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar):
    zoom, distances, start, end, length, line = handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar
    assert zoom['from'] == pytest.approx(7.084) and zoom['duration'] == pytest.approx(7.584)
    assert all(later < earlier for earlier, later in zip(distances, distances[1:])), 'closes on the ball every frame'
    assert distances[-1] < .6, 'ends inside the chrome'
    assert all((math.dist(offset, [l * along for l in line]) < 1e-06) for sample in zoom['samples'] for offset in [([b - a for a, b in zip(start, sample['position'])])] for along in [(sum((o * l for o, l in zip(offset, line))))])


def test_the_handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar_2(handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar):
    zoom, distances, start, end, length, line = handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar
    assert zoom['zoomBefore'] == 0 and zoom['zoomEarly'] < .1 and zoom['zoomEnd'] == pytest.approx(1)   # ease-in
    assert zoom['before'] == 0 and zoom['atStart'] == 0
    assert zoom['atGuitar'] == pytest.approx(zoom['flare']) and 0 < zoom['flare'] <= .6, 'a short flash on the guitar'
    assert zoom['fade'] == pytest.approx(.14) and zoom['after'] == 0


def test_the_handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar_3(handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar):
    zoom, distances, start, end, length, line = handover_dollies_straight_into_the_ball_to_a_near_white_flare_on_the_guitar
    assert zoom['change']['kind'] == 'zoom', 'the light wipe is gone'


def test_a_sheet_whose_handover_is_missing_or_starts_after_the_board_fails_at_load():
    messages = got(SHEET_WHOSE_HANDOVER_IS_MISSING_OR_STARTS_AFTER_THE_BOARD_FAILS_AT_LOAD_SCRIPT)
    assert all(text != 'passed' and 'handover' in text for text in messages), messages
