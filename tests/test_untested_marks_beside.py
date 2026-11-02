"""S10, an untested number says so, with the numbers beside it (David, 2026-11-01: a mark counts when the numbers it
speaks for sit beside it). The sibling of test_untested_marks_drawn.py and _people.py, whose check reads the mark's
nearest block and so misses a mark on a head, a label or a header.

"Beside" is named per kind, and each test asserts a digit in exactly those numbers, never anywhere else on the page:
  profile.zoneRead.mark   the cells under the Softest head, down its table (the zone's rank, 19/32).
  startsit.def.mark, startsit.wx.mark   the lanes of the label's own row (each player's cell in that row).
  dfs.tag.handcuffMark    the .pnum cells of the tagged player's own row (salary, points, value, ownership).
  parlay.tag.cbTitle, parlay.tag.roleMark   the lines (.bline) under the player's header in his Build block. The
                          header holds no number; the block is the smallest container that holds the tag and the
                          chances it speaks for.
  legsheet.matchup.mark   the matchup head (summary) of the same details block: the % or rank and the count out.
Words come from `words`; the title of cbTitle is a template, so its mark is the text after its last placeholder.

Left out, a finding: startsit.out.mark. Its row's cells hold a teammate's name and status (Coker, WR, Out), no number;
the projection the mark speaks for is in another row.
"""
import re

import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.legsheet import LegSheetPage
from pages.mark_lines import MarkLines
from pages.matchups import MatchupsPage
from pages.roster import on_roster
from test_untested_marks_people import NO_TEAM, SIZE, ST_BROWN
from wording import words

LANES = ["startsit.def.mark", "startsit.wx.mark"]


def mark(key):
    """The mark's own words: content.json's text after its last {placeholder}, whole when it has none."""
    return words(key).rsplit("}", 1)[-1].strip()


def numbered(groups):
    """At least one carrier, and each carrier has a digit in the numbers beside it."""
    return bool(groups) and all(any(re.search(r"\d", c) for c in g) for g in groups)


@pytest.mark.render
def test_the_zone_mark_sits_over_a_column_of_ranks(mount):
    profile, errors = on_roster(mount, size=SIZE)
    profile.open_player(ST_BROWN)
    profile.tab("matchup")
    cells = MarkLines(profile.page).column(mark("profile.zoneRead.mark"))
    assert numbered(cells), f"no number under the head that carries profile.zoneRead.mark: {cells}"
    assert errors == []


@pytest.mark.render
@pytest.mark.parametrize("key", LANES)
def test_a_start_sit_label_mark_sits_on_a_row_of_numbers(mount, key):
    page, errors = mount("ranks", size=SIZE)
    MatchupsPage(page).open(NO_TEAM)
    lines = MarkLines(page)
    lines.compare_two_backs()
    cells = lines.beside(mark(key), ".ssv-row", ".ssv-lanes .ssv-v")
    assert numbered(cells), f"Start/Sit's row for {key} holds no number: {cells}"
    assert errors == []


@pytest.mark.render
def test_the_handcuff_mark_sits_on_a_row_with_a_salary(mount):
    page, errors = mount("dfs", size=SIZE)
    lines = MarkLines(page)
    lines.plant_handcuff()
    cells = lines.beside(mark("dfs.tag.handcuffMark"), ".dfsrow", ".pnum")
    assert numbered(cells), f"the handcuff's DFS row holds no number: {cells}"
    assert errors == []


@pytest.mark.render
def test_the_corner_mark_sits_over_the_players_lines(mount):
    page, errors = mount("build", size=SIZE)
    cells = MarkLines(page).beside(mark("parlay.tag.cbTitle"), ".bplayer", ".bline")
    assert numbered(cells), f"Build's block for the corner tag holds no line with a number: {cells}"
    assert errors == []


@pytest.mark.render
def test_the_role_note_mark_sits_over_the_players_lines(mount):
    page, errors = mount("build", size=SIZE)
    lines = MarkLines(page)
    lines.plant_role_note()
    cells = lines.beside(mark("parlay.tag.roleMark"), ".bplayer", ".bline")
    assert numbered(cells), f"Build's block for the role tag holds no line with a number: {cells}"
    assert errors == []


@pytest.mark.render
def test_the_leg_sheet_mark_sits_in_a_matchup_block_with_a_percent(mount):
    sheet, errors = LegSheetPage.on(mount, "parlay", "dk")
    sheet.open_line("Tee Higgins", "RECS")
    cells = MarkLines(sheet.page).beside(mark("legsheet.matchup.mark"), "details.ls-match", "summary")
    assert numbered(cells), f"the leg sheet's matchup head holds no number: {cells}"
    assert errors == []
