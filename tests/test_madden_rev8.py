"""Revision 8 (docs/madden-film-rules.md rules 10, 16-19, 23): every impact on a drum hit, nothing lit
before its beat, a designed transition at every scene change, a camera that never holds still, and
the lower-third rule line kept clear."""
import json
import math
import re
from pathlib import Path

import pytest

from test_madden_stage_polish import stage_result

SHOWCASE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse'


EVERY_IMPACT_LANDS_WITHIN_TWO_FRAMES_OF_A_DRUM_ONSET_OR_DOWNBEAT_SCRIPT = ("""
const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs');
const {SYNC} = await import(base + '/music-onsets.mjs');
return {limit: SYNC.frames, hits: filmImpacts().map(impact => ({...impact, ...nearestHit(impact.at)}))};
""")

TITLE_LANDS_ON_A_HIT_AND_HOLDS_TWO_SECONDS_INSIDE_A_SHORT_INTRO_SCRIPT = ("""
const {OPENING, FILM, TRANSITION} = await import(base + '/constants.mjs');
const {nearestHit} = await import(base + '/film-impacts.mjs');
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const land = TITLE_WORDS[TITLE_WORDS.length - 1], handover = FILM.chapterAt - TRANSITION.intro / 2;
return {land, hit: nearestHit(land), handover, chapter: FILM.chapterAt};
""")

TITLE_LANDS_ON_ITS_ONSET_AND_THE_SHOCK_RING_STARTS_ON_THAT_FRAME_SCRIPT = ("""
const {TITLE_DROP, titleDrop} = await import(base + '/film-title-drop.mjs');
const {IMPACT, ringAt} = await import(base + '/film-impact.mjs');
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const at = TITLE_WORDS[TITLE_WORDS.length - 1], frame = TITLE_DROP.frame;
return {early: titleDrop(at - 3 * frame), land: titleDrop(at), held: titleDrop(at + .5), gone: titleDrop(at - TITLE_DROP.fall - .01),
  ringBefore: ringAt(titleDrop(at - frame).age), ringOn: ringAt(titleDrop(at).age), ringNext: ringAt(titleDrop(at + frame).age),
  ringLate: ringAt(titleDrop(at + IMPACT.ring.life).age)};
""")

WEEK_LIGHTS_STATIONS_AND_FINALE_ROWS_ARE_INVISIBLE_BEFORE_THEIR_MOMENT_SCRIPT = ("""
const {lightOpacity} = await import(base + '/draft-props.mjs');
const {stationReveal} = await import(base + '/draft-curse.mjs');
const {enterAt} = await import(base + '/receipt-details.mjs');
return {light: lightOpacity(0), station: stationReveal(1, 2), row: enterAt(.3, .5), lit: lightOpacity(1)};
""")

BOARD_OPENS_ON_A_LONG_CLOSE_PASS_AND_A_SHORT_WIDE_VIEW_SCRIPT = ("""
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const {filmPlan} = await import(base + '/film.mjs');
return {...ESTABLISH, duration: filmPlan().beats[0].duration};
""")

GODWINS_FRONT_FLAMES_BURN_ROUND_THE_CARD_AND_LEAVE_THE_PORTRAIT_CLEAR_SCRIPT = ("""
const {FLAME, frontCentre} = await import(base + '/draft-flame.mjs');
const {CARD_HEIGHT} = await import(base + '/draft-board.mjs');
return {...FLAME, foot: (frontCentre() - CARD_HEIGHT * FLAME.front[1] / 2) / CARD_HEIGHT};
""")

EVERY_GODWIN_STOP_HOLDS_LONG_ENOUGH_FOR_THE_FIRE_TO_REACH_THE_AVATAR_SCRIPT = ("""
const {CURSE} = await import(base + '/draft-curse.mjs');
const {TRAIL} = await import(base + '/constants.mjs');
const {BURN} = await import(base + '/draft-burn.mjs');
const leaves = [...CURSE.landings.slice(1, -1).map(time => time - CURSE.move), CURSE.leap];
const holds = leaves.map((time, index) => time - CURSE.landings[index]);
return {holds: holds.filter((_, index) => index % 2 === 0), wire: holds.filter((_, index) => index % 2), minHold: TRAIL.minHold,
  spread: BURN.flash + BURN.catch, last: CURSE.flip[1] - CURSE.lastLanding};
""")

SMASH_WEEKS_FLAME_ICON_IGNITES_ON_ITS_POP_AND_FLICKERS_THROUGH_ITS_FRAMES_SCRIPT = ("""
const noop = new Proxy(function () {}, {get: (target, key) => key === Symbol.toPrimitive ? () => 0 : noop, apply: () => noop, set: () => true});
globalThis.document = {createElement: () => ({getContext: () => noop})};   // canvas textures draw nothing in node
const {WEEK_FIRE} = await import(base + '/draft-weekfire.mjs');
const {FLAME_ICON} = await import(base + '/week-flame-icon.mjs');
const {weekLights} = await import(base + '/draft-props.mjs');
const group = weekLights(3);
const burning = () => group.children.map(light => light.children.some(child => child.visible));
group.userData.set(0, 'smash', 0, 1); group.userData.set(1, 'bust', .5, 1); group.userData.set(2, 'solid', 1, 1);
const before = burning();
group.userData.set(0, 'smash', .05, 1.1);
const icon = group.children[0].children[0].children[1], early = icon.scale.x;
const maps = new Set(), scales = [];
for (let step = 0; step < 24; step++) {
  group.userData.set(0, 'smash', 1, 2 + step / 60);
  maps.add(icon.material.map); scales.push(icon.scale.x);
}
return {before, after: burning(), early, frames: maps.size, low: Math.min(...scales), high: Math.max(...scales),
  embers: WEEK_FIRE.embers, fps: FLAME_ICON.fps};
""")

TITLES_FLARE_BURSTS_ON_ITS_HIT_AND_THE_FLOOR_HAZE_STAYS_UNDER_THE_TROPHY_BASE_SCRIPT = ("""
const {FLARE, FLOOR_HAZE, flareAmount} = await import(base + '/film-flare.mjs');
const {STAGE} = await import(base + '/environment.mjs');
return {before: flareAmount(-.01), start: flareAmount(0), peak: flareAmount(FLARE.in), early: flareAmount(.05),
  gone: flareAmount(FLARE.in + FLARE.decay), half: flareAmount(FLARE.in + FLARE.decay / 2), FLARE, layers: FLOOR_HAZE.layers,
  stage: STAGE.height};
""")

