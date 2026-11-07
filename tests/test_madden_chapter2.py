"""Chapter 2 of the Madden Curse film, the trade tracker (docs/madden-film-chapter2.md): one 6 s shot after
Romo's finale. Aura's three trades as rails to the partners, the Week 8 leads where the lights stop, then the
3-5 stamp and the headline on the bar line. Pure parts run in Node; the frame's fit runs in Chromium."""
import json
import subprocess
from pathlib import Path

import pytest
from playwright.sync_api import expect

from component import mount  # noqa: F401  (the shared browser)
from test_trophy_room import local_file

SOURCE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse'
EDITION = SOURCE / 'edition.json'
FRAME_LIMIT = 2   # rule 18: frames of the 30 fps export an impact may sit from its onset or bar line


RECORD_STAMP_IS_A_HIT_ON_THE_BAR_LINE_AND_THE_CUT_INTO_THE_SHOT_IS_A_WHIP_SCRIPT = ('''
const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs');
const {sceneChanges} = await import(base + '/film.mjs');
const impacts = filmImpacts().filter(impact => ['3-5 stamp', 'Cut to trades'].includes(impact.name));
return {impacts: impacts.map(impact => ({...impact, ...nearestHit(impact.at)})), change: sceneChanges().find(change => change.to === 'trades')};''')

SHOT_IS_ITS_OWN_CHAPTER_UNTIL_THE_CHAPTER_THREE_HANDOFF_SCRIPT = ('''
const {filmMoment} = await import(base + '/film.mjs');
return [43.9, 44.077, 47, 50.076, 50.077].map(time => filmMoment(time)).map(moment =>
  ({chapter: moment.chapter, beat: moment.beat, complete: moment.complete, statAge: moment.statAge}));''')

FINALE_CAMERA_NEVER_WHIPS_TOWARD_THE_NEW_CHAPTER_SCRIPT = ('''
const {view, shot} = await import(base + '/draft-camera.mjs');
const {filmMoment, filmPlan} = await import(base + '/film.mjs');
const finale = filmPlan().beats.find(beat => beat.id === 'finale');
const THREE = await import('three');
const card = {home: new THREE.Vector3(0, 1, 0), mesh: {position: new THREE.Vector3(0, 1, 0)}};
const ctx = {featured: {steal: card, traded: card, sleeper: card, curse: card, injury: card}, landing: new THREE.Vector3(),
  floorZ: 3, finaleX: 0, mobile: false, size: {width: 1440, height: 900}, trail: {left: -1, right: 1, reveal: 2}};
const pose = time => { const camera = view(filmMoment(time), ctx); return [...camera.position.toArray(), ...camera.target.toArray()]; };
const own = time => { const camera = shot('finale', time - finale.start, ctx); return [...camera.position.toArray(), ...camera.target.toArray()]; };
return {late: pose(44.0), own: own(44.0)};''')

TRADES_BLOCK_IS_READ_AND_CHECKED_WHERE_IT_ENTERS_SCRIPT = ('''
const {checkTrades, tradesValues} = await import(base + '/trades-data.mjs');
const good = edition.trades, teams = edition.teams;
const broken = [
  {...good, through: undefined}, {...good, team: 99}, {...good, record: {actual: '3-5'}},
  {...good, deals: []}, {...good, deals: [{...good.deals[0], partner: good.team}]},
  {...good, deals: [{...good.deals[0], leader: 7}]}, {...good, deals: [{...good.deals[0], lead: -3}]},
  {...good, deals: [{...good.deals[0], weekly: good.deals[0].weekly.slice(0, -1)}]},
  {...good, deals: [{...good.deals[0], lead: 20}]}];
const errors = broken.map(block => { try { checkTrades(block, teams); return 'passed'; } catch (error) { return error.message; } });
const flipped = {...good, deals: [{...good.deals[0], leader: good.team, weekly: [...good.deals[0].weekly.slice(0, -1),
  {...good.deals[0].weekly.at(-1), lead: -good.deals[0].lead}]}]};
return {errors, values: tradesValues(checkTrades(good, teams)), flipped: tradesValues(checkTrades(flipped, teams)).deals[0]};''')

TAG_SHOWS_IN_THE_OPENING_ONLY_SCRIPT = ('''
const {identAt} = await import(base + '/film-ident.mjs');
const {filmPlan} = await import(base + '/film.mjs');
const plan = filmPlan();
return {beats: plan.beats.flatMap(beat => [beat.start + .3, beat.start + beat.duration / 2, beat.start + beat.duration - .01].map(identAt)),
  end: identAt(plan.duration), opening: identAt(1)};''')

