"""Approved Chapter 4: three non-positive DEF starts, then W5/W8's TE reversal, on the 3D lineup desk
(docs/madden-film-chapter4.md, "Cinematic revision", David 2026-11-05)."""
import json

import pytest
from playwright.sync_api import expect

from test_madden_chapter2 import node
from test_madden_rev8 import CAMERA
from test_madden_stage_polish import stage_result
from pages.madden_lineups_set import LineupsSetFilm, PORTRAITS


DATA = "const {checkLineups, lineupValues} = await import(base + '/lineups-data.mjs'); const raw = JSON.parse((await import('node:fs')).readFileSync(new URL('lineups-receipts.json', base + '/'), 'utf8')); "
POSE = DATA + "const {lineupsPose} = await import(base + '/lineups-pose.mjs'); const cast = lineupValues(checkLineups(raw)); "
FRAME = 1 / 30          # music-onsets.mjs SYNC.fps
START = 58.077          # lineup-defense's bar line: chapter second 0
LANDINGS = [1, 4]
SECOND = 8              # lineup-tightends' bar line on the chapter clock


BLIP_HOPS_OVER_AND_PEEKS_INTO_THE_SLOT_AFTER_CHIEFS_SCRIPT = ("const {places} = await import(base + '/lineups-layout.mjs'); return [false, true].map(m => ({place: places(m),"
                  " before: lineupsPose(4.2, false, cast, m).blip, hop: lineupsPose(4.5, false, cast, m).blip, peek: lineupsPose(5.4, false, cast, m).blip,"
                  " tight: lineupsPose(9, false, cast, m).blip}));")

EACH_HELD_SHOT_FRAMES_ITS_FEATURE_WHOLE_AND_BIG_SCRIPT = ("""
return SHOTS.map(entry => {
  frame(camera, filmMoment(entry.time), {...ctx, size}); camera.updateMatrixWorld();
  const feature = project(entry.feature), whole = project([...entry.feature, ...entry.whole]);
  const ys = feature.map(point => point.y);
  return {time: entry.time, ensemble: Boolean(entry.ensemble), share: (Math.max(...ys) - Math.min(...ys)) / 2,
    inside: whole.every(point => Math.abs(point.x) <= 1 && point.y <= 1 && point.y >= -1 + 2 * CLEAR.bottom),
    clear: project(entry.whole).filter(point => point.y > 1 - 2 * CLEAR.top).length};
});
""")

CAMERA_NEVER_JUMPS_ROLLS_OR_YAWS_MORE_THAN_THREE_DEGREES_SCRIPT = ("""
await import(base + '/lineups-set.mjs');
const whips = [[57.677, 58.477], [65.677, 66.477]], step = 1 / 30, samples = [];
let before = null;
for (let time = 57.7; time < 73.6; time += step) {
  const shot = view(filmMoment(time), ctx), arm = shot.position.clone().sub(shot.target);
  const jump = before ? shot.position.distanceTo(before) : 0;
  samples.push({time, roll: shot.roll, up: shot.up ? shot.up.toArray() : [0, 1, 0], yaw: Math.abs(Math.atan2(arm.x, arm.z)) * 180 / Math.PI,
    jump, whip: whips.some(([from, to]) => time >= from && time <= to + step)});
  before = shot.position.clone();
}
const seams = [58.477, 63.6, 64.077, 67.477, 68.077, 69.477, 70.077, 71.477, 72.077].map(time =>
  view(filmMoment(time - 1e-4), ctx).position.distanceTo(view(filmMoment(time + 1e-4), ctx).position));
return {samples, seams};
""")