TRADED_CARD_LANDS_BESIDE_AURAS_BADGE_OFF_THE_BOARD_NEVER_IN_A_COLUMN_SCRIPT = ("""
const {TRADED, traded, tradePlaces} = await import(base + '/draft-beats.mjs');
const {BOARD, columnX, rowY} = await import(base + '/draft-board.mjs');
const {CELL} = await import(base + '/draft-textures.mjs');
const {nearestHit} = await import(base + '/film-impacts.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const home = new THREE.Vector3(columnX(0), rowY(1), 0), places = tradePlaces(home);
const part = () => ({position: new THREE.Vector3(), scale: new THREE.Vector3(1, 1, 1), material: {opacity: 0}, visible: false});
const item = {mesh: {position: new THREE.Vector3(), rotation: new THREE.Euler(), scale: new THREE.Vector3()}, home,
  props: {stamp: part(), stampZ: .02, cover: part(), badge: part()}};
const at = time => {
  traded(time, item, places);
  const {stamp, cover, badge} = item.props;
  return {x: item.mesh.position.x, z: item.mesh.position.z, stamp: stamp.visible, cover: cover.visible ? cover.material.opacity : 0,
    badge: badge.visible ? badge.scale.x : 0};
};
const beat = filmPlan().beats.find(beat => beat.id === 'traded');
return {lift: at(TRADED.lift[1]), arc: at((TRADED.travel[0] + TRADED.travel[1]) / 2), before: at(TRADED.stamp[1] - .01),
  land: at(TRADED.stamp[1]), end: at(beat.duration), places: {badge: places.badge.toArray(), land: places.land.toArray()},
  columns: Array.from({length: CELL.columns}, (_, column) => columnX(column)), card: BOARD.card,
  hit: nearestHit(beat.start + TRADED.stamp[1])};
""")

BOARD_TILTS_TOWARD_THE_WALL_THROUGH_THE_WHOLE_PASS_NOT_ONLY_AT_THE_END_SCRIPT = ("""
const {ESTABLISH, tilt} = await import(base + '/draft-establish.mjs');
const times = Array.from({length: 111}, (_, index) => index * ESTABLISH.stand[1] / 110);
return {values: times.map(tilt), mid: tilt(ESTABLISH.move / 2), stand: ESTABLISH.stand};
""")

BOTH_FLOORS_ARE_ONE_DARK_TURF_GREEN_TOKEN_WITH_FAINT_WHITE_YARD_LINES_SCRIPT = ("""
const {PALETTE} = await import(base + '/constants.mjs');
const {STAGE} = await import(base + '/environment.mjs');
return {turf: PALETTE.turf, line: PALETTE.fieldLine, white: PALETTE.white, opacity: STAGE.field.opacity};
""")

EVERY_ONSET_OF_THE_MUSIC_BUILD_DIMS_COLUMNS_AND_ROMOS_COLUMN_CLIMBS_TO_THE_HIT_SCRIPT = ("""
const {BUILD, dimOrder, otherLight, winnerLight, flash} = await import(base + '/draft-build.mjs');
const {ONSETS, filmTime, bar, SYNC} = await import(base + '/music-onsets.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const {INJURY} = await import(base + '/draft-curse.mjs');
const injury = filmPlan().beats.find(beat => beat.id === 'injury'), frame = 1 / SYNC.fps, start = .16;
const order = dimOrder([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 0);
const lights = clock => [...order].map(([column, step]) => otherLight(clock, step, start));
const changed = clock => lights(clock + 4 * frame).filter((light, index) => light < lights(clock - frame)[index] * .7).length;
const beats = [...ONSETS.map(filmTime), ...Array.from({length: 40}, (_, i) => bar(i - 2))];
const from = injury.start + INJURY.fade[1] - 2 * frame, to = injury.start + BUILD.hit;
const inBuild = [...new Set(beats.filter(time => time >= from && time < to - 2 * frame))].sort((a, b) => a - b);
const romo = clock => Math.max(...Array.from({length: 30}, (_, i) => winnerLight(clock + i * .01, start)));
return {inBuild, starts: BUILD.steps.map(step => injury.start + step), limit: SYNC.frames / SYNC.fps,
  changed: BUILD.steps.map(changed), order: [...order], hit: injury.start + BUILD.hit, speeds: BUILD.speeds,
  romo: [romo(BUILD.steps[0] - .3), ...BUILD.steps.map(step => romo(step + BUILD.ease))], flash: [flash(BUILD.hit - .01), flash(BUILD.hit)]};
""")

EVERY_SCENE_CHANGE_IS_A_TRANSITION_WITH_NO_JUMP_IN_THE_CAMERA_SCRIPT = ("""
const plan = filmPlan();
return sceneChanges().filter(change => change.at > plan.chapterAt).map(change => {
  const before = view(filmMoment(change.at - 1e-5), ctx), after = view(filmMoment(change.at + 1e-5), ctx);
  return {to: change.to, amount: transitionAt(change.at)?.amount, jump: before.position.distanceTo(after.position)};
});
""")

BOARD_STANDS_AND_THE_CAMERA_TRAVELS_ON_TO_EACH_CARD_ARRIVING_ON_ITS_FIRST_ONSET_SCRIPT = ("""
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const {ONSETS, filmTime, SYNC} = await import(base + '/music-onsets.mjs');
ctx.featured.steal = {home: new THREE.Vector3(-3, 7, 0), mesh: {position: new THREE.Vector3(-3, 7, 0)}};
ctx.featured.traded = {home: new THREE.Vector3(2, 3, 0), mesh: {position: new THREE.Vector3(2, 3, 0)}};
const plan = filmPlan(), step = 1 / SYNC.fps, at = time => view(filmMoment(time), ctx).position;
const onsets = ONSETS.map(filmTime);
return plan.beats.filter(beat => ['steal', 'traded', 'sleeper'].includes(beat.id)).map(beat => {
  const previous = plan.beats[plan.beats.indexOf(beat) - 1], arrive = onsets.find(time => time > beat.start + .1);
  const from = previous.id === 'board' ? previous.start + ESTABLISH.stand[0] : beat.start - .4, speeds = [];
  for (let time = from + step; time < arrive - step; time += step) speeds.push(at(time + step).distanceTo(at(time)) / step);
  const landed = shot(beat.id, arrive - beat.start, ctx).position.distanceTo(at(arrive));
  return {id: beat.id, wipe: transitionAt(beat.start), slowest: Math.min(...speeds), landed, arrive: arrive - beat.start,
    after: at(arrive + step).distanceTo(shot(beat.id, arrive - beat.start + step, ctx).position)};
});
""")

