"""Chapter 5, Midseason power rankings, as a 3D riser in the room (docs/madden-film-chapter5.md, "Cinematic
revision"). 2026-11-05, David: "Chapter 5 isnt power ranking. It's the actual rankings." and "We dont have a good
ending?": the plates land in the standings, shuffle into power order, and the trophy returns for the finale."""
import json
import math

import pytest
from playwright.sync_api import expect

from test_madden_chapter2 import node
from pages.madden_power import PowerFilm

CAST = """
const fs = await import('node:fs');
const {checkPower, powerValues} = await import(base + '/power-data.mjs');
const values = powerValues(checkPower(JSON.parse(fs.readFileSync(new URL('power-receipts.json', base + '/'), 'utf8'))));
const cast = {feature: values.feature.power, leaders: values.four.length, standings: values.order.map(team => team.standing)};
const {powerPose} = await import(base + '/power-pose.mjs');
const pose = (time, reduced = false, mobile = false) => powerPose(time, reduced, cast, mobile);
"""
STANDINGS = [1, 2, 6, 3, 8, 7, 4, 5, 9, 10, 11, 12]   # power-receipts.json: each power place's standing
NOTCH = .08           # storyboard: Jaxon's piston one notch (0.08 plate heights) above the three tied plates
LIFT = .25            # storyboard: the top four lift 0.25 plate heights
FRAME_SHARE = .4      # rule 22: a feature subject is at least 40% of a 390px phone's frame height
NAME_SHARE = .02      # rule 23: a plate's name at least 2% of the frame's height
YAW_LIMIT = math.radians(1.5) + 1e-6   # rule 19: 3 degrees of drift in all, through square-on
TRAVELS = [(73.677, 74.477), (83.677, 84.477)]   # film.mjs TRAVEL: the crane in and the travel to the four


HEADLINES_KEEP_THEIR_WINDOWS_AND_THE_IDENT_LANDS_ON_THE_SONGS_LAST_HIT_SCRIPT = ("""
const {headlineAt} = await import(base + '/power-headline.mjs');
const {identPose, identAt} = await import(base + '/film-ident.mjs');
const keys = [75.5, 77.9, 79, 81, 83, 85, 87, 89.5, 92.1, 93.8].map(time => headlineAt(time)?.key ?? null);
return {keys, reduced: headlineAt(74.1, true), sub: [76, 79].map(time => headlineAt(time).sub),
  ident: [91.987, 92.077, 92.107, 92.437].map(identPose), at: identAt(93.8), before: identPose(81)};""")

EVERY_SHOT_KEEPS_ITS_SUBJECTS_WHOLE_INSIDE_THE_FRAME_SCRIPT = ("""
const feature = time => [...plates(time, [3]), ...stampCorners(3, posed(time)[2], MOBILE)];
const close = time => [...plates(time, all), ...trophyCorners(MOBILE), perch(MOBILE), stairs(MOBILE)[0]];
return {wide: [75.9, 76.5, 77.4, 78.3].map(time => box(time, plates(Math.max(time, 76.1), all))),
  feature: [80.6, 81, 82.5, 83.5].map(time => ({...box(time, feature(time)), plate: box(time, plates(time, [3])).height})),
  four: [84.6, 85.2].map(time => box(time, plates(time, [1, 2, 3, 4]))), close: [86.2, 87, 88.2, 89.5, 90.077].map(time => box(time, close(time)))};""")

EVERY_PLATE_NAME_READS_AT_TWO_PERCENT_OF_THE_FRAME_SCRIPT = ("""
const shots = {wide: [76.5, 78.3], four: [85], close: [88.2, 89.5, 90.077]};
return Object.fromEntries(Object.entries(shots).map(([name, times]) => [name, times.map(time =>
  Math.min(...posed(time).filter(plate => plate.visible).map(plate => box(time, nameCorners(plate.place, plate, MOBILE)).height)))]));""")

