"""Chapter 3, Best pickups (docs/madden-film-chapter3.md, storyboard approved 2026-11-05): the league's three
best pickups through Week 8 land on bar lines, #3 then #2 then #1, and Love's six weeks fill under him."""
import pytest

from component import mount
from test_madden_chapter2 import node
from pages.madden_waivers import WaiversFilm, STRIP_HOLD, PAIR_HOLD


VALUES = "const {checkPickups, pickupValues} = await import(base + '/waivers-data.mjs'); "
LOVE_STRIP = [('W3', '19.5', 'QB16'), ('W4', '14.1', 'QB17'), ('W5', '25.3', 'QB8'),
              ('W6', '21.2', 'QB6'), ('W7', '18.0', 'QB13'), ('W8', '22.5', 'QB6')]


def strip(card):
    return [(week['label'], week['points'], week['rank']) for week in card['weeks']]


@pytest.fixture
def sample_pickups_append_ten_seconds_without_retiming_the_accepted_chapters():
    plan = node("const {filmPlan} = await import(base + '/film.mjs'); return filmPlan();")
    chapter = plan['beats'][7:10]
    return plan, chapter


def test_pickups_append_ten_seconds_without_retiming_the_accepted_chapters_1(sample_pickups_append_ten_seconds_without_retiming_the_accepted_chapters):
    plan, chapter = sample_pickups_append_ten_seconds_without_retiming_the_accepted_chapters
    assert [(beat['id'], beat['duration']) for beat in chapter] == [('trades', 6), ('waiver-claim', 6), ('waiver-starts', 2)]
    assert [beat['start'] for beat in chapter] == pytest.approx([44.077, 50.077, 56.077])
    assert [beat['chapter'] for beat in chapter[-2:]] == [3, 3]
    assert plan['beats'][10]['start'] == pytest.approx(58.077)


def test_pickups_append_ten_seconds_without_retiming_the_accepted_chapters_2(sample_pickups_append_ten_seconds_without_retiming_the_accepted_chapters):
    plan, chapter = sample_pickups_append_ten_seconds_without_retiming_the_accepted_chapters
    assert [beat['id'] for beat in plan['beats'][:7]] == ['board', 'steal', 'traded', 'sleeper', 'curse', 'injury', 'finale']
    assert [beat['start'] for beat in plan['beats'][:7]] == pytest.approx([7.584, 16.077, 20.077, 24.077, 28.077, 36.077, 40.077])
    assert [beat['duration'] for beat in plan['beats'][:7]] == pytest.approx([8.493, 4, 4, 4, 8, 4, 4])


def test_each_card_lands_on_a_bar_line_and_the_top_pickup_on_the_phrase_seam():
    result = node("const {sceneChanges} = await import(base + '/film.mjs'); const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs'); return {changes: sceneChanges().filter(change => change.to.startsWith('waiver')), hits: filmImpacts().filter(hit => hit.at >= 50 && hit.at < 58).map(hit => ({...hit, reference:nearestHit(hit.at)}))};")
    # 2026-11-05 (ch4/5 cinematic): Chapter 3's own changes and hits, no longer the film's last; ~~slice(-2)~~, ~~at >= 50~~.
    assert [(change['to'], change['kind']) for change in result['changes']] == [('waiver-claim', 'across'), ('waiver-starts', 'travel')]
    # 2026-11-05 (David reapproved, +2 s Chapter 3): the cut to waiver-starts ~~56.077~~.
    assert {hit['name']: hit['at'] for hit in result['hits']} == pytest.approx(
        {'Cut to waiver-claim': 50.077, '#3 card lands': 52.077, '#2 card lands': 52.077, '#1 card lands': 54.077, 'Cut to waiver-starts': 56.077})
    assert all(hit['reference']['kind'] == 'downbeat' and abs(hit['reference']['frames']) <= 2 for hit in result['hits'])