FLY_BY_FLOWS_INTO_THE_STAND_UP_WITH_NO_HOLD_ON_THE_AVATARS_SCRIPT = ("""
const {ESTABLISH, passAlong} = await import(base + '/draft-establish.mjs');
const {CARD_HEIGHT, rowY} = await import(base + '/draft-board.mjs');
const {TRANSITION} = await import(base + '/constants.mjs');
const beat = filmPlan().beats[0], step = 1 / 30;
const speeds = mobile => {
  const context = {...ctx, mobile}, out = [];
  const at = time => view({beatIndex: 0, beatProgress: time * beat.pace / beat.duration}, context).position;
  for (let time = TRANSITION.intro / 2; time + step <= ESTABLISH.stand[1] - step / 2; time += step) out.push(at(time + step).distanceTo(at(time)) / step);
  return out;
};
const look = mobile => passAlong(0, mobile) + ESTABLISH.height[mobile ? 'phone' : 'desk'] / Math.tan(ESTABLISH.pitch) * Math.cos(ESTABLISH.yaw) - ESTABLISH.from[mobile ? 'phone' : 'desk'];
return {...ESTABLISH, card: CARD_HEIGHT, round7: rowY(6), slowest: [Math.min(...speeds(false)), Math.min(...speeds(true))],
  looks: [look(false), look(true)]};
""")

TRAIL_CAMERA_HOLDS_ONE_WIDE_THEN_ONE_WHIP_PAN_AND_PUSH_TO_COOKEDS_ZERO_SCRIPT = ("""
const {TRAIL} = await import(base + '/constants.mjs');
const {nearestHit} = await import(base + '/film-impacts.mjs');
const beat = filmPlan().beats.find(beat => beat.id === 'curse');
const times = Array.from({length: 400}, (_, i) => beat.duration * i / 399);
const views = times.map(time => shot('curse', time, ctx));
return {times, distances: views.map(view => view.position.distanceTo(view.target)), xs: views.map(view => view.position.x),
  ys: views.map(view => view.position.y), pan: TRAIL.pan, push: TRAIL.push, first: TRAIL.landings[0],
  landing: nearestHit(beat.start + TRAIL.pan[1] * beat.pace), flip: nearestHit(beat.start + TRAIL.flip * beat.pace)};
""")

CAMERA_MOVES_THROUGH_EVERY_HOLD_UPRIGHT_WITH_AT_MOST_THREE_DEGREES_OF_DRIFT_SCRIPT = ("""
const {drift, RIG} = await import(base + '/draft-camera.mjs');
const yaw = view => { const arm = view.position.clone().sub(view.target); return Math.atan2(arm.x, arm.z); };
const square = {position: new THREE.Vector3(0, 0, 5), target: new THREE.Vector3()};
return {span: Math.abs(yaw(drift(square, 1, MOBILE)) - yaw(drift(square, 0, MOBILE))),
  beats: filmPlan().beats.map(beat => {
    const at = Math.min(beat.settle, beat.duration - 1), a = shot(beat.id, at, ctx), b = shot(beat.id, at + .5, ctx);
    const rolls = Array.from({length: 20}, (_, i) => view(filmMoment(beat.start + beat.duration * i / 20), ctx).roll);
    return {id: beat.id, moved: a.position.distanceTo(b.position), roll: Math.max(...rolls.map(Math.abs))};
  })};
""")


def test_every_impact_lands_within_two_frames_of_a_drum_onset_or_downbeat():
    hits = stage_result(EVERY_IMPACT_LANDS_WITHIN_TWO_FRAMES_OF_A_DRUM_ONSET_OR_DOWNBEAT_SCRIPT)
    assert len(hits['hits']) >= 20
    assert all((abs(hit['frames']) <= hits['limit']) for hit in hits['hits']), [hit for hit in hits['hits']]


def test_the_title_lands_on_a_hit_and_holds_two_seconds_inside_a_short_intro():
    # Chapter 17: the title is whole when CURSE lands, and holds from there to the hand-over, which starts on
    # the fanfare's last hit. ~~chapterAt - logoAt == 2~~ (rev 8, a 6.077 s opening).
    plan = stage_result(TITLE_LANDS_ON_A_HIT_AND_HOLDS_TWO_SECONDS_INSIDE_A_SHORT_INTRO_SCRIPT)
    assert abs(plan['hit']['frames']) <= 2
    assert plan['handover'] - plan['land'] >= 2
    assert plan['chapter'] <= 8


def test_the_title_lands_on_its_onset_and_the_shock_ring_starts_on_that_frame():
    # Rev 14: the 3D title falls, hits the floor on its onset, and the ring races out from that frame. Chapter
    # 17: the title's onset is CURSE's, the last word, the only one that shakes. ~~OPENING.logoAt~~ (rev 14).
    drop = stage_result(TITLE_LANDS_ON_ITS_ONSET_AND_THE_SHOCK_RING_STARTS_ON_THAT_FRAME_SCRIPT)
    assert drop['gone']['visible'] is False and drop['early']['visible'] and drop['early']['drop'] > 0
    assert drop['land']['drop'] == 0 and drop['land']['squash'] and drop['land']['shake'] != [0, 0]
    assert drop['held']['drop'] == 0 and not drop['held']['squash'] and drop['held']['shake'] == [0, 0]
    assert drop['ringBefore'] is None and drop['ringOn'] is not None and drop['ringNext'] is not None
    assert drop['ringLate'] is None


def test_godwins_trail_is_five_stops_roster_wire_roster_wire_cooked():
    # Rev 14 storyboard: every move is its own stop, the Oct 28 same-day drop included (no bounce).
    edition = json.loads((SHOWCASE / 'edition.json').read_text(encoding='utf8'))
    path = edition['draft']['beats']['curse']['path']
    stops = stage_result(f"""
const {{trailStops}} = await import(base + '/draft-floor.mjs');
return trailStops({json.dumps(path)});
""")
    assert [stop['station'] for stop in stops] == ['roster-3', 'pit', 'roster-3', 'pit', 'roster-2']
    assert not any(stop.get('bounce') for stop in stops)
    assert stops[2]['steps'][0]['when'][:10] == stops[3]['steps'][0]['when'][:10] == '2026-10-28'
    assert stops[-1]['steps'][0]['when'].startswith('2026-10-30T12:56')
    assert stops[-1]['steps'][-1]['points'] == [0]


def test_week_lights_stations_and_finale_rows_are_invisible_before_their_moment():
    reveal = stage_result(WEEK_LIGHTS_STATIONS_AND_FINALE_ROWS_ARE_INVISIBLE_BEFORE_THEIR_MOMENT_SCRIPT)
    assert reveal['light'] == 0 and reveal['station'] == 0 and reveal['row'] == 0
    assert reveal['lit'] == 1


