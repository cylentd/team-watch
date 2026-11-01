"""S10, an untested number says so, as drawn: the player-facing views (the sibling of test_untested_marks_drawn.py).

test_flag_marks.py proves each mark key's copy says Untested or Failed test. This file proves the profile, Start/Sit and
the Roster's brief and cards draw it: the mounted view puts `words(key)` on an element (a tap or tooltip) whose line also
draws a number, at 360px, the check `drawn_beside_a_number` makes in test_untested_marks_drawn.py. The fixture lacks the
state for some, so it is planted in the page after mount, as MarksPage.plant_cold_week does. Words come from `words`.

Left out, a finding (the mark rides on a label whose own line holds no number; the number sits in the cells beside it):
profile.zoneRead.mark (the Softest column head), startsit.def.mark, startsit.out.mark, startsit.wx.mark (a row's label).
"""
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.marks import CARRIERS
from pages.matchups import MatchupsPage
from pages.roster import on_roster
from pages.roster_brief import RosterBrief
from wording import words

SIZE = (360, 800)
ST_BROWN = {"n": "Amon-Ra St. Brown", "pos": "WR", "team": "DET", "slug": "amonra-st-brown"}
NOTHING = "() => {}"
RISING = ("() => { LIVE_SIGNALS.players['amonra-st-brown'] = "
          "{verdict: 'RISING', why: 'snaps 5.0, share 3; buy or start', series: []}; }")
WIND = ("() => { BRIEF_ALL = true; "
        "Object.assign(LIVE_WEATHER.teams.SEA, {wind: '25 mph', precip_pct: 0, short: 'Windy'}); }")
ALL_LINES = "() => { BRIEF_ALL = true; }"
CARDS = "() => { ROSTER_MODE = 'cards'; }"
NO_TEAM = "try { localStorage.removeItem('tw-team'); } catch (e) {}"
SPOT = """LIVE_STARTSIT.best = [{slug: 'joe-burrow', n: 'Joe Burrow', pos: 'QB', team: 'CIN', opp: 'PIT', home: true,
  pts: 19.4, why: ['soft pass defense']}];"""

PROFILE = [("profile.coverage.mark", NOTHING, lambda p: p.tab("matchup")),
           ("profile.matchup.mark", NOTHING, lambda p: p.tab("matchup")),
           ("profile.line.mark", NOTHING, lambda p: p.tab("matchup")),
           ("profile.signal.risingMark", RISING, lambda p: None),
           ("profile.sheet.eliteMark", NOTHING, lambda p: p.open_sheet())]
ROSTER = [("teams.brief.muMark", ALL_LINES), ("teams.brief.wxMark", ALL_LINES), ("teams.brief.wireMark", ALL_LINES),
          ("teams.brief.wxMarkWind", WIND), ("teams.card.wxMark", CARDS)]


def drawn_beside_a_number(page, key):
    carriers = page.evaluate(CARRIERS.replace("#view *", "#view *, #modal *"), words(key))
    return bool(carriers) and any(re.search(r"\d", c["block"]) for c in carriers)


@pytest.mark.render
@pytest.mark.parametrize(("key", "plant", "reach"), PROFILE, ids=[p[0] for p in PROFILE])
def test_the_profile_draws_each_untested_mark_on_a_line_with_a_number(mount, key, plant, reach):
    profile, errors = on_roster(mount, size=SIZE)
    profile.page.evaluate(plant)
    profile.open_player(ST_BROWN)
    reach(profile)
    assert drawn_beside_a_number(profile.page, key), f"the profile does not draw {key} beside a number"
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize(("key", "plant"), ROSTER, ids=[r[0] for r in ROSTER])
def test_the_roster_draws_each_untested_mark_on_a_line_with_a_number(mount, key, plant):
    page, errors = mount("roster", size=SIZE)
    page.evaluate(plant)
    brief = RosterBrief(page)
    brief.open_pack()
    page.evaluate("render()")
    brief.unfold()
    assert drawn_beside_a_number(page, key), f"the Roster does not draw {key} beside a number"
    assert errors == []


@pytest.mark.render
def test_start_sit_draws_the_board_mark_on_a_line_with_a_number(mount):
    page, errors = mount("ranks", size=SIZE)
    MatchupsPage(page).open(NO_TEAM + SPOT)
    assert drawn_beside_a_number(page, "startsit.board.mark"), "Start/Sit does not draw startsit.board.mark beside a number"
    assert errors == []
