"""design/startsit.py: the Takes block, from ff-jarvis's calls, Pitcher List's and the record."""
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "design"))
sys.path.insert(0, str(REPO / "api"))

from _espn import slugify  # noqa: E402
import contract  # noqa: E402
from sources import load_startsit  # noqa: E402
from startsit import live_startsit  # noqa: E402
from test_render import SEED, browser  # noqa: E402,F401  (browser is a fixture)


def _block():
    return live_startsit(*load_startsit(), slugify)


def test_fixture_block_is_whole_and_holds_takes_only():
    """The best spot is not a take (2026-09-29: the matchup is a Ranks tag), so Gibbs and Kittle,
    the fixture's two best spots, are gone; the page orders the rest across positions by `gap`."""
    b = _block()
    contract.validate("LIVE_STARTSIT", b)
    assert [(r["pos"], r["tag"], r["n"], r["gap"]) for r in b["calls"]] == [
        ("QB", "start", "Brock Purdy", 1.67), ("RB", "start", "Chase Brown", 1.33),
        ("WR", "start", "Tee Higgins", 1.33), ("WR", "sit", "Amon-Ra St. Brown", 1.67)]


def test_row_keeps_reason_text_and_places_home_by_the_opponent():
    rows = {r["n"]: r for r in _block()["calls"]}
    assert rows["Tee Higgins"]["why"][1] == {"k": "mx", "t": "PIT D vs WRs: 3rd softest"}
    assert rows["Tee Higgins"]["but"] == ["No red-zone targets in 2 games"]
    assert rows["Tee Higgins"]["home"] is False              # "CIN @ PIT"
    assert rows["Amon-Ra St. Brown"]["home"] is True         # "CHI @ DET"
    assert rows["Amon-Ra St. Brown"]["slug"] == slugify("Amon-Ra St. Brown")


def test_record_comes_from_the_newest_graded_week():
    """The fixture is ff-jarvis's real weeks 1-3 record (2026-09-29), before any v2 week (4+)."""
    rec = _block()["record"]
    assert {k: v for k, v in rec.items() if k != "splits"} == {
        "through": 3, "weeks": [1, 2, 3],
        "ours": {"n": 48, "score": 0.371, "score_no_dnp": 0.38},
        "pl": {"n": 18, "score": 0.633, "score_no_dnp": 0.633},
        "fp": {"n": 48, "score": 0.629, "score_no_dnp": 0.62},
        "v2": None}


def test_a_grade_file_from_before_fantasypros_and_the_splits_reads_null():
    calls, pl, grade = load_startsit()
    g = json.loads(json.dumps(grade))
    for k in ("fantasypros", "splits"):
        g["startsit_record"].pop(k)
    rec = live_startsit(calls, pl, g, slugify)["record"]
    assert rec["fp"] is None and rec["splits"] is None


def test_fantasypros_side_comes_through_when_graded():
    """FantasyPros on our takes (2026-09-29): the other call on each, so its n is ours."""
    calls, pl, grade = load_startsit()
    g = json.loads(json.dumps(grade))
    g["startsit_record"]["fantasypros"] = {"n": 31, "score": 0.676, "score_no_dnp": 0.663}
    assert live_startsit(calls, pl, g, slugify)["record"]["fp"] == {"n": 31, "score": 0.676, "score_no_dnp": 0.663}


def test_last_weeks_pitcher_list_column_is_dropped():
    calls, pl, grade = load_startsit()
    old = json.loads(json.dumps(pl))
    old["week"] = 2
    b = live_startsit(calls, old, grade, slugify)
    assert b["pl"] == [] and b["article"] is None


