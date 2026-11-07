"""Every team gets two seconds inside one finite forty-six-second show."""
import json
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1] / 'showcase/madden-curse/timeline.mjs'


def show(time, reduced=False):
    script = (f'import {{showMoment}} from {json.dumps(SOURCE.as_uri())};'
              f'console.log(JSON.stringify(showMoment({time}, {str(reduced).lower()})));')
    result = subprocess.run(['node', '--input-type=module', '-e', script],
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize('time,chapter', [(0, 'trophy'), (4.5, 'logo'), (8, 'logo'),
                                        (11, 'cold'), (12, 'team'), (35.9, 'team'),
                                        (36, 'cast'), (41, 'cast'), (43, 'final')])
def test_the_sequence_matches_the_approved_storyboard(time, chapter):
    assert show(time)['chapter'] == chapter


@pytest.mark.parametrize('index', range(12))
def test_every_team_has_a_full_two_second_slot(index):
    assert show(12 + index * 2)['teamIndex'] == index
    assert show(13.99 + index * 2)['teamIndex'] == index


def test_the_show_finishes_once_and_never_wraps():
    assert show(44)['complete'] is True
    assert show(60) == show(44)
    assert show(43.99)['complete'] is False


def test_reduced_motion_shows_the_complete_cast():
    assert show(0, True) == show(44)
    assert show(44)['ensemble'] == 1
