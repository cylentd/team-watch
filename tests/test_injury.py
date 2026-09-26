"""design/injury.py: three levels from Sleeper's injury codes, cut to the page's players."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "design"))
from injury import level, live_injury  # noqa: E402


def slug(n):
    return n.lower().replace(" ", "-")


def test_every_code_lands_in_one_level():
    assert [level(c) for c in ("Out", "IR", "PUP", "Sus", "NA", "Doubtful", "Questionable", None)] == \
        ["OUT", "OUT", "OUT", "OUT", "OUT", "D", "Q", None]


def test_only_hurt_players_on_the_page_get_a_row():
    status = {
        "josh jacobs": {"name": "Josh Jacobs", "injury": "NA", "injury_note": "Personal"},
        "dallas goedert": {"name": "Dallas Goedert", "injury": "Doubtful", "injury_note": None},
        "healthy guy": {"name": "Healthy Guy", "injury": None},
        "not rostered": {"name": "Not Rostered", "injury": "Out"},
    }
    got = live_injury(status, slug, {"josh-jacobs", "dallas-goedert", "healthy-guy"})
    assert got == {"players": {
        "josh-jacobs": {"s": "OUT", "code": "NA", "note": "Personal"},
        "dallas-goedert": {"s": "D", "code": "Doubtful", "note": None},
    }}
    assert live_injury({}, slug, set()) is None