def test_experts_week_rides_along_so_the_page_can_tell_early_from_agreed():
    """Tuesday the calls are next week's and the expert ranks last week's: no takes because nobody
    has ranked yet, which Blip says differently from 'we agree with the experts' (2026-09-29)."""
    b = _block()
    assert (b["week"], b["experts_week"]) == (3, 3)
    calls, pl, grade = load_startsit()
    early = json.loads(json.dumps(calls))
    early["inputs"]["expert_week"] = 2
    assert live_startsit(early, pl, grade, slugify)["experts_week"] == 2
    early.pop("inputs")
    assert live_startsit(early, pl, grade, slugify)["experts_week"] is None


def test_a_take_carries_its_reasons_and_a_gut_call_none():
    rows = {r["n"]: r for r in _block()["calls"]}
    assert rows["Chase Brown"]["backed"] is True
    assert [w["k"] for w in rows["Chase Brown"]["reasons"]] == ["script", "role"]
    assert rows["Tee Higgins"]["backed"] is False and rows["Tee Higgins"]["reasons"] == []


V2 = {"ours_v2": {"n": 16, "score": 0.47, "clean": {"n": 15, "score": 0.5}, "backed": {"n": 6, "score": 0.58},
                  "gut": {"n": 10, "score": 0.4}, "causes": {"injury": 1, "role": 2, "td": 3, "read": 3}},
      "fantasypros_v2": {"n": 16, "score": 0.53, "clean": {"n": 15, "score": 0.5}}}
CALLS_V2 = [{"name": "Chase Brown", "pos": "RB", "team": "CIN", "call": "START", "score": 1, "cause": "hit",
             "backed": True, "finish": 14},
            {"name": "Tee Higgins", "pos": "WR", "team": "CIN", "call": "START", "score": 0, "cause": "injury",
             "cause_note": "did not play", "backed": False, "finish": None}]


def test_v2_record_and_review_come_through_once_a_v2_week_is_graded():
    """From week 4 (METHODOLOGY 12.64): the clean, backed/gut and causes split, and last week's takes
    with their causes, David's 'let's learn from it'. None before a v2 week is graded."""
    calls, pl, grade = load_startsit()
    assert _block()["record"]["v2"] is None and _block()["review"] is None
    g = json.loads(json.dumps(grade))
    g["week"] = 4
    g["startsit_record"].update(V2)
    g.setdefault("startsit", {})["ours_v2"] = {"calls": CALLS_V2}
    b = live_startsit(calls, pl, g, slugify)
    contract.validate("LIVE_STARTSIT", b)
    v2 = b["record"]["v2"]
    assert v2["ours"]["clean"] == {"n": 15, "score": 0.5} and v2["ours"]["causes"]["injury"] == 1
    assert (v2["ours"]["backed"]["n"], v2["ours"]["gut"]["n"]) == (6, 10)
    assert v2["fp"]["clean"]["score"] == 0.5
    assert b["review"]["week"] == 4
    assert [(r["n"], r["call"], r["cause"]) for r in b["review"]["rows"]] == [
        ("Chase Brown", "start", "hit"), ("Tee Higgins", "start", "injury")]


def test_no_calls_file_is_no_block():
    assert live_startsit(None, None, None, slugify) is None
    contract.validate("LIVE_STARTSIT", None)


def test_no_graded_week_is_no_record():
    calls, pl, _ = load_startsit()
    assert live_startsit(calls, pl, None, slugify)["record"] is None


# ---- Amendment 2 (ff-jarvis METHODOLOGY 12.64, 2026-09-29): tiers, the pause rule, splits, review ----

def test_every_take_carries_its_tier_and_an_older_producer_null():
    assert [(r["n"], r["tier"]) for r in _block()["calls"]] == [
        ("Brock Purdy", "solid"), ("Chase Brown", "lean"), ("Tee Higgins", "lean"), ("Amon-Ra St. Brown", "solid")]
    calls, pl, grade = load_startsit()
    old = json.loads(json.dumps(calls))
    for d in old["positions"].values():
        for r in d["start"] + d["sit"]:
            r.pop("tier", None)
    assert {r["tier"] for r in live_startsit(old, pl, grade, slugify)["calls"]} == {None}