def test_chapter_three_seeking_clamps_and_reduced_motion_keeps_the_story():
    # 2026-11-05 (David reapproved, +2 s Chapter 3): ~~filmMoment(56.077)~~, ~~filmMoment(60.077)~~.
    # 2026-11-05 (ch4/5 cinematic): the film runs on to 98.077, so the chapter's last frame is 62.076 and the clamp is
    # tested at the film's end; ~~filmMoment(62.077)~~, ~~filmMoment(80)~~, ~~result[3]['complete']~~.
    result = node("const {filmMoment, filmPlan} = await import(base + '/film.mjs'); const end = filmPlan().duration; return [filmMoment(49.9),filmMoment(50.077),filmMoment(56.077),filmMoment(58.076),filmMoment(end),filmMoment(51,true),filmMoment(end + 20)];")
    assert [entry['chapter'] for entry in result[:4]] == ['trades', 'waivers', 'waivers', 'waivers']
    assert [entry['beat'] for entry in result[1:4]] == ['waiver-claim', 'waiver-starts', 'waiver-starts']
    assert result[4]['complete'] and result[6] == result[4]
    assert result[5]['beatProgress'] == 1 and result[5]['transition'] is None


@pytest.fixture
def sample_the_cards_read_three_two_one_from_the_edition():
    result = node(VALUES + "return pickupValues(checkPickups(edition.pickups, edition.teams));")
    cards = result['cards']
    return result, cards


def test_the_cards_read_three_two_one_from_the_edition_1(sample_the_cards_read_three_two_one_from_the_edition):
    result, cards = sample_the_cards_read_three_two_one_from_the_edition
    assert [card['rank'] for card in cards] == ['#3', '#2', '#1']
    assert [card['name'] for card in cards] == ['D. Schultz', 'E. Wilson', 'J. Love']
    assert [card['team'] for card in cards] == ['COOKed', 'Aura', 'Sausage']
    assert [card['added'] for card in cards] == ['+20.4', '+25.7', '+40.5']


def test_the_cards_read_three_two_one_from_the_edition_2(sample_the_cards_read_three_two_one_from_the_edition):
    result, cards = sample_the_cards_read_three_two_one_from_the_edition
    assert [card['starts'] for card in cards] == ['3 starts', '6 starts', None]
    assert [card['portrait'] for card in cards] == ['../../heads/lg/dalton-schultz.webp', '../../heads/lg/emanuel-wilson.webp', '../../heads/lg/jordan-love.webp']
    assert [card['badge'] for card in cards] == ['../../avatars/yahoo/2.webp', '../../avatars/yahoo/6.webp', '../../avatars/yahoo/12.webp']
    assert strip(cards[2]) == LOVE_STRIP


def test_the_cards_read_three_two_one_from_the_edition_3(sample_the_cards_read_three_two_one_from_the_edition):
    result, cards = sample_the_cards_read_three_two_one_from_the_edition
    assert result['head'] == 'Best pickups.' and result['sub'] == 'Ranked by points over replacement (PAR).'


def test_a_week_he_did_not_play_says_out_never_a_rank():
    result = node(VALUES + "return pickupValues(checkPickups(edition.pickups, edition.teams));")
    assert strip(result['cards'][1])[-1] == ('W8', '0.0', 'out')


def test_wins_swung_are_never_on_the_card():
    result = node(VALUES + "return pickupValues(checkPickups(edition.pickups, edition.teams));")
    assert all('win' not in key.lower() for card in result['cards'] for key in card)


@pytest.mark.parametrize('mutation,expected', [
    ("edition.pickups.top[0].added = 41.26", ('added', 2, '+41.3')),
    ("edition.pickups.top[0].weeks[2].pts = 30", ('points', 2, '30.0')),
    ("edition.pickups.top[0].weeks[2].rank = null", ('rank', 2, 'out')),
    ("edition.pickups.top[2].starts = 4; edition.pickups.top[2].weeks.push({week: 7, pts: 1, rank: 30})", ('starts', 0, '4 starts')),
])
def test_every_number_is_read_from_the_edition_not_hard_coded(mutation, expected):
    field, card, value = expected
    result = node(VALUES + mutation + "; return pickupValues(checkPickups(edition.pickups, edition.teams));")
    shown = result['cards'][card]
    actual = shown['weeks'][2][field] if field in ('points', 'rank') else shown[field]
    assert actual == value


