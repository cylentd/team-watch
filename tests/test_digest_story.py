"""Claude's pick of the best story between games takes the Digest banner (2026-10-04).

David: "claude should determine what is the best headline from Sunday's results, Injuries, etc." ff-jarvis
writes digest_headline.json (and the feed block of the same name) after the packet; design/sources.py reads
it, design/digest.py keeps it as LIVE_DIGEST.story for the packet's own week, and the banner draws it while no
game is on and only when it is newer than the packet. No test reads real ff-jarvis data: the block is planted."""
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

import pytest  # noqa: E402

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
import sources  # noqa: E402
from digest import live_digest  # noqa: E402
from sources import load_digest, load_digest_headline  # noqa: E402
from test_digest_live import (MONDAY_EARLY, assert_generic, cfg, digest)  # noqa: E402,F401

# The fixture packet is season 2026, week 3, asof "2026-09-25 22:40" (Pacific).
BLOCK = {"season": 2026, "week": 3, "asof": "2026-10-04T21:30:00", "llm": "ok", "kind": "result",
         "head": "Bijan Robinson runs wild in the Falcons win", "fact": "152 yards and 2 TDs on 24 carries.",
         "player": {"name": "Bijan Robinson", "club": "ATL", "pos": "RB"}, "club": "ATL", "candidate_id": "res-bijan"}


def _story(**over):
    return live_digest(load_digest(), slugify, None, {**BLOCK, **over})["story"]


# ------------------------------------------------------------------ sources