HELD_FRAME_FITS_AND_NOTHING_OVERLAPS_ITS_WORDS_SCRIPT = ('''() => {
          const box = node => { const r = node.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
          const all = selector => [...document.querySelectorAll(selector)].map(box);
          return {head: box(document.querySelector('[data-trades-head]')), stamp: box(document.querySelector('[data-trades-stamp]')),
            faces: all('[data-trades] .trades-face'), names: all('[data-trades] .trades-name'), badges: all('[data-trades] .trades-badge'),
            mask: (() => {   // a mask is never painted, so its box comes from its attributes through the SVG's screen matrix
              const rect = document.querySelector('[data-trades-mask]'), matrix = rect.ownerSVGElement.getScreenCTM();
              const corner = (x, y) => new DOMPoint(x, y).matrixTransform(matrix);
              const x = rect.x.baseVal.value, y = rect.y.baseVal.value;
              const a = corner(x, y), b = corner(x + rect.width.baseVal.value, y + rect.height.baseVal.value);
              return [a.x, a.y, b.x, b.y];
            })(),
            matrix: (() => { const m = document.querySelector('.trades-rails').getScreenCTM(); return [m.a, m.d, m.e, m.f]; })(),
            rails: [...document.querySelectorAll('.trades-rail')].map(line => ['x1', 'y1', 'x2', 'y2'].map(key => line[key].baseVal.value)),
            lit: [...document.querySelectorAll('.trades-rail-lit')].map(line => ['x1', 'y1', 'x2', 'y2'].map(key => line[key].baseVal.value)),
            drift: [...document.querySelectorAll('.trades-drift')].map(dot => [dot.cx.baseVal.value, dot.cy.baseVal.value, dot.r.baseVal.value]),
            cases: [...document.querySelectorAll('[data-trades] .trades-name')].map(name => getComputedStyle(name).textTransform),
            caps: [...document.querySelectorAll('[data-trades] .trades-name')].map(name => {
              const style = getComputedStyle(name), pen = document.createElement('canvas').getContext('2d');
              pen.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`;
              return pen.measureText(name.textContent.toUpperCase()).actualBoundingBoxAscent * name.getBoundingClientRect().height / name.offsetHeight;
            }),
            flares: document.querySelectorAll('[data-trades] .trades-glint').length,
            names_text: [...document.querySelectorAll('[data-trades] .trades-name')].map(name => name.textContent)};
        }''')

NODE_SCRIPT = ('''
import {registerHooks} from 'node:module';
const base = BASE;
registerHooks({resolve(specifier, context, next) {
  const path = specifier === 'three' ? base + '/vendor/three.module.js'
    : specifier.startsWith('three/addons/') ? base + '/vendor/' + specifier.slice('three/addons/'.length) : specifier;
  return next(path, context);
}});
const edition = JSON.parse((await import('node:fs')).readFileSync(EDITION, 'utf8'));
console.log(JSON.stringify(await (async () => {EXPRESSION})()));
''')


def node(expression):
    script = NODE_SCRIPT.replace('BASE', json.dumps(SOURCE.as_uri())).replace('EDITION', json.dumps(str(EDITION))).replace('EXPRESSION', expression)
    result = subprocess.run(['node', '--input-type=module', '-e', script], text=True, encoding='utf8', capture_output=True, check=True)
    return json.loads(result.stdout)


def sheet():
    return json.loads((SOURCE / 'timing.json').read_text(encoding='utf8'))


def test_the_trades_shot_follows_the_finale_for_six_seconds_ending_at_50_077():
    beats = sheet()['beats']
    index = next(index for index, beat in enumerate(beats) if beat['id'] == 'trades')
    assert beats[index - 1]['id'] == 'finale'
    trades = beats[index]
    assert trades['duration'] == 6 and trades['chapter'] == 2
    plan = node("const {filmPlan} = await import(base + '/film.mjs'); return filmPlan();")
    placed = next(beat for beat in plan['beats'] if beat['id'] == 'trades')
    assert placed['start'] == pytest.approx(44.077)
    assert placed['start'] + placed['duration'] == pytest.approx(50.077)