CAMERA_IS_CONTINUOUS_UPRIGHT_UNTIL_THE_CLOSING_HOLD_SCRIPT = ("""
const step = 1 / 30, rows = [];
for (let time = 74.6; time < 98.07; time += step) {
  const a = view(filmMoment(time), ctx), b = view(filmMoment(time + step), ctx), arm = a.position.clone().sub(a.target);
  rows.push({time, jump: a.position.distanceTo(b.position), yaw: Math.atan2(arm.x, arm.z), roll: a.roll, up: a.up.y});
}
const edges = [76.077, 78.077, 78.577, 80.077, 82.077, 84.077, 85.477, 86.077, 88.077, 90.077, 91.577, 92.077].map(time =>
  view(filmMoment(time - 1e-5), ctx).position.distanceTo(view(filmMoment(time + 1e-5), ctx).position));
const holds = [75, 76.5, 77.5, 80.5, 82.5, 85, 87, 89, 91].map(time =>
  view(filmMoment(time), ctx).position.distanceTo(view(filmMoment(time + .5), ctx).position));
return {rows, edges, holds};""")

POSE_IS_A_PURE_FUNCTION_OF_FILM_TIME_AND_REWINDS_SCRIPT = ("""
const first = pose(81); pose(93.8); const again = pose(81);
return {same: JSON.stringify(first) === JSON.stringify(again), early: pose(75.5).plates.map(plate => plate.visible),
  standings: pose(77).plates.map(plate => [plate.standing, plate.shuffle]), power: pose(79).plates.map(plate => plate.shuffle),
  trophy: [87, 81, 87].map(time => pose(time).trophy.visible)};""")

ALL_TWELVE_PLATES_LAND_IN_THE_STANDINGS_ON_THEIR_BAR_SCRIPT = ("""
const {plateCentre, slot} = await import(base + '/power-layout.mjs');
const at81 = pose(77).plates;
return {before: pose(75.5).plates.map(plate => plate.visible), falling: pose(75.9).plates[2], landed: pose(76.077).plates.map(plate => plate.drop),
  pops: [76.08, 76.5].map(time => pose(time).plates[2].pops),
  seats: at81.map(plate => { const centre = plateCentre(plate.place, plate, false), seat = slot(plate.standing, false); return [centre[0] - seat.x, centre[2] - seat.z]; })};""")

TOP_FOUR_LIFT_WITH_JAXONS_NOTCH_THEN_SEAT_FOR_THE_TROPHY_SCRIPT = ("""
const {RISER} = await import(base + '/power-layout.mjs');
return {before: pose(84).plates.map(plate => plate.lift), after: pose(85).plates, wide: pose(86.2).plates, height: RISER.plate.height};""")

REDUCED_MOTION_GIVES_EACH_HITS_END_STATE_ON_ITS_BAR_SCRIPT = ("""
return {before: pose(76, true).plates[2].visible, landed: pose(76.1, true).plates[2], order: [78, 78.1].map(time => pose(time, true).plates[2].shuffle),
  wave: pose(90.8, true).wave, blip: [90, 90.1].map(time => pose(time, true).blip),
  dust: Object.values(pose(88.1, true).impacts), lift: pose(84.1, true).plates[0].lift};""")

TROPHY_RETURNS_HOME_WHEN_THE_FINALE_LETS_IT_GO_SCRIPT = ("""
const THREE = await import('three');
const {makeTrophyRig} = await import(base + '/power-trophy.mjs');
const trophy = new THREE.Group(); trophy.position.set(0, 1.2, 0); trophy.rotation.set(0, .4, 0); trophy.add(new THREE.Object3D());
const read = () => ({visible: trophy.visible, position: trophy.position.toArray(), scale: trophy.scale.toArray(), turn: trophy.rotation.y});
const home = read(), rig = makeTrophyRig(trophy);
rig.pose(pose(89.5).trophy, false); const shown = read();
rig.release(); const released = read();
rig.pose(pose(81).trophy, true); const early = read();
return {home, shown, released, early};""")


def test_the_pose_is_a_pure_function_of_film_time_and_rewinds():
    result = node(CAST + POSE_IS_A_PURE_FUNCTION_OF_FILM_TIME_AND_REWINDS_SCRIPT)
    assert result['same']
    assert result['early'] == [False] * 12                    # seeking back hides every plate again
    assert result['standings'] == [[standing, 0] for standing in STANDINGS]
    assert result['power'] == [1] * 12
    assert result['trophy'] == [True, False, True]           # the trophy leaves the riser across 86.077


