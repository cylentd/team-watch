import pytest

from test_madden_stage_polish import stage_result


FIVE_GODWIN_STOPS_LAND_ON_THE_STORYBOARD_AND_MOVE_QUICKLY_SCRIPT = ("""
const {CURSE} = await import(base + '/draft-curse.mjs');
const {FILM, TRAIL} = await import(base + '/constants.mjs');
const beat = FILM.beats.find(beat => beat.id === 'curse'), landings = CURSE.landings;
const leaves = [...landings.slice(1, -1).map(time => time - CURSE.move), CURSE.leap];
return {holds: leaves.map((time, index) => (time - landings[index]) * beat.pace), move: CURSE.move * beat.pace,
  landings, remaining: beat.duration - CURSE.flip[1] * beat.pace};
""")

ACHANE_CARD_IS_CUT_CLEANLY_IN_TWO_TEXTURED_HALVES_SCRIPT = ("""
const {cutHalves} = await import(base + '/draft-props.mjs');
const {CARD_HEIGHT} = await import(base + '/draft-board.mjs');
const texture = new THREE.Texture();
const pieces = cutHalves(texture);
const ys = piece => piece.geometry.attributes.position.array.filter((_, index) => index % 3 === 1);
return {count: pieces.length, textured: pieces.every(piece => piece.material.map === texture),
  top: Math.max(...ys(pieces[0])), topLow: Math.min(...ys(pieces[0])),
  bottom: Math.min(...ys(pieces[1])), bottomHigh: Math.max(...ys(pieces[1])), half: CARD_HEIGHT / 2};
""")

BLIP_FINISHES_HIS_HOP_ON_THE_BOARD_RAIL_SCRIPT = ("""
const {steal} = await import(base + '/draft-beats.mjs');
const {BOARD} = await import(base + '/draft-board.mjs');
const mesh = new THREE.Group(), home = new THREE.Vector3(0, 5, 0);
const item = {mesh, home, pick: {weeks: []}, props: {stampZ: .03,
  stamp: new THREE.Mesh(new THREE.PlaneGeometry(), new THREE.MeshBasicMaterial()), lights: {userData: {set() {}}}}};
const blip = {position: new THREE.Vector3()};
steal(3, item, blip);
return {height: blip.position.y, rail: home.y - BOARD.pitchY / 2, depth: blip.position.z};
""")

INTRO_BLIP_IS_FULLY_IN_FRONT_OF_THE_TROPHY_PLINTH_SCRIPT = ("""
const {placeBlip} = await import(base + '/scene.mjs');
const {STAGE} = await import(base + '/environment.mjs');
const blip = {root: new THREE.Group()};
placeBlip(blip, -.92, 0, {lift: 0, squash: 1});
return {height: blip.root.position.y, depth: blip.root.position.z, radius: STAGE.radius};
""")

PHONE_WIDE_HOLDS_STILL_WHILE_THE_CARD_HOPS_SCRIPT = ("""
const {shot} = await import(base + '/draft-camera.mjs');
const card = {mesh: {position: new THREE.Vector3(.95, .36, .75)}, home: new THREE.Vector3(0, 5, 0)};
const at = (time, x) => { card.mesh.position.x = x; return shot('curse', time, {mobile: true, floorZ: 1.9, featured: {curse: card}}); };
const a = at(1.6, -.7), b = at(4.1, .7);   // from the first landing (1.5, rev 16b)
return {moved: a.position.distanceTo(b.position) + a.target.distanceTo(b.target)};
""")

FINALE_PULSES_ONE_COLUMN_WITHOUT_A_PER_PLAYER_TINT_DIRECTIVE_SCRIPT = ("""
const {finale} = await import(base + '/draft-curse.mjs');
const header = {disc: new THREE.Group(), home: 9};
const board = {headers: new Map([[1, header]]), glow: {material: {opacity: 0}}};
const tint = finale(1.5, board, 1), first = board.glow.material.opacity;
finale(1.9, board, 1);
return {directive: typeof tint, first, next: board.glow.material.opacity};
""")


def test_five_godwin_stops_land_on_the_storyboard_and_move_quickly():
    timing = stage_result(FIVE_GODWIN_STOPS_LAND_ON_THE_STORYBOARD_AND_MOVE_QUICKLY_SCRIPT)
    # Rev 14 storyboard, re-locked to the onsets a bar later (rev 16b): one stop a second from 1.5 s.
    # ~~1, 2, 3.5, 4.5, 5.37~~ (rev 15).
    # David option A (2026-11-05): COOKed lands on the 34.077 kick. ~~COOKed 5.5~~ (rev 17).
    assert timing['landings'] == [0.5, 1.5, 2.5, 3.5, 5.223]
    assert all(.3 <= hold <= 1.5 for hold in timing['holds']), timing['holds']
    assert timing['move'] == pytest.approx(.4)
    # David option A (2026-11-05): the 0.0 lands on the 34.565 onset (film 34.577) and reads for 1.5 s, the last
    # frame cut on the bar line. ~~2 s~~ (rev 17); ~~2.5-3 s~~ (rev 15).
    assert timing['remaining'] == pytest.approx(2.496)


def test_achane_card_is_cut_cleanly_in_two_textured_halves():
    cut = stage_result(ACHANE_CARD_IS_CUT_CLEANLY_IN_TWO_TEXTURED_HALVES_SCRIPT)
    assert cut['count'] == 2
    assert cut['textured']
    assert cut['top'] == pytest.approx(cut['half'])
    assert cut['bottom'] == pytest.approx(-cut['half'])
    # The cut runs through the middle of the card, so each piece is about half of it.
    assert abs(cut['topLow']) < .1 and abs(cut['bottomHigh']) < .1


def test_blip_finishes_his_hop_on_the_board_rail():
    result = stage_result(BLIP_FINISHES_HIS_HOP_ON_THE_BOARD_RAIL_SCRIPT)
    assert abs(result['height'] - result['rail']) < .025
    assert result['depth'] < .2


def test_intro_blip_is_fully_in_front_of_the_trophy_plinth():
    result = stage_result(INTRO_BLIP_IS_FULLY_IN_FRONT_OF_THE_TROPHY_PLINTH_SCRIPT)
    assert result['height'] == 0
    assert result['depth'] > result['radius'] + .2

def test_phone_wide_holds_still_while_the_card_hops():
    result = stage_result(PHONE_WIDE_HOLDS_STILL_WHILE_THE_CARD_HOPS_SCRIPT)
    assert result['moved'] < 1e-9                                         # rev 14: no per-stop moves


def test_finale_pulses_one_column_without_a_per_player_tint_directive():
    result = stage_result(FINALE_PULSES_ONE_COLUMN_WITHOUT_A_PER_PLAYER_TINT_DIRECTIVE_SCRIPT)
    assert result['directive'] == 'undefined'
    assert result['first'] > 0 and result['next'] > 0
    assert result['first'] != result['next']