def test_lineup_chapter_appends_twenty_four_seconds_preserving_earlier_placements():
    plan = node("return (await import(base + '/film.mjs')).filmPlan();")
    selected = [beat for beat in plan['beats'] if beat.get('chapter') == 4]
    # 2026-11-05 (ch4/5 cinematic): ~~12, 12~~; ~~62.077, 74.077~~; ~~106.077~~ (David approved the 16 s 3D desk).
    assert [(beat['id'], beat['duration']) for beat in selected] == [('lineup-defense', 8), ('lineup-tightends', 8)]
    assert [beat['start'] for beat in selected] == pytest.approx([58.077, 66.077])
    assert plan['duration'] == pytest.approx(98.077)   # 2026-11-05 (Chapter 5): ~~86.077~~.
    assert [beat['start'] for beat in plan['beats'][:10]] == pytest.approx([7.584, 16.077, 20.077, 24.077, 28.077, 36.077, 40.077, 44.077, 50.077, 56.077])


def test_lineup_impacts_keep_bar_lines_and_one_half_bar_entrance_without_a_second_scene_wipe():
    result = node("const {sceneChanges} = await import(base + '/film.mjs'); const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs'); return {changes:sceneChanges().slice(-4,-2),hits:filmImpacts().filter(hit=>hit.at>=58&&hit.at<74).map(hit=>({...hit,reference:nearestHit(hit.at)}))};")
    # 2026-11-05 (Chapter 5): the probe stops before the power beats (~~slice(-2)~~, ~~no upper bound~~ on the hits).
    assert [(change['to'], change['kind']) for change in result['changes']] == [('lineup-defense', 'across'), ('lineup-tightends', 'travel')]
    # 2026-11-05 (ch4/5 cinematic): ~~below 86~~; a hit on every bar from 62.077, and one swap at 74.077 replaces
    # ~~'Week 8 switch begins': 80.077, 'Week 8 starter result': 82.077~~ (old: Saints 66.077 ... W8 bench 84.077).
    assert {hit['name']: hit['at'] for hit in result['hits']} == pytest.approx({'Cut to lineup-defense': 58.077, 'Saints deduction': 59.077, 'Saints win': 60.077, 'Raiders deduction': 62.077, 'Negative-week wins': 64.077, 'Cut to lineup-tightends': 66.077, 'Week 5 starters settle': 66.077, 'Week 5 bench result': 68.077, 'Week 8 swap lands': 70.077, 'Week 8 bench result': 72.077})
    assert all(hit['reference']['kind'] == ('beat' if hit['name'] == 'Saints deduction' else 'downbeat') and abs(hit['reference']['frames']) <= 2 for hit in result['hits'])


def test_historical_starts_and_bench_scores_are_kept_distinct():
    result = node(DATA + "return {raw,values:lineupValues(checkLineups(raw))};")
    assert result['raw']['through'] == 8 and result['raw']['season'] == 2026
    assert [(row['week'], row['starter']['name'], row['starter']['points']) for row in result['raw']['defense']] == [(1, 'Rams', 2), (2, 'Chiefs', 1), (3, 'Chiefs', 8), (4, 'Saints', -3), (5, 'Raiders', -1), (6, 'Chiefs', 15), (7, 'Chiefs', 3), (8, 'Chiefs', 0)]
    assert [(row['week'], row['starter']['points'], row['bench']['points']) for row in result['raw']['tightends']] == [(5, .9, 11.9), (7, 10.6, 10.1), (8, 4.5, 18.4)]
    assert result['values']['defenseTotal'] == 25 and result['values']['negativeWins'] == 2
    assert [entry['score'] for entry in result['values']['defense']] == ['−3', '−1']
    assert [(row['starter']['name'], row['bench']['name']) for row in result['values']['tightends']] == [('H. Fannin Jr.', 'H. Henry'), ('H. Henry', 'H. Fannin Jr.')]


@pytest.mark.parametrize('mutation', ["raw.defense[0].starter.points=null", "raw.defense[0].team=11", "raw.defense[0].slot='BN'", "raw.defense.push(raw.defense[0])", "raw.defense[1].week=1", "raw.tightends[0].bench.points='11.9'", "raw.tightends[0].starter.position='WR'", "raw.tightends[0].bench.name='Someone Else'", "raw.tightends.pop()", "raw.through=9"])
def test_receipt_contract_rejects_invalid_or_misassigned_rows(mutation):
    result = node(DATA + mutation + "; try {checkLineups(raw); return null;} catch(error) {return {name:error.name,message:error.message};}")
    assert result['name'] == 'Error' and result['message'].startswith('Invalid lineup receipts:')