def test_all_twelve_plates_land_in_the_standings_on_their_bar():
    result = node(CAST + ALL_TWELVE_PLATES_LAND_IN_THE_STANDINGS_ON_THEIR_BAR_SCRIPT)
    assert result['before'] == [False] * 12
    assert result['falling']['visible'] and result['falling']['drop'] > 0
    assert result['landed'] == [0] * 12
    assert result['pops'][0][2] < .01 and result['pops'][1] == pytest.approx([1, 1, 1])   # the record pops last
    assert [value for seat in result['seats'] for value in seat] == pytest.approx([0] * 24)


PLATE_SHUFFLE_SCRIPT = "\nconst {plateCorners, plateCentre, slot} = await import(base + '/power-layout.mjs');\nconst MOBILE = __MOBILE__, boxes = time => pose(time, false, MOBILE).plates.map(plate => {\n  const corners = plateCorners(plate.place, plate, MOBILE);\n  return [0, 1, 2].map(axis => [Math.min(...corners.map(c => c[axis])), Math.max(...corners.map(c => c[axis]))]); });\nconst hits = [];\nfor (let time = 76.6; time <= 78.1; time += 1 / 60) {\n  const all = boxes(time);\n  all.forEach((a, i) => all.slice(i + 1).forEach((b, k) => {\n    if (a.every((range, axis) => range[0] < b[axis][1] && b[axis][0] < range[1])) hits.push([+time.toFixed(3), i + 1, i + k + 2]); }));\n}\nconst landed = pose(78.077, false, MOBILE).plates;\nreturn {hits, before: pose(76.6).plates.map(plate => plate.shuffle), landed: landed.map(plate => plate.shuffle),\n  seats: landed.map(plate => { const centre = plateCentre(plate.place, plate, MOBILE), seat = slot(plate.place, MOBILE); return [centre[0] - seat.x, centre[2] - seat.z]; }),\n  swap: [78, 78.5].map(time => pose(time).plates.map(plate => plate.swap))};"


@pytest.fixture
def sample_the_shuffle_flies_every_plate_to_its_power_place_without_crossing(mobile):
    result = node(CAST + PLATE_SHUFFLE_SCRIPT.replace('__MOBILE__', json.dumps(mobile)))
    return result,


@pytest.mark.parametrize('mobile', [False, True])
def test_the_shuffle_flies_every_plate_to_its_power_place_without_crossing_1(sample_the_shuffle_flies_every_plate_to_its_power_place_without_crossing, mobile):
    result, = sample_the_shuffle_flies_every_plate_to_its_power_place_without_crossing
    assert result['hits'] == []
    assert result['before'] == [0] * 12 and result['landed'] == [1] * 12
    assert [value for seat in result['seats'] for value in seat] == pytest.approx([0] * 24)
    assert result['swap'][0] == [0] * 12 and result['swap'][1] == pytest.approx([1] * 12)   # all-play pops on landing


def test_the_feature_stamps_show_from_its_bar_to_the_four():
    result = node(CAST + "return [79.9, 80.6, 83.5, 85].map(time => pose(time).stamps);")
    assert result[0] == {'power': 0, 'actual': 0}
    assert result[1] == pytest.approx({'power': 1, 'actual': 1}) and result[2] == pytest.approx({'power': 1, 'actual': 1})
    assert result[3] == {'power': 0, 'actual': 0}


@pytest.fixture
def sample_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy():
    result = node(CAST + TOP_FOUR_LIFT_WITH_JAXONS_NOTCH_THEN_SEAT_FOR_THE_TROPHY_SCRIPT)
    lifts = [plate['lift'] / result['height'] for plate in result['after']]
    return result, lifts


def test_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy_1(sample_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy):
    result, lifts = sample_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy
    assert result['before'] == [0] * 12
    assert lifts[1:4] == pytest.approx([LIFT] * 3)
    assert lifts[0] == pytest.approx(LIFT + NOTCH)
    assert lifts[4:] == [0] * 8


