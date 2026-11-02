"""Tonight's blocks count in the five: a day draws five blocks at most, the job card first, in Node.

David, 2026-11-01: a Thursday or Monday with a game on drew Tonight, Right now and four cards (six blocks), and a
second kicked-off game made seven. Each Tonight block takes one of the five places, as Right now does (see
test_js_digest_now_cap.py). The job card always draws, so a day never goes below one card.
"""
from datetime import datetime

import pytest

NOON = {"thu": "2026-10-08T19:00:00Z", "fri": "2026-10-09T19:00:00Z", "sat": "2026-10-10T19:00:00Z",
        "mon": "2026-10-05T19:00:00Z"}
BLOCKS = """([ms, now, tonight]) => {
  const plan = dgDayPlan(ms);
  const drawn = Object.fromEntries(dgCardOrder(plan).map(id => [id, "<card>"]));
  return tonight == null ? dgDayBlocks(plan, drawn, now) : dgDayBlocks(plan, drawn, now, tonight);
}"""


@pytest.fixture
def blocks(node_js):
    call = node_js("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js",
                   globals={"LIVE_SCHEDULE": {"games": [], "alias": {"LA": "LAR"}}})
    at = lambda day: int(datetime.fromisoformat(NOON[day].replace("Z", "+00:00")).timestamp() * 1000)
    return lambda day, now, tonight=None: call(BLOCKS, [at(day), now, tonight])


@pytest.mark.req("Digest", ac="Tonight's blocks count in the five")
@pytest.mark.parametrize("day, cards", [
    ("thu", ["tonight", "tiers", "status"]),
    ("mon", ["tonight", "tiers", "gains"]),
])
def test_one_tonight_block_and_right_now_leave_the_job_card_first_and_three_more(blocks, day, cards):
    assert blocks(day, "<now>", 1) == {"now": True, "ids": cards}   # 1 + 1 + 3 = five blocks


@pytest.mark.req("Digest", ac="Tonight's blocks count in the five")
@pytest.mark.parametrize("day, cards", [
    ("thu", ["tonight", "tiers"]),
    ("mon", ["tonight", "tiers"]),
])
def test_two_tonight_blocks_and_right_now_leave_the_job_card_first_and_one_more(blocks, day, cards):
    assert blocks(day, "<now>", 2) == {"now": True, "ids": cards}   # 2 + 1 + 2 = five blocks


@pytest.mark.req("Digest", ac="Tonight's blocks count in the five")
def test_tonight_alone_pushes_the_fifth_card_out(blocks):
    assert blocks("sat", "", 1) == {"now": False, "ids": ["smash", "tiers", "bold", "calls"]}   # 1 + 4


@pytest.mark.req("Digest", ac="Tonight's blocks count in the five")
@pytest.mark.parametrize("now, tonight", [("", 5), ("", 6), ("<now>", 4), ("<now>", 6)])
def test_with_no_place_left_the_job_card_still_draws(blocks, now, tonight):
    assert blocks("thu", now, tonight)["ids"] == ["tonight"]


@pytest.mark.req("Digest", ac="Tonight's blocks count in the five")
@pytest.mark.parametrize("tonight", [None, 0])
def test_no_tonight_block_is_the_landed_behaviour(blocks, tonight):
    assert blocks("fri", "<now>", tonight) == {"now": True, "ids": ["status", "tiers", "gains", "smash"]}
    assert blocks("fri", "", tonight) == {"now": False, "ids": ["status", "tiers", "gains", "smash", "weather"]}
