"""S11, one number per player in every view that prints his week: Ranks, the Roster and the profile show the same
projection, and none of them works one out (CLAUDE.md "Data": `pts` of the projections row is the single home).

test_ranks_one_projection.py proves the build side in Python. This file proves what a reader sees: the same player,
opened in Ranks, on the Roster and in the profile each opens, prints one number; and a number planted in the data
(88.8, which no fixture player has) comes out of each view unchanged, so a view that worked its own figure out of
other fields would print something else.

Not proved here: the Digest, Start/Sit, the compare sheet and the other views that print a projection; and that a
view does no arithmetic anywhere in its code, which no output test can show.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.one_number import OneNumber

PLANTED = 88.8      # no fixture player projects this many points
SIZE = (1400, 900)
SURFACES = ["roster", "ranks"]


def drawn_then_profile(view, surface, player):
    """The number the view prints for the player, then the number in the profile that row opens."""
    drawn = view.roster_number(player) if surface == "roster" else view.ranks_number(player)
    (view.open_from_roster if surface == "roster" else view.open_from_ranks)(player)
    return drawn, view.profile_number()


@pytest.mark.render
@pytest.mark.parametrize("surface", SURFACES)
def test_a_view_and_the_profile_it_opens_print_the_players_projection(mount, surface):
    page, errors = mount(surface, size=SIZE)
    view = OneNumber(page)
    player = view.shared_player()
    assert drawn_then_profile(view, surface, player) == (view.data_number(player["slug"]),) * 2, player["n"]
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("surface", SURFACES)
def test_a_planted_projection_comes_out_of_each_view_unchanged(mount, surface):
    page, errors = mount(surface, size=SIZE)
    view = OneNumber(page)
    player = view.shared_player()
    view.plant(player["slug"], PLANTED)
    assert drawn_then_profile(view, surface, player) == (f"{PLANTED:.1f}",) * 2, surface
    assert errors == []