def test_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy_2(sample_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy):
    result, lifts = sample_the_top_four_lift_with_jaxons_notch_then_seat_for_the_trophy
    assert all(plate['light'] == pytest.approx(.4) and plate['sink'] == pytest.approx(.1) for plate in result['after'][4:])
    assert all(plate['light'] == pytest.approx(1) for plate in result['after'][:4])
    assert all(plate['lift'] == 0 and plate['sink'] == 0 and plate['light'] == 1 for plate in result['wide'])


def test_the_trophy_lowers_onto_the_riser_and_lands_on_its_bar():
    result = node(CAST + """
return {heights: [86, 86.2, 87, 88.077, 93.8].map(time => pose(time).trophy), reduced: [88, 88.1].map(time => pose(time, true).trophy)};""")
    early, start, middle, landed, end = result['heights']
    assert not early['visible']
    assert start['visible'] and start['height'] > middle['height'] > 0
    assert landed['visible'] and landed['height'] == 0 and end['height'] == 0
    assert not result['reduced'][0]['visible'] and result['reduced'][1] == pytest.approx({'visible': True, 'height': 0, 'spin': 0})


@pytest.mark.parametrize('mobile', [False, True])
def test_blip_hops_up_the_tiers_to_beside_the_trophy(mobile):
    result = node(CAST + f"""
const {{perch, stairs}} = await import(base + '/power-layout.mjs');
const MOBILE = {json.dumps(mobile)}, at = time => pose(time, false, MOBILE).blip;
return {{hidden: at(85.4).visible, waiting: at(87), air: at(89), landed: at(90.077), later: at(93), perch: perch(MOBILE), start: stairs(MOBILE)[0]}};""")
    assert result['hidden'] is False
    assert result['waiting']['visible'] and result['waiting']['position'] == pytest.approx(result['start'])
    assert result['air']['lift'] > 0
    assert result['landed']['position'] == pytest.approx(result['perch']) and result['later']['position'] == pytest.approx(result['perch'])


@pytest.fixture
def sample_reduced_motion_gives_each_hits_end_state_on_its_bar():
    result = node(CAST + REDUCED_MOTION_GIVES_EACH_HITS_END_STATE_ON_ITS_BAR_SCRIPT)
    return result,


def test_reduced_motion_gives_each_hits_end_state_on_its_bar_1(sample_reduced_motion_gives_each_hits_end_state_on_its_bar):
    result, = sample_reduced_motion_gives_each_hits_end_state_on_its_bar
    assert result['before'] is False
    assert result['landed']['drop'] == 0 and result['landed']['pops'] == [1, 1, 1] and result['landed']['squash'] == 1
    assert result['order'] == [0, 1]
    assert result['wave'] is None and all(blip['lift'] == 0 for blip in result['blip'])


def test_reduced_motion_gives_each_hits_end_state_on_its_bar_2(sample_reduced_motion_gives_each_hits_end_state_on_its_bar):
    result, = sample_reduced_motion_gives_each_hits_end_state_on_its_bar
    assert result['blip'][0]['position'] != result['blip'][1]['position']
    assert all(age < 0 for age in result['dust'])
    assert result['lift'] > 0


@pytest.fixture
def sample_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit():
    result = node(HEADLINES_KEEP_THEIR_WINDOWS_AND_THE_IDENT_LANDS_ON_THE_SONGS_LAST_HIT_SCRIPT)
    return result,


def test_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit_1(sample_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit):
    result, = sample_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit
    assert result['keys'] == ['standings', 'standings', 'head', 'head', 'feature', 'apart', None, 'close', None, None]
    assert result['sub'] == [False, True]
    assert result['reduced']['enter'] == 1
    assert [pose['scale'] for pose in result['ident']] == pytest.approx([1, 1.04, result['ident'][2]['scale'], 1])


def test_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit_2(sample_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit):
    result, = sample_headlines_keep_their_windows_and_the_ident_lands_on_the_songs_last_hit
    assert 1 < result['ident'][2]['scale'] < 1.04
    assert result['ident'][2]['opacity'] == pytest.approx(result['at'])
    assert result['before'] == {'opacity': 0, 'scale': 1}


