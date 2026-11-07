"""The Godwin joke gets flames; an injury is the card cut cleanly in half and fading; every stop of
the Godwin trail and every week light is big and whole inside the frame (docs/madden-film-rules.md)."""
import json
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "showcase/madden-curse"
HOOKS = """
import {registerHooks} from "node:module";
const base = BASE;
registerHooks({resolve(specifier, context, next) {
  return next(specifier === "three" ? base + "/vendor/three.module.js" : specifier, context);
}});
const THREE = await import("three");
""".replace("BASE", json.dumps(SOURCE.as_uri()))


PAYOFF_FRAMES_THE_AVATAR_AND_ALL_TEN_ROUNDS_SCRIPT = ("""
const {shot} = await import(base + "/draft-camera.mjs");
const {boardTop, rowY, CARD_HEIGHT} = await import(base + "/draft-board.mjs");
const ctx = {mobile: MOBILE, finaleX: 0, featured: {injury: {home: new THREE.Vector3()}}};
const view = shot("finale", 10, ctx);
const camera = new THREE.PerspectiveCamera(FOV, ASPECT, .05, 80);
camera.position.copy(view.position); camera.lookAt(view.target); camera.updateMatrixWorld();
const avatar = new THREE.Vector3(0, boardTop() + .45, .035).project(camera);
const bottom = new THREE.Vector3(0, rowY(9) - CARD_HEIGHT / 2, .035).project(camera);
console.log(JSON.stringify({top: (1 - avatar.y) / 2, bottom: (1 - bottom.y) / 2}));
""")


