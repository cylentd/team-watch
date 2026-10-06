"""Stats > Ranks > Rest of season, in the browser (2026-10-06): the tab, the chart, the list and the profile's block.

David picked storyboard option B ("A doesn't have enough space and shows a lot of numbers, which seems busy"): a bump
chart of the top 10, then a quiet list of rank, name and team, ROS points, and nothing else. The rows, the ESPN
choice, the clamp and the chart's geometry are Node's (tests/test_js_ros.py, test_ros.py); these prove what the screen
draws and what a tap does. Ranks mounts alone (tests/component.py). The variants (no block, no tight ends, one week of
history) mount a page whose injected LIVE_ROS was changed, the way a build with that file would inject it."""
import copy
import json
import re

import pytest

import component
from component import mount  # noqa: F401  (the fixture)
from pages.ros import RosPage
from test_ros import RAW
import ros as ros_cut

PHONE = (360, 740)
DESKTOP = (1280, 800)
BLOCK = ros_cut.live_ros(RAW)
NO_TEAM = 'try { localStorage.removeItem("tw-team"); } catch (e) {}\n'


@pytest.fixture(scope="module")
def variant(browser, built, tmp_path_factory):
    """variant(block_or_None) -> a mount whose page carries that LIVE_ROS."""
    made = []

    def make(block):
        text = re.sub(r"^const LIVE_ROS = .*;$", lambda m: "const LIVE_ROS = " + json.dumps(block).replace("</", "<\\/") + ";",
                      built.fragment, count=1, flags=re.M)
        assert text != built.fragment or block == BLOCK
        m = component.Mounter(browser, tmp_path_factory.mktemp("ros"), text)
        made.append(m)
        return m
    yield make
    for m in made:
        m.pages.close()


def open_ros(mount, size=PHONE, init=(), pos="WR"):
    page, errors = mount("ranks", size=size, init=init)
    ros = RosPage(page)
    ros.pick_view("ros")
    if pos != "RB":
        ros.pick(pos)
    return page, errors, ros


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season is a second view tab, opened in place in the phone's tab row")
def test_ranks_gets_two_view_tabs_in_the_tab_row_and_the_second_opens_the_rest_of_season(mount):
    page, errors = mount("ranks", size=PHONE)
    ros = RosPage(page)
    assert ros.view_tabs() == [("This week", True), ("Rest of season", False)]
    assert ros.tiers() > 0, "This week is today's Ranks, unchanged"
    ros.pick_view("ros")
    assert ros.view_tabs() == [("This week", False), ("Rest of season", True)]
    assert ros.chips() == ["QB", "RB", "WR", "TE"], "no FLEX, D/ST or K: the value covers four positions"
    assert ros.tiers() == 0 and ros.surface() == "ranks"
    assert ros.fits() and errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: the chart is the top 10, then a quiet list of rank, name and points")
def test_the_phone_draws_the_top_ten_as_a_chart_then_rank_name_team_and_points(mount):
    page, errors, ros = open_ros(mount)
    chart, rows = ros.chart(), ros.rows()
    assert ros.pressed_chip() == "WR" and "half-PPR" in ros.sub()
    assert [ln["slug"] for ln in chart["lines"]] == [r["slug"] for r in rows[:10]]
    assert [ln["lead"] for ln in chart["lines"]] == [True] * 3 + [False] * 7
    assert chart["weeks"] == ["wk 3", "wk 4", "wk 5"] and len(chart["labels"]) == 10
    assert chart["labels"][0] == "J. Smith-Njigba"
    assert all(ln["line"] and ln["points"] == 3 for ln in chart["lines"][:3])
    first, pts = rows[0], str(int(next(p for p in RAW["players"] if p["slug"] == rows[0]["slug"])["ros_pts"] + 0.5))
    assert (first["rank"], first["name"], first["team"], first["pts"]) == (1, "J. Smith-Njigba", "SEA", pts)
    assert first["text"] == f"1 J. Smith-Njigba SEA {pts}", "nothing else on a row: no arrows, sparklines or extra numbers"
    assert [r["rank"] for r in rows] == sorted(r["rank"] for r in rows) and len(rows) == 13
    assert ros.fits() and errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: the phone's chart starts the data, the list follows it")
def test_at_360_the_chart_leads_and_the_first_row_follows_it(mount):
    page, errors, ros = open_ros(mount)
    top, row = ros.chart_top(), ros.first_row_top()
    print(f"ros 360: chart top {top}px, first row {row}px")
    assert top <= 200, "the chart is the first data, as STYLE.md's budget asks"
    assert row > top + ros.chart()["box"]["h"] - 1, "the list sits under the chart"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a position chip changes the list and the chart")
def test_a_chip_swaps_the_position_and_the_position_is_shared_with_this_week(mount):
    page, errors, ros = open_ros(mount, pos="RB")
    assert ros.pressed_chip() == "RB" and {r["slug"] for r in ros.rows()} >= {"breece-hall", "chase-brown"}
    ros.pick("TE")
    assert ros.pressed_chip() == "TE" and {r["slug"] for r in ros.rows()} >= {"george-kittle"}
    ros.pick_view("week")
    assert ros.pressed_chip() == "TE", "one filter, one setting: This week opens on the same position"
    ros.pick("FLEX")
    ros.pick_view("ros")
    assert ros.pressed_chip() == "RB", "FLEX has no rest of season: the list falls back to RB"
    ros.pick_view("week")
    assert ros.pressed_chip() == "FLEX", "and This week still has FLEX"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a row opens the profile, which carries the Rest of season block")
