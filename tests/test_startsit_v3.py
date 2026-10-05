"""Start/Sit v3 (2026-10-04, METHODOLOGY 12.75): design/startsit_v3.py's cut of ff-jarvis's
`startsit_v3` block, and the view that draws it (SMASH, bold calls, record, last week)."""
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
import sources  # noqa: E402
import startsit_v3  # noqa: E402
from startsit_page import PRISTINE_JS, RESET_JS, open_view  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "data" / "startsit_v3.json"


def _block():
    return startsit_v3.live_ss3(sources.load_startsit_v3(), slugify)


# ---- The cut ----

def test_the_fixture_week_is_whole_and_ordered_as_the_view_draws_it():
    b = _block()
    contract.validate("LIVE_SS3", b)
    assert (b["week"], b["season"], len(b["smash"]), len(b["takes"])) == (6, 2026, 10, 9)
    # SMASH: position order QB, RB, WR, TE, each by rank
    assert [(r["pos"], r["rank"]) for r in b["smash"]] == [("QB", 1), ("QB", 3), ("RB", 1), ("RB", 2), ("RB", 5),
                                                          ("WR", 2), ("WR", 4), ("WR", 5), ("TE", 1), ("TE", 2)]
    # takes: START first, then SIT, each by margin, widest first
    assert [(r["call"], r["margin_spots"]) for r in b["takes"]] == [
        ("START", 9.5), ("START", 8.5), ("START", 7.5), ("START", 6.5),
        ("SIT", 8.5), ("SIT", 7.5), ("SIT", 6.5), ("SIT", 6.5), ("SIT", 6.5)]


def test_a_missing_line_or_price_stays_null_and_a_row_never_loses_a_field():
    kittle = next(r for r in _block()["smash"] if r["slug"] == "george-kittle")
    assert kittle["line"] is None and kittle["td_price"] is None
    allen = next(r for r in _block()["smash"] if r["slug"] == "josh-allen")
    assert allen["line"] == {"stat": "pass_yds", "value": 251.5} and allen["td_price"] == -105


def test_the_record_carries_its_counts_the_weeks_and_the_for_fun_line():
    rec = _block()["record"]
    assert rec["since_week"] == 5
    assert rec["start"] == {"hit": 2, "miss": 2, "void": 1}
    assert rec["fun"]["fantasypros"] == {"hit": 5, "miss": 3}
    assert [w["week"] for w in rec["weeks"]] == [5] and len(rec["last_week"]) == 6


def test_no_block_is_an_empty_week_that_still_meets_the_contract():
    for missing in (None, {}):
        b = startsit_v3.live_ss3(missing, slugify)
        contract.validate("LIVE_SS3", b)
        assert b["week"] is None and b["smash"] == [] and b["takes"] == []
        assert b["record"]["since_week"] == 5 and b["record"]["weeks"] == [] and b["record"]["smash"] == {"hit": 0, "miss": 0, "void": 0}
        assert startsit_v3.report(b).startswith("Start/Sit v3: no startsit_v3 block")


def test_a_reason_in_any_of_its_shapes_reads_as_text():
    """ff-jarvis's v2 reasons are {k, text}; the spec sketch said {kind, text_key}; the page needs text."""
    take = {"name": "A B", "call": "start", "pos": "WR", "margin_spots": 7,
            "reasons": [{"k": "role", "text": "one"}, {"kind": "mx", "text_key": "two"}, {"t": "three"}, {}]}
    got = startsit_v3.live_ss3({"week": 6, "takes": [take, {"name": "No Call", "call": "COIN"}]}, slugify)
    assert [r["t"] for r in got["takes"][0]["reasons"]] == ["one", "two", "three", ""]
    assert got["takes"][0]["slug"] == "a-b" and got["takes"][0]["call"] == "START"
    assert len(got["takes"]) == 1, "a call that is not START or SIT (no coin flips) is dropped"


def test_the_report_names_the_week_and_the_record_state():
    assert startsit_v3.report(_block()) == "Start/Sit v3: week 6, 10 SMASH, 4 START, 5 SIT, record since week 5 (1 weeks graded)"
    ungraded = startsit_v3.live_ss3({"week": 5, "smash": [], "takes": []}, slugify)
    assert startsit_v3.report(ungraded).endswith("no week graded yet (counts from week 5)")


