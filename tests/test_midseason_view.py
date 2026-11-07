"""The Madden Curse edition's entry, team navigation, evidence and responsive layout."""
import json
import re

import pytest

from component import Mounter, mount
from midseason import midseason_special
from pages.midseason import MidseasonPage

pytestmark = pytest.mark.render


def edition_fragment(fragment, through=7):
    match = re.search(r"const LIVE_LEAGUE_YAHOO = (.*?);\n", fragment)
    league = json.loads(match.group(1))
    games = [{"week": week, "home": home, "away": away, "hp": points, "ap": against, "winner": "home"}
             for week in range(1, through + 1) for home, away, points, against in [(9, 10, 100, 90), (3, 7, 120, 80)]]
    league["midseason"] = midseason_special({"league_id": 75203, "season": 2026, "teams": {
        str(team["id"]): {} for team in league["teams"]}, "games": games})
    return fragment[:match.start()] + "const LIVE_LEAGUE_YAHOO = " + json.dumps(league) + ";\n" + fragment[match.end():]


@pytest.fixture(scope="module")
def special(mount, built, tmp_path_factory):
    mounter = Mounter(mount.browser, tmp_path_factory.getbasetemp() / "component-midseason", edition_fragment(built.fragment))
    yield mounter
    mounter.pages.close()


@pytest.fixture
def final_special(mount, built, tmp_path_factory):
    mounter = Mounter(mount.browser, tmp_path_factory.getbasetemp() / "component-midseason-final", edition_fragment(built.fragment, 8))
    yield mounter
    mounter.pages.close()


def test_watch_opens_the_special_and_back_returns_to_the_recap(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    assert show.visible()
    show.close()
    assert show.entry_visible() and not show.visible()
    assert errors == []


def test_preview_keeps_week_eight_editorial_hidden_until_final(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    assert "the race is crowded" in show.news().inner_text().lower()
    assert show.news().locator(".ms-form-row").count() == 4
    assert "2,730.00" not in show.news().inner_text()


def test_preview_next_story_keeps_week_eight_editorial_hidden(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    show.next_story()
    assert "the scoring race" in show.news().inner_text().lower()
    assert show.report().count() == 0
    assert show.news().locator("iframe").count() == 0
    assert errors == []


def test_the_picker_and_next_button_change_the_spotlight(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    show.pick(9)
    assert show.name() == "Chat Take the Wheel"
    show.next()
    assert show.name() == "Jaxon The Box" and show.selected() == "10"
    assert show.next_focused() and errors == []


def test_read_report_places_the_heading_below_the_phone_chrome(final_special):
    page, errors = final_special("recap", size=(360, 900))
    show = MidseasonPage(page)
    show.open()
    show.read_report()
    assert 100 <= show.report_heading_top() <= 200
    assert errors == []


def test_final_show_leads_to_player_focused_reporting(final_special):
    page, errors = final_special("recap")
    show = MidseasonPage(page)
    show.open()
    assert show.news().locator("iframe").get_attribute("src") == "showcase/madden-curse/?embed"
    assert show.news().locator(".ms-form-row").count() == 0
    assert show.report().locator("article").count() == 4
    assert show.report().locator("h4").count() == 4


def test_final_reporting_has_player_copy_without_template_tokens(final_special):
    page, errors = final_special("recap")
    show = MidseasonPage(page)
    show.open()
    assert "Matthew Stafford" in show.report().inner_text()
    assert not re.search(r"\{(?:peak|week|rank|points|average)\}", show.report().inner_text())
    assert errors == []


def test_receipts_open_on_the_selected_teams_actual_scores(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    show.pick(9)
    show.open_receipts()
    assert "100.00 points against Jaxon The Box (90.00)" in show.receipt_text()
    assert "14–7–0" in show.receipt_text()
    assert show.chart_rows() == 7 and errors == []


@pytest.mark.parametrize("width", [360, 390, 768, 1280, 1920])
def test_the_longest_team_name_fits_without_sideways_scroll(special, width):
    page, errors = special("recap", size=(width, 900))
    show = MidseasonPage(page)
    show.open()
    show.pick(3)
    assert "WE SELL EXTENDED WARREN-TY" in show.stage_text()
    assert show.overflow() == 0
    assert errors == []


def test_reduced_motion_turns_off_the_broadcast_transition(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    show.reduce_motion()
    show.pick(9)
    assert show.motion() == "none"
    show.restore_motion()
    assert errors == []


def test_opening_choreographs_identity_scores_then_the_desk_take(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.open()
    identity, headline, roast, hype, bars, lower = show.broadcast_cues()
    assert all(cue["name"] != "none" and cue["iterations"] == "1"
               and 0 < cue["duration"] + cue["delay"] <= 1 for cue in [identity, headline, roast, hype, bars, lower])
    assert identity["delay"] < bars["delay"] < roast["delay"] < hype["delay"]
    assert headline["delay"] < roast["delay"]
    finished = show.finish_broadcast()
    assert finished["before"] == finished["after"] and finished["running"] == 0
    assert errors == []


def test_reduced_motion_disables_every_cue_on_open_and_team_change(special):
    page, errors = special("recap")
    show = MidseasonPage(page)
    show.reduce_motion()
    show.open()
    assert all(cue["name"] == "none" for cue in show.broadcast_cues())
    show.pick(9)
    assert all(cue["name"] == "none" for cue in show.broadcast_cues())
    assert show.name() == "Chat Take the Wheel" and errors == []
    show.restore_motion()