def test_a_paused_types_rows_leave_the_takes_for_shadow():
    """The fixture pauses START-TE (Kraft): graded, never shown as a take. The line's numbers are the
    ones that paused it (the history entry), since the type's own n restarts with its shadow window."""
    b = _block()
    assert "Tucker Kraft" not in [r["n"] for r in b["calls"]]
    assert [(r["n"], r["tag"], r["pos"], r["tier"]) for r in b["shadow"]] == [("Tucker Kraft", "start", "TE", "strong")]
    assert b["rule"] == {"min_n": 40, "paused": [{"type": "START-TE", "tag": "start", "pos": "TE", "n": 42,
                                                  "ours": 0.214, "fp": 0.786, "since": 3}]}


def test_a_producer_before_the_rule_has_no_rule_and_no_shadow():
    calls, pl, grade = load_startsit()
    old = json.loads(json.dumps(calls))
    old.pop("v2")
    for d in old["positions"].values():
        for r in d["start"] + d["sit"]:
            r.pop("paused", None)
    b = live_startsit(old, pl, grade, slugify)
    contract.validate("LIVE_STARTSIT", b)
    assert b["rule"] is None and b["shadow"] == [] and "Tucker Kraft" in [r["n"] for r in b["calls"]]


def test_splits_before_v2_are_v1s_weeks_1_to_3_on_every_take():
    """ff-jarvis's real reference numbers (2026-09-29): START 0.241 on 29, SIT 0.621 on 19; a wider rank
    gap did not score better (lean 0.367, solid 0.386, strong 0.350). FantasyPros is 1 minus ours."""
    s = _block()["record"]["splits"]
    assert s["set"] == "v1"
    assert s["by_call"] == [{"k": "START", "n": 29, "ours": 0.241, "fp": 0.759},
                            {"k": "SIT", "n": 19, "ours": 0.621, "fp": 0.379}]
    assert [(c["k"], c["n"], c["ours"]) for c in s["by_tier"]] == [
        ("lean", 17, 0.367), ("solid", 19, 0.386), ("strong", 12, 0.35)]
    assert [c["k"] for c in s["by_pos"]] == ["QB", "RB", "WR", "TE"]
    assert s["by_pos"][3] == {"k": "TE", "n": 14, "ours": 0.44, "fp": 0.56}     # all, not clean (13)


def test_splits_after_a_v2_week_are_v2s_clean_set():
    calls, pl, grade = load_startsit()
    g = json.loads(json.dumps(grade))
    g["week"] = 4
    g["startsit_record"].update(V2)
    g["startsit_record"]["splits"]["v2"]["by_call"]["START"] = {"all": {"n": 10, "ours": 0.4, "fp": 0.6},
                                                               "clean": {"n": 9, "ours": 0.444, "fp": 0.556}}
    s = live_startsit(calls, pl, g, slugify)["record"]["splits"]
    assert s["set"] == "v2" and s["by_call"][0] == {"k": "START", "n": 9, "ours": 0.444, "fp": 0.556}
    assert s["by_call"][1] == {"k": "SIT", "n": 0, "ours": None, "fp": None}


REVIEW = pathlib.Path(__file__).parent / "fixtures" / "data" / "startsit_review.json"


def _v2_grade():
    calls, pl, grade = load_startsit()
    g = json.loads(json.dumps(grade))
    g["week"] = 4
    g["startsit_record"].update(V2)
    g.setdefault("startsit", {})["ours_v2"] = {"calls": CALLS_V2}
    return calls, pl, g


