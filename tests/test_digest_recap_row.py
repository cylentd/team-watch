"""The Digest's Recap row (2026-10-05): the one link left of the Results row.

The recap fixture is week 4, 8 of 16 games final, its last kickoff Monday 2026-10-05 5:15 PM Pacific. The row is
drawn from LIVE_RECAP and the clock; a component test on `mount("digest")` plants both (`DigestPage.plant_recap`).
Tapping the row is a journey (the hash opens the Recap view). Its end, `dgRecapEnd`, is in tests/test_js_digest.py.
"""
import re

import pytest

from component import mount  # noqa: E402,F401  (the fixture)
from pages.digest_live import DigestLivePage
from test_render import open_at

PHONE = (390, 844)

# These clocks hold in every zone from UTC-12 to UTC+11: the row goes at the end of Wednesday 10/7.
RECAP_ON, RECAP_LAST_DAY, RECAP_OFF = "2026-10-05T15:00:00Z", "2026-10-07T12:00:00Z", "2026-10-09T00:00:00Z"
# The fixture's top scorer is J. Allen (285 yds, 3 TD, his line's first two parts), Claude's picks 5-3.
NAME, WHO, CLAUDE = "J. Allen", "J. Allen 285 yds · 3 TD", "Claude 5 of 8"


@pytest.mark.render
@pytest.mark.req("Digest", ac="the Recap row shows the top scorer's day and Claude's record, and prints no fantasy points")
def test_the_recap_row_links_to_recap_with_the_top_scorers_day_and_claudes_record(mount):
    """2026-10-05: one ticker row stands in for the Results row, in the other rows' shape: "Recap", the week,
    the top scorer's day and Claude's straight-up picks. It is a link to #weekrecap, opens nothing in place, and
    prints no fantasy points (David: Digest headlines show yards and TDs, never points)."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_recap(RECAP_ON)
    row = dg.recap_facts()
    assert row and dg.row_count("recap") == 1
    assert dg.row_ids()[0] == "recap", "first in the ticker"
    assert row["href"] == "#weekrecap" and row["arrows"] == 1
    assert row["label"].upper() == "RECAP" and row["week"] == "Wk 4"
    assert row["bodies"] == 0 and row["open"] is None
    assert row["who"] == WHO and row["claude"] == CLAUDE
    assert not re.search(r"\d\.\d|pts|point", row["line"]), f"no fantasy points on a Digest headline: {row['line']!r}"
    assert errors == []


@pytest.mark.journey
@pytest.mark.render
@pytest.mark.req("Digest", ac="a tap on the Recap row is a link, not a toggle: it opens no body and the hash opens the view")
def test_a_tap_on_the_recap_row_opens_the_recap_view(browser, page_file):
    ctx, page, errors = open_at(browser, page_file, PHONE, "#digest")
    try:
        dg = DigestLivePage(page)
        dg.plant_recap(RECAP_ON)
        dg.tap_recap_link()
        assert dg.hash() == "#weekrecap"
        assert errors == []
    finally:
        ctx.close()


@pytest.mark.render
@pytest.mark.req("Digest", ac="the Recap row drops what it lacks and never prints a missing value")
def test_the_recap_row_drops_what_it_lacks_and_never_prints_a_missing_value(mount):
    """No box line: just his name. No Preview record: no Claude part. No scorer at all: the label and the week."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.top = {...LIVE_RECAP.top, line: null}")
    row = dg.recap_facts()
    assert row["who"] == NAME and row["claudes"] == 1
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.preview_record = null")
    row = dg.recap_facts()
    assert row["claudes"] == 0 and row["bold"] == 1
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.preview_record = {...LIVE_RECAP.preview_record, su: null}")
    assert dg.recap_facts()["claudes"] == 0
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.top = null")
    row = dg.recap_facts()
    assert row and row["whos"] == 0 and "undefined" not in row["text"]
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="the Recap row shows from half the week final until the end of the first Wednesday")
def test_the_recap_row_shows_from_half_the_week_final_until_the_end_of_the_first_wednesday(mount):
    """Shows when n_final * 2 >= n_games, until local midnight at the end of the first Wednesday after the
    week's last kickoff; then hides. A recap file with no kickoff to count from draws no row."""
    page, errors = mount("digest", size=PHONE)
    dg = DigestLivePage(page)

    def shown(at, edit=""):
        dg.plant_recap(at, edit)
        return dg.row_count("recap") == 1
    assert shown(RECAP_ON) and shown(RECAP_LAST_DAY)                         # Monday; Wednesday noon
    assert not shown(RECAP_OFF)                                              # Thursday
    assert not shown(RECAP_ON, "LIVE_RECAP.n_final = 7")                     # under half final
    assert shown(RECAP_ON, "LIVE_RECAP.n_final = 8")                         # exactly half
    assert not shown(RECAP_ON, "LIVE_RECAP.n_games = 0")
    gone = "LIVE_RECAP.games.forEach(g => { g.kickoff = null; }); LIVE_SCHEDULE.games = LIVE_SCHEDULE.games.filter(g => g.week !== LIVE_RECAP.week)"
    assert not shown(RECAP_ON, gone)
    # A kickoff on a Wednesday itself ends at the end of the NEXT one.
    wed = "LIVE_RECAP.games.forEach(g => { g.kickoff = '2026-10-07T20:00:00Z'; })"
    assert shown("2026-10-10T12:00:00Z", wed) and not shown("2026-10-16T12:00:00Z", wed)
    assert errors == []


@pytest.mark.render
@pytest.mark.req("Digest", ac="the Recap row fits a phone and sits in a wall band that is a link, not a toggle")
def test_the_recap_row_fits_a_phone_and_sits_in_a_wall_band(mount):
    """Nothing scrolls sideways at 360px, the row is one line at the ticker's 52px, and the wall draws it as a
    full-width band (its own named area) that is a link, not a toggle."""
    page, errors = mount("digest", size=(360, 740))
    dg = DigestLivePage(page)
    dg.plant_recap(RECAP_ON)
    got = dg.recap_row_geometry()
    assert got["h"] == 52 and not got["overflow"] and got["claudeInside"], got
    # Page turned past this week's stats (2026-10-05): the chip stays "Wk 4" and "Final tomorrow" opens the
    # wrapping text (a 192px chip left the text 31px at 360px).
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.complete = false; LIVE_SCHEDULE.week = LIVE_RECAP.week + 1")
    assert dg.row_count_text("recap") == "Wk 4"
    note = dg.recap_note()
    assert note["first"] == "Final tomorrow"
    got = dg.recap_text_geometry()
    assert got["text"] >= 100 and got["who"] >= 60 and not got["overflow"], got
    dg.plant_recap(RECAP_ON, "LIVE_RECAP.complete = true; LIVE_SCHEDULE.week = LIVE_RECAP.week + 1")
    assert dg.recap_note() is None, "stats landed: no note"
    assert errors == []
    page, errors = mount("digest", size=(1705, 1000))
    dg = DigestLivePage(page)
    dg.plant_recap(RECAP_ON)
    got = dg.recap_row_wall_band()
    assert got["area"] == "recap" and got["full"] and not got["open"] and got["line"] != "none" and got["cur"] == "pointer", got
    assert errors == []