def test_the_block_is_read_feed_first_bare_or_wrapped_then_the_file(tmp_path, monkeypatch):
    assert sources.load_startsit_v3()["week"] == 6                            # the fixture file
    feed = tmp_path / "feed.json"
    monkeypatch.setattr(sources, "FEED", feed)
    feed.write_text(json.dumps({"startsit_v3": {"data": {"week": 7, "smash": []}}}), encoding="utf-8")
    assert sources.load_startsit_v3()["week"] == 7
    feed.write_text(json.dumps({"startsit_v3": {"week": 8, "smash": []}}), encoding="utf-8")
    assert sources.load_startsit_v3()["week"] == 8
    feed.write_text("{}", encoding="utf-8")
    assert sources.load_startsit_v3()["week"] == 6                            # no block in the feed: the file
    monkeypatch.setattr(sources, "DWR", tmp_path)
    assert sources.load_startsit_v3() is None                                 # neither


# ---- The page ----

@pytest.fixture(scope="module")
def shared(browser, page_file):
    """One page for the module: view() resets it, so a test never sees another's changes."""
    errors = []
    ctx, pg = open_view(browser, page_file, errors=errors)
    pg.evaluate(PRISTINE_JS)
    assert errors == []                 # whatever the load or the snapshot raised fails here, not lost to a clear
    yield pg, errors
    ctx.close()


@pytest.fixture
def view(browser, page_file, shared):
    """view(js) resets the shared page and applies js. A hash_ opens a fresh page, because the hash on
    load is what that test proves. Any page error or console error during the test fails it."""
    pg, errors = shared
    left, errors[:] = list(errors), []  # an error raised or left over since the last test fails this one
    assert left == []
    made = []

    def go(js="", w=360, h=800, hash_=None):
        if hash_ is not None:
            ctx, fresh = open_view(browser, page_file, js, w=w, h=h, hash_=hash_, errors=errors)
            made.append(ctx)
            return fresh
        pg.set_viewport_size({"width": w, "height": h})
        pg.evaluate(RESET_JS)
        if js:
            pg.evaluate("() => {" + js + "; render(); }")
        return pg
    yield go
    for c in made:
        c.close()
    assert errors == [], errors


NO_GRADE = ("Object.assign(LIVE_SS3.record, {weeks: [], last_week: [], smash: {hit: 0, miss: 0, void: 0}, start: {hit: 0, miss: 0, void: 0},"
            " sit: {hit: 0, miss: 0, void: 0}, fun: {fantasypros: {hit: 0, miss: 0}, pitcherlist: {hit: 0, miss: 0}}})")


@pytest.mark.render
def test_the_record_is_three_separate_hit_miss_counts_since_week_5(view):
    pg = view()
    assert pg.inner_text(".mu-rec-l").lower() == "record" and pg.inner_text(".mu-rec-s") == "since week 5"
    tiles = pg.evaluate("[...document.querySelectorAll('.mu-rt')].map(t => [t.querySelector('b').textContent, t.querySelector('span').textContent, (t.querySelector('small') || {}).textContent || ''])")
    assert tiles == [["7-3", "SMASH", ""], ["2-2", "START", "1 void"], ["4-1", "SIT", ""]]     # void only when above zero
    assert pg.inner_text(".mu-fun") == "For fun: FantasyPros 5-3 · Pitcher List 3-2"


@pytest.mark.render
def test_before_any_graded_week_the_record_is_calm_not_zeros(view):
    pg = view(NO_GRADE)
    assert pg.inner_text(".mu-rec.none .mu-rec-none") == "No week graded yet."
    assert pg.locator(".mu-rt").count() == 0 and pg.locator(".mu-fun").count() == 0
    assert pg.locator(".mu-last").count() == 0
    assert pg.inner_text(".mu-rec-s") == "since week 5"


@pytest.mark.render
def test_the_for_fun_line_is_not_drawn_until_someone_has_a_graded_call(view):
    pg = view("LIVE_SS3.record.fun = {fantasypros: {hit: 0, miss: 0}, pitcherlist: {hit: 0, miss: 0}}")
    assert pg.locator(".mu-rt").count() == 3 and pg.locator(".mu-fun").count() == 0


