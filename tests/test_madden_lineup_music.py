"""The Chapter 4 music edit preserves prior time and inserts whole eight-second phrases."""
import json
import subprocess
from array import array
from pathlib import Path

import pytest

from scripts import build_lineup_music as music


def test_phrase_insertion_preserves_old_prefix_and_moves_only_the_tail(monkeypatch):
    monkeypatch.setattr(music, 'RATE', 4)
    samples = array('h', range(240))
    result = music.extend(samples, {'at': 16, 'from': 4, 'length': 4, 'repeats': 3, 'fade': .25})
    assert len(result) == 336 and result[:126] == samples[:126]
    assert result[130:158] == result[162:190] == result[194:222] == samples[34:62]
    assert result[226:] == samples[130:]


@pytest.mark.parametrize('change', [{'from': -1}, {'length': 20}, {'at': 40}, {'fade': 0}])
def test_impossible_loop_boundaries_are_rejected(monkeypatch, change):
    monkeypatch.setattr(music, 'RATE', 4)
    edit = {'at': 16, 'from': 4, 'length': 4, 'repeats': 3, 'fade': .25, **change}
    with pytest.raises(ValueError, match='Invalid music extension window'):
        music.extend(array('h', range(240)), edit)


@pytest.mark.integration
def test_played_asset_really_covers_the_full_one_hundred_six_second_film():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json',
                             str(root / 'showcase/madden-curse/assets/ascent-to-the-podium-lineups.mp3')],
                            check=True, capture_output=True, text=True)
    # 2026-11-05 (ch4/5 cinematic): four phrase copies, ~~112~~, ~~112 - 6 > 106.077 - .1~~.
    # 2026-11-05 (Chapter 5): two more phrase copies. ~~96~~, ~~96 - 6 > 86.077~~. The film ends 0.08 s past the asset
    # (104.077 vs 104); playback just stops at the asset's end.
    assert float(json.loads(result.stdout)['format']['duration']) == pytest.approx(104.077, abs=.05)
    assert 104.077 - 6 == pytest.approx(98.077)
