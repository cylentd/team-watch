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
from test_render import MU_GRADED, SEED, browser  # noqa: E402,F401  (browser is a fixture)


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


def test_weeks_1_to_3_show_no_record():
    """The record restarts at week 4 (David, 2026-09-30). The fixture is ff-jarvis's real weeks 1-3
    record (2026-09-29), so the strip says no week is graded yet."""
    assert _block()["record"] is None


def test_the_record_counts_from_week_4_with_pitcher_list_over_the_same_weeks():
    calls, pl, g = _v2_grade()
    g["startsit_record"]["weeks"] = [1, 2, 3, 4]
    g["startsit_record"]["pitcherlist_v2"] = {"n": 6, "score": 0.5, "score_no_dnp": 0.5}
    rec = live_startsit(calls, pl, g, slugify)["record"]
    assert (rec["through"], rec["weeks"]) == (4, [4])
    assert rec["pl"] == {"n": 6, "score": 0.5, "score_no_dnp": 0.5}
    # a grade file from before ff-jarvis split Pitcher List by week draws no Pitcher List bar
    g["startsit_record"].pop("pitcherlist_v2")
    assert live_startsit(calls, pl, g, slugify)["record"]["pl"] is None


def test_a_grade_file_from_before_fantasypros_and_the_splits_reads_null():
    calls, pl, g = _v2_grade()
    for k in ("fantasypros", "splits"):
        g["startsit_record"].pop(k)
    rec = live_startsit(calls, pl, g, slugify)["record"]
    assert rec["fp"] is None and rec["splits"] is None


def test_fantasypros_side_comes_through_when_graded():
    """FantasyPros on our takes (2026-09-29): the other call on each, so its n is ours."""
    calls, pl, g = _v2_grade()
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
    assert _block()["record"] is None and _block()["review"] is None
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