@pytest.mark.parametrize('mutation', [
    "data.through = 9", "data.top.pop()", "data.top.reverse()", "data.top[0].rank = 2",
    "data.top[0].team = 99", "data.top[0].added = '40.5'", "data.top[0].added = NaN", "data.top[1].starts = 6.5",
    "data.top[0].slug = '../x'", "data.top[0].name = ''", "data.top[0].via = 'trade'", "data.top[0].pos = 'K2'",
    "data.top[0].weeks = []", "data.top[0].weeks[0].pts = '19.5'", "data.top[0].weeks[0].rank = 0",
    "data.top[0].weeks[0].rank = 1.5", "data.top[0].weeks[1].week = 3", "data.top[0].weeks.push({...data.top[0].weeks[5], week: 9})",
    "data.top[0].weeks.pop()",
])
def test_a_malformed_or_out_of_edition_pickup_is_rejected(mutation):
    result = node(VALUES + "const data = edition.pickups; " + mutation + "; try {checkPickups(data, edition.teams); return null;} catch(error) {return {name:error.name, message:error.message};}")
    assert result is not None, mutation
    assert result['name'] == 'TypeError' and result['message'].startswith('Invalid pickups:')


def test_the_receipt_points_at_the_editions_pickups():
    result = node("const {checkWaivers} = await import(base + '/waivers-data.mjs'); const fs = await import('node:fs'); const data = JSON.parse(fs.readFileSync(new URL('./waivers-receipts.json', base + '/'), 'utf8')); const good = {...checkWaivers(data)}; data.key = 'trades'; try {checkWaivers(data); return {good, bad:null};} catch (error) {return {good, bad:error.message};}")
    assert result['good']['edition'] == './edition.json' and result['good']['key'] == 'pickups'
    assert result['bad'].startswith('Invalid pickups:')


@pytest.fixture
def sample_motion_lands_three_then_two_then_one_then_fills_his_weeks():
    result = node("const {waiversPose} = await import(base + '/waivers-motion.mjs'); return [.1,1.5,1.7,2.05,3.7,3.7,3.69,4,5.1,6.6,7.6,7.8].map(time => waiversPose(time));")
    cards = [pose['cards'] for pose in result]
    return result, cards


def test_motion_lands_three_then_two_then_one_then_fills_his_weeks_1(sample_motion_lands_three_then_two_then_one_then_fills_his_weeks):
    result, cards = sample_motion_lands_three_then_two_then_one_then_fills_his_weeks
    assert result[0]['head'] == 0 and result[1]['head'] == 1 and result[1]['sub'] == 1
    assert cards[2] == [0, 0, 0] and cards[3] == [1, 1, 0]
    assert cards[4] == [1, 1, 0] and cards[5] == [1, 1, 0]
    assert cards[6] == [1, 1, 0] and cards[7] == [1, 1, 1]


def test_motion_lands_three_then_two_then_one_then_fills_his_weeks_2(sample_motion_lands_three_then_two_then_one_then_fills_his_weeks):
    result, cards = sample_motion_lands_three_then_two_then_one_then_fills_his_weeks
    assert result[7]['dim'] == 0 and result[9]['dim'] == 1
    assert result[8]['weeks'] == [0] * 6 and result[10]['weeks'] == [1] * 6
    assert result[8]['push'] == 0 and 0 < result[11]['push'] < 1


def test_motion_is_reversible_and_reduced_motion_shows_each_beats_story():
    # 2026-11-05 (David reapproved, +2 s Chapter 3): ~~waiversPose(9)~~, ~~waiversPose(7, true)~~.
    result = node("const {waiversPose} = await import(base + '/waivers-motion.mjs'); const first = waiversPose(4.5); waiversPose(11); return {first, again: waiversPose(4.5), claim: waiversPose(1, true), starts: waiversPose(9, true)};")
    assert result['first'] == result['again']
    assert result['claim']['cards'] == [1, 1, 0] and result['claim']['weeks'] == [0] * 6 and result['claim']['head'] == 1
    assert result['starts']['cards'] == [1, 1, 1] and result['starts']['weeks'] == [1] * 6 and result['starts']['push'] == 0


@pytest.fixture(params=[(1440, 900), (390, 844), (360, 800)])
def waiver_film(mount, request):
    film = WaiversFilm(mount.browser, *request.param)
    with film:
        film.load()
        yield film


