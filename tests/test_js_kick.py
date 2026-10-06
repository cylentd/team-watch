"""The one kickoff format (lib/kick.js), in Node: "Sun 1:00 PM" in the reader's clock, everywhere.

Before 2026-10-05 four formats lived side by side: "Mon 8:15 PM ET" (Preview, Eastern), "5:15p" (Bets,
Digest-style Pacific), "Sun 10:00 AM" (Start/Sit, Pacific) and the browser's own "Sun, 1:00 PM" (Ranks,
Weather, Live). One formatter now, fed an ISO time. KICK_TZ pins the zone in a test; the page leaves it
unset, so a browser reads its own clock."""
import pytest

PT = {"KICK_TZ": "America/Los_Angeles"}
ET = {"KICK_TZ": "America/New_York"}


@pytest.fixture(scope="module")
def pt(node_js):
    return node_js("lib/kick.js", globals=PT)


@pytest.fixture(scope="module")
def et(node_js):
    return node_js("lib/kick.js", globals=ET)


def test_one_format_weekday_then_clock_no_comma_no_zone(pt):
    assert pt("kickFmt", "2026-10-04T17:00:00Z") == "Sun 10:00 AM"
    assert pt("kickFmt", "2026-10-05T00:15:00Z") == "Sun 5:15 PM"      # still Sunday in Pacific


def test_the_same_kickoff_is_the_readers_clock_not_a_fixed_zone(pt, et):
    assert et("kickFmt", "2026-10-06T00:15:00Z") == "Mon 8:15 PM"
    assert pt("kickFmt", "2026-10-06T00:15:00Z") == "Mon 5:15 PM"


def test_it_takes_every_shape_a_kickoff_arrives_in(pt):
    sunday = "Sun 10:00 AM"
    assert pt("kickFmt", "2026-10-04T17:00:00+00:00") == sunday
    assert pt("kickFmt", "2026-10-04 17:00:00") == sunday               # the props' "YYYY-MM-DD HH:MM:SS", UTC
    assert pt("kickFmt", 1791133200000) == sunday                       # epoch ms (Live's clock)


def test_nothing_in_nothing_out(pt):
    assert pt("kickFmt", None) == ""
    assert pt("kickFmt", "") == ""
    assert pt("kickFmt", "not a time") == ""


def test_the_time_alone_for_a_window_that_names_its_day(pt):
    assert pt("kickTime", "2026-10-04T20:25:00Z") == "1:25 PM"


def test_the_date_of_a_played_week_follows_the_same_clock(pt, et):
    assert pt("kickDate", "2026-09-14T01:15:00Z") == "Sep 13"           # Monday night, still Sunday in Pacific
    assert et("kickDate", "2026-09-14T01:15:00Z") == "Sep 13"
    assert pt("kickDate", "2026-09-14T08:00:00Z") == "Sep 14"
    assert pt("kickDate", None) == ""


def test_a_body_clock_reads_in_the_same_words(pt):
    """Preview's travel line: a team's own 24-hour clock, not the reader's, in the same 12-hour style."""
    assert pt("kickClock", "13:25") == "1:25 PM"
    assert pt("kickClock", "00:05") == "12:05 AM"
    assert pt("kickClock", "12:00") == "12:00 PM"


def test_past_kickoff_is_the_viewers_clock_at_the_whistle(pt):
    """Monday 2026-10-05: Thursday night (PIT @ CLE) is long gone, Monday night is still to come."""
    noon_monday = 1791205200000                                          # 2026-10-05T13:00:00Z
    assert pt("kickPast", "2026-10-02 00:15:00", noon_monday) is True
    assert pt("kickPast", "2026-10-06 00:15:00", noon_monday) is False
    assert pt("kickPast", "2026-10-06 00:15:00", noon_monday + 12 * 3600e3) is True
    assert pt("kickPast", None, noon_monday) is False, "a row with no kickoff is not called played"


def test_a_row_set_is_relabelled_from_its_own_iso_time(pt):
    rows = [{"commence": "2026-10-06 00:15:00", "kick": "Mon 5:15p"}, {"commence": None, "kick": "Sun 1:00p"}]
    got = pt("(rows => { kickLabel(rows, 'commence'); return rows; })", rows)
    assert [r["kick"] for r in got] == ["Mon 5:15 PM", "Sun 1:00p"]     # no ISO time: the old label stays
