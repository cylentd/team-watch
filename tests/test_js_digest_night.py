"""The Digest's night-game card, in Node (data/dayplan.js; 2026-10-07, TODO "Digest previews the night games").

One preview card, two days: Wednesday previews Thursday night's game, Sunday previews Sunday night's. Which game,
where the card sits in the day's order and the five-card cap are pure, so they run here; what the card draws and
what a tap does is tests/test_digest_night.py (component).

Pacific noon of week 5: Wednesday 2026-10-07, Sunday 2026-10-04. Thursday night kicks 5:15 PM Pacific Oct 8
(00:15Z Oct 9); Sunday night kicks 5:20 PM Pacific Oct 4 (00:20Z Oct 5).
"""
from datetime import datetime

import pytest

NOON = {"wed": "2026-10-07T19:00:00Z", "sun": "2026-10-04T19:00:00Z", "thu": "2026-10-08T19:00:00Z",
        "mon": "2026-10-05T19:00:00Z", "sat": "2026-10-10T19:00:00Z", "tue": "2026-10-06T19:00:00Z", "fri": "2026-10-09T19:00:00Z"}
SUN_AFTER_KICK = "2026-10-05T00:30:00Z"        # 5:30 PM Sunday Pacific, ten minutes after the night game began
TNF, SNF = "2026-10-09T00:15:00Z", "2026-10-05T00:20:00Z"
GAMES = [
    {"away": "JAX", "home": "LA", "kickoff": "2026-10-04T17:00:00Z", "slot": "sun1"},
    {"away": "PIT", "home": "CLE", "kickoff": TNF, "slot": "thu"},
    {"away": "CIN", "home": "DEN", "kickoff": SNF, "slot": "sunnight"},
    {"away": "DAL", "home": "NYG", "kickoff": "2026-10-06T00:15:00Z", "slot": "mon"},
]
ALL = ["usage", "night", "tiers", "gains", "defenses", "adds", "calls"]     # the tier sheet since 2026-10-08 (Home draft B)


def ms(iso):
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000)


@pytest.fixture
def plan(node_js):
    return node_js("data/schedule.js", "data/navmap.js", "data/dayplan.js", "data/digest.js",
                   globals={"LIVE_SCHEDULE": {"games": [], "alias": {"LA": "LAR"}}})


@pytest.mark.req("Digest", ac="Wednesday previews Thursday night's game")
def test_wednesday_picks_thursday_nights_game_by_its_index(plan):
    got = plan("([p, ms]) => dgPickNight(p, 'wed', ms)", [{"games": GAMES}, ms(NOON["wed"])])
    assert got == {"i": 1, "game": GAMES[1]}


@pytest.mark.req("Digest", ac="Sunday previews Sunday night's game until it kicks off")
def test_sunday_picks_sunday_nights_game_until_it_kicks_off(plan):
    pick = "([p, ms]) => { const n = dgPickNight(p, 'sun', ms); return n && n.i; }"
    assert plan(pick, [{"games": GAMES}, ms(NOON["sun"])]) == 2
    assert plan(pick, [{"games": GAMES}, ms(SNF) - 1]) == 2, "one millisecond before the kickoff, the card is there"
    assert plan(pick, [{"games": GAMES}, ms(SUN_AFTER_KICK)]) is None, "kicked off: the card is gone"


@pytest.mark.req("Digest", ac="the night card is on Wednesday and Sunday only")
@pytest.mark.parametrize("day", ["mon", "tue", "thu", "fri", "sat"])
def test_no_other_day_has_a_night_card(plan, day):
    assert plan("([p, k, ms]) => dgPickNight(p, k, ms)", [{"games": GAMES}, day, ms(NOON[day])]) is None


@pytest.mark.req("Digest", ac="a week with no night game has no card")
def test_a_week_without_the_night_game_has_no_card(plan):
    pick = "([p, k, ms]) => dgPickNight(p, k, ms)"
    others = [g for g in GAMES if g["slot"] not in ("thu", "sunnight")]
    assert plan(pick, [{"games": others}, "wed", ms(NOON["wed"])]) is None
    assert plan(pick, [{"games": others}, "sun", ms(NOON["sun"])]) is None
    assert plan(pick, [{"games": []}, "wed", ms(NOON["wed"])]) is None
    assert plan(pick, [None, "sun", ms(NOON["sun"])]) is None


@pytest.mark.req("Digest", ac="Sunday's card is Sunday night's, not a later Sunday's")
def test_sunday_does_not_preview_next_weeks_night_game(plan):
    far = [{"away": "A", "home": "B", "kickoff": "2026-10-12T00:20:00Z", "slot": "sunnight"}]
    assert plan("([p, ms]) => dgPickNight(p, 'sun', ms)", [{"games": far}, ms(NOON["sun"])]) is None


@pytest.mark.req("Digest", ac="the night card sits second: after usage movers on Wednesday, after Need to know on Sunday")
@pytest.mark.parametrize("day,order", [
    ("wed", ALL), ("sun", ["need", "night", "tiers", "now", "weather", "calls"]),
    ("thu", ["tonight", "tiers", "status", "calls"]), ("mon", ["tonight", "tiers", "gains", "calls"]), ("tue", ["adds", "tiers", "gains", "usage"]),
    ("fri", ["status", "tiers", "gains", "smash", "weather"]), ("sat", ["smash", "tiers", "bold", "calls", "weather"])])
def test_the_night_card_is_second_on_wednesday_and_sunday_and_no_other_day_changes(plan, day, order):
    assert plan("ms => dgCardOrder(dgDayPlan(ms))", ms(NOON[day])) == order


@pytest.mark.req("Digest", ac="five cards at most")
def test_wednesday_keeps_five_cards_and_drops_the_last(plan):
    got = plan("ms => { const p = dgDayPlan(ms), d = {}; dgCardOrder(p).forEach(id => { d[id] = '<' + id + '>'; }); return dgCardList(p, d); }", ms(NOON["wed"]))
    assert got == ["usage", "night", "tiers", "gains", "defenses"]


@pytest.mark.req("Digest", ac="five cards at most")
def test_sunday_with_every_card_drawn_is_five(plan):
    got = plan("ms => { const p = dgDayPlan(ms), d = {}; dgCardOrder(p).forEach(id => { d[id] = '<' + id + '>'; }); return dgCardList(p, d); }", ms(NOON["sun"]))
    assert got == ["need", "night", "tiers", "now", "calls"], "Right now takes Weather's place (Home draft B)"


@pytest.mark.req("Digest", ac="a card with nothing to show is skipped")
def test_without_the_night_card_wednesday_is_the_plan_it_was(plan):
    got = plan("""ms => { const p = dgDayPlan(ms);
      return dgCardList(p, {usage: '<u>', night: '', gains: '<g>', defenses: '<d>', adds: '<a>', calls: '<c>'}); }""", ms(NOON["wed"]))
    assert got == ["usage", "gains", "defenses", "adds", "calls"]


@pytest.mark.req("Digest", ac="a day whose cards are all empty shows Need to know")
@pytest.mark.parametrize("day", ["wed", "sun", "thu"])
def test_every_card_empty_still_shows_need_to_know(plan, day):
    assert plan("ms => dgCardList(dgDayPlan(ms), {})", ms(NOON[day])) == ["need"]
