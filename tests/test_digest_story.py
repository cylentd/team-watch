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
from test_digest_live import (MONDAY_EARLY, assert_generic, digest)  # noqa: E402,F401
from test_render import browser  # noqa: E402,F401  (the suite's one Chromium)

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


@pytest.mark.render
def test_between_games_the_banner_is_claudes_story(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete")
    assert banner(page) == "St. Brown went off for 31.4 points"          # no story yet: the top scorer
    page.evaluate(SET, STORY)
    assert banner(page) == STORY["head"]
    assert page.locator(".dg-lead-fact").inner_text() == STORY["fact"]
    lead = page.locator("article.dg-lead")
    assert "team" in lead.get_attribute("class") and "--team:" in lead.get_attribute("style")    # ATL's colours
    assert page.locator(".dg-lead-go[data-dglv]").count() == 1                                    # the band opens his profile
    assert_generic(page)
    page.locator(".dg-lead-go").click()
    assert "on" in page.locator("#modal").get_attribute("class")
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_after_the_last_final_the_story_still_leads(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=AFTER_THE_LAST_FINAL, sunState="complete", monStates=["complete"])
    page.evaluate(SET, STORY)
    assert banner(page) == STORY["head"]
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_game_in_play_beats_the_story(browser, page_file):
    ctx, page, errors = digest(browser, page_file)          # Sunday afternoon, games on
    page.evaluate(SET, STORY)
    assert banner(page) == "St. Brown goes off: 31.4 points"
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_story_older_than_the_packet_does_not_show(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete")
    for asof in ("2026-09-20 10:00:00", "2026-09-25 22:40:00"):          # older, and the same minute as the packet
        page.evaluate(SET, {**STORY, "asof": asof})
        assert banner(page) == "St. Brown went off for 31.4 points", asof
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_a_preview_without_a_player_wears_the_clubs_colours_or_is_quiet(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete")
    page.evaluate(SET, {**STORY, "kind": "preview", "player": None, "club": "KC", "head": "Chiefs and Texans on Monday night"})
    lead = page.locator("article.dg-lead")
    assert banner(page) == "Chiefs and Texans on Monday night"
    assert "team" in lead.get_attribute("class") and page.locator(".dg-lead-go").count() == 0
    page.evaluate(SET, {**STORY, "kind": "preview", "player": None, "club": None})
    assert "quiet" in page.locator("article.dg-lead").get_attribute("class")
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_storys_words_are_escaped(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete")
    page.evaluate(SET, {**STORY, "head": "<img src=x onerror=window.__pwned=1> Gibbs & co", "fact": "<b>bold</b> 1 < 2"})
    assert banner(page) == "<img src=x onerror=window.__pwned=1> Gibbs & co"
    assert page.locator(".dg-lead img[src='x']").count() == 0 and page.locator(".dg-lead-fact b").count() == 0
    assert page.evaluate("window.__pwned") is None
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_story_names_no_fantasy_team_or_league(browser, page_file):
    ctx, page, errors = digest(browser, page_file, at=MONDAY_EARLY, sunState="complete")
    page.evaluate(SET, STORY)
    assert_generic(page)
    ctx.close()
    assert errors == []


def test_the_digest_story_code_reads_no_league_roster_or_matchup():
    """lead.js is under test_digest_live's grep already; this pins that the story path adds no personal read."""
    src = (REPO / "design" / "src" / "js" / "surface" / "digest" / "lead.js").read_text(encoding="utf-8")
    code = re.sub(r"/\*.*?\*/|//[^\n]*", "", src, flags=re.S)
    assert not re.search(r"\bGD\.leagues|\blg\.(me|teams|games|median)\b|\bgdMineIn\b", code)


# ------------------------------------------------------------------ the top scorer's call, by the size of his day
#
# David, 2026-10-04, on "McMillan leads the week with 38.2 points": "38.2 is insane number in fantasy... use
# more excited wording. This is the headline afterall. Should be like NFL announcer to build the hype."

TOP = """(rows) => { GD_STATS.lead = Object.fromEntries(rows.map(([n, pos, team, pts, s], i) => [String(100 + i), {n, pos, team, pts, s: s || {}}]));
  DG_CUT = null; render(); }"""
ON = {"at": "2026-10-04T14:00:00Z"}                       # Sunday, games on: the present tense
FINAL = {"at": MONDAY_EARLY, "sunState": "complete"}      # between windows: the past
BIG_ON = ["{n} goes off: {p} points", "{n} can’t be stopped: {p} points"]
BIG_FIN = ["{n} went off for {p} points", "{n} was unstoppable: {p} points"]
SOLID_ON = ["{n} is rolling: {p} points", "{n} piles up {p} points"]
SOLID_FIN = ["{n} rolled to {p} points", "{n} piled up {p} points"]


def call(browser, page_file, rows, **state):
    ctx, page, errors = digest(browser, page_file, **state)
    page.evaluate(TOP, rows)
    text = banner(page)
    ctx.close()
    assert errors == []
    return text


def said(options, n, p):
    return [o.format(n=n, p=p) for o in options]


@pytest.mark.render
def test_a_plain_day_is_the_plain_count(browser, page_file):
    rows = [["Tee Higgins", "WR", "CIN", 14.2], ["Cam Skattebo", "RB", "NYG", 9.0]]
    assert call(browser, page_file, rows, **ON) == "Higgins has 14.2 points"
    assert call(browser, page_file, rows, **FINAL) == "Higgins leads the week with 14.2 points"


@pytest.mark.render
def test_twenty_points_is_a_solid_call_and_it_follows_the_tense(browser, page_file):
    rows = [["Cam Skattebo", "RB", "NYG", 24.0], ["Tee Higgins", "WR", "CIN", 14.2]]
    assert call(browser, page_file, rows, **ON) in said(SOLID_ON, "Skattebo", "24.0")
    assert call(browser, page_file, rows, **FINAL) in said(SOLID_FIN, "Skattebo", "24.0")
    # 29.9 with no big stat line is still solid, not big
    assert call(browser, page_file, [["Cam Skattebo", "RB", "NYG", 29.9], ["Tee Higgins", "WR", "CIN", 20.0]], **ON) in said(SOLID_ON, "Skattebo", "29.9")


@pytest.mark.render
def test_thirty_points_is_a_big_call(browser, page_file):
    rows = [["Cam Skattebo", "RB", "NYG", 33.0], ["Tee Higgins", "WR", "CIN", 28.0]]
    assert call(browser, page_file, rows, **ON) in said(BIG_ON, "Skattebo", "33.0")
    assert call(browser, page_file, rows, **FINAL) in said(BIG_FIN, "Skattebo", "33.0")


@pytest.mark.render
def test_ten_points_clear_of_the_field_laps_it(browser, page_file):
    rows = [["Tetairoa McMillan", "WR", "CAR", 38.2], ["Tee Higgins", "WR", "CIN", 20.1]]
    assert call(browser, page_file, rows, **ON) == "McMillan laps the field with 38.2 points"
    assert call(browser, page_file, rows, **FINAL) == "McMillan lapped the field with 38.2 points"
    # a big day with the second score close behind does not lap anyone
    close = [["Tetairoa McMillan", "WR", "CAR", 38.2], ["Tee Higgins", "WR", "CIN", 33.0]]
    assert call(browser, page_file, close, **ON) in said(BIG_ON, "McMillan", "38.2")


@pytest.mark.render
@pytest.mark.parametrize("pos,s", [("RB", {"rush_td": 2, "rec_td": 1}), ("WR", {"rec_yd": 160}), ("RB", {"rush_yd": 120, "rec_yd": 30}),
                                   ("QB", {"pass_yd": 310}), ("QB", {"pass_td": 3})])
def test_three_touchdowns_or_a_big_yard_count_make_a_big_call_at_any_score(browser, page_file, pos, s):
    rows = [["Cam Skattebo", pos, "NYG", 22.0, s], ["Tee Higgins", "WR", "CIN", 21.0]]
    assert call(browser, page_file, rows, **ON) in said(BIG_ON, "Skattebo", "22.0")


@pytest.mark.render
def test_a_big_stat_line_that_falls_short_stays_solid(browser, page_file):
    rows = [["Cam Skattebo", "WR", "NYG", 22.0, {"rec_td": 2, "rec_yd": 149}], ["Tee Higgins", "WR", "CIN", 21.0]]
    assert call(browser, page_file, rows, **ON) in said(SOLID_ON, "Skattebo", "22.0")


@pytest.mark.render
def test_the_phrasing_is_fixed_by_the_player_and_both_phrasings_are_used(browser, page_file):
    names = ["Cam Skattebo", "Tee Higgins", "Josh Allen", "Jahmyr Gibbs", "Puka Nacua", "Ja'Marr Chase", "Bijan Robinson", "Drake London"]
    ctx, page, errors = digest(browser, page_file, **ON)
    seen = set()
    for n in names:
        page.evaluate(TOP, [[n, "WR", "NYG", 33.0], ["Z Second", "WR", "CIN", 30.0]])
        first = banner(page)
        page.evaluate("paintDigestLive()")                                   # a poll
        page.evaluate("GD_STATS.lead[100].pts = 34.5; paintDigestLive()")      # more points: same words
        assert banner(page) == first.replace("33.0", "34.5")
        seen.add("goes off" in first)
    assert seen == {True, False}, seen
    ctx.close()
    assert errors == []


@pytest.mark.render
def test_the_call_is_plain_words(browser, page_file):
    text = call(browser, page_file, [["Tetairoa McMillan", "WR", "CAR", 38.2], ["Tee Higgins", "WR", "CIN", 20.1]], **ON)
    assert not re.search(r"fantasy|bet|parlay|lock|odds|spread|projected|should|may|might|luck", text, re.I), text
