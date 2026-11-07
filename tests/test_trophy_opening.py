"""The opening is finite, deterministic, and safe to inspect without motion."""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TIMELINE = ROOT / "showcase/madden-curse/timeline.mjs"


def moment(time, reduced=False):
    source = (f"import {{openingMoment}} from {json.dumps(TIMELINE.as_uri())};"
              f"console.log(JSON.stringify(openingMoment({time}, {str(reduced).lower()})));")
    result = subprocess.run(["node", "--input-type=module", "-e", source],
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize("time,chapter", [(0, "trophy"), (2, "trophy"),
                                          (3.5, "blip"), (8, "logo"), (10, "logo")])
def test_the_camera_follows_trophy_blip_then_logo(time, chapter):
    assert moment(time)["chapter"] == chapter


def test_the_opening_stops_at_six_seconds():
    assert moment(60) == moment(10)
    assert moment(10)["complete"] is True


def test_reduced_motion_shows_the_complete_composition():
    assert moment(0, reduced=True) == moment(12)


def test_negative_seek_stays_at_the_beginning():
    assert moment(-1) == moment(0)
