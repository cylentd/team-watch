"""Chapter 5 (docs/madden-film-chapter5.md): the power-rankings beats' timing, the music tail and the returning ident."""
import pytest

from test_madden_chapter2 import node


MUSIC_TAIL_PLAYS_THE_SONGS_OWN_ENDING_UNDER_THE_CLOSE_SCRIPT = ("""const {MUSIC_EDIT} = await import(base + '/music-edit.mjs');
const {ONSETS} = await import(base + '/music-onsets.mjs');
const {nearestHit} = await import(base + '/film-impacts.mjs');
const cues = [64.077, 66.077, 68.077, 70.077, 72.077, 74.077, 76.077];
return {repeats: MUSIC_EDIT.extension.repeats, onsets: ONSETS, frames: cues.map(cue => nearestHit(cue).frames)};""")

IDENT_RETURNS_ACROSS_THE_CLOSE_IDENT_EVENT_AND_HOLDS_TO_THE_END_SCRIPT = ("""const {identAt} = await import(base + '/film-ident.mjs');
const {filmPlan} = await import(base + '/film.mjs');
return {before: [74.1, 84.1, 91.4].map(identAt), rising: [91.7, 91.9].map(identAt),
  held: [92.1, filmPlan().duration].map(identAt), opening: identAt(1)};""")


def test_power_beats_extend_the_film_to_one_hundred_six_seconds_without_moving_earlier_starts():
    plan = node("return (await import(base + '/film.mjs')).filmPlan();")
    selected = [beat for beat in plan['beats'] if beat.get('chapter') == 5]
    # 2026-11-05 (ch4/5 cinematic): ~~12, 8~~; ~~86.077, 98.077~~; ~~106.077~~; the first 12 ended ~~62.077, 74.077~~.
    assert [(beat['id'], beat['duration']) for beat in selected] == [('power-board', 10), ('power-close', 14)]
    assert [beat['start'] for beat in selected] == pytest.approx([74.077, 84.077])
    assert plan['duration'] == pytest.approx(98.077)
    assert [beat['start'] for beat in plan['beats'][:12]] == pytest.approx(
        [7.584, 16.077, 20.077, 24.077, 28.077, 36.077, 40.077, 44.077, 50.077, 56.077, 58.077, 66.077])


def test_power_close_travels_on_the_same_set_after_one_scene_wipe():
    changes = node("return (await import(base + '/film.mjs')).sceneChanges().slice(-2);")
    # 2026-11-05 (ch4/5 cinematic): the crane from Chapter 4's rack is a travel, ~~('power-board', 'across')~~.
    assert [(change['to'], change['kind']) for change in changes] == [('power-board', 'travel'), ('power-close', 'travel')]


def test_power_impacts_land_on_bar_lines():
    hits = node("""const {filmImpacts, nearestHit} = await import(base + '/film-impacts.mjs');
return filmImpacts().filter(hit => hit.at >= 74).map(hit => ({...hit, reference: nearestHit(hit.at)}));""")
    # 2026-11-05 (ch4/5 cinematic): ~~from 86~~: ~~'Cut to power-board': 86.077, 'Plates settle': 88.077, 'Top six
    # settle': 92.077, 'Sausage #3 power': 96.077, 'Cut to power-close': 98.077, 'Top four settle': 100.077, "Still
    # anyone's game lands": 102.077~~. The ident lands on the song's last hit, an onset, not a bar line.
    # 2026-11-05 (David: "Chapter 5 isnt power ranking", "We dont have a good ending?"): standings shuffle into
    # power order, the trophy returns. ~~'Places 7-12 land': 80.077, 'Top six land': 82.077, 'Sausage #3 power':
    # 86.077, 'Blip lands': 90.077, 'File shuts': 92.077, 'Tail begins': 94.077~~.
    assert {hit['name']: hit['at'] for hit in hits} == pytest.approx(
        {'Cut to power-board': 74.077, 'Standings land': 76.077, 'Power order': 78.077, 'Sausage plate lifts': 80.077,
         'Better than the record.': 82.077, 'Cut to power-close': 84.077, 'Top four settle': 84.077, 'Wide': 86.077,
         'Trophy lands': 88.077, 'Blip lands': 90.077, 'Ident lands': 92.077})
    assert all(abs(hit['reference']['frames']) <= 2 for hit in hits)


def test_music_tail_plays_the_songs_own_ending_under_the_close():
    result = node(MUSIC_TAIL_PLAYS_THE_SONGS_OWN_ENDING_UNDER_THE_CLOSE_SCRIPT)
    # 2026-11-05 (ch4/5 cinematic): ~~repeats 5~~; ~~111.59 in, 95.59 and 109.59 out~~; ~~cues 66.077-84.077~~.
    assert result['repeats'] == 4
    # The song's own tail starts at asset 100.077 (68.077 + 4 x 8), so its last hit, read-hold 71.59, lands at 103.59.
    assert any(abs(onset - 98.074) < .001 for onset in result['onsets'])
    assert 103.59 not in result['onsets'] and 111.59 not in result['onsets']
    assert all(abs(frames) <= 2 for frames in result['frames'])


def test_ident_returns_across_the_close_ident_event_and_holds_to_the_end():
    opacity = node(IDENT_RETURNS_ACROSS_THE_CLOSE_IDENT_EVENT_AND_HOLDS_TO_THE_END_SCRIPT)
    # 2026-11-05 (ch4/5 cinematic): ~~before 86.1, 98.1, 103.9; rising 104.2, 104.4; held 105~~.
    assert opacity['before'] == [0, 0, 0]
    assert 0 < opacity['rising'][0] < opacity['rising'][1] < 1
    assert opacity['held'] == pytest.approx([1, 1])
    assert opacity['opening'] == pytest.approx(1)


def test_the_beat_menu_names_both_power_beats():
    beats = node("return (await import(base + '/film-copy.mjs')).FILM_COPY.review.beats;")
    assert beats['power-board'] == 'Power rankings' and beats['power-close'] == "Still anyone's game"
