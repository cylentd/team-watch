"""A live game pushes one card out: a day draws five blocks at most, Right now included, in Node.

David, 2026-11-01: Right now drawn ahead of the cards on a day whose plan has no "now" card (Friday and
Saturday plan five) made six blocks. A live game takes one place, the job card stays first.
"""
from datetime import datetime

import pytest

NOON = {"sun": "2026-10-04T19:00:00Z", "wed": "2026-10-07T19:00:00Z", "fri": "2026-10-09T19:00:00Z",
        "sat": "2026-10-10T19:00:00Z"}
BLOCKS = """([ms, now]) => {
  const plan = dgDayPlan(ms);   // digest.js draws only the cards the plan orders, "now" only where it places it
  const drawn = Object.fromEntries(dgCardOrder(plan).map(id => [id, "<card>"]));
  return dgDayBlocks(plan, drawn, now);
}"""


@pytest.fixture
def blocks(node_js):
    call = node_js("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js",
                   globals={"LIVE_SCHEDULE": {"games": [], "alias": {"LA": "LAR"}}})
    return lambda day, now: call(BLOCKS, [int(datetime.fromisoformat(NOON[day].replace("Z", "+00:00")).timestamp() * 1000), now])


@pytest.mark.req("Digest", ac="a live game pushes one card out, five blocks at most")
@pytest.mark.parametrize("day, cards", [
    ("fri", ["status", "tiers", "gains", "smash"]),
    ("sat", ["smash", "tiers", "bold", "calls"]),
    ("wed", ["usage", "night", "tiers", "gains"]),
])
def test_right_now_showing_leaves_the_job_card_first_and_four_more(blocks, day, cards):
    assert blocks(day, "<now>") == {"now": True, "ids": cards}


@pytest.mark.req("Digest", ac="a live game pushes one card out, five blocks at most")
@pytest.mark.parametrize("day, cards", [
    ("fri", ["status", "tiers", "gains", "smash", "weather"]),
    ("sat", ["smash", "tiers", "bold", "calls", "weather"]),
])
def test_right_now_empty_keeps_all_five_cards(blocks, day, cards):
    assert blocks(day, "") == {"now": False, "ids": cards}


@pytest.mark.req("Digest", ac="a live game pushes one card out, five blocks at most")
def test_a_plan_that_holds_now_is_unchanged(blocks):
    assert blocks("sun", "<now>") == {"now": False, "ids": ["need", "night", "tiers", "now", "calls"]}
