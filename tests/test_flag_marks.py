"""The flag cleanup (2026-10-06, David, from the ff-jarvis flag inventory): every flag the page shows that failed a
METHODOLOGY test, or was never tested, says so in its own tap or tooltip text, and the flags the failed tests priced in
or got the wrong sign for are gone. This file holds the copy; each surface's own test file holds what it draws.

The mark's wording is the repo's copy rule: "Untested" or "Failed test (12.xx): <the result in a few words>", one short
line, in content.json (copy is data). Tests in other files pin the rendered page: test_profile_panes (F1),
test_digest_after_kickoff (F2), test_prop_picks and test_parlay_grid (F3, F4), test_top_calls and test_js_topcalls (F5),
test_roster_cards (F21), test_preview (F18, U4), test_digest (F25), test_render_waivers (U9, U13).
"""
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
COPY = json.loads((ROOT / "design" / "src" / "content.json").read_text(encoding="utf-8"))

# Every key that carries a mark, with the inventory row it answers.
MARKS = {
    "slips.tier.mark": "F6", "parlay.tag.cbTitle": "F7", "slips.flag.mark": "F8", "legsheet.matchup.mark": "F9",
    "profile.zoneRead.mark": "F10", "profile.coverage.mark": "F11", "profile.matchup.mark": "F12",
    "ranks.row.mxMark": "F13", "startsit.board.mark": "F14", "startsit.def.mark": "F15", "digest.foot.muMark": "F16",
    "teams.brief.muMark": "F17", "preview.travel.mark": "F19", "weather.cond.coldMark": "F20",
    "teams.card.wxMark": "F22", "teams.brief.wxMark": "F22", "startsit.out.mark": "F23", "startsit.wx.mark": "F24",
    "matchups.takes.markStart": "F25", "waiver.lane.usageMark": "F27", "dfs.tag.handcuffMark": "F28",
    "matchups.takes.markSmash": "U1", "matchups.takes.markSit": "U2", "preview.conf.mark": "U4",
    "preview.call.mark": "U5", "slips.claude.mark": "U6", "parlay.tag.roleMark": "U8", "waiver.tier.mark": "U9",
    "waiver.lane.starterMark": "U10", "waiver.lane.roleMark": "U11", "waiver.lane.injuredMark": "U12",
    "waiver.swap.mark": "U13", "waiver.rail.pathMark": "U14", "teams.brief.wireMark": "U15",
    "teams.brief.wxMarkWind": "U16", "lboard.offer.mark": "U17", "lboard.chip.mark": "U18",
    "profile.signal.risingMark": "U19", "profile.sheet.eliteMark": "U20", "profile.line.mark": "U21",
    "trades.lead.dueMark": "U23",
}

# Keys the removals left behind: gone from the copy, so a reader can never see them.
REMOVED = [
    "digest.tn.flat", "digest.tn.group.pass", "digest.tn.group.qb", "digest.tn.group.rb", "digest.tn.moved",
    "digest.tn.moved.h", "digest.tn.other",                       # F2
    "profile.market.line.z",                                      # F1
    "slips.chip.rise", "slips.chip.noneRise",                     # F3
    "slips.flag.out",                                             # F4
    "slips.top.edge", "slips.top.noEdge",                         # F5
    "teams.card.wxRun",                                           # F21
]

SAYS = re.compile(r"Untested|Failed test \(12\.\d+(?:, 12\.\d+)*\)[:.] \S")


@pytest.mark.parametrize("key", sorted(MARKS))
def test_a_mark_says_untested_or_the_failed_test_with_its_entry(key):
    text = COPY[key]
    assert SAYS.search(text), f"{MARKS[key]} {key}: {text!r} names neither 'Untested' nor 'Failed test (12.xx): result'"
    assert "\n" not in text and len(text) < 220, f"{MARKS[key]} {key}: a mark is one short line"


@pytest.mark.parametrize("key", REMOVED)
def test_a_removed_flags_copy_is_gone(key):
    assert key not in COPY, f"{key} is copy for a flag the cleanup removed (an orphan the build should refuse)"


def test_the_result_words_come_from_the_inventory_not_from_a_guess():
    """The numbers a mark quotes are the inventory's. A spot check of the ones a reader is most likely to test."""
    assert "49.6% against 62.9%" in COPY["slips.tier.mark"]
    assert "-0.74" in COPY["weather.cond.coldMark"] and "t -2.93" in COPY["weather.cond.coldMark"]
    assert "10 of 24" in COPY["matchups.takes.markStart"] and "26 of 31" in COPY["matchups.takes.markSit"]
    assert "52 of 69" in COPY["matchups.takes.markSmash"]
    assert "t 0.73" in COPY["parlay.tag.cbTitle"] and "0 of 8" in COPY["parlay.tag.cbTitle"]
    assert "no edge past the line" in COPY["preview.travel.mark"]
    assert "-0.03 a game" in COPY["waiver.lane.usageMark"]