def test_the_record_stamp_is_a_hit_on_the_bar_line_and_the_cut_into_the_shot_is_a_whip():
    trades = next(beat for beat in sheet()['beats'] if beat['id'] == 'trades')
    record = next(event for event in trades['events'] if event['name'] == 'record')
    assert record['hit'] is True and record['to'] == pytest.approx(2)   # film 46.077, two bars after the cut
    result = node(RECORD_STAMP_IS_A_HIT_ON_THE_BAR_LINE_AND_THE_CUT_INTO_THE_SHOT_IS_A_WHIP_SCRIPT)
    assert [impact['name'] for impact in result['impacts']] == ['Cut to trades', '3-5 stamp']
    assert [impact['at'] for impact in result['impacts']] == pytest.approx([44.077, 46.077])
    assert all(abs(impact['frames']) <= FRAME_LIMIT for impact in result['impacts'])
    assert result['change']['kind'] == 'across' and result['change']['to'] == 'trades'


def test_the_shot_is_its_own_chapter_until_the_chapter_three_handoff():
    result = node(SHOT_IS_ITS_OWN_CHAPTER_UNTIL_THE_CHAPTER_THREE_HANDOFF_SCRIPT)
    assert [moment['chapter'] for moment in result] == ['draft', 'trades', 'trades', 'trades', 'waivers']
    assert result[0]['beat'] == 'finale' and result[1]['beat'] == 'trades'
    assert result[2]['statAge'] == pytest.approx(47 - 46.077)
    assert result[3]['complete'] is False and result[4]['complete'] is False


def test_the_finale_camera_never_whips_toward_the_new_chapter():
    # Chapter 1's frames stay as accepted: the board's camera has no shot of the trades card to blend toward.
    result = node(FINALE_CAMERA_NEVER_WHIPS_TOWARD_THE_NEW_CHAPTER_SCRIPT)
    assert result['late'] == pytest.approx(result['own'], abs=1e-6)   # the finale's own shot, no whip blended in


@pytest.fixture
def sample_the_trades_block_is_read_and_checked_where_it_enters():
    result = node(TRADES_BLOCK_IS_READ_AND_CHECKED_WHERE_IT_ENTERS_SCRIPT)
    values = result['values']
    return result, values


def test_the_trades_block_is_read_and_checked_where_it_enters_1(sample_the_trades_block_is_read_and_checked_where_it_enters):
    result, values = sample_the_trades_block_is_read_and_checked_where_it_enters
    assert all(message.startswith('Invalid trades block') for message in result['errors']), result['errors']
    assert [deal['partner'] for deal in values['deals']] == [3, 12, 5]   # rail order = edition.json deals order
    assert [deal['label'] for deal in values['deals']] == ['+17.9', '+63.7', '+4.5']
    assert values['actual'] == '3-5' and values['noTrades'] == '5-3'


def test_the_trades_block_is_read_and_checked_where_it_enters_2(sample_the_trades_block_is_read_and_checked_where_it_enters):
    result, values = sample_the_trades_block_is_read_and_checked_where_it_enters
    assert values['headline'] == 'No trades? Aura goes 5-3.'
    assert values['name'] == 'Aura'
    assert [deal['winner'] for deal in values['deals']] == ['partner'] * 3
    assert all('stop' not in deal for deal in values['deals'])


def test_the_trades_block_is_read_and_checked_where_it_enters_3(sample_the_trades_block_is_read_and_checked_where_it_enters):
    result, values = sample_the_trades_block_is_read_and_checked_where_it_enters
    assert result['flipped']['winner'] == 'team'


@pytest.mark.parametrize('width,height', [(1440, 900), (390, 844), (360, 800)])
def test_the_frame_holds_every_avatar_and_indicator_whole_and_big_enough(width, height):  # shape: allow one viewport composition requires checking all coupled avatar, type and rail bounds
    layout = node(f"const {{tradesLayout}} = await import(base + '/trades-layout.mjs'); return tradesLayout({width}, {height}, 3, {{headHeight: 80}});")
    circles = [layout['aura'], *layout['partners']]
    assert all((0 <= width / 2 + (x - width / 2) * grow <= width and 0 <= height / 2 + (y - height / 2) * grow <= height) for circle in circles for grow in [(1 + layout['push'])] for (x, y) in [(circle['x'] - circle['r'], circle['y'] - circle['r']), (circle['x'] + circle['r'], circle['y'] + circle['r'])])
    assert layout['light'] >= .04 * height and layout['badge']['height'] >= .04 * height   # rule 30
    assert layout['badge']['font'] >= .02 * height and layout['name'] >= .02 * height      # rule 25
    assert layout['aura']['r'] > max(partner['r'] for partner in layout['partners'])
    if width < 640:   # phone: Aura at the bottom, the partners at the top, the headline directly above Aura
        assert layout['phone'] and layout['aura']['y'] > height / 2  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        assert all(partner['y'] < height / 3 for partner in layout['partners'])  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        assert layout['headline']['bottom'] <= layout['aura']['y'] - layout['aura']['r']  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
    else:            # desktop: Aura on the left, the partners on the right, the headline beside Aura
        assert not layout['phone'] and layout['aura']['x'] < width / 3  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        assert all(partner['x'] > width * 2 / 3 for partner in layout['partners'])  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        assert layout['headline']['left'] >= layout['aura']['x'] + layout['aura']['r']  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        # The symmetric fan (rule 28) puts its lowest rail across Aura's lower right, so the headline sits beside
        # Aura's stack (avatar, name, stamp), under that rail, rather than beside the avatar alone.
        assert layout['aura']['y'] < layout['headline']['top'] < layout['stamp']['top'] + layout['stamp']['size']  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked


@pytest.mark.parametrize('width,height', [(390, 844), (360, 800)])
def test_on_a_phone_the_rails_fan_from_a_node_clear_above_the_headline(width, height):
    # Rule 36: the rails never reach the headline. They start from a node 4% of the height above its top.
    head = 80
    layout = node(f"const {{tradesLayout}} = await import(base + '/trades-layout.mjs'); return tradesLayout({width}, {height}, 3, {{headHeight: {head}}});")
    hub = layout['node']
    assert hub['y'] + hub['r'] <= layout['headline']['bottom'] - head - .04 * height + 1e-6
    assert all((((rail['x1'] - hub['x']) ** 2 + (rail['y1'] - hub['y']) ** 2) ** 0.5 == pytest.approx(hub['r'])) for rail in layout['rails'])
    assert all((max(rail['y1'], rail['y2']) <= hub['y'] + hub['r'] + 1e-06) for rail in layout['rails'])


@pytest.mark.parametrize('width,height', [(390, 844), (360, 800)])
def test_on_a_phone_the_partner_labels_keep_four_percent_of_the_width_apart(width, height):
    # Rule 36 at 360: the names use the full width, with even gaps, never smaller type.
    items = [106, 96, 62]   # px: WARREN-TY, SAUSAGE and GIBBS in the display face at the name size
    layout = node(f"const {{tradesLayout}} = await import(base + '/trades-layout.mjs'); return tradesLayout({width}, {height}, 3, {{headHeight: 80, items: {items}}});")
    spans = [(partner['x'] - max(item, 2 * partner['r']) / 2, partner['x'] + max(item, 2 * partner['r']) / 2)
             for partner, item in zip(layout['partners'], items)]
    assert spans[0][0] >= 0 and spans[-1][1] <= width
    assert all(second[0] - first[1] >= .04 * width - 1e-6 for first, second in zip(spans, spans[1:]))
    gaps = [second[0] - first[1] for first, second in zip(spans, spans[1:])]
    assert spans[0][0] == pytest.approx(width - spans[-1][1]) and max(gaps) == pytest.approx(min(gaps))   # even
    assert layout['name'] == pytest.approx(max(17, .026 * height))


def test_on_a_desktop_the_fan_is_centred_on_aura_and_the_frame_has_even_margins():
    # Rule 28: the partner column's centre is Aura's centre line, and the shot sits in the middle of the frame.
    layout = node("const {tradesLayout} = await import(base + '/trades-layout.mjs'); return tradesLayout(1440, 900, 3, {headHeight: 130});")
    ys = [partner['y'] for partner in layout['partners']]
    assert sum(ys) / len(ys) == pytest.approx(layout['aura']['y'])
    top, bottom = layout['bounds']['top'], layout['bounds']['bottom']
    assert top == pytest.approx(900 - bottom, abs=1)
    aura, label, stamp = layout['aura'], layout['auraName'], layout['stamp']   # Aura is named like the partners
    assert label['x'] == aura['x'] and label['top'] > aura['y'] + aura['r'] and stamp['top'] > label['top'] + layout['name']
    assert layout['headline']['top'] + 130 <= bottom + 1


def test_the_tag_shows_in_the_opening_only():
    result = node(TAG_SHOWS_IN_THE_OPENING_ONLY_SCRIPT)
    assert result['opening'] == pytest.approx(1)
    # 2026-11-05 (Chapter 5): the tag returns across the last beat's final seconds, so its last sample (its end - .01 s)
    # and the film's end read 1. ~~every sample and the end == 0~~.
    assert result['beats'][:-1] == [0] * (len(result['beats']) - 1)
    assert result['beats'][-1] == pytest.approx(1) and result['end'] == pytest.approx(1)