@pytest.mark.render
def test_smash_rows_lead_with_the_main_line_and_the_td_price(view):
    pg = view()
    rows = pg.evaluate("""() => [...document.querySelectorAll('.mu-smash .mu-sm')].map(r => [
      r.querySelector('.mu-nm b').textContent, r.querySelector('.mu-nm span').textContent,
      [...r.querySelectorAll('.mu-lg span')].map(s => s.textContent.trim())])""")
    assert len(rows) == 10
    assert rows[0] == ["J. Allen", "QB1 · BUF vs MIA · Sun 10:00 AM", ["251.5 pass yds", "TD -105"]]
    assert rows[5] == ["P. Nacua", "WR2 · LA @ PHI · Sun 1:25 PM", ["72.0 rec yds", "TD +135"]]
    assert rows[6][0] == "A. St. Brown"                                   # initials, a two-word surname stays whole
    assert rows[9][2] == []                                               # no book prices Kittle: the row stands alone
    assert pg.inner_text(".mu-smash .mu-tag.smash") == "SMASH"
    assert pg.evaluate("[...document.querySelectorAll('.mu-smash .mu-sm')].every(e => e.offsetHeight >= 52)")


@pytest.mark.render
def test_the_smash_card_ends_in_a_link_to_slips(view):
    pg = view()
    assert pg.inner_text(".mu-smash .mu-cf .mu-go").strip() == "Build in Slips"
    pg.click(".mu-smash [data-ssgo]")
    assert pg.evaluate("SURFACE") == "parlay"


@pytest.mark.render
def test_bold_calls_are_a_start_group_then_a_sit_group_ours_over_his_average(view):
    pg = view()
    assert pg.evaluate("[...document.querySelectorAll('.mu-takes .mu-grp')].map(h => h.textContent)") == ["Start", "Sit"]
    rows = pg.evaluate("""() => [...document.querySelectorAll('.mu-takes .mu-call')].map(r => [
      r.querySelector('.mu-tag').textContent, r.querySelector('.mu-nm b').textContent,
      r.querySelector('.mu-nm span').textContent, r.querySelector('.mu-rk b').textContent, r.querySelector('.mu-rk span').textContent])""")
    assert rows[0] == ["START", "R. Stevenson", "NE @ BUF · Sun 10:00 AM", "RB15", "avg RB36"]
    assert rows[1][3:] == ["WR16", "avg WR41"]
    assert [r[0] for r in rows] == ["START"] * 4 + ["SIT"] * 5
    # 52px, or a second meta line (the kickoff wraps rather than being cut) -- never taller
    assert pg.evaluate("[...document.querySelectorAll('.mu-takes .mu-call-h')].every(e => e.offsetHeight >= 52 && e.offsetHeight <= 66)")


@pytest.mark.render
def test_a_take_opens_to_its_reasons_one_at_a_time_and_links_to_the_profile(view):
    pg = view()
    first, second = pg.locator(".mu-call-h").nth(0), pg.locator(".mu-call-h").nth(1)
    assert pg.locator(".mu-b").first.evaluate("e => e.inert") is True
    second.click()
    assert [e.strip() for e in pg.locator(".mu-call[data-open] .mu-ev").all_inner_texts()] == ["PIT D vs WRs: 3rd softest", "Team total 27.5, 3rd of 32"]
    first.click()
    assert pg.locator(".mu-call[data-open]").count() == 1                  # the second closed
    assert pg.locator(".mu-call[data-open] .mu-ev").count() == 1
    pg.locator(".mu-call[data-open] [data-muslug]").click()
    assert "STEVENSON" in pg.locator("#modal").inner_text().upper()


@pytest.mark.render
def test_no_call_is_close_or_expert_led_and_no_old_block_is_left(view):
    pg = view()
    pg.evaluate("() => document.querySelectorAll('.mu-call').forEach(r => muSetOpen(r, true))")
    text = " ".join(pg.locator(".mu-rec, .mu-calls, .mu-last").all_inner_texts())    # the picker above keeps its own coin flip
    for gone in ("Close call", "CLOSE", "Coin flip", "More takes", "Most confident", "Higher than", "Lower than", "Splits",
                 "Backed", "Gut", "Pitcher List's column", "Claude's read"):
        assert gone not in text, gone
    assert "FantasyPros" in text and text.count("FantasyPros") == 1               # only the for-fun line names them
    assert pg.locator(".mu-top, .mu-more, .mu-ps, .mu-read, .mu-rb, .mu-spt, .mu-list").count() == 0