def test_the_rule_line_token_matches_the_cameras_rule_line():
    tokens = (SHOWCASE / 'tokens.css').read_text(encoding='utf8')
    desk = float(re.search(r'--broadcast-rule-top:(\d+)%', tokens).group(1)) / 100
    phone = float(re.search(r'--broadcast-rule-top-phone:(\d+)%', tokens).group(1)) / 100
    rig = stage_result("const {RIG} = await import(base + '/draft-camera.mjs'); return RIG;")
    assert (rig['ruleLine']['desk'], rig['ruleLine']['phone']) == pytest.approx((desk, phone))
    assert rig['gap'] >= .04


CAMERA = """
const {view, shot} = await import(base + '/draft-camera.mjs');
const {filmPlan, filmMoment, sceneChanges, transitionAt} = await import(base + '/film.mjs');
const card = () => ({home: new THREE.Vector3(0, 5, 0), mesh: {position: new THREE.Vector3(0, 5, 0)}});
const featured = Object.fromEntries(['steal', 'traded', 'sleeper', 'curse', 'injury'].map(id => [id, card()]));
const ctx = {mobile: MOBILE, floorZ: 1.9, finaleX: 0, featured, landing: new THREE.Vector3(2, 5, 0)};
"""


# Ch17 (David, coordinator): the fly-by skims the board at most this many card heights above its faces; a phone
# flies higher so more rounds show in its narrow frame.
MAX_ALTITUDE_CARDS = {'desk': 1.5, 'phone': 3}
# Ch17 (coordinator): the skim looks diagonally across the columns, this far off the board's axis.
SKIM_YAW_DEGREES = -27   # toward the top-left, ending near Golden's corner (ch17, David)
BOARD_PITCH = .76   # draft-board.mjs BOARD.pitchY, one round

@pytest.mark.parametrize('mobile', [False, True])
def test_every_scene_change_is_a_transition_with_no_jump_in_the_camera(mobile):
    result = stage_result(CAMERA.replace('MOBILE', json.dumps(mobile)) + EVERY_SCENE_CHANGE_IS_A_TRANSITION_WITH_NO_JUMP_IN_THE_CAMERA_SCRIPT)
    # Ch17 (coordinator, for David): a beat on the same board is a camera travel with no wipe; the whip and its
    # light sweep stay only where the scene changes: onto the curse's floor, back to the board, the finale's pull-back.
    # 2026-11-05 (David reapproved): Chapter 3's weeks card stays on the pickups' stage, so it has no wipe either.
    # 2026-11-05 (ch4/5 cinematic): Chapter 4's second beat, the crane onto Chapter 5's riser and Chapter 5's close
    # travel on their sets too. ~~['steal', 'traded', 'sleeper', 'waiver-starts']~~.
    assert [change['to'] for change in result if change.get('amount') is None] == ['steal', 'traded', 'sleeper',
                                                                                    'waiver-starts', 'lineup-tightends',
                                                                                    'power-board', 'power-close']
    assert all((change['amount'] == pytest.approx(0.5, abs=0.02)) for change in result if change.get('amount') is not None), [change for change in result if change.get('amount') is not None]
    assert all((change['jump'] < 0.01) for change in result), [change for change in result]


@pytest.mark.parametrize('mobile', [False, True])
def test_the_board_stands_and_the_camera_travels_on_to_each_card_arriving_on_its_first_onset(mobile):
    # Ch17 (coordinator, for David): the board stands up and the camera carries on in one move to Golden's card,
    # easing out onto it on the steal's first onset; card to card the same, never still in between.
    result = stage_result(CAMERA.replace('MOBILE', json.dumps(mobile)) + BOARD_STANDS_AND_THE_CAMERA_TRAVELS_ON_TO_EACH_CARD_ARRIVING_ON_ITS_FIRST_ONSET_SCRIPT)
    assert all((travel['wipe'] is None) for travel in result), [travel for travel in result]
    assert all((travel['slowest'] > 0.001) for travel in result), [travel for travel in result]
    assert all((travel['landed'] < 1e-06 and travel['after'] < 1e-06) for travel in result), [travel for travel in result]
    assert all((0 < travel['arrive'] <= 1) for travel in result), [travel for travel in result]


@pytest.mark.parametrize('mobile', [False, True])
def test_the_camera_moves_through_every_hold_upright_with_at_most_three_degrees_of_drift(mobile):
    # Rule 19, David rev 9: rev 8's orbit tilted everything. A slow push keeps the camera moving; the yaw
    # drift is 3 degrees at most and the roll is zero on every frame of every beat.
    result = stage_result(CAMERA.replace('MOBILE', json.dumps(mobile)) + CAMERA_MOVES_THROUGH_EVERY_HOLD_UPRIGHT_WITH_AT_MOST_THREE_DEGREES_OF_DRIFT_SCRIPT.replace('MOBILE', json.dumps(mobile)))
    assert result['span'] <= 3 * 3.14159265 / 180 + 1e-9
    assert all((beat['moved'] > 0.005) for beat in result['beats']), [beat for beat in result['beats']]
    assert all((beat['roll'] == 0) for beat in result['beats']), [beat for beat in result['beats']]


def test_transitions_run_seven_tenths_to_a_second_and_the_title_hands_over_in_one():
    changes = stage_result("const {sceneChanges} = await import(base + '/film.mjs'); return sceneChanges();")
    assert changes[0]['window'] == pytest.approx(1)
    # Ch17: a travel on the same board has no whip (test above); every whip still runs 0.7 to 1 s.
    assert all(.7 <= change['window'] <= 1 for change in changes if change['kind'] != 'travel'), changes


def test_the_board_opens_on_a_long_close_pass_and_a_short_wide_view():
    # Rule 12, David rev 9: the fly-by is 3 s or more, the whole board about 1 s.
    shot = stage_result(BOARD_OPENS_ON_A_LONG_CLOSE_PASS_AND_A_SHORT_WIDE_VIEW_SCRIPT)
    assert shot['fly'][1] - shot['fly'][0] >= 3
    # Ch17: the board beat runs on to the bar line after the guitar's entry, so the wall holds about 1 s.
    # 2026-11-05 (David reapproved, polish note 2): the full board holds 2.5 s, so the wall shows about 3 s; ~~1 s~~.
    assert shot['duration'] - shot['stand'][1] == pytest.approx(3, abs=.1)   # plus half of the 0.8 s whip out


def test_the_finale_names_the_next_best_class_from_the_data():
    edition = json.loads((SHOWCASE / 'edition.json').read_text(encoding='utf8'))['draft']
    finale = edition['beats']['finale']['team']
    best = max(team['value'] for team in edition['teams'] if team['id'] != finale)
    details = stage_result(f"""
const {{draftDetails}} = await import(base + '/draft-data.mjs');
const fs = await import('node:fs');
const next = draftDetails(JSON.parse(fs.readFileSync({json.dumps(str(SHOWCASE / 'edition.json'))}, 'utf8')).draft).finale.next;
const minus = String.fromCodePoint(0x2212);   // ASCII out: Windows decodes the child's stdout as cp1252
return {{minus: next.startsWith(minus), next: next.replace(minus, '-')}};
""")
    assert details['next'] == (str(best) if best < 0 else f'+{best}')
    assert details['minus'] == (best < 0)
    assert details['next'] == '-14'   # Jaxon The Box, 2026-11-04 edition, drawn with a true minus sign


