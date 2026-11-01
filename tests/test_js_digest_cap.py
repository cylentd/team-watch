"""The Digest holds five cards at most, the day's job first (scenario S7), in Node.

S7: a weekday morning, a reader opens Home: the Digest leads with that day's job and at most five
cards. Wednesday plans six cards and its night card makes seven, so the cap is what keeps it at five.
CLAUDE.md: "the day's job card first, then the cards with data that day, five at most (since
2026-10-07; Tue adds, Wed usage movers, Thu Claude vs Vegas, Fri practice report, Sat SMASH, Sun Need
to know, Mon tonight's game)". Thursday's and Monday's game is one Tonight card (Home draft B,
2026-10-08), the practice report is the "status" card.
"""
from datetime import datetime

import pytest

NOON ={"sun": "2026-10-04T19:00:00Z", "mon": "2026-10-05T19:00:00Z", "tue": "2026-10-06T19:00:00Z",
        "wed": "2026-10-07T19:00:00Z", "thu": "2026-10-08T19:00:00Z", "fri": "2026-10-09T19:00:00Z",
        "sat": "2026-10-10T19:00:00Z"}
JOB_CARD = {"tue": "adds", "wed": "usage", "thu": "tonight", "fri": "status", "sat": "smash",
            "sun": "need", "mon": "tonight"}
EVERY_CARD = """ms => {
  const ids = new Set(["night", "now"]);
  Object.values(DG_PLAN).forEach(p => p.cards.forEach(id => ids.add(id)));
  const drawn = Object.fromEntries([...ids].map(id => [id, "<card>"]));
  return dgCardList(dgDayPlan(ms), drawn);
}"""


@pytest.fixture
def plan(node_js):
    return node_js("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js",
                   globals={"LIVE_SCHEDULE": {"games": [], "alias": {"LA": "LAR"}}})


@pytest.mark.req("Digest", ac="a day holds five cards at most, the day's job first")
@pytest.mark.parametrize("day", list(NOON))
def test_every_day_with_every_card_present_draws_five_at_most_and_the_job_first(plan, day):
    noon = datetime.fromisoformat(NOON[day].replace("Z", "+00:00"))
    cards = plan(EVERY_CARD, int(noon.timestamp() * 1000))
    assert len(cards) <= 5, f"{day}: {cards}"
    assert cards[0] == JOB_CARD[day], f"{day}: {cards}"
