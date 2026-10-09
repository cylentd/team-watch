"""Start/Sit's lineup card (ledger #94, draft A): the build's one map from a player to our call on him, so
the card marks a reader's player SMASH, START or SIT without searching the lists itself (design/startsit_v3.py)."""
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
import startsit_v3  # noqa: E402

SMASH = {"name": "Josh Allen", "pos": "QB", "rank": 1}
START = {"name": "Cam Skattebo", "pos": "RB", "call": "START", "margin_spots": 10.5}
SIT = {"slug": "ollie-gordon-ii", "name": "Ollie Gordon II", "pos": "RB", "call": "sit", "margin_spots": 7}


@pytest.mark.req("Start/Sit", ac="the lineup marks each player with our call")
def test_each_called_player_maps_to_his_one_call():
    got = startsit_v3.live_ss3({"week": 5, "smash": [SMASH], "takes": [START, SIT]}, slugify)
    assert got["calls"] == {"josh-allen": "SMASH", "cam-skattebo": "START", "ollie-gordon-ii": "SIT"}
    contract.validate("LIVE_SS3", got)


@pytest.mark.req("Start/Sit", ac="the lineup marks each player with our call")
def test_a_player_on_both_lists_wears_smash():
    """SMASH is the stronger call: a player ff-jarvis also lists as a bold START keeps the one tag."""
    both = {**START, "name": "Josh Allen", "pos": "QB"}
    got = startsit_v3.live_ss3({"week": 5, "smash": [SMASH], "takes": [both]}, slugify)
    assert got["calls"] == {"josh-allen": "SMASH"}


@pytest.mark.req("Start/Sit", ac="the lineup marks each player with our call")
@pytest.mark.parametrize("block, week", [(None, None), ({}, None), ({"week": 5, "smash": [SMASH], "takes": [START]}, 6)],
                         ids=["no-block", "empty", "another-week"])
def test_no_calls_this_week_is_an_empty_map(block, week):
    got = startsit_v3.live_ss3(block, slugify, week=week)
    assert got["calls"] == {}
    contract.validate("LIVE_SS3", got)