@pytest.mark.render
def test_an_empty_group_is_omitted_and_no_takes_at_all_is_one_quiet_line(view):
    pg = view("LIVE_SS3.takes = LIVE_SS3.takes.filter(r => r.call === 'SIT')")
    assert pg.evaluate("[...document.querySelectorAll('.mu-takes .mu-grp')].map(h => h.textContent)") == ["Sit"]
    pg = view("LIVE_SS3.takes.length = 0")
    assert pg.locator(".mu-takes").count() == 0
    assert pg.inner_text(".mu-calls .mu-empty") == "No bold START or SIT calls this week."
    assert pg.locator(".mu-smash .mu-sm").count() == 10                    # SMASH stands
    assert pg.locator(".mu-calls.two").count() == 0


@pytest.mark.render
def test_no_calls_at_all_is_blip_not_an_error(view):
    pg = view("LIVE_SS3.takes.length = 0; LIVE_SS3.smash.length = 0")
    assert pg.locator(".mu-blip q").inner_text() == "No calls posted yet this week."
    assert pg.locator(".mu-smash, .mu-takes, .mu-empty").count() == 0
    assert pg.locator(".mu-rec").count() == 1 and pg.locator(".ssv-pick").count() == 1     # the picker and record stand


@pytest.mark.render
def test_a_missing_block_renders_the_empty_states(view):
    """The producer has not written startsit_v3: the build's empty week (week null, no rows, zero record)."""
    empty = startsit_v3.live_ss3(None, slugify)
    pg = view("for (const k of Object.keys(LIVE_SS3)) delete LIVE_SS3[k]; Object.assign(LIVE_SS3, %s)" % json.dumps(empty))
    assert pg.locator(".mu-blip").count() == 1 and pg.locator(".mu-rec.none").count() == 1
    assert pg.locator(".mu-last, .mu-smash, .mu-takes").count() == 0


@pytest.mark.render
def test_last_weeks_calls_are_a_list_of_hit_miss_and_void_under_the_calls(view):
    pg = view()
    assert pg.inner_text(".mu-last .mu-ch").lower() == "week 5: how the calls did"
    rows = pg.evaluate("[...document.querySelectorAll('.mu-last .mu-rv')].map(r => [r.className, r.querySelector('.mu-rv-r').textContent, r.querySelector('b').textContent, r.querySelector('i').textContent])")
    assert rows[0] == ["mu-rv hit", "Hit", "T. Higgins", "START · finished WR14"]
    assert rows[2] == ["mu-rv void", "Void", "S. LaPorta", "START · TE"]                 # no finish for a void call
    assert rows[5][3] == "SMASH · finished WR2" and rows[4][1] == "Miss"
    assert pg.evaluate("document.querySelector('.mu-calls').compareDocumentPosition(document.querySelector('.mu-last')) & 4") == 4
    assert pg.locator(".mu-last").count() == 1 and view("LIVE_SS3.record.last_week = []").locator(".mu-last").count() == 0


@pytest.mark.render
def test_nothing_scrolls_sideways_at_360_with_every_row_open(view):
    pg = view()
    pg.evaluate("() => document.querySelectorAll('.mu-call').forEach(r => muSetOpen(r, true))")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360


@pytest.mark.render
def test_desktop_sets_the_two_cards_side_by_side_ending_level(view):
    pg = view(w=1400, h=900)
    box = lambda sel: pg.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top + scrollY, r.bottom + scrollY, r.width]; }", sel)
    a, b = box(".mu-smash"), box(".mu-takes")
    assert abs(a[1] - b[1]) < 4 and a[0] < b[0]                            # one top edge, SMASH on the left
    assert abs(a[2] - b[2]) <= 150                                         # STYLE.md: sections side by side end within 150px
    assert a[3] <= 600 and b[3] <= 600                                     # a label stays within 560px of its value, give or take the card's own padding
    assert pg.evaluate("document.documentElement.scrollWidth") <= 1400


@pytest.mark.render
def test_the_hash_still_opens_the_view_and_the_picker_and_board_keep_their_place(view):
    for h in ("#matchups", "#startsit", "#takes"):
        pg = view(hash_=h)
        assert pg.evaluate("SURFACE") == "matchups" and pg.locator(".ssv-pick").count() == 1
    assert pg.evaluate("""() => { const q = s => document.querySelector(s);
      return [q('.ssv').compareDocumentPosition(q('.mu-rec')) & 4, q('.mu-rec').compareDocumentPosition(q('.mu-calls')) & 4]; }""") == [4, 4]