def test_defense_outcomes_are_derived_instead_of_hardcoded():
    result = node(DATA + "raw.defense[3].points=70; return lineupValues(checkLineups(raw));")
    assert result['negativeWins'] == 1
    assert result['outcome'] == 'Won 1 negative week.'


@pytest.fixture
def sample_pose_is_pure_and_a_reverse_seek_hides_everything_later(mobile):
    result = node(POSE + f"const m = {json.dumps(mobile)}; const first = lineupsPose(1, false, cast, m); lineupsPose(15.5, false, cast, m); lineupsPose(12.3, true, cast, m);"
                  " return {first, again: lineupsPose(1, false, cast, m), early: lineupsPose(-.5, false, cast, m)};")
    return result,


@pytest.mark.parametrize('mobile', [False, True])
def test_pose_is_pure_and_a_reverse_seek_hides_everything_later_1(sample_pose_is_pure_and_a_reverse_seek_hides_everything_later, mobile):
    result, = sample_pose_is_pure_and_a_reverse_seek_hides_everything_later
    assert result['first'] == result['again']
    assert [shield['visible'] for shield in result['first']['shields']] == [True, False]
    assert not any(card['visible'] for card in result['first']['cards'])
    assert not any(stamp['visible'] for stamp in result['first']['stamps'].values())


@pytest.mark.parametrize('mobile', [False, True])
def test_pose_is_pure_and_a_reverse_seek_hides_everything_later_2(sample_pose_is_pure_and_a_reverse_seek_hides_everything_later, mobile):
    result, = sample_pose_is_pure_and_a_reverse_seek_hides_everything_later
    assert result['first']['slot'] == 'Saints' and result['first']['flash'] == 0
    assert not any(shield['visible'] for shield in result['early']['shields'])
    assert result['early']['slot'] is None


@pytest.fixture
def sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after(mobile):
    result = node(POSE + f"const m = {json.dumps(mobile)}; const {{places}} = await import(base + '/lineups-layout.mjs'); const place = places(m);"
                  " const at = s => lineupsPose(s, false, cast, m);"
                  # 2026-11-05 (shield ejects): `after` is ~~10~~ 6 frames past the bar, before a negative score's eject.
                  " return {place, shields: [1, 4].map((land, i) => ({before: at(land - .36).shields[i], falling: at(land - .1).shields[i], after: at(land + 6/30).shields[i], ledge: at(6.6).shields[i], stays: at(7.9).shields[i]})),"
                  " cards: {before: at(7.64).cards, after: at(8 + 10/30).cards, swapped: at(12 + 10/30).cards},"
                  " stamps: [7.99, 8.2, 9.99, 10.2, 12.19, 12.4, 13.99, 14.2].map(s => at(s).stamps)};")
    place = result['place']
    shown = [{key: stamp['visible'] for key, stamp in moment.items()} for moment in result['stamps']]
    keys = ['s5start', 's5bench', 's8start', 's8bench']
    return result, place, shown, keys


@pytest.mark.parametrize('mobile', [False, True])
def test_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after_1(sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after, mobile):
    result, place, shown, keys = sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after
    assert all((not shield['before']['visible']) for (index, shield) in enumerate(result['shields'])), [index for (index, shield) in enumerate(result['shields'])]
    assert all((shield['falling']['visible'] and shield['falling']['position'][1] > place['socket'][1]) for (index, shield) in enumerate(result['shields'])), [index for (index, shield) in enumerate(result['shields'])]
    assert all((shield['after']['visible'] and shield['after']['position'] == pytest.approx(place['socket'])) for (index, shield) in enumerate(result['shields'])), [index for (index, shield) in enumerate(result['shields'])]
    assert all((shield['ledge']['visible'] is (index == 1)) for (index, shield) in enumerate(result['shields'])), [index for (index, shield) in enumerate(result['shields'])]