def node(script):
    result = subprocess.run(["node", "--input-type=module", "-e", HOOKS + script],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


TREATMENT_SCRIPT = """

const {injury, curse, INJURY} = await import(base + "/draft-curse.mjs");
const {cutHalves} = await import(base + "/draft-props.mjs");
const flameCalls = [];
const faces = Array.from({length: 6}, () => new THREE.MeshBasicMaterial());
const status = new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial({transparent: true}));
const item = {mesh: new THREE.Mesh(new THREE.BoxGeometry(), faces), home: new THREE.Vector3(), front: faces[4],
  pick: {weeks: ["solid", "solid", "bust", "out", "out", "out", "out", "out"]},
  props: {root: new THREE.Group(), stampZ: .03, status, lights: Object.assign(new THREE.Group(), {userData: {set() {}}}),
    flame: {update(...args) {flameCalls.push(args);}}}};
const pieces = cutHalves(new THREE.Texture());
const end = INJURY.cut + 3;
const frames = [0, .4, INJURY.cut - .05, INJURY.cut + .2, end, 0, end].map(seconds => {
  injury(seconds, item, pieces);
  return {card: faces.every(face => face.visible), halves: pieces.map(piece => piece.visible && piece.material.opacity > 0),
    opacity: pieces.map(piece => +piece.material.opacity.toFixed(3)),
    gap: +(pieces[0].position.y - pieces[1].position.y).toFixed(4), position: item.mesh.position.toArray()};
});
const stations = {first: {kind: "lineup", x: 0, z: 1}, last: {kind: "lineup", x: 1, z: 2}};
const steps = [{station: "first", kind: "start"}, {station: "last", kind: "start"}];
const blip = {home: new THREE.Vector3(), position: new THREE.Vector3()};
const tile = new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial());
[0, .2, .4, 1, 2, 3, 5].forEach(seconds => curse(seconds, item, stations, steps, blip, tile));
console.log(JSON.stringify({frames, flameCalls}));
"""


@pytest.fixture(scope="module")
def treatment():
    return node(TREATMENT_SCRIPT)


@pytest.mark.parametrize("frame_index", range(3))
def test_the_injured_card_stays_whole_until_the_cut(treatment, frame_index):
    frame = treatment["frames"][frame_index]
    assert frame["card"] and frame["halves"] == [False, False]


def test_the_cut_leaves_two_halves_that_part_and_fade(treatment):
    cut, end = treatment["frames"][3], treatment["frames"][4]
    assert not cut["card"] and cut["halves"] == [True, True]
    assert end["halves"] == [False, False]
    assert end["gap"] > cut["gap"]


def test_injury_card_restores_the_same_pose_when_seeking_backward(treatment):
    assert treatment["frames"][0] == treatment["frames"][5]
    assert treatment["frames"][4] == treatment["frames"][6]


def test_godwin_flames_follow_the_motion_clock(treatment):
    assert [call[0] for call in treatment["flameCalls"]] == [0, .2, .4, 1, 2, 3, 5]
    # Rev 14 storyboard: the card catches fire as it drops onto WARREN-TY's pad, on the first landing (0.5 s).
    assert all(call[1] == 0 for call in treatment["flameCalls"][:3])
    assert all(call[1] > 0 for call in treatment["flameCalls"][3:])


FRAMING = """
const {frame, RIG} = await import(base + "/draft-camera.mjs");
const {filmPlan} = await import(base + "/film.mjs");
const {CARD_HEIGHT, BOARD} = await import(base + "/draft-board.mjs");
const {PROPS} = await import(base + "/draft-props.mjs");
const {CURSE} = await import(base + "/draft-curse.mjs");
const {STEAL} = await import(base + "/draft-beats.mjs");
const {FLOOR} = await import(base + "/draft-floor.mjs");
const {filmMoment} = await import(base + "/film.mjs");
const [width, height] = SIZE, mobile = width < 640;
const camera = new THREE.PerspectiveCamera(mobile ? 44 : 36, width / height, .05, 80);
const card = position => ({home: position.clone(), mesh: {position: position.clone()}});
const project = (camera, point) => { const p = point.clone().project(camera); return [(p.x + 1) / 2, (1 - p.y) / 2]; };
const look = seconds => {
  const moment = filmMoment(seconds), featured = {};
  ["steal", "traded", "sleeper", "curse", "injury"].forEach(id => { featured[id] = card(new THREE.Vector3(0, 5, 0)); });
  return {moment, featured};
};
"""


EDITION_PATH = json.loads((SOURCE / "edition.json").read_text(encoding="utf-8"))["draft"]["beats"]["curse"]["path"]


WIDE_SCRIPT = """
const {stationLayout, trailStops} = await import(base + "/draft-floor.mjs");
const {TRAIL} = await import(base + "/constants.mjs");
const steps = trailStops(PATH), placed = stationLayout(steps, mobile), end = placed.find(entry => entry.key === steps.at(-1).station);
const shown = placed.filter(entry => entry !== end).map(entry => entry.x);
const trail = {left: Math.min(...shown), right: Math.max(...shown), reveal: end.x};
const beat = filmPlan().beats.find(beat => beat.id === "curse");
const stand = CARD_HEIGHT / 2 + PROPS.padHeight, bar = RIG.ruleLine[mobile ? 'phone' : 'desk'] - RIG.gap;
const measure = (seconds, stations) => {
  const {moment, featured} = look(beat.start + seconds * beat.pace);
  frame(camera, moment, {featured, mobile, floorZ: FLOOR.z, trail, size: {width, height}, landing: new THREE.Vector3()});
  camera.updateMatrixWorld(); camera.updateProjectionMatrix();
  return stations.map(({x}) => {
    const z = FLOOR.z, avatar = new THREE.Vector3(x + PROPS.avatarSide, PROPS.avatarHeight, z);
    const top = project(camera, avatar.clone().setY(avatar.y + PROPS.avatar)), bottom = project(camera, avatar.clone().setY(avatar.y - PROPS.avatar));
    const left = project(camera, new THREE.Vector3(x + PROPS.avatarSide - PROPS.nameWidth / 2, PROPS.nameHeight, z));
    const right = project(camera, new THREE.Vector3(x + BOARD.card / 2, stand + CARD_HEIGHT / 2, z));
    const word = project(camera, new THREE.Vector3(x + PROPS.labelWidth / 2, PROPS.labelLift, z + PROPS.pad + PROPS.labelAhead));
    return {avatar: bottom[1] - top[1], left: left[0], right: right[0], top: Math.min(top[1], right[1]), word: word[1], bar};
  });
};
const wide = placed.filter(entry => entry !== end);
console.log(JSON.stringify({wide: CURSE.landings.slice(0, -1).flatMap(landing => measure(landing + .3, wide)),
  reveal: measure(TRAIL.flip, [end]), stations: placed.length}));
"""

LIGHT_SCRIPT = """
const {steal} = await import(base + "/draft-beats.mjs");
const {weekLights} = await import(base + "/draft-props.mjs");
const beat = filmPlan().beats.find(beat => beat.id === "steal");
const {moment, featured} = look(beat.start + 2.5 * beat.pace);
const mesh = new THREE.Group(), lights = weekLights(8);
lights.userData.set = () => {};   // the tiles draw on a canvas, which Node has not got; only their size is measured
mesh.add(lights);
const item = {mesh, home: featured.steal.home, pick: {weeks: Array(8).fill("smash")},
  props: {stampZ: .03, lights, stamp: new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial())}};
steal(2.5, item, {position: new THREE.Vector3()});
featured.steal = item;
frame(camera, moment, {featured, mobile, size: {width, height}, landing: new THREE.Vector3()});
camera.updateMatrixWorld(); camera.updateProjectionMatrix(); mesh.updateMatrixWorld(true);
const light = lights.children[0], centre = light.getWorldPosition(new THREE.Vector3());
const top = project(camera, centre.clone().setY(centre.y + PROPS.lightHeight / 2));
const bottom = project(camera, centre.clone().setY(centre.y - PROPS.lightHeight / 2));
const first = project(camera, lights.children[0].getWorldPosition(new THREE.Vector3()));
const last = project(camera, lights.children[7].getWorldPosition(new THREE.Vector3()));
const foot = lights.children[7].getWorldPosition(new THREE.Vector3());
const low = project(camera, foot.setY(foot.y - PROPS.lightHeight / 2));
console.log(JSON.stringify({height: bottom[1] - top[1], first: first[0], last: last[0], low: low[1], bar: RIG.ruleLine[mobile ? 'phone' : 'desk'] - RIG.gap}));
"""


@pytest.fixture(scope='module', params=[(1920, 1080), (390, 844)])
def broadcast_framing(request):
    script = WIDE_SCRIPT.replace('PATH', json.dumps(EDITION_PATH))
    return node(FRAMING.replace('SIZE', json.dumps(request.param)) + script)


def test_the_godwin_trail_keeps_all_three_stations_and_all_nine_sampled_stops(broadcast_framing):
    assert broadcast_framing['stations'] == 3
    assert len(broadcast_framing['wide']) == 8
    assert len(broadcast_framing['reveal']) == 1


@pytest.mark.parametrize('stop_index', range(9))
def test_both_wide_stops_and_cookeds_reveal_sit_whole_in_frame(broadcast_framing, stop_index):
    stop = (broadcast_framing['wide'] + broadcast_framing['reveal'])[stop_index]
    assert 0 < stop['left'] and stop['right'] < 1 and 0 < stop['top'], stop
    assert stop['word'] < stop['bar'], "The stop's word stays clear above the lower-third rule (rule 23)"


def test_the_wide_avatars_are_large_and_cookeds_reveal_is_larger_and_centered(broadcast_framing):
    assert all(stop['avatar'] >= .05 for stop in broadcast_framing['wide'])
    reveal = broadcast_framing['reveal'][0]
    assert reveal['avatar'] >= .1
    assert abs((reveal['left'] + reveal['right']) / 2 - .5) < .1


@pytest.fixture(scope='module', params=[(1920, 1080), (390, 844)])
def week_framing(request):
    return node(FRAMING.replace('SIZE', json.dumps(request.param)) + LIGHT_SCRIPT)


def test_a_week_light_is_at_least_four_percent_of_the_frame(week_framing):
    assert week_framing['height'] >= .04
    assert 0 < week_framing['first'] and week_framing['last'] < 1
    assert week_framing['low'] < week_framing['bar'], 'Both rows stay clear of the lower-third rule (rule 23)'


@pytest.mark.parametrize('week_framing', [(1920, 1080)], indirect=True)
def test_the_desktop_week_lights_are_centered(week_framing):
    assert abs((week_framing['first'] + week_framing['last']) / 2 - .5) < .1


@pytest.mark.parametrize('mobile,fov,aspect', [(True, 44, 390 / 844), (False, 36, 1920 / 1000)])
def test_payoff_frames_the_avatar_and_all_ten_rounds(mobile, fov, aspect):
    frame = node(PAYOFF_FRAMES_THE_AVATAR_AND_ALL_TEN_ROUNDS_SCRIPT.replace('MOBILE', json.dumps(mobile)).replace('FOV', str(fov)).replace('ASPECT', str(aspect)))
    assert .02 < frame["top"] < .15, "The avatar must remain inside the full-column frame"
    assert .85 < frame["bottom"] < .98, "Round ten must remain onscreen near the foot of the frame"
    assert frame["bottom"] - frame["top"] > .75, "The column must use the available vertical space"