CAMERA = CAST + """
const THREE = await import('three');
await import(base + '/power-set.mjs');
const {view, frame} = await import(base + '/draft-camera.mjs');
const {filmMoment} = await import(base + '/film.mjs');
const {plateCorners, nameCorners, stampCorners, trophyCorners, perch, stairs, RISER} = await import(base + '/power-layout.mjs');
const MOBILE = DEVICE, size = MOBILE ? {width: 390, height: 844} : {width: 1440, height: 900};
const card = () => ({home: new THREE.Vector3(0, 5, 0), mesh: {position: new THREE.Vector3(0, 5, 0)}});
const featured = Object.fromEntries(['steal', 'traded', 'sleeper', 'curse', 'injury'].map(id => [id, card()]));
const ctx = {mobile: MOBILE, floorZ: 1.9, finaleX: 0, featured, landing: new THREE.Vector3(2, 5, 0), size};
const camera = new THREE.PerspectiveCamera(36, size.width / size.height, .05, 76);
const box = (time, points) => {
  frame(camera, filmMoment(time), ctx); camera.updateMatrixWorld();
  const ndc = points.map(point => new THREE.Vector3(...point).project(camera));
  const ys = ndc.map(point => point.y), xs = ndc.map(point => point.x);
  return {left: Math.min(...xs), right: Math.max(...xs), bottom: Math.min(...ys), top: Math.max(...ys), height: (Math.max(...ys) - Math.min(...ys)) / 2};
};
const posed = time => pose(time, false, MOBILE).plates;
const plates = (time, places) => places.flatMap(place => plateCorners(place, posed(time)[place - 1], MOBILE));
const all = Array.from({length: 12}, (_, index) => index + 1);
"""


def camera(mobile, expression):
    return node(CAMERA.replace('DEVICE', json.dumps(mobile)) + expression)


def inside(frame, margin=0):
    return frame['left'] >= -1 + margin and frame['right'] <= 1 - margin and frame['bottom'] >= -1 + margin and frame['top'] <= 1 - margin


@pytest.mark.parametrize('mobile', [False, True])
def test_every_shot_keeps_its_subjects_whole_inside_the_frame(mobile):
    # 2026-11-05 (standings shuffle, trophy finale): ~~topsix at 82.6, 83.3~~ (no top-six shot: the wide holds over
    # the shuffle); the close frames the trophy and Blip's perch, ~~the file~~.
    result = camera(mobile, EVERY_SHOT_KEEPS_ITS_SUBJECTS_WHOLE_INSIDE_THE_FRAME_SCRIPT)
    for frame in [*result['wide'], *result['four'], *result['close']]:
        assert inside(frame, .02), frame  # honest: allow COND_ASSERT every scripted camera or headline sample must retain its own diagnostic
    for frame in result['feature']:
        assert inside(frame), frame  # honest: allow COND_ASSERT every scripted camera or headline sample must retain its own diagnostic
        assert frame['plate'] >= FRAME_SHARE, frame  # honest: allow COND_ASSERT every scripted camera or headline sample must retain its own diagnostic
    assert all((frame['bottom'] >= -1 + 2 * 0.07) for frame in result['close']), [frame for frame in result['close']]


@pytest.mark.parametrize('mobile', [False, True])
def test_every_plate_name_reads_at_two_percent_of_the_frame(mobile):
    result = camera(mobile, EVERY_PLATE_NAME_READS_AT_TWO_PERCENT_OF_THE_FRAME_SCRIPT)
    assert all((all((height >= NAME_SHARE for height in heights))) for (shot, heights) in result.items()), [(shot, heights) for (shot, heights) in result.items()]


@pytest.mark.parametrize('mobile', [False, True])
def test_the_camera_is_continuous_upright_until_the_closing_hold(mobile):
    result = camera(mobile, CAMERA_IS_CONTINUOUS_UPRIGHT_UNTIL_THE_CLOSING_HOLD_SCRIPT)
    travelling = lambda time: any(start <= time <= end for start, end in TRAVELS)
    steady = [row for row in result['rows'] if not travelling(row['time'])]
    assert max(row['jump'] for row in result['rows']) < .5, max(result['rows'], key=lambda row: row['jump'])
    assert all(edge < .01 for edge in result['edges']), result['edges']
    assert all(abs(row['yaw']) <= YAW_LIMIT for row in steady), max(abs(row['yaw']) for row in steady)
    assert all(row['roll'] == 0 and row['up'] == pytest.approx(1) for row in result['rows'])
    assert all(moved > .005 for moved in result['holds']), result['holds']