def test_splits_are_v2s_clean_set():
    calls, pl, g = _v2_grade()
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
        r.querySelector('.mu-nm b').textContent, r.querySelector('.mu-tag').textContent])""")


@pytest.mark.render
def test_each_take_leads_with_start_or_sit_and_the_row_stays_52px(page):
    # START / SIT replaced the STRONG / SOLID / LEAN chip on 2026-10-03; no tier word is left on a row
    assert list_rows(page)[:4] == [["Brock Purdy", "START"], ["Chase Brown", "START"], ["Tee Higgins", "START"],
                                   ["Amon-Ra St. Brown", "SIT"]]
    assert page.evaluate("[...document.querySelectorAll('.mu-list .mu-call:not([data-mukey^=\"t:\"]) .mu-call-h')].map(e => e.offsetHeight)") == [52] * 7
    assert page.evaluate("document.querySelector('.mu-list').textContent.match(/STRONG|SOLID|LEAN/)") is None


@pytest.mark.render
def test_most_confident_leads_with_the_widest_backed_gaps(page):
    # 2026-10-03, David: "most confident picks": backed, graded takes, widest gap first, at most 3
    page.evaluate("""() => { LIVE_STARTSIT.calls.forEach((r, i) => { r.backed = true; r.graded = true; r.gap = i; });
      LIVE_STARTSIT.calls[0].backed = false; LIVE_STARTSIT.calls[0].gap = 99;
      if (LIVE_STARTSIT.calls[1]) LIVE_STARTSIT.calls[1].graded = false; render(); }""")
    want = page.evaluate("""() => LIVE_STARTSIT.calls.filter(r => r.backed && r.graded).sort((a, b) => b.gap - a.gap).slice(0, 3).map(r => r.n)""")
    got = page.evaluate("[...document.querySelectorAll('.mu-list [data-mukey^=\"t:\"] .mu-nm b')].map(e => e.textContent)")
    assert got == want and 1 <= len(got) <= 3
    assert page.inner_text(".mu-top") == "MOST CONFIDENT" or page.inner_text(".mu-top").lower() == "most confident"
    page.evaluate("() => { LIVE_STARTSIT.calls.forEach(r => { r.backed = false; }); render(); }")
    assert page.locator(".mu-top").count() == 0                       # no backed take: no section


@pytest.mark.render
def test_takes_shown_but_not_graded_follow_their_own_line(page):
    # Amendment 3 (2026-10-03): week 4's rank-5+ takes are shown, not counted in the record
    page.set_viewport_size({"width": 360, "height": 800})
    page.evaluate("() => { LIVE_STARTSIT.calls[0].graded = false; render(); }")
    order = page.evaluate("""() => [...document.querySelector('.mu-list').children].filter(e => !(e.dataset.mukey || '').startsWith('t:')).map(e =>
        e.classList.contains('mu-more') ? 'MORE' : e.querySelector && e.querySelector('.mu-nm b') ? e.querySelector('.mu-nm b').textContent : null).filter(Boolean)""")
    assert order[:4] == ["Chase Brown", "Tee Higgins", "MORE", "Brock Purdy"]   # Purdy, the first START, moves under the line
    assert page.locator(".mu-more").count() == 1 and page.inner_text(".mu-more") == "More takes · not in the record"
    assert page.evaluate("[...document.querySelectorAll('.mu-list .mu-call:not([data-mukey^=\"t:\"]) .mu-call-h')].map(e => e.offsetHeight)") == [52] * 7


@pytest.mark.render
def test_a_paused_type_is_one_line_and_a_tap_shows_its_shadow_takes(page):
    assert "Tucker Kraft" not in [n for n, _ in list_rows(page)]
    line = page.locator(".mu-ps-h").first
    assert line.inner_text().replace("\n", " ").startswith(
        "Paused: our START TE takes, 0.21 vs FantasyPros 0.79 on 42")
    assert page.locator(".mu-ps-b").first.evaluate("e => e.inert") is True
    line.click()
    assert page.locator(".mu-ps[data-open] [data-mukey='s:tucker-kraft'] .mu-tag").inner_text() == "START"
    assert line.get_attribute("aria-expanded") == "true"
    line.click()
    assert page.locator(".mu-ps[data-open]").count() == 0


@pytest.fixture
def graded(browser, page_file):
    ctx, pg = open_takes(browser, page_file, js=MU_GRADED)
    yield pg
    ctx.close()


@pytest.mark.render
def test_the_page_says_no_week_is_graded_before_week_4(page):
    assert page.inner_text(".mu-rec.none .mu-rec-none") == "No week graded yet."


@pytest.mark.render
def test_the_splits_open_in_place_under_the_record(graded):
    page = graded
    assert page.locator(".mu-sp[data-open]").count() == 0
    page.click("[data-musplits]")
    rows = page.evaluate("""() => [...document.querySelectorAll('.mu-spt tbody tr:not(.mu-spg)')].map(r =>
        [...r.children].map(c => c.textContent.trim() + (c.classList.contains('mu-lead') ? '*' : '')))""")
    assert rows[:2] == [["START", "0.24", "0.76*", "29"], ["SIT", "0.62*", "0.38", "19"]]
    assert [r[0] for r in rows] == ["START", "SIT", "QB", "RB", "WR", "TE", "Small", "Medium", "Big"]
    assert rows[8] == ["Big","0.35", "0.65*", "12"]
    assert page.inner_text(".mu-spt caption") == "Ours vs FantasyPros, wk 4"


@pytest.mark.render
def test_takes_print_no_method_rule_or_version_notes(graded):
    """Show, don't tell (2026-09-30): the record, the takes and their reasons; no how-it-works prose."""
    page = graded
    page.click("[data-musplits]")
    page.evaluate("() => document.querySelectorAll('.mu-call').forEach(r => muSetOpen(r, true))")
    text = page.inner_text("#view")
    for gone in ("A take is where", "Not backtested", "scores 1 for the right call", "v2 starts", "v1",
                 "paused after", "None can pause", "Still tracked", "half-PPR", "full-PPR", "rank gap alone", "not advice"):
        assert gone not in text, gone
    assert page.locator(".mu-foot, .mu-rule, .mu-rec-sub").count() == 0


