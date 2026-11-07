"""Chapter 1, Draft Receipts: seven beats after the six-second opening, cut to the music's bars,
each headline held 2 s after its motion (revision 8); reduced motion shows each beat's final frame."""
import json
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse/film.mjs'
TIMING = SOURCE.with_name('timing.json')
REVIEW = SOURCE.with_name('film-review.mjs')
FRAME_LIMIT = 2
# Chapter 2's trades and Chapter 3's two pickups beats, 2026-11-05.
BEATS = ['board', 'steal', 'traded', 'sleeper', 'curse', 'injury', 'finale', 'trades',
         'waiver-claim', 'waiver-starts', 'lineup-defense', 'lineup-tightends', 'power-board', 'power-close']


BEAT_MENU_OPENS_ON_ITS_TAB_OR_M_AND_CLOSES_ON_A_JUMP_ESC_OR_THREE_SECONDS_AWAY_SCRIPT = ('''
const {menuOpen, CLOSE_AFTER_MS} = await import(base + '/film-review.mjs');
const events = ['toggle', 'jump', 'escape', 'leave', 'scrub'];
console.log(JSON.stringify({wait: CLOSE_AFTER_MS, closed: events.map(event => menuOpen(false, event)),
  open: events.map(event => menuOpen(true, event))}));
''')

NODE_SCRIPT = ('''
import {registerHooks} from 'node:module';
const base = BASE, timing = TIMING;
registerHooks({
  resolve(specifier, context, next) {
    const path = specifier === 'three' ? base + '/vendor/three.module.js'
      : specifier.startsWith('three/addons/') ? base + '/vendor/' + specifier.slice('three/addons/'.length) : specifier;
    return next(path, context);
  },
  load(url, context, next) {
    return timing && url.endsWith('/timing.json') ? {format: 'json', source: timing, shortCircuit: true} : next(url, context);
  }});
''')