@pytest.fixture
def fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars():
    shot = stage_result(CAMERA.replace('MOBILE', 'false') + FLY_BY_FLOWS_INTO_THE_STAND_UP_WITH_NO_HOLD_ON_THE_AVATARS_SCRIPT)
    return shot,


def test_the_fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars_1(fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars):
    shot, = fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars
    assert shot['fly'][1] - shot['fly'][0] >= 3
    assert shot['move'] == pytest.approx(shot['stand'][1])   # the dolly ends on the stand-up onset, not before it
    assert all(slowest > 1e-3 for slowest in shot['slowest']), shot['slowest']   # board units a second, never still
    assert all(abs(look) <= 1e-9 for look in shot['looks'])


def test_the_fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars_2(fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars):
    shot, = fly_by_flows_into_the_stand_up_with_no_hold_on_the_avatars
    assert all((shot['altitude'][device] <= MAX_ALTITUDE_CARDS[device]) for device in ('desk', 'phone'))
    assert all((shot['height'][device] == pytest.approx(shot['altitude'][device] * shot['card'])) for device in ('desk', 'phone'))
    assert shot['from']['desk'] <= shot['round7'] + BOARD_PITCH / 2
    assert shot['stand'][1] == pytest.approx(5.5)   # onset 17.578, rev 16b


STRAIGHT_DOLLY_SCRIPT = "\nconst {ESTABLISH, riding, flatten, tilt} = await import(base + '/draft-establish.mjs');\nconst {BOARD, CARD_HEIGHT} = await import(base + '/draft-board.mjs');\nconst {frame} = await import(base + '/draft-camera.mjs');\nconst {TRANSITION} = await import(base + '/constants.mjs');\nconst beat = filmPlan().beats[0], size = {width: __WIDTH__, height: __HEIGHT__};\nconst camera = new THREE.PerspectiveCamera(36, __WIDTH__ / __HEIGHT__, .05, 200);\nconst points = [];\nfor (let x = -3.6; x <= 3.6; x += .3) for (let z = -1; z >= -12; z -= .25) points.push(new THREE.Vector3(x, ESTABLISH.table, z));\nconst step = 1 / 30, from = TRANSITION.intro / 2, to = ESTABLISH.stand[0];\nlet last = null, cross = 0, turn = 0, worst = null;\nconst angles = [], positions = [], board = [];\nfor (let time = from; time <= to + 1e-9; time += step) {\n  frame(camera, {beatIndex: 0, beatProgress: time * beat.pace / beat.duration}, {...ctx, size});\n  camera.updateMatrixWorld(); camera.updateProjectionMatrix();\n  const screen = points.map(point => riding(point, time).project(camera));   // rev 17: the points tilt with the board\n  if (last) {\n    screen.forEach((now, index) => {\n      const before = last.screen[index];\n      if (Math.abs(now.x) > 1 || Math.abs(now.y) > 1 || now.z > 1 || before.z > 1) return;\n      const dx = (now.x - before.x) / 2 * __WIDTH__, dy = (now.y - before.y) / 2 * __HEIGHT__;\n      const speed = Math.hypot(dx, dy) / __WIDTH__ / step;\n      if (speed > cross) { cross = speed; worst = [time, index, now.x, now.y]; }\n    });\n    turn = Math.max(turn, camera.quaternion.angleTo(last.quaternion) / step);\n  }\n  const euler = new THREE.Euler().setFromQuaternion(camera.quaternion, 'YXZ');\n  positions.push(camera.position.toArray());\n  const ahead = camera.position.clone().add(camera.getWorldDirection(new THREE.Vector3()));\n  const right = camera.position.clone().add(new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion));\n  const [at, look, side] = [camera.position, ahead, right].map(point => flatten(point, time));   // in the flat board's frame\n  board.push({at: at.toArray(), pitch: Math.atan2(at.y - look.y, Math.hypot(look.x - at.x, look.z - at.z)),\n    yaw: Math.atan2(look.x - at.x, at.z - look.z), roll: side.y - at.y});\n  angles.push([euler.y, euler.x, euler.z]);\n  last = {screen, quaternion: camera.quaternion.clone()};\n}\nreturn {cross, worst, turn, angles, positions, board, limit: ESTABLISH.cross, limitTurn: ESTABLISH.turn, fov: camera.fov,\n  altitude: ESTABLISH.altitude, card: CARD_HEIGHT, face: ESTABLISH.table + BOARD.depth / 2};\n"


@pytest.fixture(params=[False, True])
def fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second(request):
    mobile = request.param
    width, height = (390, 844) if mobile else (1920, 1080)
    result = stage_result(CAMERA.replace('MOBILE', json.dumps(mobile)) + STRAIGHT_DOLLY_SCRIPT.replace('__WIDTH__', str(width)).replace('__HEIGHT__', str(height)))
    yaws, pitches, rolls = zip(*result['angles'])
    device = 'phone' if mobile else 'desk'
    flat = [row['at'] for row in result['board']]
    start, end = flat[0], flat[-1]
    line = [b - a for a, b in zip(start, end)]
    length = math.hypot(*line)
    return width, height, result, yaws, pitches, rolls, device, flat, start, end, line, length


def test_the_fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second_1(fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second):
    width, height, result, yaws, pitches, rolls, device, flat, start, end, line, length = fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second
    assert result['cross'] < result['limit'] == pytest.approx(1), (result['cross'], result['worst'])
    assert result['turn'] < result['limitTurn'], result['turn']
    assert all(row['yaw'] == pytest.approx(math.radians(SKIM_YAW_DEGREES), abs=math.radians(.5)) for row in result['board'])
    assert max(row['yaw'] for row in result['board']) - min(row['yaw'] for row in result['board']) < math.radians(.1)


def test_the_fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second_2(fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second):
    width, height, result, yaws, pitches, rolls, device, flat, start, end, line, length = fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second
    assert all(abs(row['roll']) < 1e-6 for row in result['board'])
    assert all(row['pitch'] == pytest.approx(math.radians(27), abs=math.radians(.5)) for row in result['board'])   # down
    assert all(row['at'][1] - result['face'] <= MAX_ALTITUDE_CARDS[device] * result['card'] + 1e-6 for row in result['board'])
    assert all(later >= earlier - 1e-4 for earlier, later in zip(pitches, pitches[1:]))   # the table's lift settling, 0.002 degrees