@pytest.mark.parametrize('mobile', [False, True])
def test_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after_2(sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after, mobile):
    result, place, shown, keys = sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after
    assert all((shield['stays']['visible'] is (index == 1)) for (index, shield) in enumerate(result['shields'])), [index for (index, shield) in enumerate(result['shields'])]
    assert all((shield['stays']['position'] == pytest.approx(place['socket']) and (not shield['stays']['ledge'])) for (index, shield) in enumerate(result['shields'])), [index for (index, shield) in enumerate(result['shields'])]
    assert not any(card['visible'] for card in result['cards']['before'])
    assert [card['position'] for card in result['cards']['after']] == [pytest.approx(place['start']), pytest.approx(place['rack'])]


@pytest.mark.parametrize('mobile', [False, True])
def test_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after_3(sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after, mobile):
    result, place, shown, keys = sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after
    assert [card['position'] for card in result['cards']['swapped']] == [pytest.approx(place['rack']), pytest.approx(place['start'])]
    assert [[moment[key] for key in keys] for moment in shown] == [
        [False, False, False, False], [True, False, False, False], [True, False, False, False], [True, True, False, False],
        [False, False, False, False], [False, False, True, False], [False, False, True, False], [False, False, True, True]]
    assert [moment['week']['text'] for moment in result['stamps']] == ['W5', 'W5', 'W5', 'W5', 'W8', 'W8', 'W8', 'W8']
    assert result['stamps'][-1]['s8bench']['scale'] > result['stamps'][-1]['s8start']['scale']   # the last largest


@pytest.mark.parametrize('mobile', [False, True])
def test_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after_4(sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after, mobile):
    result, place, shown, keys = sample_every_shield_card_and_stamp_is_hidden_before_its_bar_and_placed_after
    assert [result['stamps'][-1][key]['text'] for key in ['s8start', 's8bench']] == ['4.50', '18.40']


# 2026-11-05 (David chose "Score slams, shield ejects"): ~~the flap opens six frames after Chiefs~~ and ~~deductions
# drain the token rail~~. Per bar: the shield lands, its W and score stamps slam 4 frames apart, and a negative score
# flashes the slot red 6 frames later and ejects the shield up and back-left onto the ledge in 0.5 s (outCubic).
def test_week_and_score_slam_four_frames_apart_on_every_shield():
    result = node(POSE + "const at = s => lineupsPose(s, false, cast).shieldStamps; return [1, 4].map(land => ({before: at(land - .01), bar: at(land + .001), score: at(land + 4/30 + .001), settled: at(land + 8/30 + .001)}));")
    assert all((not moments['before'][index]['week']['visible']) for (index, moments) in enumerate(result)), [index for (index, moments) in enumerate(result)]
    assert all((moments['bar'][index]['week']['visible'] and moments['bar'][index]['week']['scale'] > 1) for (index, moments) in enumerate(result)), [index for (index, moments) in enumerate(result)]
    assert all((not moments['bar'][index]['score']['visible']) for (index, moments) in enumerate(result)), [index for (index, moments) in enumerate(result)]
    assert all((moments['score'][index]['score']['visible'] and moments['score'][index]['score']['scale'] > 1) for (index, moments) in enumerate(result)), [index for (index, moments) in enumerate(result)]
    assert all((moments['settled'][index]['week']['scale'] == pytest.approx(1) and moments['settled'][index]['score']['scale'] == pytest.approx(1)) for (index, moments) in enumerate(result)), [index for (index, moments) in enumerate(result)]


def test_negative_scores_are_kept_as_started_receipts_not_ejected():
    result = node(POSE + "const at = s => lineupsPose(s, false, cast); return {held: [1, 3, 5].map(at), recap: at(6.5), wins: [1.99, 2.2, 5.99, 6.2].map(s => at(s).shieldStamps.map(mark => mark.win.visible))};")
    for pose in result['held']:
        hero = next(shield for shield in pose['shields'] if shield['visible'])
        assert not hero['ledge'] and pose['flash'] == 0  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
    assert [shield['name'] for shield in result['recap']['shields']] == ['Saints', 'Raiders']
    assert [shield['visible'] for shield in result['recap']['shields']] == [False, True]
    assert not any(shield['ledge'] for shield in result['recap']['shields'])
    assert result['wins'] == [[False, False], [True, False], [True, False], [True, True]]


