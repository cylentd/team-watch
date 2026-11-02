"""S11, one number per player: Start/Sit, the Compare sheet and League > Teams print the player's projection, and a number
planted where each view reads it (88.8, which no fixture player has) comes out unchanged.

test_one_number_every_view.py does Ranks, the Roster and the profile; this file adds the three more views that read
a projection. Start/Sit and the Compare sheet read the projections row, so the plant goes there. Teams reads the copy the
build cut from that row into LIVE_TEAMS, so the plant goes there and the first test proves the copy equals the row.

Not proved here: the Digest, whose SMASH card prints LIVE_SS3's own `pts`, not the projections row (S11 finding,
2026-11-01); and that a view does no arithmetic anywhere in its code, which no output test can show.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.one_number_more import open_view

PLANTED = 88.8      # no fixture player projects this many points
SURFACES = ["startsit", "compare", "teams"]


@pytest.mark.render
@pytest.mark.parametrize("surface", SURFACES)
def test_a_view_prints_the_players_projections_row_number(mount, surface):
    view, errors = open_view(mount, surface)
    player = view.player()
    assert view.number(player) == view.data_number(player), surface
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("surface", SURFACES)
def test_a_planted_projection_comes_out_of_the_view_unchanged(mount, surface):
    view, errors = open_view(mount, surface)
    player = view.player()
    view.plant(player, PLANTED)
    assert view.number(player) == f"{PLANTED:.1f}", surface
    assert errors == []