def test_the_fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second_3(fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second):
    width, height, result, yaws, pitches, rolls, device, flat, start, end, line, length = fly_by_is_one_straight_dolly_nothing_crossing_faster_than_a_quarter_frame_a_second
    assert pitches[-1] - pitches[0] > math.radians(20)
    assert all((math.hypot(*offset) ** 2 - along ** 2 < 1e-06) for point in flat for offset in [([p - a for a, p in zip(start, point)])] for along in [(sum((o * d for o, d in zip(offset, line))) / length)])


def test_godwins_front_flames_burn_round_the_card_and_leave_the_portrait_clear():
    flame = stage_result(GODWINS_FRONT_FLAMES_BURN_ROUND_THE_CARD_AND_LEAVE_THE_PORTRAIT_CLEAR_SCRIPT)
    width, height = flame['front']
    card_left, card_right = (width - 1) / 2 / width, 1 - (width - 1) / 2 / width
    card_bottom = flame['frontBelow'] / height
    left, bottom, right, top, _ = flame['hole']
    assert width > 1 and flame['foot'] < -.5          # wider than the card, its foot under the card's
    assert card_left < left and right < card_right    # flames up both sides, on the card
    assert card_bottom < bottom                       # and over its lower edge
    assert (bottom - card_bottom) * height <= .2      # the portrait and name stay clear above that strip
    assert top > 1


@pytest.fixture
def curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes():
    edition = json.loads((SHOWCASE / 'edition.json').read_text(encoding='utf8'))
    path = edition['draft']['beats']['curse']['path']
    burn = stage_result(f"""
const {{trailStops}} = await import(base + '/draft-floor.mjs');
const {{CURSE}} = await import(base + '/draft-curse.mjs');
const {{BURN, ownerVisits, ownerState}} = await import(base + '/draft-burn.mjs');
const visits = ownerVisits(trailStops({json.dumps(path)}), CURSE.landings, CURSE.move);
const at = seconds => Object.fromEntries([...visits].map(([key, list]) => [key, ownerState(seconds, list)]));
const samples = Array.from({{length: 161}}, (_, index) => at(index * .05));
return {{arrivals: Object.fromEntries([...visits].map(([key, list]) => [key, list.map(visit => visit.arrive)])),
  landings: CURSE.landings, flash: BURN.flash, out: BURN.out, keys: Object.keys(BURN),
  burning: samples.map(state => Object.values(state).filter(owner => owner.burn > 0).length),
  before: at(.49), run: at(.65), first: at(1), wire: at(1.8), back: at(2.95), wire2: at(3.8), flip: at(CURSE.flip[1] + .5)}};   // rev 16b: the stops a bar later
""")
    return edition, path, burn


def test_the_curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes_1(curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes):
    edition, path, burn = curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes
    assert burn['arrivals'] == {'roster-3': [0.5, 2.5], 'roster-2': [5.223]}
    assert all(time in burn['landings'] for times in burn['arrivals'].values() for time in times)
    assert burn['flash'] == pytest.approx(.2) and not {'travel', 'ball', 'trail'} & set(burn['keys'])
    assert all(owner == {'flash': 0, 'burn': 0} for owner in burn['before'].values())


def test_the_curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes_2(curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes):
    edition, path, burn = curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes
    assert burn['run']['roster-3']['flash'] > 0 and burn['run']['roster-3']['burn'] == 0   # 0.15 s in: the flash
    assert burn['first']['roster-3'] == {'flash': 0, 'burn': 1}
    assert burn['wire']['roster-3'] == {'flash': 0, 'burn': 0}            # out and clean, not charred
    assert burn['back']['roster-3']['burn'] == 1                          # the return relights him


def test_the_curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes_3(curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes):
    edition, path, burn = curse_leaves_with_him_and_each_avatar_is_clean_once_he_goes
    assert burn['wire2']['roster-3'] == {'flash': 0, 'burn': 0}
    assert burn['flip']['roster-3'] == {'flash': 0, 'burn': 0} and burn['flip']['roster-2']['burn'] == 1
    assert max(burn['burning']) == 1


def test_only_the_two_wide_stations_are_in_the_wide_and_cookeds_waits_off_frame_right():
    edition = json.loads((SHOWCASE / 'edition.json').read_text(encoding='utf8'))
    path = edition['draft']['beats']['curse']['path']
    layout = stage_result(f"""
const {{FLOOR, stationLayout, trailStops}} = await import(base + '/draft-floor.mjs');
const steps = trailStops({json.dumps(path)});
return {{desk: stationLayout(steps), phone: stationLayout(steps, true), floor: FLOOR}};
""")
    assert all((list(x) == ['roster-3', 'pit', 'roster-2']) for device in ('desk', 'phone') for x in [({entry['key']: entry['x'] for entry in layout[device]})])
    assert all((x['roster-3'] + x['pit'] == pytest.approx(0)) for device in ('desk', 'phone') for x in [({entry['key']: entry['x'] for entry in layout[device]})])
    assert all((x['pit'] - x['roster-3'] == pytest.approx(layout['floor']['gap'][device])) for device in ('desk', 'phone') for x in [({entry['key']: entry['x'] for entry in layout[device]})])
    assert all((x['roster-2'] - x['pit'] == pytest.approx(layout['floor']['reveal'])) for device in ('desk', 'phone') for x in [({entry['key']: entry['x'] for entry in layout[device]})])


def test_every_godwin_stop_holds_long_enough_for_the_fire_to_reach_the_avatar():
    # David rev 12: a stop that left at once never showed its fire. Rev 14: the leap leaves at TRAIL.leap.
    hold = stage_result(EVERY_GODWIN_STOP_HOLDS_LONG_ENOUGH_FOR_THE_FIRE_TO_REACH_THE_AVATAR_SCRIPT)
    assert hold['minHold'] > hold['spread']
    assert all(time >= hold['minHold'] - 1e-9 for time in hold['holds']), hold['holds']
    assert all(time >= .3 for time in hold['wire'])                       # the wire burns nobody, so its stops are quicker
    assert hold['last'] > 0                                               # COOKed lands before the 0.0