def test_blip_hops_over_and_peeks_into_the_slot_after_chiefs():
    result = node(POSE + BLIP_HOPS_OVER_AND_PEEKS_INTO_THE_SLOT_AFTER_CHIEFS_SCRIPT)
    assert all((layout['before']['position'] == pytest.approx(place['blip']['gibbs'])) for layout in result for place in [(layout['place'])])
    assert all((layout['hop']['position'][1] > place['blip']['gibbs'][1]) for layout in result for place in [(layout['place'])])
    assert all((layout['peek']['position'] == pytest.approx(place['blip']['peek']) and layout['peek']['lean'] > 0) for layout in result for place in [(layout['place'])])
    assert all((layout['tight']['visible'] and layout['tight']['position'] == pytest.approx(place['blip']['lamarley'])) for layout in result for place in [(layout['place'])])


@pytest.mark.parametrize('seconds', [0.01, 1, 2.2, 4.4, 5.2, 6.5, 8.05, 10.1, 11.7, 12.1, 14.1, 15.9])
def test_reduced_motion_shows_each_end_state_with_no_travel(seconds):  # shape: allow complete reduced-motion state requires checking every visible prop
    result = node(POSE + f"const {{places}} = await import(base + '/lineups-layout.mjs'); return {{pose: lineupsPose({seconds}, true, cast), place: places(false)}};")
    pose, place = result['pose'], result['place']
    homes = [place['socket'], *place['ledge']]
    for shield in pose['shields']:
        if shield['visible']:
            assert any(shield['position'] == pytest.approx(home) for home in homes), shield  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
            assert shield['squash'] == 1  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
    assert all((card['position'] in (pytest.approx(place['start']), pytest.approx(place['rack']))) for card in pose['cards'] if card['visible']), [card for card in pose['cards'] if card['visible']]
    assert pose['shake'] == 0 and set(pose['shafts'].values()) == {0}
    assert set(pose['impacts'].values()) == {-1} and pose['flash'] == 0
    # ~~tokens on the rail~~ (2026-11-05, no tokens): every stamp is whole the moment it shows.
    assert all(entry['scale'] == pytest.approx(1) for shield in pose['shieldStamps'] for entry in shield.values() if entry['visible'])
    assert pose['blip']['position'][1] == pytest.approx(place['blip']['gibbs'][1]) and pose['blip']['squash'] == 1


def test_titles_slam_in_with_each_station_and_leave_before_the_punchline():
    # 2026-11-05 (David: "you have to have some text to describe what's going on"): each beat opens on its title,
    # in over 8-12 frames, out faster, gone before the beat's punchline lands (craft, "Chyron slam").
    result = node("const {headlineAt, HEADLINE} = await import(base + '/lineups-headline.mjs'); const {LINEUPS_COPY} = await import(base + '/lineups-copy.mjs');"
                  " return {copy: LINEUPS_COPY, frames: [HEADLINE.enter * 30, HEADLINE.leave * 30], at: [0.001, 3, 5.79, 5.83, 6.01, 7.95, 8.001, 11, 13.8, 13.83, 14.01, 15.5].map(s => headlineAt(s))};")
    keys = [entry and entry['key'] for entry in result['at']]
    assert keys == ['defense', 'defenseWin', 'defenseNext', None, 'outcome', None, 'tightends', 'tightends', 'tightends', None, 'payoff', 'payoff']
    assert result['at'][1]['enter'] == 1 and result['at'][0]['enter'] < 1
    assert 8 <= result['frames'][0] <= 12 and result['frames'][1] < result['frames'][0]
    assert result['copy']['defense'] == 'The defense experiment.' and result['copy']['tightends'] == 'Lamarley: the tight-end switch.'
    assert all(len(result['copy'][key].split()) <= 6 for key in ['defense', 'tightends', 'payoff'])


