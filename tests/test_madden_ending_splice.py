"""Approved shorter pickups and original-song ending, November 6, 2026."""
from array import array
from statistics import correlation
import subprocess

import pytest

from scripts import build_lineup_music as music
from test_madden_chapter2 import node


def test_pickups_take_eight_seconds_and_preserve_the_opening():
    plan = node("return (await import(base + '/film.mjs')).filmPlan();")
    beats = {beat['id']: beat for beat in plan['beats']}
    assert [(beats[name]['start'], beats[name]['duration']) for name in ['waiver-claim', 'waiver-starts']] == [(50.077, 6), (56.077, 2)]
    assert beats['trades']['start'] == 44.077
    assert beats['power-board']['start'] == 74.077
    assert plan['duration'] == pytest.approx(98.077)


def test_finale_uses_original_closing_passage_not_another_loop():
    edit = node("return (await import(base + '/music-edit.mjs')).MUSIC_EDIT;")
    assert edit['finale']['at'] == 80.077
    assert edit['finale']['length'] == 24
    assert edit['finale']['source'].endswith('-finale.flac')


def test_splice_preserves_prefix_and_uses_real_tail(monkeypatch):
    monkeypatch.setattr(music, 'RATE', 4)
    original = array('h', [100] * 96)
    ending = array('h', [200] * 64)
    result = music.splice_ending(original, ending, {'at': 4, 'length': 6, 'crossfade': .25, 'fadeOut': .5})
    assert len(result) == 80
    assert result[:30] == original[:30]
    assert list(result[32:74]) == [200] * 42
    assert result[-1] == result[-2] == 0


@pytest.mark.parametrize('change', [{'at': -1}, {'length': 20}, {'crossfade': 0}, {'fadeOut': 7}])
def test_invalid_finale_edit_rejected(monkeypatch, change):
    monkeypatch.setattr(music, 'RATE', 4)
    edit = {'at': 4, 'length': 6, 'crossfade': .25, 'fadeOut': .5, **change}
    with pytest.raises(ValueError, match='Invalid music finale window'):
        music.splice_ending(array('h', [100] * 96), array('h', [200] * 64), edit)


def test_real_ending_can_extend_beyond_the_old_trim(monkeypatch):
    monkeypatch.setattr(music, 'RATE', 4)
    result = music.splice_ending(array('h', [100] * 40), array('h', [200] * 64),
                                {'at': 4, 'length': 6, 'crossfade': .25, 'fadeOut': .5})
    assert len(result) == 80
    assert result[60] == 200


def test_old_false_final_hit_is_removed_and_ident_uses_real_closing_chord():
    result = node("const {ONSETS}=await import(base + '/music-onsets.mjs'); const {filmImpacts,nearestHit}=await import(base + '/film-impacts.mjs'); return {onsets:ONSETS,ident:filmImpacts().filter(hit=>hit.name==='Ident lands').map(hit=>({...hit,reference:nearestHit(hit.at)}))};")
    assert 103.59 not in result['onsets']
    assert result['ident'][0]['at'] == pytest.approx(92.077)
    assert abs(result['ident'][0]['reference']['frames']) <= 2


@pytest.mark.integration
def test_played_file_contains_original_ending_and_reaches_silence():
    config = music.configuration()
    played = music.decode(music.FILM / config['source'])
    ending = music.decode(music.FILM / config['finale']['source'])
    start = round(80.077 * music.RATE) * music.CHANNELS
    offset = music.RATE * music.CHANNELS
    assert len(played) / music.CHANNELS / music.RATE == pytest.approx(104.077, abs=1 / music.RATE)
    assert correlation(played[start + offset:start + offset * 2:100], ending[offset:offset * 2:100]) > .99
    assert max(abs(value) for value in played[-music.CHANNELS * 100:]) < 20


@pytest.mark.integration
def test_accepted_early_music_is_unchanged_and_download_does_not_grow(tmp_path):
    config = music.configuration()
    played = music.decode(music.FILM / config['source'])
    legacy = music.extend(music.decode(music.FILM / config['baseSource']), config['extension'])
    reference = tmp_path / 'legacy.mp3'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 's16le', '-ar', str(music.RATE), '-ac', str(music.CHANNELS),
                    '-i', '-', '-c:a', 'libmp3lame', '-b:a', music.BITRATE, str(reference)], input=legacy.tobytes(), check=True)
    base = music.decode(reference)
    start, end = 8 * music.RATE * music.CHANNELS, 44 * music.RATE * music.CHANNELS
    assert correlation(played[start:end:100], base[start:end:100]) > .999
    assert (music.FILM / config['source']).stat().st_size < 2_600_000