@pytest.mark.journey
@pytest.mark.parametrize('width,height', [(1440, 900), (390, 844), (360, 800)])
def test_the_held_frame_fits_and_nothing_overlaps_its_words(mount, width, height):  # shape: allow single held-frame browser session checks all coupled visible elements
    context = mount.browser.new_context(viewport={'width': width, 'height': height})
    with context:
        context.route('http://trophy.test/**', local_file)
        context.route('https://**', lambda route: route.abort())
        page = context.new_page()
        page.goto('http://trophy.test/?film')
        expect(page.locator('[data-play]')).to_be_enabled(timeout=30000)
        page.locator('[data-seek]').evaluate("element => {element.value = 49.8; element.dispatchEvent(new Event('input'));}")
        expect(page.locator('[data-trades]')).to_be_visible()
        expect(page.locator('[data-receipt]')).to_be_hidden()
        expect(page.locator('.brand')).to_be_hidden()
        expect(page.locator('[data-trades-head]')).to_have_text('No trades? Aura goes 5-3.')
        boxes = page.evaluate(HELD_FRAME_FITS_AND_NOTHING_OVERLAPS_ITS_WORDS_SCRIPT)
        assert boxes['names_text'] == ['WARREN-TY', 'Sausage', 'Gibbs', 'Aura'] and set(boxes['cases']) == {'uppercase'}   # one case
        faces, badges = boxes['faces'], boxes['badges']   # faces: the partners in deal order, then Aura
        words = [boxes['head'], boxes['stamp'], *boxes['names'], *badges]
        assert all((left >= 0 and top >= 0 and (right <= width) and (bottom <= height)) for (left, top, right, bottom) in [*words, *faces]), [(left, top, right, bottom) for (left, top, right, bottom) in [*words, *faces]]
        overlap = lambda a, b: a[0] < b[2] - .5 and b[0] < a[2] - .5 and a[1] < b[3] - .5 and b[1] < a[3] - .5
        things = [*words, *faces]
        for index, first in enumerate(things):   # rule 36: no two of them overlap
            for second in things[index + 1:]:
                assert not overlap(first, second), (first, second)  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        phone = width < 640
        assert all((gap == pytest.approx((0.007 if phone else 0.009) * height, abs=1)) for (face, badge) in zip(faces[:3], badges) for gap in [(badge[1] - face[3] if phone else face[0] - badge[2])]), [(face, badge) for (face, badge) in zip(faces[:3], badges) for gap in [(badge[1] - face[3] if phone else face[0] - badge[2])]]
        assert all((cap >= 0.02 * height - 0.5) for cap in boxes['caps']), [boxes['caps'] for cap in boxes['caps']]
        sx, sy, ex, ey = boxes['matrix']
        screen = lambda x, y: (x * sx + ex, y * sy + ey)
        for rail, lit in zip(boxes['rails'], boxes['lit']):   # the beam starts at its source and runs to the winner
            middle = ((rail[0] + rail[2]) / 2, (rail[1] + rail[3]) / 2)
            assert lit[0] == pytest.approx(rail[0], abs=.5) and lit[1] == pytest.approx(rail[1], abs=.5)  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
            assert ((lit[2] - rail[0]) ** 2 + (lit[3] - rail[1]) ** 2) > ((middle[0] - rail[0]) ** 2 + (middle[1] - rail[1]) ** 2)  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        assert boxes['flares'] == 1   # one flare for the whole sequence
        for (cx, cy, r), rail in zip(boxes['drift'], boxes['rails']):   # a drifting light stays on its rail's bright half
            assert min(rail[0], rail[2]) - r <= cx <= max(rail[0], rail[2]) + r and min(rail[1], rail[3]) - r <= cy <= max(rail[1], rail[3]) + r  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        if phone:   # rule 36: the rails stop 4% of the height above the headline
            lowest = max(screen(0, max(rail[1], rail[3]))[1] for rail in boxes['rails'])
            assert lowest <= boxes['head'][1] - .04 * height, (lowest, boxes['head'])  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
            spans = sorted(boxes['names'][:3])
            assert all(second[0] - first[2] >= .04 * width - .5 for first, second in zip(spans, spans[1:])), spans  # honest: allow COND_ASSERT viewport-specific rail geometry; every pair and sampled light must be checked
        head, mask = boxes['head'], boxes['mask']   # the rails are masked wherever the headline sits
        assert mask[0] <= head[0] and mask[1] <= head[1] and mask[2] >= head[2] and mask[3] >= head[3]