def test_every_card_and_his_weeks_fit_without_overlapping(waiver_film):
    for time, beat in [(PAIR_HOLD, 'pair'), (STRIP_HOLD, 'strip')]:
        waiver_film.seek(time)
        waiver_film.require_hold(beat)
        result = waiver_film.geometry(beat)
        assert result['visible'] and result['within'] and not result['overlaps'], result  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
        assert result['minCapHeight'] >= waiver_film.height * .02 - .5, result  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
    assert waiver_film.errors == []


def test_desktop_reads_left_to_right_and_a_phone_puts_the_top_pickup_on_top(waiver_film):  # shape: allow desktop and phone composition invariants share one settled frame
    waiver_film.seek(STRIP_HOLD)
    waiver_film.require_hold('strip')
    boxes = waiver_film.card_boxes()
    three, two, one = boxes['3'], boxes['2'], boxes['1']
    assert one['height'] > two['height'] and one['height'] > three['height']
    if waiver_film.width >= 640:
        assert three['right'] <= two['left'] and two['right'] <= one['left']  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
        assert waiver_film.strip_rows() == [6]  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
    else:
        assert one['bottom'] <= min(two['top'], three['top'])  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
        assert one['height'] >= waiver_film.height * .4  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
        assert waiver_film.strip_rows() == [3, 3]  # honest: allow COND_ASSERT parametrized viewport and seek holds have distinct required compositions
    assert waiver_film.errors == []


def test_the_hold_shows_the_storyboards_words_and_no_wins(waiver_film):
    waiver_film.seek(STRIP_HOLD)
    waiver_film.require_hold('strip')
    assert waiver_film.card_text() == [
        ['#3', 'D. Schultz', 'COOKed', '+20.4', '3 starts'],
        ['#2', 'E. Wilson', 'Aura', '+25.7', '6 starts'],
        ['#1', 'J. Love', 'Sausage', '+40.5']]
    assert waiver_film.strip_text() == [' '.join((week[0], week[2])) for week in LOVE_STRIP]
    assert waiver_film.dimmed() == {'3': True, '2': True, '1': False}
    assert 'win' not in waiver_film.all_text().lower()
    assert waiver_film.errors == []


def test_nothing_is_drawn_before_its_bar_line(waiver_film):
    waiver_film.seek(51.5)
    assert waiver_film.shown() == {'head': True, '3': False, '2': False, '1': False, 'weeks': False}
    waiver_film.seek(53)
    assert waiver_film.shown() == {'head': True, '3': True, '2': True, '1': False, 'weeks': False}
    waiver_film.seek(53.5)
    assert waiver_film.shown() == {'head': True, '3': True, '2': True, '1': False, 'weeks': False}
    assert waiver_film.errors == []


def test_reduced_motion_is_wired_into_the_application(mount):
    film = WaiversFilm(mount.browser, 390, 844, reduced=True)
    with film:
        film.load()
        film.seek(57.8)   # 2026-11-05 (David reapproved, +2 s Chapter 3). ~~57~~.
        film.require_hold('strip')
        film.seek(51)
        film.require_hold('pair')
        assert film.shown() == {'head': True, '3': True, '2': True, '1': False, 'weeks': False}
        assert film.visibility() == {'trades': False, 'draft': False}
        assert film.errors == []


@pytest.mark.parametrize('resource', ['**/heads/lg/jordan-love.webp', '**/heads/lg/dalton-schultz.webp', '**/assets/big-shoulders.ttf'])
def test_play_waits_for_each_required_asset_after_base_initialization(mount, resource):
    film = WaiversFilm(mount.browser, 390, 844)
    with film:
        film.load_with_delayed_asset(resource)
        assert film.assets_ready() and film.errors == []


def test_a_failed_new_asset_disposes_the_prepared_scene(mount):
    film = WaiversFilm(mount.browser, 390, 844)
    with film:
        assert film.fail_portrait_after_base_ready() == 1


def test_seeking_back_removes_future_cards_and_other_chapters(waiver_film):
    waiver_film.seek(STRIP_HOLD)
    waiver_film.seek(51)
    assert waiver_film.shown() == {'head': True, '3': False, '2': False, '1': False, 'weeks': False}
    assert waiver_film.visibility() == {'trades': False, 'draft': False}
    waiver_film.seek(47.5)
    assert not waiver_film.card_shown()
    assert waiver_film.errors == []