# Browser journeys at the three review sizes. Expected copy comes from the storyboard, never from production state.
# 2026-11-05 (standings shuffle): 79.5 reads "Standings.", ~~"Power rankings." / "All-play, Weeks 1-8"~~.
EXPECTED = {75.5: ('Standings.', None), 79: ('Power rankings.', 'All-play, Weeks 1-8'),
            81: ('Power rankings.', 'All-play, Weeks 1-8'), 83: ('Better than the record.', None),
            85: ('One all-play win apart.', None), 87: (None, None), 89.5: ("Still anyone's game.", None), 93.8: (None, None)}


@pytest.fixture(params=[(1440, 900), (390, 844), (360, 800)])
def power_film(browser, request):
    film = PowerFilm(browser, *request.param)
    with film:
        film.load()
        yield film


@pytest.mark.journey
def test_each_seek_shows_its_headline_upright_and_readable(power_film):
    for time, (head, sub) in EXPECTED.items():
        power_film.seek(time)
        shown = power_film.headline()
        assert shown['head'] == head and shown['sub'] == sub, (time, shown)  # honest: allow COND_ASSERT every scripted camera or headline sample must retain its own diagnostic
        if head:
            assert shown['within'] and shown['capHeight'] >= power_film.height * .02 - .5, (time, shown)  # honest: allow COND_ASSERT every scripted camera or headline sample must retain its own diagnostic
            assert shown['upright'], (time, shown)  # honest: allow COND_ASSERT every scripted camera or headline sample must retain its own diagnostic
    assert power_film.errors == []


@pytest.mark.journey
def test_reverse_seek_restores_the_earlier_headlines_and_hides_the_ident(power_film):
    for time in [93.8, 81, 75.5]:
        power_film.seek(time)
    assert power_film.headline()['head'] == 'Standings.'
    assert power_film.ident() == 'hidden'
    power_film.seek(93.8)
    assert power_film.ident() == 'visible'
    power_film.seek(81)
    assert power_film.ident() == 'hidden'
    assert power_film.errors == []


@pytest.mark.journey
def test_reduced_motion_keeps_the_headline_windows(browser):
    film = PowerFilm(browser, 390, 844, reduced=True)
    with film:
        film.load()
        film.seek(83)
        assert film.headline()['head'] == 'Better than the record.'
        film.seek(89.5)
        assert film.headline()['head'] == "Still anyone's game."
        film.seek(75.5)
        assert film.headline()['head'] == 'Standings.' and film.errors == []


@pytest.mark.journey
def test_play_waits_for_the_badges(browser):
    film = PowerFilm(browser, 390, 844)
    with film:
        film.load_with_delayed_badge()
        assert film.errors == []


@pytest.mark.journey
def test_a_failed_badge_drops_the_prepared_room_and_disables_play(browser):
    film = PowerFilm(browser, 390, 844)
    with film:
        assert film.fail_badge() == {'canvas': 0, 'headline': 0, 'phase': 'fallback'}
        expect(film.page.locator('[data-play]')).to_be_disabled()
        assert film.errors == []


@pytest.mark.journey
def test_pagehide_removes_the_riser_headline_and_canvas(power_film):
    power_film.seek(89.5)
    power_film.page.evaluate("window.dispatchEvent(new Event('pagehide'))")
    assert power_film.page.locator('[data-power]').count() == 0
    assert power_film.page.locator('[data-viewport] canvas').count() == 0
    assert power_film.errors == []


def test_the_trophy_returns_home_when_the_finale_lets_it_go():
    """The finale borrows the opening's trophy (scene.mjs createRoom); letting go puts it back where the opening
    stood it, hidden, so a seek before 84.077 or into Chapters 1-4 never shows it on the riser."""
    result = node(CAST + TROPHY_RETURNS_HOME_WHEN_THE_FINALE_LETS_IT_GO_SCRIPT)
    home = result['home']
    assert result['shown']['visible'] and result['shown']['scale'][0] < home['scale'][0]
    assert result['shown']['position'] != home['position']
    assert result['released'] == {**home, 'visible': False}
    assert result['early'] == {**home, 'visible': False}