@pytest.mark.parametrize('mobile', [False, True])
def test_the_trail_camera_holds_one_wide_then_one_whip_pan_and_push_to_cookeds_zero(mobile):
    # Rev 14 storyboard: fixed wide for stops 1-5 (to 5.5 s), one whip pan into a push on an onset, then
    # a slow push while the 0.0 flips in on its hit.
    result = stage_result(CAMERA.replace('MOBILE', json.dumps(mobile)) + TRAIL_CAMERA_HOLDS_ONE_WIDE_THEN_ONE_WHIP_PAN_AND_PUSH_TO_COOKEDS_ZERO_SCRIPT)
    times, pan = result['times'], result['pan']
    wide = [(x, y, d) for t, x, y, d in zip(times, result['xs'], result['ys'], result['distances']) if result['first'] <= t <= pan[0]]
    assert max(abs(a - b) for row in wide for a, b in zip(row, wide[0])) < 1e-9          # fixed wide
    moving = [x for t, x in zip(times, result['xs']) if pan[0] <= t <= pan[1]]
    assert all(b >= a - 1e-9 for a, b in zip(moving, moving[1:])) and moving[-1] > moving[0] + 3   # one pan right
    after = [d for t, d in zip(times, result['distances']) if t >= pan[1]]
    assert all(b <= a + 1e-9 for a, b in zip(after, after[1:])) and after[0] > after[-1]   # push in, never back
    assert abs(result['landing']['frames']) <= 1                          # the bar line at 6, onset 5.998
    assert abs(result['flip']['frames']) <= 1      # the 0.0 on its hit: rev 16's onset 34.075 sits on the bar line


@pytest.mark.parametrize('mobile', [False, True])
def test_the_fly_by_ends_looking_at_the_team_avatars_before_the_board_stands(mobile):
    # David rev 13: the pass stopped short of the top; it must end on the avatars and their names.
    end = stage_result(f"""
const {{ESTABLISH, establishing, flatten}} = await import(base + '/draft-establish.mjs');
const {{BOARD, boardTop, rowY}} = await import(base + '/draft-board.mjs');
const wall = {{position: new THREE.Vector3(0, 5, 20), target: new THREE.Vector3(0, 5, 0)}};
const at = time => flatten(establishing(time, {json.dumps(mobile)}, wall).target, time);   // rev 17: the board tilts as it goes
return {{last: -at(ESTABLISH.stand[0]).z, settled: -at(ESTABLISH.stand[0] - .3).z, avatars: boardTop(),
  names: boardTop() - BOARD.teamName.below, round1: rowY(0), fly: ESTABLISH.fly}};
""")
    assert end['fly'][1] - end['fly'][0] >= 3   # rule 12; rev 15's pass is 2.65 s moving and a 0.4 s hold
    assert end['names'] - .01 <= end['last'] <= end['avatars'] + .01      # looking at the avatar row and its names
    assert end['last'] > end['round1']                                    # past round 1
    assert end['last'] - end['settled'] < .2                              # slowed onto them (under 0.7 a second), so they read


@pytest.fixture
def smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames():
    fire = stage_result(SMASH_WEEKS_FLAME_ICON_IGNITES_ON_ITS_POP_AND_FLICKERS_THROUGH_ITS_FRAMES_SCRIPT)
    return fire,


def test_a_smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames_1(smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames):
    fire, = smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames
    assert fire['before'] == [False, False, False]                        # not before its pop; bust and solid never
    assert fire['after'] == [True, False, False]
    assert fire['early'] < .3                                             # it scales up from nothing as it ignites
    assert 3 <= fire['frames'] <= 4                                       # a drawn flicker cycle, not one still sprite


def test_a_smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames_2(smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames):
    fire, = smash_weeks_flame_icon_ignites_on_its_pop_and_flickers_through_its_frames
    assert fire['low'] == pytest.approx(1) and fire['high'] == pytest.approx(1.08)
    assert 2 <= fire['embers'] <= 3
    assert 8 <= fire['fps'] <= 15                                         # a frame lasts a few film frames


def test_the_titles_flare_bursts_on_its_hit_and_the_floor_haze_stays_under_the_trophy_base():
    # David rev 13: a white flare from the ball on the title's onset, 0.4 s in and 0.8 s out, and a low haze.
    flare = stage_result(TITLES_FLARE_BURSTS_ON_ITS_HIT_AND_THE_FLOOR_HAZE_STAYS_UNDER_THE_TROPHY_BASE_SCRIPT)
    assert flare['before'] == 0 and flare['start'] == 0 and flare['peak'] == pytest.approx(1)
    assert flare['early'] > .3                                            # it bursts on the onset, not after it
    assert flare['gone'] == 0 and 0 < flare['half'] < 1
    assert (flare['FLARE']['in'], flare['FLARE']['decay']) == (pytest.approx(.4), pytest.approx(.8))
    assert max(flare['layers']) < flare['stage']                          # the haze never rises past the trophy base


@pytest.fixture
def traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column():
    trade = stage_result(TRADED_CARD_LANDS_BESIDE_AURAS_BADGE_OFF_THE_BOARD_NEVER_IN_A_COLUMN_SCRIPT)
    half = trade['card'] / 2
    left_edge = min(trade['columns']) - half
    source = (SHOWCASE / 'draft.mjs').read_text(encoding='utf8')
    return trade, half, left_edge, source


def test_the_traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column_1(traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column):
    trade, half, left_edge, source = traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column
    assert all((card['x'] + half < left_edge and card['z'] >= 0.5) for moment in ('land', 'end') for card in [(trade[moment])]), [moment for moment in ('land', 'end') for card in [(trade[moment])]]
    assert all((all((abs(card['x'] - x) >= trade['card'] for x in trade['columns']))) for moment in ('land', 'end') for card in [(trade[moment])])
    assert trade['arc']['z'] > trade['places']['land'][2]                  # it arcs out toward the camera
    assert abs(trade['places']['badge'][0] - trade['places']['land'][0]) >= trade['card']   # beside the badge


def test_the_traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column_2(traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column):
    trade, half, left_edge, source = traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column
    assert trade['lift']['badge'] > 0 and trade['end']['badge'] == pytest.approx(1)
    assert trade['lift']['cover'] == 0 and trade['before']['cover'] == pytest.approx(1)   # the tag fades before the stamp
    assert not trade['before']['stamp'] and trade['land']['stamp']
    assert trade['hit']['kind'] == 'onset' and abs(trade['hit']['frames']) <= 2


def test_the_traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column_3(traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column):
    trade, half, left_edge, source = traded_card_lands_beside_auras_badge_off_the_board_never_in_a_column
    assert 'aura.column' not in source and 'landingNudge' not in source   # no re-slot path left