def test_claudes_read_rides_under_the_graded_week_it_reviews():
    calls, pl, g = _v2_grade()
    doc = json.loads(REVIEW.read_text(encoding="utf-8"))
    b = live_startsit(calls, pl, g, slugify, doc)
    contract.validate("LIVE_STARTSIT", b)
    read = b["review"]["read"]
    assert read["note"].startswith("Week 4 split down the middle") and len(read["patterns"]) == 2
    assert read["watch"][0] == {"type": "START-WR", "tag": "start", "pos": "WR", "text": doc["watch"][0]["text"],
                                "status": "active", "n": 3, "ours": 0.167, "fp": 0.833}


def test_claudes_read_of_another_week_or_none_is_dropped():
    calls, pl, g = _v2_grade()
    doc = json.loads(REVIEW.read_text(encoding="utf-8"))
    assert live_startsit(calls, pl, g, slugify, None)["review"]["read"] is None
    assert live_startsit(calls, pl, g, slugify, {**doc, "week": 3})["review"]["read"] is None
    # before a v2 week is graded there is no review at all, so no read either
    assert live_startsit(*load_startsit(), slugify, doc)["review"] is None


def test_the_review_is_read_feed_first_then_the_file(tmp_path, monkeypatch):
    import sources
    assert sources.load_startsit_review()["week"] == 4                       # the fixture file
    feed = tmp_path / "feed.json"
    feed.write_text(json.dumps({"startsit_review": {"data": {"week": 5, "note": "from the feed"}}}), encoding="utf-8")
    monkeypatch.setattr(sources, "FEED", feed)
    assert sources.load_startsit_review() == {"week": 5, "note": "from the feed"}


# ---- The page, rendered from the fixture build ----

def open_takes(browser, page_file, w=360, h=800, js=""):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", has_touch=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + "#matchups")
    pg.wait_for_function("document.querySelector('.mu') !== null")
    if js:
        pg.evaluate("() => {" + js + "; render(); }")
    return ctx, pg


@pytest.fixture
def page(browser, page_file):
    ctx, pg = open_takes(browser, page_file)
    yield pg
    ctx.close()


def list_rows(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('.mu-list [data-mukey^="c:"]')].map(r => [
        r.querySelector('.mu-nm b').textContent, (r.querySelector('.mu-cf') || {}).textContent || null])""")


@pytest.mark.render
def test_each_take_shows_its_tier_under_the_ranks_and_the_row_stays_52px(page):
    assert list_rows(page)[:4] == [["Brock Purdy", "SOLID"], ["Chase Brown", "LEAN"], ["Tee Higgins", "LEAN"],
                                   ["Amon-Ra St. Brown", "SOLID"]]
    # 52px before the chip too (measured 2026-09-29): 4 takes, the shadow take under its line, 2 Pitcher List
    assert page.evaluate("[...document.querySelectorAll('.mu-list .mu-call-h')].map(e => e.offsetHeight)") == [52] * 7
    assert page.evaluate("[...document.querySelectorAll('.mu-rk .mu-cf')].length") == 5


@pytest.mark.render
def test_a_paused_type_is_one_line_and_a_tap_shows_its_shadow_takes(page):
    assert "Tucker Kraft" not in [n for n, _ in list_rows(page)]
    line = page.locator(".mu-ps-h").first
    assert line.inner_text().replace("\n", " ").startswith(
        "Paused: our START TE takes, 0.21 vs FantasyPros 0.79 on 42")
    assert page.locator(".mu-ps-b").first.evaluate("e => e.inert") is True
    line.click()
    assert page.locator(".mu-ps[data-open] [data-mukey='s:tucker-kraft'] .mu-cf").inner_text() == "STRONG"
    assert line.get_attribute("aria-expanded") == "true"
    line.click()
    assert page.locator(".mu-ps[data-open]").count() == 0


@pytest.mark.render
def test_the_splits_open_in_place_under_the_record(page):
    assert page.locator(".mu-sp[data-open]").count() == 0
    page.click("[data-musplits]")
    rows = page.evaluate("""() => [...document.querySelectorAll('.mu-spt tbody tr:not(.mu-spg)')].map(r =>
        [...r.children].map(c => c.textContent.trim() + (c.classList.contains('mu-lead') ? '*' : '')))""")
    assert rows[:2] == [["START", "0.24", "0.76*", "29"], ["SIT", "0.62*", "0.38", "19"]]
    assert [r[0] for r in rows] == ["START", "SIT", "QB", "RB", "WR", "TE", "LEAN", "SOLID", "STRONG"]
    assert rows[8] == ["STRONG", "0.35", "0.65*", "12"]
    assert page.inner_text(".mu-spt caption") == "Ours vs FantasyPros, wk 1–3"


@pytest.mark.render
def test_takes_print_no_method_rule_or_version_notes(page):
    """Show, don't tell (2026-09-30): the record, the takes and their reasons; no how-it-works prose."""
    page.click("[data-musplits]")
    page.evaluate("() => document.querySelectorAll('.mu-call').forEach(r => muSetOpen(r, true))")
    text = page.inner_text("#view")
    for gone in ("A take is where", "Not backtested", "scores 1 for the right call", "v2 starts", "v1",
                 "paused after", "None can pause", "Still tracked", "half-PPR", "full-PPR", "rank gap alone", "not advice"):
        assert gone not in text, gone
    assert page.locator(".mu-foot, .mu-rule, .mu-rec-sub").count() == 0


