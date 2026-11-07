"""Chapters 4 and 5 as 3D sets in the room (docs/madden-film-chapter4.md, docs/madden-film-chapter5.md,
"Cinematic revision", approved by David 2026-11-05): the set registry, the scene and camera plumbing, and the
16 s + 20 s retime that ends the film at 98.077."""
import pytest

from test_madden_chapter2 import node

FRAME_LIMIT = 2   # rule 18: frames of the 30 fps export an impact may sit from its bar line or onset
IDENT_LANDS = 92.077   # the song's last hit, read-hold 71.59 moved 4 phrases (8 s each) later, minus the 6 s offset
# A fake set: its shot puts the camera `seconds` along x, so a test reads which clock it was handed.
FAKE = """
const THREE = await import('three');
const sets = await import(base + '/film-sets.mjs');
const calls = [];
const fake = (chapter) => (scene, context) => ({ready: Promise.resolve(), warmAt: [chapter === 'lineups' ? 63 : 80],
  update: (moment, ctx) => { calls.push([chapter, 'update', moment.elapsed]); return {shake: 0}; },
  hide: () => calls.push([chapter, 'hide']), dispose: () => calls.push([chapter, 'dispose'])});
const fakeShot = (id, seconds) => ({position: new THREE.Vector3(seconds, 2, 10), target: new THREE.Vector3(seconds, 2, 0)});
"""
CAMERA_CTX = """
const card = () => ({home: new THREE.Vector3(0, 5, 0), mesh: {position: new THREE.Vector3(0, 5, 0)}});
const featured = Object.fromEntries(['steal', 'traded', 'sleeper', 'curse', 'injury'].map(id => [id, card()]));
const ctx = {mobile: false, floorZ: 1.9, finaleX: 0, featured, landing: new THREE.Vector3(2, 5, 0), size: {width: 1440, height: 900}};
"""


BOARD_STILL_TRAVELS_TO_THE_STEALS_FIRST_ONSET_SCRIPT = ("""
const {travelAt} = await import(base + '/draft-camera.mjs');
const {filmMoment} = await import(base + '/film.mjs');
return [16.57, 16.6].map(time => travelAt(filmMoment(time))?.to.id ?? null);""")

ORIGINAL_CLOSING_CHORD_REPLACES_THE_OLD_LOOPED_FINAL_HIT_SCRIPT = ("""const {MUSIC_EDIT} = await import(base + '/music-edit.mjs');
const {ONSETS} = await import(base + '/music-onsets.mjs');
return {repeats: MUSIC_EDIT.extension.repeats, onsets: ONSETS};""")

REGISTERED_SET_ROUND_TRIPS_AND_JOINS_THE_DRAWN_CHAPTERS_SCRIPT = ("""
const before = sets.drawnChapters(), factory = fake('lineups'), camera = {shot: fakeShot, lift: {desk: {'lineup-defense': .1}}};
sets.registerSet('lineups', factory, camera);
return {before, after: sets.drawnChapters(), same: sets.setFor('lineups').factory === factory,
  shot: sets.setFor('lineups').shot === fakeShot, power: sets.setFor('power') ?? null};""")

ROOM_DRAWS_A_SET_FROM_THE_INCOMING_WHIP_AND_NEVER_A_DOM_CHAPTER_SCRIPT = ("""
const {filmMoment} = await import(base + '/film.mjs');
const draws = time => sets.roomDraws(filmMoment(time));
const before = [57.8, 65, 50, 20].map(draws);
sets.registerSet('lineups', fake('lineups'), {shot: fakeShot});
return {before, after: [57.8, 65, 50, 55, 76].map(draws), entering: sets.activeSets(filmMoment(57.8))};""")

BUILT_SETS_UPDATE_THE_CURRENT_CHAPTER_AND_HIDE_THE_REST_SCRIPT = ("""
const {filmMoment} = await import(base + '/film.mjs');
sets.registerSet('lineups', fake('lineups'), {shot: fakeShot});
sets.registerSet('power', fake('power'), {shot: fakeShot});
const built = sets.buildSets({}, {});
await built.ready;
const steps = {};
for (const time of [65, 74, 85, 30]) { calls.length = 0; const routed = built.update(filmMoment(time), {}); steps[time] = {routed, calls: [...calls]}; }
calls.length = 0; built.dispose();
return {steps, warm: built.warmAt, disposed: [...calls]};""")