# The eight held shots (composition table): the film second, the shot, the feature that must be big, and what else
# must be whole in frame. The ledge pair is the phone's one ensemble shot (rule 51), whole at a third of the frame.
SUBJECT = """
await import(base + '/lineups-set.mjs');   // registers the set's camera (film-sets.mjs)
const {frame} = await import(base + '/draft-camera.mjs');
const {places, SHIELD, CARD, SIGN, corners} = await import(base + '/lineups-layout.mjs');
const place = places(MOBILE), shield = c => corners(c, SHIELD.width, SHIELD.height), face = c => corners(c, CARD.width, CARD.height);
const sign = (c, size = place.sign) => corners(c, size.width, size.height);
// 2026-11-05 (David: "the bottom is like cut off"): each station's nameplate (badge and name) and its DEF or START
// placard are whole in its shots, on the phone too. ~~The phone's down shots held both cards whole~~: with the titles
// back (David, same day) a 390 px frame cannot hold both cards, the nameplate and a title at 40%, so the phone's down
// shot holds START's card, placard, week and nameplate, and the up shot the rack, BENCH and START's name band.
const plateY = key => key === 'lamarley' ? place.plates.lamarleyY : place.plates.y;
const plate = key => [...corners([place.plates[key][0], plateY(key), place.front], place.plates.badge * 2, place.plates.badge * 2),
  ...corners([place.plates[key][1], plateY(key), place.front], place.plates.width, place.plates.height)];
const both = [...face(place.start), ...face(place.rack), ...sign(place.startSign), ...sign(place.benchSign), ...plate('lamarley')];
const down = MOBILE ? [...face(place.start), ...sign(place.startSign), ...sign(place.week, place.weekSize), ...plate('lamarley')] : both;
const band = c => corners([c[0], c[1] + CARD.height / 2 - place.band / 2, c[2]], CARD.width, place.band);
const up = MOBILE ? [...sign(place.benchSign), ...band(place.start), ...sign(place.startSign)] : both;
const gibbs = shield(place.socket);
const SHOTS = [
  {time: 59.6, feature: shield(place.socket), whole: gibbs}, {time: 61.6, feature: shield(place.socket), whole: gibbs},
  {time: 63.5, feature: shield(place.socket), whole: gibbs},
  {time: 65.4, feature: shield(place.socket), whole: gibbs},
  {time: 67, feature: face(place.start), whole: down}, {time: 69, feature: face(place.rack), whole: up},
  {time: 71, feature: face(place.start), whole: down}, {time: 73.2, feature: face(place.rack), whole: up},
];
// The clear frame: under the title (12% safe top plus its line) and above the review controls with rule 28's 4% gap.
const CLEAR = MOBILE ? {top: .16, bottom: .125} : {top: .2, bottom: .04};
const size = MOBILE ? {width: 390, height: 844} : {width: 1440, height: 900};
const camera = new THREE.PerspectiveCamera(36, size.width / size.height, .1, 200);
const project = points => points.map(point => new THREE.Vector3(...point).project(camera));
"""


@pytest.mark.parametrize('mobile', [False, True])
def test_each_held_shot_frames_its_feature_whole_and_big(mobile):
    # Rules 22 and 29: the feature is 40% of a 390 x 844 frame (a third for the ledge pair, rule 51), and everything
    # the story needs is whole in frame at 1440 x 900 and 390 x 844.
    result = stage_result((CAMERA + SUBJECT).replace('MOBILE', json.dumps(mobile)) + EACH_HELD_SHOT_FRAMES_ITS_FEATURE_WHOLE_AND_BIG_SCRIPT)
    assert all((shot['inside'] and shot['clear'] == 0) for shot in result), [shot for shot in result]
    assert all((shot['share'] >= (0.3 if shot['ensemble'] else 0.4)) for shot in result if mobile), [shot for shot in result if mobile]