V2_JS = MU_GRADED + """ Object.assign(LIVE_STARTSIT.record, {weeks: [4], through: 4, v2: {
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


# ---- Start / Sit (2026-10-03): the picker, the matchup board, the #startsit hash ----
# LIVE_SSB is another unit's block (design/startsit_board.py); these tests fill it through the page, so
# the view is proved on its own. The fixture's LIVE_RANKS holds five players, so a test that needs more
# of one position clones the first (picks_js).

BOARD = {"QB": ("DAL", "NYG"), "RB": ("CIN", "PIT"), "WR": ("DET", "CHI"), "TE": ("KC", "LV")}
CLEAR_SSB = """
      if (typeof LIVE_SSB === 'object' && LIVE_SSB) { for (const k of Object.keys(LIVE_SSB)) delete LIVE_SSB[k]; }"""


def _board():
    def row(team, opp, pts, rank):
        return {"team": team, "opp": opp, "pts": pts, "rank": rank}
    return {pos: {"avg": 18.9, "n": 3,
                  "best": [row(t, o, 26.1, 32), row("SF", "MIA", 24.0, 31), row("KC", "LV", 23.2, 30), row("BUF", "NE", 22.5, 29)],
                  "worst": [row("NYG", "SF", 12.4, 1), row("LV", "BUF", 13.0, 2), row("PIT", "CIN", 13.8, 3), row("CHI", "DET", 14.2, 4)]}
            for pos, (t, o) in BOARD.items()}


def picks_js(*pts, pos="QB"):
    """Pick len(pts) LIVE_RANKS players at `pos` with exactly these projections, cloning when short."""
    return f"""
      const rows = LIVE_RANKS.rows.filter(r => r.pos === '{pos}');
      while (rows.length < {len(pts)}) {{
        const c = Object.assign({{}}, rows[0], {{slug: 'test-{pos.lower()}-' + rows.length, n: 'Test Player ' + rows.length}});
        LIVE_RANKS.rows.push(c); rows.push(c);
      }}
      {json.dumps(list(pts))}.forEach((p, i) => {{
        rows[i].pts = p;
        LIVE_PROJECTIONS.players[rows[i].slug] = Object.assign(LIVE_PROJECTIONS.players[rows[i].slug] || {{}}, {{pts: p}});
      }});
      SS_PICKS = rows.slice(0, {len(pts)}).map(r => r.slug); SS_OPEN = false; SS_Q = ''; SS_BTAB = '';"""


def ssb_js():
    """Fill LIVE_SSB for the picks: the board, FantasyPros ranks, a teammate out for the first pick."""
    return """
      const pos = LIVE_RANKS.rows.find(r => r.slug === SS_PICKS[0]).pos;
      const stub = {week: LIVE_RANKS.week, board: %s,
        fp: {[SS_PICKS[0]]: {ecr: 14, pos}, [SS_PICKS[1]]: {ecr: 21, pos}},
        out: {[SS_PICKS[0]]: [{n: 'Jalen Coker', pos: 'WR', s: 'Out'}]}};
      if (typeof LIVE_SSB === 'object' && LIVE_SSB) { for (const k of Object.keys(LIVE_SSB)) delete LIVE_SSB[k]; Object.assign(LIVE_SSB, stub); }
      else window.LIVE_SSB = stub;""" % json.dumps(_board())


def open_view(browser, page_file, js="", w=360, h=800, hash_="#matchups"):
    ctx = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", has_touch=True)
    pg = ctx.new_page()
    pg.set_default_timeout(5000)
    pg.route(re.compile(r"^https?://"), lambda route: route.abort())
    pg.add_init_script(SEED)
    pg.goto(page_file.as_uri() + hash_)
    pg.wait_for_function("document.querySelector('.mu') !== null")
    if js:
        pg.evaluate("() => {" + js + "; render(); }")
    return ctx, pg


@pytest.fixture
def ss(browser, page_file):
    made = []

    def go(js="", **kw):
        ctx, pg = open_view(browser, page_file, js, **kw)
        made.append(ctx)
        return pg
    yield go
    for c in made:
        c.close()


def verdict(pg):
    return pg.evaluate("""() => { const v = document.querySelector('.ssv-verdict'); return v && {
        tag: v.querySelector('.mu-tag') && v.querySelector('.mu-tag').textContent,
        name: v.querySelector('b') && v.querySelector('b').textContent,
        gain: v.querySelector('.ssv-gain') && v.querySelector('.ssv-gain').textContent,
        flip: v.querySelector('.ssv-coin') && v.querySelector('.ssv-coin').textContent}; }""")


@pytest.mark.render
def test_the_higher_projection_starts_and_names_the_margin(ss):
    pg = ss(picks_js(12.0, 9.0))
    top = pg.evaluate("shortName(ssCols()[0].p.n)")
    assert verdict(pg) == {"tag": "START", "name": top, "gain": "+3.0", "flip": None}
    assert pg.locator(".ssv-who").count() == 2


@pytest.mark.render
def test_inside_half_a_point_is_a_coin_flip_with_no_start(ss):
    for pts in [(10.0, 9.6), (10.5, 10.0)]:                      # 0.4 and exactly 0.5
        pg = ss(picks_js(*pts))
        assert verdict(pg) == {"tag": None, "name": None, "gain": None, "flip": "Coin flip"}
        assert pg.locator(".ssv-verdict .mu-tag").count() == 0
    # a tenth past the line starts someone, whichever order the two were picked in
    pg = ss(picks_js(9.0, 9.6))
    v = verdict(pg)
    assert v["tag"] == "START" and v["gain"] == "+0.6"
    assert v["name"] == pg.evaluate("shortName(ssCols()[1].p.n)")


@pytest.mark.render
def test_the_verdict_judges_the_margin_as_shown_to_one_decimal(ss):
    """0.54 shows as 0.5, which is a coin flip (never a START at "+0.5"); 0.56 shows as 0.6, a START."""
    pg = ss(picks_js(10.0, 9.46))
    assert verdict(pg)["flip"] == "Coin flip" and pg.locator(".ssv-verdict .mu-tag").count() == 0
    pg = ss(picks_js(10.0, 9.44))
    assert verdict(pg)["tag"] == "START" and verdict(pg)["gain"] == "+0.6"
    pg = ss(picks_js(9.0, 9.56))
    v = verdict(pg)
    assert v["tag"] == "START" and v["gain"] == "+0.6"


@pytest.mark.render
def test_focus_lands_on_the_search_box_then_back_on_a_control(ss):
    pg = ss(ROSTER_JS % (17.0, 17.0))
    pg.click("[data-ssadd]")
    assert pg.evaluate("document.activeElement.id") == "ssv-q"
    pg.keyboard.press("Escape")
    assert pg.evaluate("document.activeElement.hasAttribute('data-ssadd')")
    # the third pick removes the Add button, so the first Remove takes focus (never the page body)
    pg.click("[data-ssadd]")
    pg.fill("#ssv-q", "Gibbs")
    pg.locator(".ssv-opt").first.click()
    assert pg.locator("[data-ssadd]").count() == 0
    assert pg.evaluate("document.activeElement.classList.contains('ssv-x')")


@pytest.mark.render
def test_one_player_or_none_is_a_prompt_not_a_verdict(ss):
    pg = ss(picks_js(11.0))
    assert pg.locator(".ssv-verdict").count() == 0
    assert pg.inner_text(".ssv-prompt") == "Add one more to see who starts."
    pg = ss("SS_PICKS = [];")
    assert pg.inner_text(".ssv-prompt") == "Pick two players to see who starts."
    assert pg.locator(".ssv-who, .ssv-row").count() == 0
    assert pg.locator("[data-ssadd]").count() == 1


@pytest.mark.render
def test_the_wr_note_rides_on_the_defense_row_only_when_a_wr_is_picked(ss):
    pg = ss(picks_js(12.0, 9.0, pos="WR"))
    row = pg.locator(".ssv-row", has=pg.locator(".ssv-lbl", has_text="Defense vs WR"))
    assert row.locator(".ssv-lbl em").inner_text() == "matters little for WRs"
    # a mixed pair names no one position, and still says it for the receiver
    pg = ss(picks_js(12.0, 9.0) + "; SS_PICKS[1] = 'amonra-st-brown'")
    assert pg.locator(".ssv-lbl span", has_text="Defense").text_content() == "Defense"
    assert pg.locator(".ssv-lbl em").inner_text() == "matters little for WRs"
    for pos in ("QB", "RB"):
        pg = ss(picks_js(12.0, 9.0, pos=pos))
        assert pg.locator(".ssv-lbl", has_text=f"Defense vs {pos}").count() == 1
        assert pg.locator(".ssv-lbl em").count() == 0


@pytest.mark.render
def test_rows_read_the_blocks_and_drop_when_nobody_has_data(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + """
      LIVE_PROJECTIONS.players[SS_PICKS[0]].wx = {adj: -1.06, cond: ['wind', 'precip']};
      LIVE_PROJECTIONS.players[SS_PICKS[1]].wx = null;""")
    rows = pg.evaluate("""() => Object.fromEntries([...document.querySelectorAll('.ssv-row')].map(r =>
        [r.querySelector('.ssv-lbl span').textContent, [...r.querySelectorAll('.ssv-v')].map(v => v.textContent)]))""")
    assert list(rows) == ["Projected", "Rank", "Defense vs QB", "FantasyPros", "Teammate out", "Weather"]
    assert rows["Projected"] == ["12.0", "9.0"]
    assert rows["FantasyPros"] == ["QB14", "QB21"]
    assert rows["Teammate out"] == ["J. CokerWR · Out", "—"]
    assert rows["Weather"] == ["−1.1wind · rain", "—"]
    # with no block and no weather, FantasyPros, Teammate out and Weather are not drawn
    pg = ss(picks_js(12.0, 9.0) + CLEAR_SSB + "; for (const s of SS_PICKS) LIVE_PROJECTIONS.players[s].wx = null;")
    assert pg.evaluate("[...document.querySelectorAll('.ssv-lbl span')].map(e => e.textContent)") == [
        "Projected", "Rank", "Defense vs QB"]


@pytest.mark.render
def test_the_defense_row_says_softest_or_toughest_with_the_opponent(ss):
    pg = ss(picks_js(12.0, 9.0))
    cells = pg.evaluate("""() => [...[...document.querySelectorAll('.ssv-row')].find(r => r.textContent.startsWith('Defense'))
        .querySelectorAll('.ssv-v')].map(v => v.textContent)""")
    assert len(cells) == 2
    for c in cells:
        assert re.search(r"(softest|toughest)(vs|@) [A-Z]+$", c) or re.match(r"—(vs|@) [A-Z]+$", c), c


@pytest.mark.render
def test_the_board_tabs_switch_position_in_place(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js())
    assert pg.evaluate("[...document.querySelectorAll('[data-ssbpos]')].map(b => b.textContent)") == ["QB", "RB", "WR", "TE"]
    assert pg.locator(".ssv-board h3").text_content().startswith("QB matchups")          # opens on the first pick's position
    assert pg.locator("[data-ssbpos='QB']").get_attribute("aria-pressed") == "true"
    first = lambda: pg.evaluate("""() => [...document.querySelectorAll('.ssv-bl')].map(l =>
        [l.querySelector('h4').firstChild.textContent, l.querySelectorAll('.ssv-br').length, l.querySelector('.ssv-bt').textContent,
         l.querySelector('.ssv-bo').textContent, l.querySelector('em').textContent])""")
    assert first() == [["Best matchups", 4, "DAL", "vs NYG", "26.1"], ["Worst matchups", 4, "NYG", "vs SF", "12.4"]]
    pg.evaluate("window.__takes = document.querySelector('.mu-list')")
    pg.click("[data-ssbpos='RB']")
    assert pg.locator(".ssv-board h3").text_content().startswith("RB matchups")
    assert pg.locator("[data-ssbpos='RB']").get_attribute("aria-pressed") == "true"
    assert first()[0][2:4] == ["CIN", "vs PIT"]
    assert pg.evaluate("window.__takes === document.querySelector('.mu-list')")   # the Takes were not redrawn
    assert pg.inner_text(".ssv-key").strip() == "League average 18.9"


SPOT_JS = """; LIVE_STARTSIT.best = [{n: 'Stefon Diggs', slug: 'stefon-diggs', pos: 'WR', team: 'WAS', opp: 'IND', home: true,
    pts: 9.6, why: ['24% target share']}];
  LIVE_SSB.out['stefon-diggs'] = [{n: 'Terry McLaurin', pos: 'WR', s: 'Out'}]; SS_BTAB = 'WR'"""


@pytest.mark.render
def test_the_board_names_the_best_spot_with_its_teammate_out(ss):
    # The Digest's Matchups card, back on Start / Sit (2026-10-03, David: "Diggs is a good start because Terry is out")
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + SPOT_JS)
    spot = pg.locator(".ssv-board .ssv-spot")
    assert spot.locator(".mu-nm b").text_content() == "S. Diggs"
    meta = spot.locator(".mu-nm span").text_content()
    assert "24% target share" in meta and "T. McLaurin Out" in meta
    assert spot.locator("em").text_content() == "9.6"
    pg.click("[data-ssbpos='QB']")                                   # no best spot at QB: no row
    assert pg.locator(".ssv-spot").count() == 0
    assert pg.evaluate("document.documentElement.scrollWidth <= innerWidth")


@pytest.mark.render
def test_a_board_row_has_a_bar_against_the_league_average(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js())
    got = pg.evaluate("""() => { const b = document.querySelector('.ssv-bar'), r = b.getBoundingClientRect();
      const tick = getComputedStyle(b, '::after');
      return {fill: b.querySelector('i').getBoundingClientRect().width / r.width, avg: parseFloat(tick.left) / r.width}; }""")
    assert got["fill"] == pytest.approx(1.0, abs=0.01)          # the largest value fills its bar
    assert got["avg"] == pytest.approx(18.9 / 26.1, abs=0.01)   # the tick is the average on the same scale


@pytest.mark.render
def test_a_missing_block_draws_no_board_and_no_error(ss):
    pg = ss(picks_js(12.0, 9.0) + CLEAR_SSB)
    assert pg.locator(".ssv-board").count() == 0 and pg.locator(".ssv-pick").count() == 1
    pg = ss(picks_js(12.0, 9.0) + ssb_js() + "; LIVE_SSB.board.TE = null; LIVE_SSB.board.QB = {avg: 'x'};")
    assert pg.evaluate("[...document.querySelectorAll('[data-ssbpos]')].map(b => b.textContent)") == ["RB", "WR"]
    assert pg.locator(".ssv-board h3").text_content().startswith("RB matchups")          # the first pick's tab is gone


@pytest.mark.render
def test_startsit_hash_opens_the_view_under_its_new_name(ss):
    pg = ss(hash_="#startsit")
    assert pg.locator(".ssv-pick").count() == 1 and pg.locator(".mu-rec").count() == 1
    assert pg.evaluate("SURFACE") == "matchups"
    assert pg.inner_text(".mode-sub[aria-pressed='true']") == "Start/Sit"
    for old in ("#takes", "#matchups"):                                  # the old names still land
        assert ss(hash_=old).evaluate("SURFACE") == "matchups"


ROSTER_JS = """
      TEAMS.yahoo.roster = [P('Joe Burrow', 'QB', 'CIN', 'joe-burrow', {slot: 'QB', start: 1}),
        P('Chase Brown', 'RB', 'CIN', 'chase-brown', {slot: 'RB1', start: 1}),
        P('Brock Purdy', 'QB', 'SF', 'brock-purdy', {slot: 'BN'}), P('Test Back', 'RB', 'CIN', 'test-back', {slot: 'BN'})];
      LIVE_RANKS.rows.push({slug: 'test-back', n: 'Test Back', pos: 'RB', team: 'CIN', opp: 'NYJ', home: false, pts: %s, rank: 2});
      LIVE_PROJECTIONS.players['test-back'] = {pts: %s};
      SS_PICKS = null; try { localStorage.removeItem('tw-ss-picks'); } catch (e) {}"""


@pytest.mark.render
def test_it_opens_on_the_closest_call_the_roster_brief_names(ss):
    # the bench RB out-projects his starter by 0.8: that swap, bench player first, beats Purdy's 1.3 deficit
    pg = ss(ROSTER_JS % (17.0, 17.0))
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["test-back", "chase-brown"]
    # nobody on the bench gains on a starter: the smallest gap is the pair, bench first
    pg = ss(ROSTER_JS % (9.0, 9.0))
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["brock-purdy", "joe-burrow"]
    assert verdict(pg)["name"] == "J. Burrow"
    # a reader who kept picks gets them back, and one who cleared them keeps an empty card
    pg = ss(ROSTER_JS % (9.0, 9.0) + "; SS_PICKS = null; localStorage.setItem('tw-ss-picks', JSON.stringify({week: schedWeek(), picks: []}))")
    assert pg.locator(".ssv-who").count() == 0
    # last week's picks are dropped: the card opens on this week's closest call
    pg = ss(ROSTER_JS % (9.0, 9.0) + "; SS_PICKS = null; localStorage.setItem('tw-ss-picks', JSON.stringify({week: schedWeek() - 1, picks: []}))")
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["brock-purdy", "joe-burrow"]


@pytest.mark.render
def test_the_picker_and_board_lead_and_the_takes_stay_under_them(ss):
    pg = ss()
    assert pg.evaluate("""() => { const q = s => document.querySelector(s);
      return [!!(q('.ssv').compareDocumentPosition(q('.mu-rec')) & 4), !!(q('.ssv').compareDocumentPosition(q('.mu-cols')) & 4)]; }""") == [True, True]
    assert pg.locator(".mu-list [data-mukey^='c:']").count() >= 4


@pytest.mark.render
def test_add_by_search_and_remove_keep_the_picks(ss):
    pg = ss(ROSTER_JS % (17.0, 17.0))                      # two picks: Test Back and Chase Brown
    pg.click("[data-ssadd]")
    assert pg.locator("#ssv-box").count() == 1 and pg.locator("[data-ssadd]").get_attribute("aria-expanded") == "true"
    # his roster at the first pick's position comes first, and neither pick is offered again
    assert pg.evaluate("[...document.querySelectorAll('.ssv-opt')].map(b => b.dataset.ssslug)") == []
    assert pg.inner_text(".ssv-none") == "Search for a player to add."
    pg.click("[data-ssx='test-back']")                     # one pick left: the other roster RB is offered, list still open
    assert pg.locator(".ssv-cap").text_content() == "Chat Take the Wheel · RB"
    assert pg.evaluate("[...document.querySelectorAll('.ssv-opt')].map(b => b.dataset.ssslug)") == ["test-back"]
    pg.click(".ssv-opt")                                   # a roster tap adds him and closes the list
    assert pg.locator("#ssv-box").count() == 0 and pg.locator(".ssv-who").count() == 2
    pg.click("[data-ssadd]")
    slug = pg.evaluate("searchFind('Gibbs', 8)[0].e.slug")
    pg.fill("#ssv-q", "Gibbs")
    pg.locator(f".ssv-opt[data-ssslug='{slug}']").click()
    assert pg.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)") == ["chase-brown", "test-back", slug]
    assert pg.locator("#ssv-box").count() == 0 and pg.locator("[data-ssadd]").count() == 0   # three is the most
    assert pg.evaluate("JSON.parse(localStorage.getItem('tw-ss-picks')).picks") == ["chase-brown", "test-back", slug]
    pg.click(f"[data-ssx='{slug}']")
    assert pg.locator(".ssv-who").count() == 2 and pg.locator("[data-ssadd]").count() == 1
    assert pg.evaluate("JSON.parse(localStorage.getItem('tw-ss-picks')).picks") == ["chase-brown", "test-back"]
    pg.click("[data-ssadd]")
    pg.keyboard.press("Escape")
    assert pg.locator("#ssv-box").count() == 0


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360_with_three_players_and_every_row(ss):
    pg = ss(picks_js(12.0, 9.0, 8.0) + ssb_js() + """
      LIVE_PROJECTIONS.players[SS_PICKS[0]].wx = {adj: -1.06, cond: ['wind', 'precip']};
      LIVE_SSB.out[SS_PICKS[1]] = [{n: 'Jalen Coker', pos: 'WR', s: 'Out'}, {n: 'Tetairoa McMillan', pos: 'WR', s: 'Doubtful'}];""")
    assert pg.locator(".ssv-who").count() == 3
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360
    pg.click("[data-ssbpos='TE']")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360
    pg.evaluate("SS_PICKS.pop(); SS_OPEN = true; render()")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360


@pytest.mark.render
def test_desktop_puts_the_picker_and_board_side_by_side_on_shared_edges(ss):
    pg = ss(picks_js(12.0, 9.0) + ssb_js(), w=1400, h=900)
    box = pg.evaluate("""() => ['.ssv-pick', '.ssv-board'].map(s => { const r = document.querySelector(s).getBoundingClientRect();
        return [Math.round(r.top), Math.round(r.bottom), Math.round(r.left)]; })""")
    assert box[0][0] == box[1][0] and box[0][1] == box[1][1] and box[0][2] < box[1][2]
    lists = pg.evaluate("[...document.querySelectorAll('.ssv-bl')].map(l => Math.round(l.getBoundingClientRect().left))")
    assert len(set(lists)) == 2                                   # Best and Worst side by side in a half-width card