def _where(monkeypatch, tmp_path, feed=None, file=None):
    """Point sources at a scratch feed and data dir: never the real ff-jarvis checkout."""
    data = tmp_path / "data"
    data.mkdir()
    if feed is not None:
        (tmp_path / "feed.json").write_text(json.dumps({"digest_headline": {"data": feed}}), encoding="utf-8")
    if file is not None:
        (data / "digest_headline.json").write_text(json.dumps(file), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", tmp_path / "feed.json")
    monkeypatch.setattr(sources, "DWR", data)


def test_the_feed_block_is_read_first(monkeypatch, tmp_path):
    _where(monkeypatch, tmp_path, feed=BLOCK, file={**BLOCK, "head": "From the file"})
    assert load_digest_headline()["head"] == BLOCK["head"]


def test_the_file_is_the_fallback(monkeypatch, tmp_path):
    _where(monkeypatch, tmp_path, file=BLOCK)
    assert load_digest_headline() == BLOCK


def test_neither_source_is_none(monkeypatch, tmp_path):
    _where(monkeypatch, tmp_path)
    assert load_digest_headline() is None


# ------------------------------------------------------------------ digest.py and the contract


def test_the_story_is_passed_through_and_the_producers_bookkeeping_is_dropped():
    s = _story()
    assert s == {"head": BLOCK["head"], "fact": BLOCK["fact"], "kind": "result", "asof": "2026-10-04 21:30:00",
                 "club": "ATL", "player": {"n": "Bijan Robinson", "slug": "bijan-robinson", "pos": "RB", "team": "ATL"}}
    assert "llm" not in s and "candidate_id" not in s


def test_a_story_for_another_week_or_season_is_dropped():
    assert _story(week=2) is None
    assert _story(week=4) is None
    assert _story(season=2025) is None


def test_no_block_is_no_story():
    assert live_digest(load_digest(), slugify)["story"] is None
    assert live_digest(load_digest(), slugify, None, None)["story"] is None


def test_a_story_without_words_or_a_clock_is_dropped():
    for bad in ({"head": ""}, {"fact": None}, {"kind": ""}, {"asof": None}, {"asof": "not a date"}):
        assert _story(**bad) is None, bad


def test_a_story_may_have_no_player_and_no_club():
    s = _story(kind="preview", player=None, club=None)
    assert s["player"] is None and s["club"] is None
    contract.validate("LIVE_DIGEST", live_digest(load_digest(), slugify, None, {**BLOCK, "player": None, "club": None}))


def test_a_stamp_with_an_offset_is_moved_to_pacific():
    # 2026-10-05 04:30 UTC is 21:30 the evening before in Pacific daylight time (UTC-7)
    assert _story(asof="2026-10-05T04:30:00Z")["asof"] == "2026-10-04 21:30:00"
    assert _story(asof="2026-10-05T04:30:00+00:00")["asof"] == "2026-10-04 21:30:00"


def test_the_block_passes_the_contract_and_a_missing_story_key_fails_it():
    b = live_digest(load_digest(), slugify, None, BLOCK)
    contract.validate("LIVE_DIGEST", b)
    assert contract.problems("LIVE_DIGEST", {k: v for k, v in b.items() if k != "story"}) == ["LIVE_DIGEST.story"]
    cut = {**b, "story": {k: v for k, v in b["story"].items() if k != "kind"}}
    assert contract.problems("LIVE_DIGEST", cut) == ["LIVE_DIGEST.story.kind"]
    contract.validate("LIVE_DIGEST", live_digest(load_digest(), slugify))      # null story is fine


# ------------------------------------------------------------------ the banner


AFTER_THE_LAST_FINAL = "2026-10-06T12:00:00Z"
STORY = {"head": "Bijan Robinson runs wild in the Falcons win", "fact": "152 yards and 2 TDs on 24 carries.",
         "kind": "result", "asof": "2026-10-05 05:30:00", "club": "ATL",
         "player": {"n": "Bijan Robinson", "slug": "bijan-robinson", "pos": "RB", "team": "ATL"}}

SET = """(story) => { LIVE_DIGEST.story = story; DG_CUT = null; render(); }"""


def banner(page):
    return re.sub(r"\s+", " ", page.locator(".dg-lead-h").inner_text()).strip()


# A planted Digest page per state, built once per file per worker and reused: a load is the cost (about
# 0.7 s), a plant is not. Re-planting on the same page would push LIVE_RANKS rows again, so a test that
# takes a page gets it back as the plant left it: the story, the scorers and the open sheet are reset.
RESET = """() => { 'use strict'; LIVE_DIGEST.story = window.__story0; GD_STATS.lead = JSON.parse(window.__lead0);
  document.getElementById('modal').classList.remove('on'); DG_CUT = null; render(); }"""


@pytest.fixture(scope="module")
def _pages(browser, page_file):
    pages = {}
    yield browser, page_file, pages
    for ctx, _, _ in pages.values():
        ctx.close()


@pytest.fixture
def planted(_pages):
    """planted(**state) -> (page, errors), the Digest as `digest()` plants it for that state."""
    browser, page_file, pages = _pages

    def get(**state):
        key = json.dumps(cfg(**state), sort_keys=True)
        if key not in pages:
            ctx, page, errors = digest(browser, page_file, **state)
            page.evaluate("() => { window.__story0 = LIVE_DIGEST.story; window.__lead0 = JSON.stringify(GD_STATS.lead); }")
            assert errors == []          # whatever the load or the plant raised fails here, not lost to a clear
            pages[key] = (ctx, page, errors)
        _, page, errors = pages[key]
        left, errors[:] = list(errors), []   # each test answers for its own page errors only,
        assert left == []                    # and an error raised or left over since the last one fails this
        page.evaluate(RESET)
        return page, errors
    return get


@pytest.mark.render
def test_between_games_the_banner_is_claudes_story(planted):
    page, errors = planted(at=MONDAY_EARLY, sunState="complete")
    assert banner(page) == "St. Brown went off for 60 yards"             # no story yet: the top scorer, by his line
    page.evaluate(SET, STORY)
    assert banner(page) == STORY["head"]
    assert page.locator(".dg-lead-fact").inner_text() == STORY["fact"]
    lead = page.locator("article.dg-lead")
    assert "team" in lead.get_attribute("class") and "--team:" in lead.get_attribute("style")    # ATL's colours
    assert page.locator(".dg-lead-go[data-dglv]").count() == 1                                    # the band opens his profile
    assert_generic(page)
    page.locator(".dg-lead-go").click()
    assert "on" in page.locator("#modal").get_attribute("class")
    page.keyboard.press("Escape")
    page.wait_for_selector("#modal.on", state="detached")
    assert errors == []


@pytest.mark.render
def test_after_the_last_final_the_story_still_leads(planted):
    page, errors = planted(at=AFTER_THE_LAST_FINAL, sunState="complete", monStates=["complete"])
    page.evaluate(SET, STORY)
    assert banner(page) == STORY["head"]
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert errors == []


@pytest.mark.render
def test_a_game_in_play_beats_the_story(planted):
    page, errors = planted()          # Sunday afternoon, games on
    page.evaluate(SET, STORY)
    assert banner(page) == "St. Brown ERUPTS: 60 yards"
    assert errors == []


@pytest.mark.render
def test_a_story_older_than_the_packet_does_not_show(planted):
    page, errors = planted(at=MONDAY_EARLY, sunState="complete")
    for asof in ("2026-09-20 10:00:00", "2026-09-25 22:40:00"):          # older, and the same minute as the packet
        page.evaluate(SET, {**STORY, "asof": asof})
        assert banner(page) == "St. Brown went off for 60 yards", asof
    assert errors == []


@pytest.mark.render
def test_a_preview_without_a_player_wears_the_clubs_colours_or_is_quiet(planted):
    page, errors = planted(at=MONDAY_EARLY, sunState="complete")
    page.evaluate(SET, {**STORY, "kind": "preview", "player": None, "club": "KC", "head": "Chiefs and Texans on Monday night"})
    lead = page.locator("article.dg-lead")
    assert banner(page) == "Chiefs and Texans on Monday night"
    assert "team" in lead.get_attribute("class") and page.locator(".dg-lead-go").count() == 0
    page.evaluate(SET, {**STORY, "kind": "preview", "player": None, "club": None})
    assert "quiet" in page.locator("article.dg-lead").get_attribute("class")
    assert errors == []


@pytest.mark.render
def test_the_storys_words_are_escaped(planted):
    page, errors = planted(at=MONDAY_EARLY, sunState="complete")
    page.evaluate(SET, {**STORY, "head": "<img src=x onerror=window.__pwned=1> Gibbs & co", "fact": "<b>bold</b> 1 < 2"})
    assert banner(page) == "<img src=x onerror=window.__pwned=1> Gibbs & co"
    assert page.locator(".dg-lead img[src='x']").count() == 0 and page.locator(".dg-lead-fact b").count() == 0
    assert page.evaluate("window.__pwned") is None
    assert errors == []


@pytest.mark.render
def test_the_story_names_no_fantasy_team_or_league(planted):
    page, errors = planted(at=MONDAY_EARLY, sunState="complete")
    page.evaluate(SET, STORY)
    assert_generic(page)
    assert errors == []

# test_the_digest_story_code_reads_no_league_roster_or_matchup was deleted (2026-10-05): its grep is a
# strict subset of test_digest_live.py::test_the_digest_surface_reads_no_league_roster_or_matchup, which
# reads every file under surface/digest (lead.js included) for a superset of the same names.


# ------------------------------------------------------------------ the top scorer's call, by the size of his day
#
# David, 2026-10-04, on "McMillan leads the week with 38.2 points": "38.2 is insane number in fantasy... use
# more excited wording. This is the headline afterall. Should be like NFL announcer to build the hype."

TOP = """(rows) => { GD_STATS.lead = Object.fromEntries(rows.map(([n, pos, team, pts, s], i) => [String(100 + i), {n, pos, team, pts, s: s || {}}]));
  DG_CUT = null; render(); }"""
ON = {"at": "2026-10-04T14:00:00Z"}                       # Sunday, games on: the present tense
FINAL = {"at": MONDAY_EARLY, "sunState": "complete"}      # between windows: the past
# David, 2026-10-05: the headline "should use yards and TDs", not fantasy points (every league scores
# differently). The tier is still chosen by points; what prints is his real line.
BIG_ON = ["{n} ERUPTS: {p}", "{n} can’t be stopped: {p}"]
BIG_FIN = ["{n} went off for {p}", "{n} was unstoppable: {p}"]
SOLID_ON = ["{n} is rolling: {p}", "{n} piles up {p}"]
SOLID_FIN = ["{n} rolled to {p}", "{n} piled up {p}"]
RUSH = {"rush_att": 22, "rush_yd": 177, "rush_td": 2}      # "177 yards, 2 TDs"
CATCH = {"rec": 14, "rec_yd": 192, "rec_td": 2}            # "14 catches, 192 yards, 2 TDs"


def call(planted, rows, **state):
    page, errors = planted(**state)
    page.evaluate(TOP, rows)
    text = banner(page)
    assert errors == []
    return text


def said(options, n, p):
    return [o.format(n=n, p=p) for o in options]


@pytest.mark.render
def test_a_plain_day_is_his_yards_and_tds(planted):
    rows = [["Tee Higgins", "WR", "CIN", 14.2, {"rec_yd": 87, "rec_td": 1}], ["Cam Skattebo", "RB", "NYG", 9.0]]
    assert call(planted, rows, **ON) == "Higgins: 87 yards, 1 TD"
    assert call(planted, rows, **FINAL) == "Higgins: 87 yards, 1 TD"


@pytest.mark.render
def test_a_scorer_with_nothing_to_count_is_said_without_a_number(planted):
    rows = [["Harrison Butker", "K", "KC", 14.0, {"fgm": 4, "fga": 4}], ["Tee Higgins", "WR", "CIN", 9.0]]
    assert call(planted, rows, **ON) == "Butker is out in front"
    assert call(planted, rows, **FINAL) == "Butker led the week"


@pytest.mark.render
def test_twenty_points_is_a_solid_call_and_it_follows_the_tense(planted):
    s = {"rush_yd": 104}
    rows = [["Cam Skattebo", "RB", "NYG", 24.0, s], ["Tee Higgins", "WR", "CIN", 14.2]]
    assert call(planted, rows, **ON) in said(SOLID_ON, "Skattebo", "104 yards")
    assert call(planted, rows, **FINAL) in said(SOLID_FIN, "Skattebo", "104 yards")
    # 29.9 with no big stat line is still solid, not big
    got = call(planted,[["Cam Skattebo", "RB", "NYG", 29.9, {"rush_yd": 120, "rush_td": 1}], ["Tee Higgins", "WR", "CIN", 20.0]], **ON)
    assert got in said(SOLID_ON, "Skattebo", "120 yards, 1 TD")


@pytest.mark.render
def test_thirty_points_is_a_big_call(planted):
    rows = [["Cam Skattebo", "RB", "NYG", 33.0, RUSH], ["Tee Higgins", "WR", "CIN", 28.0]]
    assert call(planted, rows, **ON) in said(BIG_ON, "Skattebo", "177 yards, 2 TDs")
    assert call(planted, rows, **FINAL) in said(BIG_FIN, "Skattebo", "177 yards, 2 TDs")


@pytest.mark.render
def test_ten_points_clear_of_the_field_laps_it(planted):
    rows = [["Tetairoa McMillan", "WR", "CAR", 38.2, CATCH], ["Tee Higgins", "WR", "CIN", 20.1]]
    assert call(planted, rows, **ON) == "McMillan laps the field with 14 catches, 192 yards, 2 TDs"
    assert call(planted, rows, **FINAL) == "McMillan lapped the field with 14 catches, 192 yards, 2 TDs"
    # a big day with the second score close behind does not lap anyone
    close = [["Tetairoa McMillan", "WR", "CAR", 38.2, CATCH], ["Tee Higgins", "WR", "CIN", 33.0]]
    assert call(planted,close, **ON) in said(BIG_ON, "McMillan", "14 catches, 192 yards, 2 TDs")


@pytest.mark.render
@pytest.mark.parametrize("pos,s,line", [("RB", {"rush_td": 2, "rec_td": 1}, "3 TDs"), ("WR", {"rec_yd": 160}, "160 yards"),
                                        ("RB", {"rush_yd": 120, "rec_yd": 30}, "150 yards"),
                                        ("QB", {"pass_yd": 310}, "310 yards"), ("QB", {"pass_yd": 250, "pass_td": 3}, "250 yards, 3 TDs")])
def test_three_touchdowns_or_a_big_yard_count_make_a_big_call_at_any_score(planted, pos, s, line):
    rows = [["Cam Skattebo", pos, "NYG", 22.0, s], ["Tee Higgins", "WR", "CIN", 21.0]]
    assert call(planted, rows, **ON) in said(BIG_ON, "Skattebo", line)


@pytest.mark.render
def test_a_big_stat_line_that_falls_short_stays_solid(planted):
    rows = [["Cam Skattebo", "WR", "NYG", 22.0, {"rec_td": 2, "rec_yd": 149}], ["Tee Higgins", "WR", "CIN", 21.0]]
    assert call(planted, rows, **ON) in said(SOLID_ON, "Skattebo", "149 yards, 2 TDs")


@pytest.mark.render
@pytest.mark.parametrize("pos,s,line", [
    ("QB", {"pass_cmp": 24, "pass_att": 31, "pass_yd": 312, "pass_td": 3}, "312 yards, 3 TDs"),
    ("QB", {"pass_yd": 280, "pass_td": 2, "rush_yd": 40, "rush_td": 1}, "280 yards, 3 TDs"),    # a passer's rushing TD counts too
    ("RB", {"rush_att": 22, "rush_yd": 177, "rush_td": 2}, "177 yards, 2 TDs"),
    ("WR", {"rec": 14, "rec_yd": 192, "rec_td": 2}, "14 catches, 192 yards, 2 TDs"),           # 10+ catches name the catches
    ("WR", {"rec": 9, "rec_yd": 140, "rec_td": 1}, "140 yards, 1 TD"),                          # fewer do not; one TD is singular
    ("RB", {"rush_yd": 90, "rec": 12, "rec_yd": 60}, "150 yards")])                             # yards are rushing plus receiving
def test_the_line_is_the_yards_and_tds_that_make_the_call(planted, pos, s, line):
    rows = [["Cam Skattebo", pos, "NYG", 40.0, s], ["Tee Higgins", "WR", "CIN", 9.0]]
    got = call(planted, rows, **ON)
    assert line in got, (got, line)
    assert "point" not in got


@pytest.mark.render
def test_the_phrasing_is_fixed_by_the_player_and_both_phrasings_are_used(planted):
    names = ["Cam Skattebo", "Tee Higgins", "Josh Allen", "Jahmyr Gibbs", "Puka Nacua", "Ja'Marr Chase", "Bijan Robinson", "Drake London"]
    page, errors = planted(**ON)
    seen = set()
    for n in names:
        page.evaluate(TOP, [[n, "WR", "NYG", 33.0, {"rec_yd": 120, "rec_td": 2}], ["Z Second", "WR", "CIN", 30.0]])
        first = banner(page)
        page.evaluate("paintDigestLive()")                                   # a poll
        page.evaluate("GD_STATS.lead[100].s.rec_yd = 135; paintDigestLive()")  # more yards: same words
        assert banner(page) == first.replace("120 yards", "135 yards")
        seen.add("ERUPTS" in first)
    assert seen == {True, False}, seen
    assert errors == []


@pytest.mark.render
def test_the_call_is_plain_words(planted):
    text = call(planted,[["Tetairoa McMillan", "WR", "CAR", 38.2, CATCH], ["Tee Higgins", "WR", "CIN", 20.1]], **ON)
    assert not re.search(r"fantasy|bet|parlay|lock|odds|spread|projected|should|may|might|luck", text, re.I), text


BY_LINES = [
    ("QB", {"pass_cmp": 24, "pass_att": 31, "pass_yd": 312, "pass_td": 3, "pass_int": 1, "rush_att": 4, "rush_yd": 18}, "24/31 · 1 INT · 4 car 18"),
    ("RB", {"rush_att": 22, "rush_yd": 177, "rush_td": 2, "rec": 3, "rec_tgt": 4, "rec_yd": 20}, "22 car · 3/4 rec"),
    ("WR", {"rec": 14, "rec_tgt": 17, "rec_yd": 192, "rec_td": 2}, "17 tgt"),             # the head has the 14, so the by-line gives targets
    ("WR", {"rec": 7, "rec_tgt": 9, "rec_yd": 104}, "7/9 rec"),
    ("RB", {"rush_att": 20, "rush_yd": 90, "rush_td": 2, "rec": 2, "rec_tgt": 2, "rec_yd": 8}, "20 car"),   # 2/2 rec shares a 2 with "2 TDs": dropped
    ("WR", {"rec_yd": 88, "rec_td": 1}, "")]                                              # nothing left: just the clock


@pytest.mark.render
@pytest.mark.parametrize("pos,s,by", BY_LINES)
def test_the_by_line_adds_what_the_head_lacks_and_repeats_no_number(planted, pos, s, by):
    """David's coordinator, 2026-10-05: the by-line never repeats a number the head prints; it keeps the
    rest of his day and the game's clock, and when nothing is left it is the clock alone."""
    page, errors = planted(**ON)
    page.evaluate(TOP, [["Cam Skattebo", pos, "NYG", 40.0, s], ["Tee Higgins", "WR", "CIN", 9.0]])
    head, fact = banner(page), page.locator(".dg-lead-fact").inner_text().strip()
    assert errors == []
    assert not set(re.findall(r"\d+", head)) & set(re.findall(r"\d+", fact)), (head, fact)
    assert fact.startswith(by)
    assert by or "·" not in fact                                  # no leftovers: the clock alone


@pytest.mark.render
def test_the_banner_never_prints_points(planted):
    """David, 2026-10-05: every league scores differently, so the banner counts yards and TDs. A pt count
    in the head or by-line would be one league's scoring."""
    rows = [["Tetairoa McMillan", "WR", "CAR", 38.2, CATCH], ["Tee Higgins", "WR", "CIN", 20.1, {"rec_yd": 80}]]
    for state in (ON, FINAL):
        page, errors = planted(**state)
        page.evaluate(TOP, rows)
        assert not re.search(r"point|pts|38\.2", page.locator(".dg-lead").inner_text(), re.I)
        assert errors == []