@pytest.mark.parametrize('mobile', [False, True])
def test_the_camera_never_jumps_rolls_or_yaws_more_than_three_degrees(mobile):
    # Rule 19: upright and square, roll 0, yaw at most 3 degrees; rule 20: the only fast moves are the whips.
    result = stage_result(CAMERA.replace('MOBILE', json.dumps(mobile)) + CAMERA_NEVER_JUMPS_ROLLS_OR_YAWS_MORE_THAN_THREE_DEGREES_SCRIPT)
    assert all((sample['roll'] == 0 and sample['up'] == [0, 1, 0]) for sample in result['samples']), [sample for sample in result['samples']]
    assert all((sample['yaw'] <= 3) for sample in result['samples']), [sample for sample in result['samples']]
    assert all((sample['jump'] < 0.5) for sample in result['samples'] if not sample['whip']), [sample for sample in result['samples'] if not sample['whip']]
    assert max(result['seams']) < .01, result['seams']


@pytest.fixture(params=[(1440, 900), (390, 844), (360, 800)])
def lineups_film(browser, request):
    film = LineupsSetFilm(browser, *request.param)
    with film:
        film.load()
        yield film


# What each settled shot prints, as textures on the desk (storyboard "Visible copy"), and its DOM headline.
# 2026-11-05 (ch4 corrective): the titles are back (~~None~~ at 63.6-67.5 and 73.6), and Gibbs's nameplate prints.
SHOWN = {
    59.6: (['SAINTS', 'STARTED · WEEK 4', '−3 PTS'], 'The defense experiment.'),
    61.6: (['SAINTS', 'STARTED · WEEK 4', '−3 PTS'], 'Still won.'),
    63.5: (['RAIDERS', 'STARTED · WEEK 5', '−1 PTS'], None),
    65.4: (['RAIDERS', 'STARTED · WEEK 5', '−1 PTS'], 'Won both weeks.'),
    69.6: (['H. Fannin Jr.', 'H. Henry', 'START', 'BENCH', 'W8'], 'Lamarley: the tight-end switch.'),
    73.5: (['H. Henry', 'H. Fannin Jr.', '4.50', '18.40', 'BENCH'], 'Again.'),
}


@pytest.mark.parametrize('time', list(SHOWN))
@pytest.mark.journey
def test_settled_shots_print_their_words_whole_and_the_headline_clears_the_set(lineups_film, time):  # shape: allow headline clearance and prop visibility form one coupled held-shot geometry check
    lineups_film.seek(time)
    words, headline = SHOWN[time]
    shown = lineups_film.shown_text()
    assert all(word in shown for word in words), (words, shown)
    readout = lineups_film.readout()
    assert readout['shown'] and readout['camera'] == 'lineups', readout
    # Rule 30: a stamp is at least 4% of the frame's height.
    stamps = [label for label in readout['labels'] if label['kind'] == 'stamp' and label['visible'] and label['inside']]
    assert all(label['box']['bottom'] - label['box']['top'] >= lineups_film.height * .04 - .5 for label in stamps), stamps
    text = lineups_film.headline()
    if headline is None:
        assert not text['visible'], text  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
    else:
        assert text['visible'] and text['text'] == headline and text['transform'] == 'none', text  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
        assert text['cap'] >= lineups_film.height * .02, text   # rule 19's floor: 2% of the frame  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
        box = text['box']
        assert box['left'] >= 0 and box['right'] <= lineups_film.width and box['top'] >= 0, text  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
        # Rule 36: nothing on the desk crosses the headline.
        crossing = [label['text'] for label in readout['labels'] + readout['objects'] if label['visible'] and label['box']['left'] < box['right']
                    and box['left'] < label['box']['right'] and label['box']['top'] < box['bottom'] and box['top'] < label['box']['bottom']]
        assert crossing == [], crossing  # honest: allow COND_ASSERT parametrized scene poses require per-visible-subject geometry and headline checks
    assert lineups_film.errors == []


