"""The profile's pure helpers (ui/matchup.js, surface/profile/facts.js, sheet.js, sections.js), in Node.

Each one takes data and returns a string, a rank or a class name, so none needs a page. They were
the asserts of five test_profile.py tests that loaded Chromium for a function call; moved out
2026-10-05. What the page draws from them (the sphere's caption, the ladder, the strip) is still
test_profile.py, in the browser."""
import html
import re

import pytest

# The sheet's rank reads USAGE.sheet (data/usage.js, declared after the profile files on the page). A
# stub with three players tied and not: A and B on 10 carries, C on 5, one game each, position "XX".
USAGE = {"sheet": {"axes": {}, "rows": [
    {"n": "A", "slug": "a", "pos": "XX", "team": "T", "g": 1, "v": {"car": 10}},
    {"n": "B", "slug": "b", "pos": "XX", "team": "T", "g": 1, "v": {"car": 10}},
    {"n": "C", "slug": "c", "pos": "XX", "team": "T", "g": 1, "v": {"car": 5}},
]}}


@pytest.fixture(scope="module")
def matchup(node_js):
    return node_js("ui/matchup.js")


@pytest.fixture(scope="module")
def profile(node_js):
    # sample.js (sheetThin) before sheet.js, as on the page; facts.js holds the rank helpers.
    return node_js("surface/profile/sample.js", "surface/profile/sheet.js", "surface/profile/facts.js",
                   globals={"USAGE": USAGE})


@pytest.fixture(scope="module")
def sections(node_js):
    return node_js("surface/profile/sections.js")


def test_ordinal_and_colour_class(matchup):
    got = {
        "nth": matchup("ordinal(easiestRank({rank: 24, of: 32}))"),
        "suffixes": matchup("[1, 2, 3, 4, 11, 12, 13, 21, 22, 23].map(ordinal)"),
        "cls": matchup("[8, 9, 24, 25].map(n => matchupClass(n, 32))"),
    }
    assert got["nth"] == "9th"
    assert got["suffixes"] == ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd"]
    assert got["cls"] == ["mu-easy", "", "", "mu-hard"]


def test_ties_share_a_rank(profile):
    """Competition ranking: two tied for first are both 1st and say so, the next is 3rd -- never
    RB1 and RB2 by whichever the sort happened to put first."""
    assert profile("sheetRank", "XX", "car", "a") == [1, 3, True]
    assert profile("sheetRank", "XX", "car", "b") == [1, 3, True]
    assert profile("sheetRank", "XX", "car", "c") == [3, 3, False]
    assert profile("sheetRank", "XX", "car", "nobody") is None
    # The tie is in the rank itself -- both are 1st and the next is 3rd -- not in a marker on it.
    assert profile("rankText", "XX", [1, 3, True]) == "XX1"
    assert profile("rankText", "XX", [3, 3, False]) == "XX3"
    assert profile("rankMark", [1, 3, True]) == "#1"
    assert profile("rankAmong", {"a": 2.5, "b": 2.5, "c": 2.5}, "b") == [1, 3, True]


def test_height_reads_in_feet_not_inches(profile):
    """Sleeper stores height as bare inches in a string; nobody reads a receiver as 73."""
    assert profile("inchesText", "73") == "6′1″"
    assert profile("inchesText", "72") == "6′0″"
    assert profile("inchesText", None) is None
    assert profile("shortName", "Xavier Worthy") == "X. Worthy"
    assert profile("shortName", "Kenneth Walker III") == "K. Walker III"
    assert profile("shortName", "Ja'Marr Chase") == "J. Chase"


def text_of(markup):
    """What the browser's textContent would give for a string of markup."""
    return html.unescape(re.sub(r"<[^>]*>", "", markup))


def test_red_zone_line_switches_at_ten(sections):
    nouns = ["team target", "team targets"]
    got = [text_of(sections("rzLineHTML", n, team, share, nouns, False))
           for n, team, share in ((1, 5, 0.2), (3, 10, 0.3))]
    assert got[0].startswith("1 of 5") and "%" not in got[0]
    assert got[1].startswith("30% · 3 of 10")


