"""Chapter 17 (2026-11-04): THE MADDEN CURSE lands one word at a time, each on its own hit of the three-hit
"dun dun dunnn" at film 4-5 s (David's cue): THE on OPENING.logoAt with Blip's last landing, CURSE last with the
biggest hit. The opening then runs to the guitar's entry. The words' onsets and the opening's length live in
timing.json; the words' size in film-title-drop.mjs TITLE_DROP."""
import pytest

from test_madden_stage_polish import stage_result

WORDS = ['THE', 'MADDEN', 'CURSE']


PLAN_SCRIPT = ("""
const {OPENING} = await import(base + '/constants.mjs');
const {ONSETS, SYNC, filmTime} = await import(base + '/music-onsets.mjs');
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const {TITLE_DROP, titleWords} = await import(base + '/film-title-drop.mjs');
return {logoAt: OPENING.logoAt, onsets: ONSETS.map(filmTime), frames: SYNC.frames, fps: SYNC.fps,
  at: TITLE_WORDS, words: titleWords(0).map(word => word.word), drop: TITLE_DROP};
""")

EACH_WORD_FALLS_AND_SQUASHES_ON_ITS_OWN_HIT_AND_NOT_BEFORE_SCRIPT = ("""
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const {TITLE_DROP, titleWords} = await import(base + '/film-title-drop.mjs');
const frame = TITLE_DROP.frame;
return TITLE_WORDS.map(at => ({before: titleWords(at - TITLE_DROP.fall - .01), falling: titleWords(at - 3 * frame),
  on: titleWords(at), after: titleWords(at + .5)}));
""")

LAST_WORDS_HIT_IS_THE_BIGGEST_AND_ONLY_IT_SHAKES_THE_CAMERA_SCRIPT = ("""
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const {TITLE_DROP, titleShake} = await import(base + '/film-title-drop.mjs');
const {ringAt} = await import(base + '/film-impact.mjs');
return {hits: TITLE_DROP.hits, shakes: TITLE_WORDS.map(titleShake),
  rings: TITLE_DROP.hits.map(hit => ringAt(.2, hit.ring).radius)};
""")

EVERY_TITLE_WORD_IS_AN_IMPACT_ON_A_HIT_SCRIPT = ("""
const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs');
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const impacts = filmImpacts();
return TITLE_WORDS.map(at => impacts.filter(impact => Math.abs(impact.at - at) < 1e-6).map(impact => ({...impact, ...nearestHit(impact.at)})));
""")

OPENING_RUNS_TO_THE_GUITARS_ENTRY_AND_HANDS_OVER_FROM_THE_FANFARES_LAST_HIT_SCRIPT = ("""
const {OPENING, FILM, TRANSITION} = await import(base + '/constants.mjs');
const {nearestHit} = await import(base + '/film-impacts.mjs');
const {TITLE_WORDS} = await import(base + '/timing.mjs');
const handover = OPENING.duration - TRANSITION.intro / 2;
return {duration: OPENING.duration, chapter: FILM.chapterAt, start: nearestHit(OPENING.duration),
  handover: nearestHit(handover), hold: handover - TITLE_WORDS[TITLE_WORDS.length - 1]};
""")

SHEET_WITH_NO_TITLE_WORDS_FAILS_AT_LOAD_SCRIPT = ("""
const {checkTiming} = await import(base + '/timing.mjs');
const beat = {id: 'board', duration: 4, hold: 1, events: []};
return [{beats: [beat]}, {beats: [beat], opening: {titleWords: [2, 1]}}].map(sheet => {
  try { checkTiming(sheet); return 'passed'; } catch (error) { return error.message; } });
""")


def plan():
    return stage_result(PLAN_SCRIPT)