CURSE_STOPS = """
const {curse, CURSE} = await import(base + '/draft-curse.mjs');
const {CARD_HEIGHT} = await import(base + '/draft-board.mjs');
const {PROPS} = await import(base + '/draft-props.mjs');
const faces = Array.from({length: 6}, () => new THREE.MeshBasicMaterial());
const item = {mesh: new THREE.Mesh(new THREE.BoxGeometry(), faces), home: new THREE.Vector3(), front: faces[4],
  props: {root: new THREE.Group(), stampZ: .03, flame: {update() {}}}};
const names = ['wr', 'wire', 'wr', 'wire', 'cooked'];
const stations = Object.fromEntries(names.map((name, index) => [name + index, {kind: 'lineup', x: index, z: 0}]));
const steps = names.map((name, index) => ({station: name + index, kind: 'start'}));
const blip = {home: new THREE.Vector3(), position: new THREE.Vector3()};
const tile = new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial());
const pose = seconds => { curse(seconds, item, stations, steps, blip, tile);
  return {y: item.mesh.position.y, scaleY: item.mesh.scale.y}; };
const frame = 1 / 30, holds = CURSE.landings.map((landing, index) => {
  const leaves = index === CURSE.landings.length - 1 ? CURSE.flip[1] : index === CURSE.landings.length - 2 ? CURSE.leap : CURSE.landings[index + 1] - CURSE.move;
  return Array.from({length: 12}, (_, step) => pose(landing + (leaves - landing) * step / 12));
});
return {holds, squash: CURSE.landings.map(landing => [1, 2, 3, 4].map(count => pose(landing + count * frame).scaleY)),
  standing: CARD_HEIGHT / 2 + PROPS.padHeight, keys: Object.keys(await import(base + '/draft-curse.mjs'))};
"""


def test_the_card_lands_on_every_pad_with_a_three_frame_squash_and_stays_above_the_disc():
    # David rev 17 reversed the sink: on every stop the card squashes and settles in 2-3 frames and stays fully
    # on top of the disc. ~~It sank a quarter of its height into the WARREN-TY and wire discs~~ (rev 16).
    pose = stage_result(CURSE_STOPS)
    assert 'SINK' not in pose['keys'] and 'makeRipple' not in pose['keys']
    assert all((all((sample['y'] == pytest.approx(pose['standing']) for sample in hold))) for hold in pose['holds'])
    assert all((frames[0] < 1 - 0.001) for frames in pose['squash'])
    assert all((frames[2] == pytest.approx(1) and frames[3] == pytest.approx(1)) for frames in pose['squash'])


def test_the_film_controls_are_one_slim_bar_along_the_bottom_under_the_lower_third():
    # David rev 16: the controls covered the lower-third headline. They sit in a bar at the frame's foot, under
    # the lower third's foot, and fade after 2 s without a move once the film has started.
    css = (SHOWCASE / 'film-bar.css').read_text(encoding='utf8')
    tokens = (SHOWCASE / 'tokens.css').read_text(encoding='utf8')
    assert 'body[data-film] footer.controls{top:auto;bottom:0;left:0;right:0' in css
    assert 'height:var(--film-bar)' in css and '--film-bar:44px' in tokens
    assert '--broadcast-safe-bottom:max(6%,calc(var(--film-bar) + var(--space-3)))' in tokens
    assert 'film-bar.css' in (SHOWCASE / 'index.html').read_text(encoding='utf8')
    app = (SHOWCASE / 'app.mjs').read_text(encoding='utf8')
    assert 'const AWAKE_MS = 2000;' in app and 'root.dataset.started = state.started' in app


def test_the_board_tilts_toward_the_wall_through_the_whole_pass_not_only_at_the_end():
    # David rev 17: the board starts standing early in the pass, one continuous ease from about flat at its
    # start to the wall on the stand-up onset (17.578), not a sudden stand at the end. ~~Flat until 5.05 s~~ (rev 16b).
    tilt = stage_result(BOARD_TILTS_TOWARD_THE_WALL_THROUGH_THE_WHOLE_PASS_NOT_ONLY_AT_THE_END_SCRIPT)
    values = tilt['values']
    assert values[0] < .02 and values[-1] == pytest.approx(1)
    assert all(later > earlier for earlier, later in zip(values, values[1:]))   # always rising, never a stall
    assert .2 <= tilt['mid'] <= .6                                     # well on its way mid-pass
    assert tilt['stand'][1] == pytest.approx(5.5)


def test_both_floors_are_one_dark_turf_green_token_with_faint_white_yard_lines():
    # David rev 17: a muted broadcast turf, not game green; one token, so it can be reverted in one place.
    palette = stage_result(BOTH_FLOORS_ARE_ONE_DARK_TURF_GREEN_TOKEN_WITH_FAINT_WHITE_YARD_LINES_SCRIPT)
    red, green, blue = (palette['turf'] >> 16) & 255, (palette['turf'] >> 8) & 255, palette['turf'] & 255
    assert green > red and green > blue                                    # green
    assert max(red, green, blue) <= 64 and green - max(red, blue) <= 24    # dark and muted, not game green
    assert palette['line'] == palette['white'] and palette['opacity'] <= .2   # faint white lines
    environment = (SHOWCASE / 'environment.mjs').read_text(encoding='utf8')
    draft = (SHOWCASE / 'draft.mjs').read_text(encoding='utf8')
    assert 'MeshStandardMaterial({color: PALETTE.turf' in environment       # lit by the stadium rig
    assert 'color: PALETTE.turf' in draft and 'fieldMarkings()' in draft   # the draft room stands on it too


@pytest.fixture
def onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit():
    build = stage_result(EVERY_ONSET_OF_THE_MUSIC_BUILD_DIMS_COLUMNS_AND_ROMOS_COLUMN_CLIMBS_TO_THE_HIT_SCRIPT)
    ranks = [abs(column) for column, step in sorted(build['order'], key=lambda pair: pair[1])]
    return build, ranks


def test_every_onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit_1(onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit):
    build, ranks = onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit
    assert len(build['inBuild']) >= 2, build['inBuild']
    assert all((min((abs(onset - start) for start in build['starts'])) <= build['limit'] + 1e-09) for onset in build['inBuild']), [(onset, build['starts']) for onset in build['inBuild']]
    assert all(count >= 1 for count in build['changed']), build['changed']
    assert sum(build['changed']) == 11                                    # every other column, once


def test_every_onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit_2(onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit):
    build, ranks = onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit
    assert ranks == sorted(ranks)                                          # nearest Romo's first
    assert all(later > earlier for earlier, later in zip(build['romo'], build['romo'][1:]))   # a step brighter each time
    assert all(later > earlier for earlier, later in zip(build['speeds'], build['speeds'][1:]))   # and a faster pulse
    assert build['hit'] == pytest.approx(40.077, abs=build['limit'])  # the big hit


def test_every_onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit_3(onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit):
    build, ranks = onset_of_the_music_build_dims_columns_and_romos_column_climbs_to_the_hit
    assert build['flash'][0] == 0 and build['flash'][1] > .5