def test_a_row_opens_the_profile_with_his_rest_of_season_block(mount):
    page, errors, ros = open_ros(mount)
    ros.open_row("amonra-st-brown")
    block = ros.profile_block()
    raw = next(p for p in RAW["players"] if p["slug"] == "amonra-st-brown")
    assert block["pts"] == str(int(raw["ros_pts"] + 0.5))
    assert block["lead"].endswith("#2 WR") and "week 5 to 17" in block["lead"]
    assert block["pg"] == f"{raw['ros_pg']:.1f}"
    assert block["games"] == f"{raw['games_left']:.1f} of {raw['sched_left']} games"
    assert block["chart"]["line"] and block["chart"]["dots"] == 3 and block["chart"]["weeks"] == ["wk 3", "wk 4", "wk 5"]
    assert block["chart"]["axis"][0] == "#1"
    assert "ESPN" not in block["note"] and "Half-PPR" in block["note"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a chart label opens the same profile")
def test_a_chart_label_opens_the_profile_too(mount):
    page, errors, ros = open_ros(mount)
    profile = ros.open_label("chris-olave")
    assert profile.title().lower() == "chris olave" and ros.profile_block()["lead"].endswith("#4 WR")
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a player the file lacks has no block")
def test_a_player_outside_the_file_has_no_block_and_no_error(mount):
    page, errors = mount("ranks", size=PHONE)
    page.evaluate("openProfile({n: 'Nobody Here', pos: 'WR', team: 'SEA', slug: 'nobody-here'})")
    page.wait_for_selector("#modal.on")
    assert RosPage(page).profile_block() is None
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: an ESPN team reads ESPN's numbers and says they are not backtested")
def test_an_espn_team_reads_espn_numbers_and_says_they_are_not_backtested(mount):
    page, errors, ros = open_ros(mount)
    half = ros.rows()
    assert "half-PPR" in ros.sub() and "ESPN" not in ros.sub()
    ros.pick_team("espn")
    page.wait_for_function("document.querySelector('[data-testid=ros-sub]').textContent.includes('ESPN')")
    espn = ros.rows()
    wilson = next(r for r in espn if r["slug"] == "michael-wilson")
    raw = next(p for p in RAW["players"] if p["slug"] == "michael-wilson")
    assert wilson["rank"] == raw["espn"]["rank"] == 13 and wilson["pts"] == str(int(raw["espn"]["ros_pts"] + 0.5))
    assert [r["slug"] for r in espn] != [r["slug"] for r in half]
    assert "ESPN-scaled" in ros.sub() and "not backtested" in ros.sub()
    ros.open_row("michael-wilson")
    assert "ESPN-scaled" in ros.profile_block()["note"] and "not backtested" in ros.profile_block()["note"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: no team picked reads half-PPR")
def test_no_team_picked_reads_half_ppr(mount):
    page, errors, ros = open_ros(mount, init=(NO_TEAM,))
    assert "half-PPR" in ros.sub() and "ESPN" not in ros.sub()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a desktop has the chart across the width above the list")
def test_a_desktop_draws_the_chart_across_the_width_above_the_list(mount):
    page, errors, ros = open_ros(mount, size=DESKTOP)
    assert ros.view_tabs() == [("This week", False), ("Rest of season", True)], "the view's own bar from 760px"
    chart = ros.chart()
    assert chart["box"]["w"] > 700, "wide, not a phone's chart in a corner"
    assert chart["box"]["y"] + chart["box"]["h"] <= ros.first_row_top() + 1
    assert chart["box"]["h"] < 420, "a desktop chart is not a poster"
    rows = page.get_by_test_id("ros-row")
    boxes = [rows.nth(i).bounding_box() for i in range(rows.count())]
    assert max(b["width"] for b in boxes) < 560, "a label stays within 560px of its value (STYLE.md)"
    assert ros.fits() and errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a week with no earlier history draws dots, not lines")
def test_a_week_with_no_earlier_history_draws_dots(variant):
    fresh = copy.deepcopy(BLOCK)
    for p in fresh["players"]:
        p["hist"], p["espn"]["hist"] = p["hist"][-1:], p["espn"]["hist"][-1:]
    page, errors = variant(fresh)("ranks", size=PHONE)
    ros = RosPage(page)
    ros.pick_view("ros")
    chart = ros.chart()
    assert chart["weeks"] == ["wk 5"]
    assert all(not ln["line"] and ln["points"] == 1 for ln in chart["lines"])
    page.evaluate("p => openProfile(p)", {"n": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "slug": "amonra-st-brown"})
    page.wait_for_selector("#modal.on")
    assert ros.profile_block()["chart"]["line"] is False and ros.profile_block()["chart"]["dots"] == 1
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a rank below the axis sits on its bottom edge as a hollow dot")
def test_a_rank_below_the_chart_is_a_hollow_dot_on_its_bottom_edge(mount):
    page, errors, ros = open_ros(mount)
    lines = ros.chart()["lines"]
    assert sum(ln["hollow"] for ln in lines) >= 1, "the fixture's top-ten WR who was below 12th in week 3"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: a position with no rows says so")
def test_a_position_with_no_rows_says_so(variant):
    no_te = {**BLOCK, "players": [p for p in BLOCK["players"] if p["pos"] != "TE"]}
    page, errors = variant(no_te)("ranks", size=PHONE)
    ros = RosPage(page)
    ros.pick_view("ros")
    ros.pick("TE")
    assert ros.empty() and "TE" in ros.empty()
    assert ros.chart() is None and ros.rows() == []
    assert ros.chips() == ["QB", "RB", "WR", "TE"] and ros.fits()
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Ranks", ac="Rest of season: with no block there is no tab and Ranks reads as before")
def test_no_block_means_no_tab_and_ranks_as_before(variant):
    page, errors = variant(None)("ranks", size=PHONE)
    ros = RosPage(page)
    assert not ros.has_view_tabs()
    assert ros.tiers() > 0
    assert errors == []