@pytest.mark.journey
def test_a_reverse_seek_restores_week_five_and_hides_the_desk_before_its_chapter(lineups_film):
    lineups_film.seek(73.5)
    assert {'4.50', '18.40'} <= set(lineups_film.shown_text())
    lineups_film.seek(69.6)
    shown = lineups_film.shown_text()
    assert '4.50' not in shown and '18.40' not in shown, shown
    lineups_film.seek(68.9)
    assert {'0.90', '11.90', 'W5'} <= set(lineups_film.shown_text())
    lineups_film.seek(57.5)
    assert not lineups_film.readout()['shown']
    assert not lineups_film.headline()['visible']
    assert lineups_film.errors == []


@pytest.mark.journey
def test_reduced_motion_shows_each_result_and_rewinds(browser):
    film = LineupsSetFilm(browser, 390, 844, reduced=True)
    with film:
        film.load()
        film.seek(73.5)
        assert {'4.50', '18.40', 'BENCH'} <= set(film.shown_text())
        assert film.headline()['text'] == 'Again.'
        film.seek(68.5)
        assert {'0.90', '11.90', 'W5'} <= set(film.shown_text())
        film.seek(62.5)
        assert film.readout()['slot'] == 'Raiders'   # 2026-11-05: ~~the flap shown open~~; Chiefs 0 stays in the slot
        assert {'RAIDERS', 'STARTED · WEEK 5', '−1 PTS'} <= set(film.shown_text())
        expect(film.page.locator('[data-defense-manager]')).to_have_text('Gibbs')
        assert film.errors == []


@pytest.mark.parametrize('resource', PORTRAITS)
@pytest.mark.journey
def test_play_waits_for_both_portraits(browser, resource):
    film = LineupsSetFilm(browser, 390, 844)
    with film:
        assert film.load_with_held_portrait(resource)
        assert film.readout()['ready'] and film.errors == []


@pytest.mark.journey
def test_a_failed_portrait_disposes_the_prepared_room_and_disables_play(browser):
    film = LineupsSetFilm(browser, 390, 844)
    with film:
        readout = film.fail_portrait(PORTRAITS[0])
        assert readout['built'] == readout['disposed'] == 1, readout
        expect(film.page.locator('[data-play]')).to_be_disabled()
        assert film.canvases() == 0 and film.page.locator(HEADLINE_SELECTOR).count() == 0
        assert film.errors == []


@pytest.mark.journey
def test_pagehide_removes_the_desk_headline_and_canvas(lineups_film):
    lineups_film.seek(73.5)
    lineups_film.page.evaluate("window.dispatchEvent(new Event('pagehide'))")
    assert lineups_film.page.locator(HEADLINE_SELECTOR).count() == 0
    assert lineups_film.canvases() == 0
    assert lineups_film.readout()['disposed'] == 1
    assert lineups_film.errors == []


HEADLINE_SELECTOR = '[data-lineup-headline]'


def test_music_extension_covers_the_chapter_without_moving_existing_cues():
    result = node("const {MUSIC_EDIT} = await import(base + '/music-edit.mjs'); const {ONSETS, MUSIC_OFFSET} = await import(base + '/music-onsets.mjs'); return {edit:MUSIC_EDIT,onsets:ONSETS,offset:MUSIC_OFFSET};")
    # 2026-11-05 (ch4/5 cinematic): ~~'repeats': 5~~. 2026-11-05 (Chapter 5): ~~'repeats': 3~~.
    assert result['edit']['extension'] == {'at': 68.077, 'from': 50.077, 'length': 8, 'repeats': 4, 'fade': .005}
    assert result['offset'] == 6
    assert 39.3 in result['onsets'] and 42.078 in result['onsets']
    # 2026-11-05 (ch4/5 cinematic): four phrases, ~~111.59~~. 2026-11-05 (Chapter 5): ~~95.59~~.
    assert any(abs(onset - 98.074) < .001 for onset in result['onsets']) and 71.59 not in result['onsets']