# ---- the profile's headline is this week's projection (plan U3, 2026-10-05) ----

@pytest.fixture(scope="module")
def lede(node_js):
    return node_js("data/lede.js")


def cells(lede, **kw):
    inp = {"proj": {"pts": 17.4, "out": None, "done": None}, "ppg": 26.2, "rank": "WR3",
           "share": {"id": "targets", "pct": "31%"}, "snaps": "88%"}
    inp.update(kw)
    return lede("ledeCells", inp)


def test_the_projection_leads_the_strip_and_season_ppg_comes_second(lede):
    got = cells(lede)
    # "WR3 / 26.2 PPG" used to lead and read as the projection; now it is labelled as what it is.
    assert [c["id"] for c in got] == ["proj", "ppg", "rank", "share", "snaps"]
    assert (got[0]["value"], got[0]["label"]) == ("17.4", "Proj.")
    assert (got[1]["value"], got[1]["label"]) == ("26.2", "PPG")
    assert got[2]["label"] == "Rank" and got[2]["value"] == "WR3"      # right after the PPG it is ranked by


def test_an_injured_or_idle_player_headlines_the_reason_not_a_zero(lede):
    out = cells(lede, proj={"pts": 0, "out": "Out", "done": None})[0]
    assert (out["id"], out["value"]) == ("proj", "Out")
    assert cells(lede, proj={"pts": 21.0, "out": None, "done": "played"})[0]["value"] == "PLAYED"
    assert cells(lede, proj={"pts": 0, "out": None, "done": "bye"})[0]["value"] == "BYE"


def test_a_cell_with_no_source_is_left_out_and_nothing_means_no_strip(lede):
    assert [c["id"] for c in cells(lede, proj=None, ppg=None)] == ["rank", "share", "snaps"]
    assert lede("ledeCells", {"proj": None, "ppg": None, "rank": None, "share": None, "snaps": None}) == []
    # A projection of 0.0 for a healthy player is a number, not a gap.
    assert cells(lede, proj={"pts": 0, "out": None, "done": None})[0]["value"] == "0.0"


# ---- plain words for the profile's signal line (plan U3, 2026-10-05) ----

@pytest.fixture(scope="module")
def sig(node_js):
    return node_js("data/signals.js")


def test_a_rising_verdict_says_who_gained_what_in_a_sentence(sig):
    got = sig("signalWords", "RISING", "snaps +5.0, share +19; buy or start")
    assert got == "Snaps up 5.0 points and his share of the work up 19 points. Worth a start, or an add if he is free."


# The audit's own line: "RISING snaps −5.0, share +19; buy or start", with a real minus sign.
@pytest.mark.parametrize("why", ["snaps -5.0, share +19; buy or start", "snaps −5.0, share +19; buy or start"],
                         ids=["hyphen minus", "real minus sign"])
def test_a_rising_verdict_with_snaps_down_says_down_and_keeps_the_minus_out_of_it(sig, why):
    got = sig("signalWords", "RISING", why)
    assert got.startswith("Snaps down 5.0 points and his share of the work up 19 points."), got
    assert "-" not in got and "−" not in got and "+" not in got


def test_flat_snaps_and_flat_share_read_as_flat(sig):
    assert sig("signalWords", "RISING", "snaps +0.0, share -0; buy or start").startswith("Snaps flat and his share of the work flat.")


def test_sell_high_says_he_scored_more_than_his_work_earned(sig):
    got = sig("signalWords", "SELL HIGH", "+45% over what the usage bought, on a part-time role")
    assert got == "Scoring 45% more than his snaps and touches earned, on a part-time role. The points are likely to cool."


def test_a_reason_the_page_does_not_know_is_passed_through_not_dropped(sig):
    assert sig("signalWords", "RISING", "something new") == "something new"
    assert sig("signalWords", "SELL HIGH", "") == ""
    assert sig("signalWords", None, "x") == ""
