"""S9, the season record is in view on Start/Sit: "the reader's lineup leads with our one swap, decided by our own
points, with the season record in view".

test_matchups_view.py proves the lineup leads, the swap is the pickers' call by points, and that the record line
starts with its label. This file proves the record's figures: each call's hit-miss and void count as the reader reads
them, the week it counts from, the for-fun line, and the sentence before any week is graded. The figures are planted
here, so each expected value is worked out by hand from them.
"""
import pytest

from component import mount  # noqa: F401  (the fixture)
from pages.matchups import MatchupsPage
from pages.matchups_record import RecordPage
from wording import words

GRADED = """
  Object.assign(LIVE_SS3.record, {since_week: 6, weeks: [{week: 6}],
    smash: {hit: 6, miss: 4, void: 0}, start: {hit: 3, miss: 1, void: 2}, sit: {hit: 5, miss: 0, void: 0},
    fun: {fantasypros: {hit: 5, miss: 3}, pitcherlist: {hit: 3, miss: 2}}});
"""
UNGRADED = """
  Object.assign(LIVE_SS3.record, {since_week: 6, weeks: [],
    smash: {hit: 0, miss: 0, void: 0}, start: {hit: 0, miss: 0, void: 0}, sit: {hit: 0, miss: 0, void: 0}});
"""
REQ = pytest.mark.req("Start/Sit", ac="the record in view")


@pytest.fixture
def record(mount):
    def open_(plant):
        page, errors = mount("ranks", size=(360, 800))
        MatchupsPage(page).open(plant)
        return RecordPage(page), errors
    return open_


@REQ
def test_the_record_says_each_calls_hits_and_misses_and_when_it_started(record):
    rec, errors = record(GRADED)
    assert rec.head() == f'{words("matchups.record.label")} {words("matchups.record.since").format(wk=6)}'
    assert {k: (v["wl"], v["word"]) for k, v in rec.tiles().items()} == {
        "smash": ("6-4", words("matchups.call.smash")), "start": ("3-1", words("matchups.call.start")),
        "sit": ("5-0", words("matchups.call.sit"))}
    assert errors == []


@REQ
def test_a_void_count_shows_only_beside_a_call_that_has_one(record):
    rec, errors = record(GRADED)
    assert {k: v["void"] for k, v in rec.tiles().items()} == {"smash": "", "start": words("matchups.record.void").format(n=2), "sit": ""}
    assert errors == []


@REQ
def test_the_for_fun_line_gives_the_other_two_records_and_the_record_fits_a_phone(record):
    rec, errors = record(GRADED)
    assert rec.fun() == words("matchups.record.fun").format(fp="5-3", pl="3-2")
    assert rec.on_screen()
    assert errors == []


@REQ
def test_before_any_week_is_graded_the_record_says_so_in_place_of_the_figures(record):
    rec, errors = record(UNGRADED)
    assert rec.tiles() == {} and rec.fun() == ""
    assert rec.after_head() == words("matchups.record.none")
    assert errors == []
