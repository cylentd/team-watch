"""The pack's stage stands in the middle of the free area (David, 2026-10-07): the pack sat too high, 45% down
the window. The group (the hint over the pack, the pack, the lead line under it) is centred between the header
bar and the bottom bar a phone draws, the hint over the pack where the drag happens and the lead line under
it, and the numeral on the pack clears its bottom crimp. Component layer (`mount`, `PackLayout`) and Node
for the pack's art (`packArtSVG`)."""
import re

import pytest

from component import mount as base_mount
from pages.pack_layout import PackLayout
from pages.roster_motion import show_cards
from pages.warm import warm

PHONES = [(360, 740), (390, 844)]


@pytest.fixture(scope="module")
def mount(base_mount):
    """Both phone sizes open once: a size the module reaches through `stage_at` is a cold context in the test's call."""
    return warm(base_mount, *[("roster", size) for size in PHONES])


@pytest.fixture(scope="module", params=PHONES, ids=["size0", "size1"])
def stage(mount, request):
    """The pack's stage open at one phone size, read once for the tests below (they only read rects): the stage
    opening is setup, ~150 ms and more under load, not part of any test's call. -> (layout, page errors)."""
    page, errors = mount("roster", size=request.param)
    roster = PackLayout(page)
    assert show_cards(roster, "espn", "rip") == 1, "the fixture's schedule has a week ahead, so a pack waits"
    roster.wait_for_stage()
    return roster.layout(), errors


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the pack stands in the middle of the free area between the header and the bottom bar")
def test_the_pack_stands_in_the_middle_of_the_free_area(stage):
    lay, errors = stage
    mid = (lay["pack"]["top"] + lay["pack"]["bottom"]) / 2
    assert abs(mid - lay["areaMid"]) <= 1, f"the pack's middle is {mid}px, the free area's {lay['areaMid']}px"
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Phone layout", ac="the rip hint stands over the pack and the lead line under it, each in the same room")
def test_the_hint_stands_over_the_pack_and_the_lead_line_under_it(stage):
    lay, errors = stage
    assert lay["hintText"] == "DRAG ACROSS THE TOP TO RIP" and re.fullmatch(r"Week \d+ is in\. Your starters are inside, best card last\.", lay["msgText"])
    assert lay["hint"]["bottom"] <= lay["pack"]["top"], "the hint is over the pack"
    assert lay["msg"]["top"] >= lay["pack"]["bottom"], "the lead line is under the pack"
    over, under = lay["pack"]["top"] - lay["hint"]["top"], lay["msg"]["bottom"] - lay["pack"]["bottom"]
    assert abs(over - under) <= 1, f"the group is symmetric about the pack: {over}px over, {under}px under"
    assert errors == []


@pytest.fixture(scope="module")
def art(node_js):
    return node_js("surface/teams/pack.js")


def numeral(svg):
    """(baseline, size, label baseline) of the numeral drawn in the pack's art, in its 140-unit-high box."""
    wk = re.search(r'class="pa-wk" x="50" y="([\d.]+)" text-anchor="middle" font-size="([\d.]+)"', svg)
    wl = re.search(r'class="pa-wl" x="50" y="([\d.]+)"', svg)
    return float(wk.group(1)), float(wk.group(2)), float(wl.group(1))


@pytest.mark.parametrize("week", [5, 12])
def test_the_numeral_clears_the_bottom_crimp_and_the_label_sits_over_it(art, week):
    baseline, size, label = numeral(art("packArtSVG", week))
    assert baseline <= 140 - 20, f"week {week}: the numeral's foot is {140 - baseline} units above the pack's, not 20 or more"
    assert label < baseline - size * .6, f"week {week}: WEEK sits over the numeral's top"