CAMERA_TAKES_A_REGISTERED_SETS_SHOT_AND_HOLDS_THE_FINALE_FOR_TRADES_SCRIPT = ("""
const {view} = await import(base + '/draft-camera.mjs');
const {filmMoment} = await import(base + '/film.mjs');
const trades = () => view(filmMoment(46), ctx).position.toArray();
const held = trades();
sets.registerSet('lineups', fake('lineups'), {shot: fakeShot});
return {defense: view(filmMoment(65), ctx).position.toArray(), whip: view(filmMoment(57.8), ctx).position.toArray(),
  held, trades: trades()};""")

SETS_LIFT_REPLACES_THE_DEFAULT_LIFT_FOR_ITS_BEAT_SCRIPT = ("""
const {frame, RIG} = await import(base + '/draft-camera.mjs');
const {filmMoment} = await import(base + '/film.mjs');
sets.registerSet('lineups', fake('lineups'), {shot: fakeShot, lift: {desk: {'lineup-defense': .3}}});
const lifted = time => { const camera = new THREE.PerspectiveCamera(40, 1440 / 900, .1, 100); frame(camera, filmMoment(time), ctx); return camera.view.offsetY / 900; };
return {defense: lifted(65), tightends: lifted(73), all: RIG.lift.desk.all};""")


def test_a_registered_set_round_trips_and_joins_the_drawn_chapters():
    result = node(FAKE + REGISTERED_SET_ROUND_TRIPS_AND_JOINS_THE_DRAWN_CHAPTERS_SCRIPT)
    assert result['before'] == ['draft']
    assert result['after'] == ['draft', 'lineups']
    assert result['same'] and result['shot'] and result['power'] is None


def test_the_room_draws_a_set_from_the_incoming_whip_and_never_a_dom_chapter():
    result = node(FAKE + ROOM_DRAWS_A_SET_FROM_THE_INCOMING_WHIP_AND_NEVER_A_DOM_CHAPTER_SCRIPT)
    # Unregistered, Chapter 4 draws nothing; the board (20) always draws; trades (50) is the board under its card.
    assert result['before'] == [False, False, False, True]
    # Registered: from the whip out of Chapter 3 (61.677) on; Chapter 3 itself (59) and Chapter 5 (80) stay off.
    assert result['after'] == [True, True, False, False, False]
    # The whip hands the set its own clock, negative before its first bar line.
    assert [(entry['chapter'], entry['beat']) for entry in result['entering']] == [('lineups', 'lineup-defense')]
    assert result['entering'][0]['seconds'] == pytest.approx(57.8 - 58.077)


@pytest.fixture
def sample_built_sets_update_the_current_chapter_and_hide_the_rest():
    result = node(FAKE + BUILT_SETS_UPDATE_THE_CURRENT_CHAPTER_AND_HIDE_THE_REST_SCRIPT)
    steps = result['steps']
    return result, steps


def test_built_sets_update_the_current_chapter_and_hide_the_rest_1(sample_built_sets_update_the_current_chapter_and_hide_the_rest):
    result, steps = sample_built_sets_update_the_current_chapter_and_hide_the_rest
    assert steps['65']['routed'] == {'shake': 0}
    assert steps['65']['calls'] == [['lineups', 'update', 65], ['power', 'hide']]
    assert sorted(call[0] for call in steps['74']['calls'] if call[1] == 'update') == ['lineups', 'power']
    assert steps['85']['calls'] == [['lineups', 'hide'], ['power', 'update', 85]]


def test_built_sets_update_the_current_chapter_and_hide_the_rest_2(sample_built_sets_update_the_current_chapter_and_hide_the_rest):
    result, steps = sample_built_sets_update_the_current_chapter_and_hide_the_rest
    assert steps['30']['routed'] is None and steps['30']['calls'] == [['lineups', 'hide'], ['power', 'hide']]
    assert result['warm'] == [63, 80]
    assert result['disposed'] == [['lineups', 'dispose'], ['power', 'dispose']]


