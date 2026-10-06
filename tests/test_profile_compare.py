"""Compare, opened from the profile's head, and the head rail that holds its button. The test that presses
Back to close the layer is test_profile_journeys.py. Each test mounts the roster and works through
pages/profile.py (see test_profile.py)."""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster import on_roster

REQ = "The profile modal"
ST_BROWN = "Amon-Ra St. Brown"


@pytest.mark.render
@pytest.mark.req(REQ, ac="a search pick joins the set, the lists come back and the box never keeps a stale query")
def test_compare_search_reaches_any_player(mount):
    """A search pick joins the set and the lists come back; the box never keeps a stale query."""
    profile, errors = on_roster(mount)
    profile.open_from_roster(ST_BROWN)
    profile.compare_open()
    profile.compare_search("kittle")
    assert profile.compare_rows_named("Kittle") == 1
    profile.compare_pick_named("Kittle")
    assert profile.compare_query() == ""
    assert profile.compare_picked("Kittle") == 1
    profile.press_escape()
    assert profile.compare_layers() == 0
    assert profile.is_open()
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="a tap on another card moves the graph's focus and the labels follow it")
def test_compare_card_tap_moves_the_graph_focus(mount):
    """Three receivers on one graph (storyboard v5): the profile's player is in focus first, his
    ranks on the labels; a tap on another card moves the focus and the labels follow it."""
    profile, errors = on_roster(mount, (360, 800))
    profile.open_from_roster(ST_BROWN)
    profile.compare_pick_two("wr")
    assert profile.compare_shapes() == 3
    before = profile.compare_graph_ranks()
    assert "cmp-s0" in profile.compare_graph_class()
    profile.compare_card(1)
    assert profile.compare_focus() == "1"
    assert "cmp-s1" in profile.compare_graph_class()
    assert profile.compare_front_shapes(1) == 1
    assert profile.compare_graph_ranks() != before
    assert profile.compare_graph_buttons() == 0              # labels choose nothing here
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("size", [(1280, 720), (1400, 900), (360, 800)])
@pytest.mark.req(REQ, ac="the Compare sheet opens without scrolling on a desktop and a 360x800 phone")
def test_compare_sheet_opens_without_scrolling(mount, size):
    """David, 2026-09-30: "it should open up without having to scroll". A desktop puts the graph
    beside the strips; a 360x800 phone fits the stacked sheet."""
    profile, errors = on_roster(mount, size)
    profile.open_from_roster(ST_BROWN)
    profile.compare_pick_two("wr")
    over = profile.compare_sheet_overflow()
    assert over <= 0, f"the Compare sheet scrolls {over}px at {size}"
    assert errors == []


@pytest.mark.render
@pytest.mark.req(REQ, ac="the head rail orders role, style, sphere, Compare and centres what he has; with only Compare it is a small button")
def test_head_rail_orders_and_centres_what_he_has(mount):
    """The head rail (2026-09-30, rail.js): role, style, the sphere and Compare, always in that
    order, centred under the name on a phone, so a player with fewer has no hole; with nothing but
    Compare there is no rail and Compare is a small button in the name block."""
    profile, errors = on_roster(mount, (360, 800))
    got = profile.rail_survey()
    order = ["role", "style", "orb", "cmp"]
    for key, v in got.items():
        if key == "none":
            assert v["small_compare"], "no rail: Compare stays in the name block"
            continue
        kinds = key.split(",")
        assert kinds[-1] == "cmp" and kinds == sorted(kinds, key=order.index), key
        assert v["centred"], f"{key} is not centred"
    assert errors == []
