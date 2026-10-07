"""The roster as a lineup sheet (2026-09-25): full-size rows on a phone in the cards' frame (it was
squeezed to one screen, and David found it read small), the bench beside the starters on a
desktop. Runs on the ESPN fixture, the one with a bench.

Component tests (2026-10-06): the roster mounted (`mount`), read through `RosterSheet`
(tests/pages/roster_sheet.py)."""
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.roster_sheet import RosterSheet


def espn_roster(mount, size):
    """The ESPN team's roster as the Sheet, mounted at a size: (RosterSheet, errors)."""
    page, errors = mount("roster", size=size, heads=True)     # the headshot files beside the page, as served
    return RosterSheet(page), errors


@pytest.mark.render
def test_a_phone_row_is_full_size(mount):
    sheet, errors = espn_roster(mount, (360, 660))
    heads = sheet.head_widths()
    assert heads and min(heads) >= 40, heads
    slots = sheet.starter_slots()
    assert slots and not any(re.search(r"\d", s) for s in slots), slots   # RB1 prints RB, FLX2 prints FLX
    # The bench is one to a row, like the starters: every bench row as wide as a starter row.
    widths = sheet.row_widths()
    assert len(widths) == 1, widths
    assert errors == []


@pytest.mark.render
def test_a_starter_row_shows_usage_and_a_td_chance(mount):
    """Usage by position where the snap-share line was, and the TD chance under the projection
    only from 25% up (2026-09-25, storyboard option A)."""
    sheet, errors = espn_roster(mount, (1280, 900))
    assert sheet.trend_lines() == 0, "the snap-share line is gone"
    words = sheet.usage_words()
    assert set(words) <= {"targets", "touches", "dropbacks"}, words
    # The fixture's props give no roster player a TD line: plant 47 (lime), 30 and 24 (under the 25% floor).
    assert len(sheet.plant_td_chances([47, 30, 24])) == 3, "three projected starters to plant on"
    shown = sheet.td_chances()
    assert shown, "the fixture must draw a TD chance"
    assert sorted(shown) == [30, 47], shown                  # 24 is under the floor and stays off the row
    assert all(n >= 25 for n in shown), shown
    assert sheet.every_td_chance_from_25_is_drawn()
    assert errors == []


@pytest.mark.render
def test_an_early_projection_wears_a_label_and_a_lined_or_unstamped_one_does_not(mount):
    """ff-jarvis's `stage` (2026-10-05): "early" = no prop line for his game yet, drawn as an EARLY tag with
    its note; "lined" = the normal state, a hover note and no tag; no field = nothing, and no error.
    Fixture: Purdy early, Chase Brown lined, Kittle unstamped."""
    sheet, errors = espn_roster(mount, (1280, 900))
    got = sheet.stages(["brock-purdy", "chase-brown", "george-kittle"])
    assert got["brock-purdy"] == {"stage": "early", "tag": "EARLY", "rowTip": "",
                                  "tip": "No prop line for this game yet: model, opponent and game total."}, got
    assert got["chase-brown"] == {"stage": "lined", "tag": None, "tip": None,
                                  "rowTip": "Lines are up for this game; blended with his own line if he has one."}, got
    assert got["george-kittle"] == {"stage": None, "tag": None, "tip": None, "rowTip": ""}, got
    assert sheet.early_tags_drawn() == sheet.early_projections()
    assert errors == []


def test_the_projection_cut_carries_stage_and_an_older_feed_without_it_is_no_error():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
    import projections
    slugify = lambda n: n.lower().replace(" ", "-")
    rows = [{"name": "A One", "pos": "QB", "pts": 10.0, "src": "model", "stage": "early"},
            {"name": "B Two", "pos": "QB", "pts": 9.0, "src": "model", "stage": "lined"},
            {"name": "C Three", "pos": "QB", "pts": 8.0, "src": "model"}]
    raw = {"players": rows, "stage": {"early": 1, "lined": 1}}
    out = projections.live_projections(raw, slugify, {"a-one", "b-two", "c-three"})
    assert [out["players"][s]["stage"] for s in ("a-one", "b-two", "c-three")] == ["early", "lined", None]
    assert out["meta"]["stage"] == {"early": 1, "lined": 1}
    assert projections.live_projections({"players": rows[2:]}, slugify, {"c-three"})["meta"]["stage"] is None


@pytest.mark.render
@pytest.mark.parametrize("width", [360, 1100, 1280])
def test_no_name_loses_its_end(mount, width):
    """A long name wraps to a second line, never ends in "..." (2026-09-25: "Tetairoa McMill..."
    at 1280, nearly every name at 1100). The check measures the text itself against its cell, so
    an ellipsis set on any ancestor counts."""
    sheet, errors = espn_roster(mount, (width, 900))
    # A third line is clamped away; scrollHeight past the box by more than a descender's 2px says so.
    assert sheet.names_drawn(), "the fixture must draw names to measure"
    assert sheet.names_cut() == []
    assert errors == []


@pytest.mark.render
def test_a_desktop_puts_the_bench_beside_the_starters(mount):
    sheet, errors = espn_roster(mount, (1280, 900))
    cols = sheet.column_corners()
    assert len(cols) == 2 and cols[0]["top"] == cols[1]["top"] and cols[1]["left"] > cols[0]["left"]
    assert errors == []