def test_the_camera_takes_a_registered_sets_shot_and_holds_the_finale_for_trades():
    result = node(FAKE + CAMERA_CTX + CAMERA_TAKES_A_REGISTERED_SETS_SHOT_AND_HOLDS_THE_FINALE_FOR_TRADES_SCRIPT)
    assert result['defense'] == pytest.approx([65 - 58.077, 2, 10], abs=1e-6)
    assert result['whip'] == pytest.approx([57.8 - 58.077, 2, 10], abs=1e-6)   # Chapter 3's card covers no camera of its own
    assert result['trades'] == pytest.approx(result['held'])


def test_a_sets_lift_replaces_the_default_lift_for_its_beat():
    result = node(FAKE + CAMERA_CTX + SETS_LIFT_REPLACES_THE_DEFAULT_LIFT_FOR_ITS_BEAT_SCRIPT)
    assert result['defense'] == pytest.approx(.3)
    assert result['tightends'] == pytest.approx(result['all'])


@pytest.mark.parametrize('start,into', [(66.077, 'lineup-tightends'), (74.077, 'power-board')])
def test_a_travel_with_no_onset_near_its_bar_is_centred_on_the_bar_line(start, into):
    result = node(f"""
const {{travelAt}} = await import(base + '/draft-camera.mjs');
const {{filmMoment}} = await import(base + '/film.mjs');
return [{start} - .41, {start} - .39, {start} + .39, {start} + .41].map(time => travelAt(filmMoment(time))?.to.id ?? null);""")
    # TRANSITION.window 0.8 s: 0.4 s each side of the bar, like an `across` whip (rule 20).
    assert result == [None, into, into, None]


def test_the_board_still_travels_to_the_steals_first_onset():
    result = node(BOARD_STILL_TRAVELS_TO_THE_STEALS_FIRST_ONSET_SCRIPT)
    # The steal starts at 16.077; its first onset is source 20.584 s, 2 s later in the read-hold edit, 6 s before film.
    assert result == ['steal', None]


def test_the_retimed_plan_ends_the_film_at_ninety_eight_seconds():
    plan = node("return (await import(base + '/film.mjs')).filmPlan();")
    later = plan['beats'][10:]
    assert [(beat['id'], beat['duration']) for beat in later] == [('lineup-defense', 8), ('lineup-tightends', 8),
                                                                 ('power-board', 10), ('power-close', 14)]
    assert [beat['start'] for beat in later] == pytest.approx([58.077, 66.077, 74.077, 84.077])
    assert plan['duration'] == pytest.approx(98.077)
    assert [beat['start'] for beat in plan['beats'][:11]] == pytest.approx(
        [7.584, 16.077, 20.077, 24.077, 28.077, 36.077, 40.077, 44.077, 50.077, 56.077, 58.077])


def test_chapter_four_and_five_hits_use_the_approved_music_grid():
    hits = node("""const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs');
return filmImpacts().filter(hit => hit.at >= 58).map(hit => ({...hit, reference: nearestHit(hit.at)}));""")
    assert len(hits) == 21
    off = [hit for hit in hits if abs(hit['reference']['frames']) > FRAME_LIMIT
           or hit['reference']['kind'] != ('beat' if hit['name'] == 'Saints deduction' else 'downbeat')]
    assert off == []
    assert [hit['at'] for hit in hits if hit['name'] == 'Saints deduction'] == pytest.approx([59.077])
    assert [hit['at'] for hit in hits if hit['name'] == 'Ident lands'] == pytest.approx([IDENT_LANDS])

def test_the_original_closing_chord_replaces_the_old_looped_final_hit():
    result = node(ORIGINAL_CLOSING_CHORD_REPLACES_THE_OLD_LOOPED_FINAL_HIT_SCRIPT)
    assert result['repeats'] == 4
    assert 98.074 in result['onsets']
    assert 103.59 not in result['onsets'] and 111.59 not in result['onsets']


def test_the_ident_rises_on_the_bar_after_the_tail_and_holds_to_the_end():
    opacity = node("""const {identAt} = await import(base + '/film-ident.mjs');
return [91.5, 91.577, 91.7, 91.9, 92.077, 93, 98.077].map(identAt);""")
    assert opacity[0] == 0 and opacity[1] == 0
    assert 0 < opacity[2] < opacity[3] < 1
    assert opacity[4:] == pytest.approx([1, 1, 1])