def test_each_word_lands_on_its_own_consecutive_onset_the_last_on_the_titles():
    got = plan()
    assert got['words'] == WORDS
    assert len(got['at']) == len(WORDS) and got['at'] == sorted(got['at'])
    assert got['at'][0] == pytest.approx(got['logoAt'])
    assert all(4 <= at <= 5 for at in got['at']), 'the three-hit David hears at 4-5 s'
    onsets = got['onsets']
    picked = [min(range(len(onsets)), key=lambda index: abs(onsets[index] - at)) for at in got['at']]
    assert all((abs(at - onsets[index]) * got['fps'] <= got['frames']) for (at, index) in zip(got['at'], picked)), [(at, onsets[index]) for (at, index) in zip(got['at'], picked)]
    assert picked == list(range(picked[0], picked[0] + len(WORDS))), 'three consecutive onsets'


def test_each_word_falls_and_squashes_on_its_own_hit_and_not_before():
    states = stage_result(EACH_WORD_FALLS_AND_SQUASHES_ON_ITS_OWN_HIT_AND_NOT_BEFORE_SCRIPT)
    assert all((state['before'][index]['visible'] is False) for (index, state) in enumerate(states))
    assert all((state['falling'][index]['visible'] and state['falling'][index]['drop'] > 0) for (index, state) in enumerate(states))
    assert all((state['on'][index]['drop'] == 0 and state['on'][index]['squash']) for (index, state) in enumerate(states))
    assert all((state['after'][index]['drop'] == 0 and (not state['after'][index]['squash'])) for (index, state) in enumerate(states))
    assert all((all((not word['visible'] for word in state['on'][index + 1:] if word['age'] < -0.31))) for (index, state) in enumerate(states))
    assert all((all((word['drop'] == 0 for word in state['on'][:index]))) for (index, state) in enumerate(states)), ['an earlier word stays down' for (index, state) in enumerate(states)]


def test_the_last_words_hit_is_the_biggest_and_only_it_shakes_the_camera():
    got = stage_result(LAST_WORDS_HIT_IS_THE_BIGGEST_AND_ONLY_IT_SHAKES_THE_CAMERA_SCRIPT)
    hits, last = got['hits'], got['hits'][-1]
    assert len(hits) == len(WORDS)
    assert all((last['ring'] > earlier['ring'] and last['sparks'] > earlier['sparks'] and (last['flash'] >= earlier['flash'])) for earlier in hits[:-1])
    assert got['rings'][-1] > max(got['rings'][:-1])
    assert got['shakes'][-1] != [0, 0]
    assert all(shake == [0, 0] for shake in got['shakes'][:-1])


def test_the_words_span_about_seventy_percent_of_the_frame_with_caps_fourteen_percent_tall():
    drop = plan()['drop']
    assert drop['desk']['width'] == pytest.approx(.7, abs=.02)
    assert .14 <= drop['desk']['cap'] <= .16   # a ceiling: at 16:9 the width sets caps of ~14% (the stills)
    assert drop['phone']['rows'] == [[0, 1], [2]] and drop['desk']['rows'] == [[0, 1, 2]]
    # Rule 25: no character under 2% of the frame height; the phone's caps are set by its width.
    assert drop['phone']['width'] > .8


def test_every_title_word_is_an_impact_on_a_hit():
    got = stage_result(EVERY_TITLE_WORD_IS_AN_IMPACT_ON_A_HIT_SCRIPT)
    assert all((found and all((abs(hit['frames']) <= 2 and hit['kind'] == 'onset' for hit in found))) for found in got)


def test_the_opening_runs_to_the_guitars_entry_and_hands_over_from_the_fanfares_last_hit():
    got = stage_result(OPENING_RUNS_TO_THE_GUITARS_ENTRY_AND_HANDS_OVER_FROM_THE_FANFARES_LAST_HIT_SCRIPT)
    assert got['chapter'] == got['duration'] == pytest.approx(7.584)
    assert got['start']['kind'] == 'onset' and abs(got['start']['frames']) <= 2
    assert got['handover']['kind'] == 'onset' and abs(got['handover']['frames']) <= 2
    assert got['hold'] >= 2, 'the payoff holds about 2 s (rule 16)'


def test_a_sheet_with_no_title_words_fails_at_load():
    message = stage_result(SHEET_WITH_NO_TITLE_WORDS_FAILS_AT_LOAD_SCRIPT)
    assert all(text != 'passed' and 'titleWords' in text for text in message), message