def film(expression):
    script = (f'import * as film from {json.dumps(SOURCE.as_uri())};'
              f'console.log(JSON.stringify({expression}));')
    result = subprocess.run(['node', '--input-type=module', '-e', script],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def moment(time, reduced=False):
    return film(f'film.filmMoment({time}, {str(reduced).lower()})')


def test_the_approved_cut_preserves_the_opening_and_runs_98_seconds():
    plan = film('film.filmPlan()')
    assert plan['chapterAt'] == pytest.approx(7.584)
    assert plan['duration'] == pytest.approx(98.077)
    assert [beat['id'] for beat in plan['beats']] == BEATS

@pytest.mark.parametrize('time,chapter', [(0, 'trophy'), (3, 'blip'), (5, 'logo'), (7.6, 'draft'), (37, 'draft')])
def test_the_opening_hands_over_to_the_draft_room(time, chapter):
    assert moment(time)['chapter'] == chapter


def test_beats_after_the_board_start_on_the_approved_bar_downbeats():
    starts = [beat['start'] for beat in film('film.filmPlan()')['beats'][1:]]
    assert starts == pytest.approx([16.077, 20.077, 24.077, 28.077, 36.077, 40.077, 44.077,
                                   50.077, 56.077, 58.077, 66.077, 74.077, 84.077])

READING_SCRIPT = """
const {receipts} = await import(base + '/draft-data.mjs');
const {tradesValues} = await import(base + '/trades-data.mjs');
const {checkPickups, pickupValues} = await import(base + '/waivers-data.mjs');
const fs = await import('node:fs');
const edition = JSON.parse(fs.readFileSync(editionPath, 'utf8'));
const card = tradesValues(edition.trades);
const words = [card.headline, card.name, card.actual, ...card.deals.flatMap(deal => [deal.name, deal.label])];
const pick = pickupValues(checkPickups(edition.pickups, edition.teams));
const said = card => [card.rank, card.name, card.team, card.added, card.starts ?? ''].join(' ');
console.log(JSON.stringify({...receipts(edition.draft), trades: {headline: words.join(' '), sub: ''},
  waivers: {headline: [pick.head, ...pick.cards.map(said)].join(' '), sub: pick.sub}}));
"""


@pytest.fixture(scope="module")
def reading_copy():
    setup = f'const base = {json.dumps(SOURCE.parent.as_uri())}, editionPath = {json.dumps(str(SOURCE.with_name("edition.json")))};'
    result = subprocess.run(['node', '--input-type=module', '-e', setup + READING_SCRIPT],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize('beat_id', ['board', 'steal', 'traded', 'sleeper', 'curse', 'injury', 'finale', 'trades', 'waivers'])
def test_each_reading_cluster_fits_its_continuous_visible_scene(beat_id, reading_copy):
    beats = film('film.filmPlan()')['beats']
    group = [beat for beat in beats if beat['id'] in ('waiver-claim', 'waiver-starts')] if beat_id == 'waivers' else [next(beat for beat in beats if beat['id'] == beat_id)]
    words = f"{reading_copy[beat_id]['headline']} {reading_copy[beat_id]['sub']}".split()
    prose = [word for word in words if any(letter.isalpha() for letter in word)]
    allowance = .5 if beat_id == 'injury' else 0
    assert len(prose) / 3 + 1 <= sum(beat['duration'] for beat in group) + allowance

def test_blip_hops_with_a_crouch_and_a_landing_and_never_slides():
    uri = json.dumps(SOURCE.with_name('blip-hop.mjs').as_uri())
    script = (f'import {{hop}} from {uri};'
              f'console.log(JSON.stringify([0, .05, .1667, .3, .45, .6, .99, 1].map(t => hop(t, 3))));')
    steps = json.loads(subprocess.run(['node', '--input-type=module', '-e', script],
                                      text=True, capture_output=True, check=True).stdout)
    crouch, air, end = steps[1], steps[2], steps[-1]
    assert crouch['squash'] < 1 and crouch['lift'] == 0 and crouch['travel'] == 0
    assert air['lift'] > 0 and air['squash'] > 1
    assert end == {'travel': 1, 'lift': 0, 'squash': 1}
    travel = [step['travel'] for step in steps]
    assert travel == sorted(travel)


def test_every_beat_retains_its_approved_duration():
    durations = [beat['duration'] for beat in film('film.filmPlan()')['beats']]
    assert durations == pytest.approx([8.493, 4, 4, 4, 8, 4, 4, 6, 6, 2, 8, 8, 10, 14])

def test_the_curse_score_follows_cookeds_listening_marker_with_a_reading_hold():
    curse = film('film.filmPlan()')['beats'][4]
    cooked = max(event['at'] for beat in sheet()['beats'] if beat['id'] == 'curse'
                 for event in beat['events'] if event['name'] == 'stop')
    assert curse['start'] + cooked == pytest.approx(33.300)
    assert curse['start'] + curse['stat'] * curse['pace'] == pytest.approx(33.581)
    assert curse['duration'] - curse['stat'] * curse['pace'] == pytest.approx(2.496)

def test_the_board_opens_on_the_bar_line_after_the_titles_hit():
    board = film('film.filmPlan()')['beats'][0]
    assert board['start'] == pytest.approx(13.584 - 6)   # ch17: the guitar's entry; ~~the bar line after the title~~


@pytest.fixture(scope="module", params=BEATS)
def placed_beat(request):
    return next(beat for beat in film('film.filmPlan()')['beats'] if beat['id'] == request.param)


def test_every_beat_plays_in_order_and_owns_its_own_slot(placed_beat):
    middle = moment(placed_beat['start'] + placed_beat['duration'] / 2)
    assert middle['beat'] == placed_beat['id']
    assert 0 < middle['beatProgress'] < 1


def test_a_headline_comes_in_on_the_frame_its_motion_starts(placed_beat):
    stand = next(event for event in sheet()['beats'][0]['events'] if event['name'] == 'stand')['to']
    enter = placed_beat['start'] + (stand * placed_beat['pace'] if placed_beat['id'] == 'board' else 0)
    first = moment(enter)
    assert moment(placed_beat['start'])['beatProgress'] == pytest.approx(0, abs=1e-9)
    assert (first['headline'], first['headlineAge']) == (placed_beat['id'], pytest.approx(0, abs=1e-9))


def test_the_board_headline_stays_hidden_until_the_board_stands():
    board = film('film.filmPlan()')['beats'][0]
    stand = next(event for event in sheet()['beats'][0]['events'] if event['name'] == 'stand')['to']
    assert moment(board['start'] + stand * board['pace'] - .02)['headline'] is None


@pytest.mark.parametrize('beat_id', BEATS[1:])
def test_a_headline_leaves_at_its_cut_not_before(beat_id):
    beats = film('film.filmPlan()')['beats']
    index = BEATS.index(beat_id)
    assert moment(beats[index]['start'] - .02)['headline'] == BEATS[index - 1]


@pytest.mark.parametrize('beat_id,minimum', [(beat_id, 1 if beat_id == 'waiver-starts' else
    1.5 if beat_id in ('injury', 'curse') else 2) for beat_id in BEATS if beat_id != 'board'])
def test_the_motion_preserves_its_approved_reading_hold(beat_id, minimum):
    beat = next(beat for beat in film('film.filmPlan()')['beats'] if beat['id'] == beat_id)
    assert beat['duration'] - beat['settle'] >= minimum - 1e-9


@pytest.mark.parametrize('beat_id', ['steal', 'traded', 'sleeper', 'curse', 'injury', 'trades',
    'waiver-claim', 'lineup-defense', 'lineup-tightends', 'power-board', 'power-close'])
def test_a_stat_lands_on_the_frame_of_its_stamp(beat_id):
    beat = next(beat for beat in film('film.filmPlan()')['beats'] if beat['id'] == beat_id)
    stamp = beat['start'] + beat['stat'] * beat['pace']
    assert moment(stamp - .02)['statAge'] < 0
    assert moment(stamp)['statAge'] == pytest.approx(0, abs=1e-9)

def test_the_film_finishes_once_and_never_wraps():
    end = film('film.filmPlan().duration')
    assert moment(end)['complete'] is True
    assert moment(end + 30) == moment(end)


def test_reduced_motion_shows_each_beats_final_frame_with_its_headline(placed_beat):
    still = moment(placed_beat['start'] + .01, True)
    assert (still['beat'], still['beatProgress'], still['headline']) == (placed_beat['id'], 1, placed_beat['id'])

def sheet():
    return json.loads(TIMING.read_text(encoding='utf8'))


def node(script, timing=None):
    """Runs `script` with `base` and THREE resolved for the showcase; `timing` stands in for timing.json."""
    hooks = NODE_SCRIPT.replace('BASE', json.dumps(SOURCE.parent.as_uri())).replace('TIMING', json.dumps(timing and json.dumps(timing)))
    result = subprocess.run(['node', '--input-type=module', '-e', hooks + script], text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


def sheet_starts(beats, chapter_at):
    starts, start = [], chapter_at
    for beat in beats:
        starts.append(start)
        start += beat['duration']
    return starts


def nearest(times):
    return node(f"const {{nearestHit}} = await import(base + '/film-impacts.mjs');"
                f'console.log(JSON.stringify({json.dumps(times)}.map(nearestHit)));')


def test_the_timing_sheet_lists_the_approved_beats():
    assert [beat['id'] for beat in sheet()['beats']] == BEATS


@pytest.fixture(scope='module', params=BEATS)
def timed_beat(request):
    return next(beat for beat in sheet()['beats'] if beat['id'] == request.param)


def test_the_timing_sheet_holds_each_beats_duration_camera_and_events(timed_beat):
    assert timed_beat['duration'] > 0 and 0 <= timed_beat['hold'] <= timed_beat['duration']
    assert {'type', 'duration', 'ease'} <= set(timed_beat['camera'])
    assert timed_beat['events']


@pytest.mark.parametrize('beat_id,event', [(beat['id'], event) for beat in sheet()['beats'] for event in beat['events']])
def test_each_timing_event_has_exactly_one_position_form(beat_id, event):
    assert ('at' in event) != ('from' in event and 'to' in event), (beat_id, event)

def test_the_film_reads_its_beats_from_the_timing_sheet(timed_beat):
    beat = next(beat for beat in film('film.filmPlan()')['beats'] if beat['id'] == timed_beat['id'])
    assert beat['duration'] == timed_beat['duration']
    assert beat['settle'] == pytest.approx(timed_beat['duration'] - timed_beat['hold'])
    assert beat['stat'] == timed_beat['stat']

def test_a_sheet_missing_a_beats_fields_fails_at_load():
    timing = json.dumps(SOURCE.with_name('timing.mjs').as_uri())
    result = node(f'const {{checkTiming}} = await import({timing});'
                  'const tries = [{beats: [{id: "board", duration: 4, hold: 1}]}, {beats: [{id: "board", hold: 1, events: []}]}, {}];'
                  'console.log(JSON.stringify(tries.map(sheet => { try { checkTiming(sheet); return "passed"; } catch (error) { return error.message; } })));')
    assert all(message != 'passed' and 'timing.json' in message for message in result), result


@pytest.fixture(scope='module')
def beat_hits():
    starts = sheet_starts(sheet()['beats'], film('film.filmPlan().chapterAt'))
    return dict(zip(BEATS, nearest(starts)))


@pytest.mark.parametrize('beat_id', BEATS)
def test_every_beat_in_the_sheet_starts_on_a_bar_line_or_an_onset(beat_id, beat_hits):
    assert abs(beat_hits[beat_id]['frames']) <= FRAME_LIMIT, (beat_id, beat_hits[beat_id])

@pytest.fixture(scope='module')
def timing_hits():
    beats = sheet()['beats']
    starts = sheet_starts(beats, film('film.filmPlan().chapterAt'))
    hits = [(beat['id'], event.get('label', event['name']), start + event.get('at', event.get('to')) * beat['pace'])
            for beat, start in zip(beats, starts) for event in beat['events'] if event.get('hit')]
    return hits, nearest([time for _, _, time in hits])


def test_the_timing_sheet_retains_at_least_fifteen_impacts(timing_hits):
    assert len(timing_hits[0]) >= 15


@pytest.mark.parametrize('hit_index', range(sum(bool(event.get('hit')) for beat in sheet()['beats'] for event in beat['events'])))
def test_every_hit_in_the_sheet_lands_within_two_frames_of_an_onset_or_bar_line(hit_index, timing_hits):
    hits, nearest_hits = timing_hits
    assert abs(nearest_hits[hit_index]['frames']) <= FRAME_LIMIT, (hits[hit_index], nearest_hits[hit_index])

EDITED_SHEET_SCRIPT = """
const {filmPlan} = await import(base + '/film.mjs');
const {TRAIL} = await import(base + '/constants.mjs');
const {ESTABLISH} = await import(base + '/draft-establish.mjs');
const {filmImpacts} = await import(base + '/film-impacts.mjs');
const plan = filmPlan();
console.log(JSON.stringify({duration: plan.duration - plan.chapterAt, board: plan.beats[0].duration, flip: TRAIL.flip,
  move: ESTABLISH.move, impact: filmImpacts().find(impact => impact.name === '0.0 flip').at - plan.beats[4].start}));
"""

@pytest.fixture(scope='module')
def edited_sheet_result():
    edited = sheet()
    curse = next(beat for beat in edited['beats'] if beat['id'] == 'curse')
    next(event for event in curse['events'] if event['name'] == 'flip')['to'] = 6
    curse['stat'] = 6
    edited['beats'][0]['camera']['duration'] = 2
    edited['beats'][0]['duration'] = 3
    return node(EDITED_SHEET_SCRIPT, edited)


def test_editing_one_number_in_the_sheet_re_times_the_film_with_no_code_edit(edited_sheet_result):
    assert edited_sheet_result == {'duration': pytest.approx(85), 'board': 3, 'flip': 6, 'move': 2, 'impact': pytest.approx(6)}


MENU_SCRIPT = """
const {reviewStops, stopAt, step, looped} = await import(base + '/film-review.mjs');
const stops = reviewStops();
const board = stops[1];
console.log(JSON.stringify({stops, at: stopAt(stops, board.at + .5).id, next: step(stops, board.at + .5, 1),
  back: step(stops, board.at + .5, -1), first: step(stops, 0, -1), last: step(stops, stops.at(-1).at + 1, 1),
  wrapped: looped(stops, 1, board.end + .01), inside: looped(stops, 1, board.at + 1), free: looped(stops, null, board.end + .01)}));
"""

@pytest.fixture(scope='module')
def review_menu():
    return node(MENU_SCRIPT)


def test_the_beat_menu_lists_the_intro_and_every_beat_from_the_sheet(review_menu):
    stops = review_menu['stops']
    assert [stop['id'] for stop in stops] == ['intro', *BEATS]
    assert stops[0]['at'] == 0 and stops[1]['at'] == pytest.approx(film('film.filmPlan().chapterAt'))
    assert all(stop['label'] for stop in stops)
    assert review_menu['at'] == 'board'


def test_the_beat_menu_steps_to_the_next_previous_and_boundary_stops(review_menu):
    stops = review_menu['stops']
    assert review_menu['next'] == pytest.approx(stops[2]['at'])
    assert review_menu['back'] == pytest.approx(stops[1]['at'])
    assert review_menu['first'] == 0
    assert review_menu['last'] == pytest.approx(stops[-1]['at'])


def test_the_beat_menu_loops_only_inside_the_selected_beat(review_menu):
    board = review_menu['stops'][1]
    assert review_menu['wrapped'] == pytest.approx(board['at'])
    assert review_menu['inside'] == pytest.approx(board['at'] + 1)
    assert review_menu['free'] == pytest.approx(board['end'] + .01)


def test_the_beat_menu_reads_the_sheet_instead_of_hardcoding_beats():
    source = REVIEW.read_text(encoding='utf8')
    assert not any(f"'{beat}'" in source for beat in BEATS)


def test_the_beat_menu_opens_on_its_tab_or_m_and_closes_on_a_jump_esc_or_three_seconds_away():
    # David 2026-11-04: the open list hid the scene. It starts as a one-line tab; the tab or M opens it.
    result = node(BEAT_MENU_OPENS_ON_ITS_TAB_OR_M_AND_CLOSES_ON_A_JUMP_ESC_OR_THREE_SECONDS_AWAY_SCRIPT)
    assert result['wait'] == 3000
    assert result['closed'] == [True, False, False, False, False]
    assert result['open'] == [False, False, False, False, True]   # dragging the scrubber keeps it open
    source = REVIEW.read_text(encoding='utf8')
    assert "key === 'm'" in source and "'Escape'" in source and 'mouseleave' in source


def test_the_collapsed_tab_is_one_translucent_line_and_the_open_list_dims_while_the_film_plays():
    css = SOURCE.with_name('film-review.css').read_text(encoding='utf8')
    tokens = SOURCE.with_name('tokens.css').read_text(encoding='utf8')
    assert '--review-tab-width:160px' in tokens and '--review-dim:.35' in tokens
    assert '.film-review:not([data-open]){width:var(--review-tab-width)' in css
    assert '.film-review[data-open]:not(:hover):not(:focus-within){opacity:var(--review-dim)}' in css
    # A phone: the tab rides above the playback bar and the list opens as a sheet from the bottom.
    assert 'bottom:calc(var(--film-bar) + var(--space-2))' in css
    assert '.controls.film-review[data-open]{left:0;right:0;bottom:var(--film-bar)' in css


def test_back_to_the_league_moves_into_the_playback_bar_on_the_film():
    page = SOURCE.with_name('index.html').read_text(encoding='utf8')
    footer = page[page.index('<footer class="controls"'):page.index('</footer>')]
    assert 'class="film-back" href="../../#recap" data-copy="back"' in footer
    bar = SOURCE.with_name('film-bar.css').read_text(encoding='utf8')
    assert 'body[data-film] .masthead .back{display:none}' in bar
    assert 'body:not([data-film]) .film-back{display:none}' in bar
