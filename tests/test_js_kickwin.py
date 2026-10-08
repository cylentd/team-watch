"""Bets window names (data/kickwin.js, 2026-10-05), in Node.

A window is named by the league's Eastern slot, with Preview's own words, never by a Pacific hour: its times
are written in the reader's clock, and "Sunday morning" beside "1:00 PM" is wrong for a New York reader."""
import pytest

from wording import words


@pytest.fixture(scope="module")
def kw(node_js):
    return node_js("data/kickwin.js")


@pytest.mark.parametrize("slot, name, part", [
    ("thu", "preview.win.thu", "Night"), ("sunam", "preview.win.sunam", "Morning"), ("sun1", "preview.win.sun1", "Early"),
    ("sunlate", "preview.win.sunlate", "Late"), ("sunnight", "preview.win.sunnight", "Night"), ("mon", "preview.win.mon", "Night"),
])
def test_a_window_wears_previews_name_for_its_slot(kw, slot, name, part):
    w = {"k": "morning", "label": "Sunday Morning", "slot": slot}
    assert kw("kickWinName", w) == words(name)
    assert kw("kickWinPart", w) == part


def test_the_one_p_m_wave_is_early_not_morning_in_any_clock(kw):
    """The 1 PM ET wave is key `morning` (a Pacific bucket) and slot sun1: it is "Sunday early", never "morning"."""
    w = {"k": "morning", "label": "Sunday Morning", "slot": "sun1", "date": "2026-10-04"}
    assert kw("kickWinName", w) == words("preview.win.sun1") and "orning" not in kw("kickWinPart", w)


def test_a_day_and_a_window_with_no_slot_keep_their_own_words(kw):
    day = {"k": "day-2026-10-04", "label": "All Sunday", "wins": ["morning"], "slot": "sun1"}
    assert kw("kickWinName", day) is None
    assert kw("kickWinName", {"k": "evening", "label": "Saturday Night"}) is None
    assert kw("kickWinPart", {"k": "morning-sat", "label": "x"}) == "Early"
    assert kw("kickWinPart", {"k": "afternoon", "label": "x"}) == "Late"
    assert kw("kickWinPart", {"k": "evening-mon", "label": "x"}) == "Night"
