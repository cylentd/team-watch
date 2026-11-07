import pytest
from component import mount
from test_madden_stage_polish import stage_result
from test_madden_headline_entrance import headline_page, seek


MOBILE_PASS_CROSSES_MORE_ROUNDS_AND_LIGHTS_THE_VISIBLE_CORRIDOR_SCRIPT = ("""
const {ESTABLISH,passLook} = await import(base + '/draft-establish.mjs');
const {makePathBeams} = await import(base + '/draft-path-beams.mjs');
const {BOARD,rowY,columnX} = await import(base + '/draft-board.mjs');
const cards = new Map(Array.from({length:120}, (_, index) => [index,
 {pick:{pos:'WR'},home:new THREE.Vector3(columnX(index%12),rowY(Math.floor(index/12)),0)}]));
const beams=makePathBeams(cards); beams.update(2,true);
const active=beams.group.children.filter(mesh=>mesh.visible && mesh.material.uniforms.strength.value>.15);
const aim=passLook(2,true);
return {reach:ESTABLISH.reach.phone,active:active.map(mesh=>({along:mesh.position.y,height:mesh.geometry.parameters.height*mesh.scale.z})),aim:aim.along};
""")

MOBILE_SUSPENSE_MOVES_FROM_THE_FULL_BOARD_TO_THE_WINNER_ON_THE_REVEAL_SCRIPT = ("""
const {frame} = await import(base + '/draft-camera.mjs');
const {filmMoment} = await import(base + '/film.mjs');
const {BOARD,columnX,rowY,boardTop} = await import(base + '/draft-board.mjs');
const ctx={mobile:true,size:{width:360,height:800},finaleX:columnX(4),
 featured:{injury:{home:new THREE.Vector3(columnX(8),rowY(1),0)}}};
return [39,39.8,40.077].map(time=>{
 const camera=new THREE.PerspectiveCamera(44,360/800,.1,100);
 frame(camera,filmMoment(time),ctx);camera.updateMatrixWorld();
 return {shift:camera.view.offsetX,points:[columnX(0),columnX(11)].flatMap(x=>
 [rowY(9),boardTop()].map(y=>new THREE.Vector3(x,y,0).project(camera).toArray()))};
});
""")

MOBILE_REVEAL_CONTAINS_EVERY_COLUMN_AND_ROUND_SCRIPT = ("""
const {frame} = await import(base + '/draft-camera.mjs');
const {filmMoment} = await import(base + '/film.mjs');
const {BOARD, CARD_HEIGHT, columnX, rowY, boardTop} = await import(base + '/draft-board.mjs');
const camera = new THREE.PerspectiveCamera(44, VIEW_WIDTH / VIEW_HEIGHT, .1, 100);
const ctx = {mobile:true, size:{width:VIEW_WIDTH,height:VIEW_HEIGHT}, featured:{}};
frame(camera, filmMoment(14), ctx); camera.updateMatrixWorld();
return [columnX(0)-BOARD.card/2, columnX(11)+BOARD.card/2].flatMap(x =>
 [rowY(9)-CARD_HEIGHT/2,boardTop()+BOARD.avatar].map(y => new THREE.Vector3(x,y,0).project(camera).toArray()));
""")


@pytest.mark.parametrize('width,height', [(360, 800), (390, 844), (430, 932)])
def test_mobile_reveal_contains_every_column_and_round(width, height):
    result = stage_result(MOBILE_REVEAL_CONTAINS_EVERY_COLUMN_AND_ROUND_SCRIPT.replace('VIEW_WIDTH', str(width)).replace('VIEW_HEIGHT', str(height)))
    assert all(-.94 <= point[0] <= .94 for point in result)
    assert all(-.24 <= point[1] <= .94 for point in result)


def test_mobile_pass_crosses_more_rounds_and_lights_the_visible_corridor():
    result = stage_result(MOBILE_PASS_CROSSES_MORE_ROUNDS_AND_LIGHTS_THE_VISIBLE_CORRIDOR_SCRIPT)
    assert result['reach'] >= 4.5
    assert result['active']
    assert any(beam['along'] < result['aim'] - .5 and beam['height'] > 2 for beam in result['active'])


def test_mobile_suspense_moves_from_the_full_board_to_the_winner_on_the_reveal():
    result = stage_result(MOBILE_SUSPENSE_MOVES_FROM_THE_FULL_BOARD_TO_THE_WINNER_ON_THE_REVEAL_SCRIPT)
    assert result[0]['shift'] == 0
    assert result[2]['shift'] < result[1]['shift'] < result[0]['shift']
    assert all(-1 < point[0] < 1 and -.3 < point[1] < 1 for point in result[0]['points'])


@pytest.mark.parametrize('width,height', [(360, 800), (390, 844), (1440, 900)])
def test_verdict_headline_precedes_the_returns_without_overlap(headline_page, width, height):
    headline_page.set_viewport_size({'width': width, 'height': height})
    seek(headline_page, 43)
    head = headline_page.locator('[data-receipt-head]').bounding_box()
    details = headline_page.locator('.receipt-returns').bounding_box()
    assert head['y'] >= 0
    assert head['y'] + head['height'] < details['y']
    assert details['y'] + details['height'] < height - 40