V2_JS = """Object.assign(LIVE_STARTSIT.record, {weeks: [1, 2, 3, 4], through: 4, v2: {
  ours: {n: 16, score: .47, clean: {n: 15, score: .5}, backed: {n: 6, score: .58}, gut: {n: 10, score: .4},
         causes: {injury: 1, role: 2, td: 3, read: 3}}, fp: {n: 16, score: .53, clean: {n: 15, score: .5}}}});
  LIVE_STARTSIT.review = {week: 4, read: null, rows: [
    {n: 'Chase Brown', slug: 'chase-brown', pos: 'RB', team: 'CIN', call: 'start', score: 1, cause: 'hit', note: null, backed: true, finish: 14}]}"""
READ_JS = """; LIVE_STARTSIT.review.read = {model: 'opus', note: 'Week 4 split down the middle.',
  patterns: ['3 of 9 misses came on touchdowns'], watch: [
  {type: 'START-WR', tag: 'start', pos: 'WR', text: '2 of 3 missed on read', status: 'paused', n: 3, ours: .167, fp: .833}]}"""


@pytest.mark.render
def test_claudes_read_heads_the_graded_week_and_its_absence_draws_nothing(browser, page_file):
    ctx, pg = open_takes(browser, page_file, js=V2_JS)
    try:
        assert pg.locator(".mu-review").count() == 1 and pg.locator(".mu-read").count() == 0
    finally:
        ctx.close()
    ctx, pg = open_takes(browser, page_file, js=V2_JS + READ_JS)
    try:
        assert pg.inner_text(".mu-read-l").lower() == "claude's read of week 4"
        assert pg.inner_text(".mu-read-n") == "Week 4 split down the middle."
        assert pg.inner_text(".mu-read-p li") == "3 of 9 misses came on touchdowns"
        assert pg.inner_text(".mu-read-t") == "START WR · paused"
        assert pg.inner_text(".mu-read-w em") == "0.17 vs FantasyPros 0.83 · 3 takes"
        # the read comes before the week's takes
        assert pg.evaluate("document.querySelector('.mu-read').compareDocumentPosition(document.querySelector('.mu-rvs')) & 4") == 4
    finally:
        ctx.close()


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360_with_everything_open(browser, page_file):
    ctx, pg = open_takes(browser, page_file, js=V2_JS + READ_JS)
    try:
        pg.click("[data-musplits]")
        pg.click(".mu-ps-h")
        pg.click("[data-mukey='s:tucker-kraft'] .mu-call-h")
        assert pg.evaluate("document.documentElement.scrollWidth") <= 360
    finally:
        ctx.close()
