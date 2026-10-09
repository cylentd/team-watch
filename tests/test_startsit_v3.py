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
from wording import words  # noqa: E402

FIX = REPO / "tests" / "fixtures" / "data" / "startsit_v3.json"


def _block():
    return startsit_v3.live_ss3(sources.load_startsit_v3(), slugify)


# ---- The cut ----

def test_the_fixture_week_is_whole_and_ordered_as_the_view_draws_it():
    b = _block()
    contract.validate("LIVE_SS3", b)
    assert (b["week"], b["season"], len(b["smash"]), len(b["takes"])) == (2, 2026, 10, 9)
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


@pytest.mark.parametrize("missing", [None, {}], ids=["none", "empty"])
def test_no_block_is_an_empty_week_that_still_meets_the_contract(missing):
    b = startsit_v3.live_ss3(missing, slugify)
    contract.validate("LIVE_SS3", b)
    assert b["week"] is None and b["smash"] == [] and b["takes"] == []
    assert b["record"]["since_week"] == 5 and b["record"]["weeks"] == [] and b["record"]["smash"] == {"hit": 0, "miss": 0, "void": 0}
    assert startsit_v3.report(b).startswith("Start/Sit v3: no startsit_v3 block")


def test_a_block_for_another_week_than_the_page_loses_its_calls_but_keeps_its_record():
    """After the turn the file still holds last week's calls: the view must say none are posted (2026-10-05)."""
    raw = sources.load_startsit_v3()
    other = startsit_v3.live_ss3(raw, slugify, week=raw["week"] + 1)
    assert other["smash"] == [] and other["takes"] == []
    assert other["record"] == _block()["record"], "the record is backward-looking and stays"
    contract.validate("LIVE_SS3", other)
    same = startsit_v3.live_ss3(raw, slugify, week=raw["week"])
    assert (len(same["smash"]), len(same["takes"])) == (10, 9)
    assert len(_block()["smash"]) == 10, "no page week passed: the block is not judged"


def test_a_reason_in_any_of_its_shapes_reads_as_text():
    """ff-jarvis's v2 reasons are {k, text}; the spec sketch said {kind, text_key}; the page needs text."""
    take = {"name": "A B", "call": "start", "pos": "WR", "margin_spots": 7,
            "reasons": [{"k": "role", "text": "one"}, {"kind": "mx", "text_key": "two"}, {"t": "three"}, {}]}
    got = startsit_v3.live_ss3({"week": 6, "takes": [take, {"name": "No Call", "call": "COIN"}]}, slugify)
    assert [r["t"] for r in got["takes"][0]["reasons"]] == ["one", "two", "three", ""]
    assert got["takes"][0]["slug"] == "a-b" and got["takes"][0]["call"] == "START"
    assert len(got["takes"]) == 1, "a call that is not START or SIT (no coin flips) is dropped"


def test_the_report_names_the_week_and_the_record_state():
    assert startsit_v3.report(_block()) == "Start/Sit v3: week 2, 10 SMASH, 4 START, 5 SIT, record since week 5 (1 weeks graded)"
    ungraded = startsit_v3.live_ss3({"week": 5, "smash": [], "takes": []}, slugify)
    assert startsit_v3.report(ungraded).endswith("no week graded yet (counts from week 5)")


def test_the_block_is_read_feed_first_bare_or_wrapped_then_the_file(tmp_path, monkeypatch):
    assert sources.load_startsit_v3()["week"] == 2                            # the fixture file
    feed = tmp_path / "feed.json"
    monkeypatch.setattr(sources, "FEED", feed)
    feed.write_text(json.dumps({"startsit_v3": {"data": {"week": 7, "smash": []}}}), encoding="utf-8")
    assert sources.load_startsit_v3()["week"] == 7
    feed.write_text(json.dumps({"startsit_v3": {"week": 8, "smash": []}}), encoding="utf-8")
    assert sources.load_startsit_v3()["week"] == 8
    feed.write_text("{}", encoding="utf-8")
    assert sources.load_startsit_v3()["week"] == 2                            # no block in the feed: the file
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


RECORD = ".mu-calls [data-testid='matchups-record']"       # one line in the calls card's head since 2026-10-09 (draft A)
# A page of calls on a phone, read from its constants file (design/src/js/data/lineup.js), never retyped.
PAGE_ROWS = int(re.search(r"const MU_PAGE_ROWS = (\d+);", (REPO / "design/src/js/data/lineup.js").read_text(encoding="utf-8"))[1])
CALL = {k: words(f"matchups.call.{k}") for k in ("smash", "start", "sit")}
ROW_FITS = "[...document.querySelectorAll('.mu-calls .mu-call-h')].every(e => e.offsetHeight >= 52 && e.offsetHeight <= 66)"


def smash_rows(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('.mu-calls .mu-sm')].map(r => [
      r.querySelector('.mu-nm b').textContent, r.querySelector('.mu-nm span').textContent,
      [...r.querySelectorAll('.mu-lg span')].map(s => s.textContent.trim())])""")


def take_rows(pg):
    return pg.evaluate("""() => [...document.querySelectorAll('.mu-calls .mu-call')].map(r => [
      r.querySelector('.mu-nm b').textContent, r.querySelector('.mu-nm span').textContent,
      r.querySelector('.mu-rk b').textContent, r.querySelector('.mu-rk span').textContent, !!r.querySelector('.mu-tag')])""")


@pytest.mark.render
def test_the_record_is_three_separate_hit_miss_counts_since_week_5(view):
    pg = view()
    head = f"{words('matchups.record.label')} {words('matchups.record.since').format(wk=5)}"
    void = words("matchups.record.void").format(n=1)
    want = f"{head}: 7-3 {CALL['smash']} · 2-2 {CALL['start']} {void} · 4-1 {CALL['sit']}"      # void only when above zero
    assert pg.inner_text(RECORD + " p:first-child") == want
    assert pg.inner_text(RECORD + " .mu-fun") == words("matchups.record.fun").format(fp="5-3", pl="3-2")


@pytest.mark.render
def test_before_any_graded_week_the_record_is_calm_not_zeros(view):
    pg = view(NO_GRADE)
    head = f"{words('matchups.record.label')} {words('matchups.record.since').format(wk=5)}"
    assert pg.inner_text(RECORD) == f"{head}: {words('matchups.record.none')}"
    assert pg.locator(".mu-fun").count() == 0 and pg.locator(".mu-last").count() == 0


@pytest.mark.render
def test_the_for_fun_line_is_not_drawn_until_someone_has_a_graded_call(view):
    pg = view("LIVE_SS3.record.fun = {fantasypros: {hit: 0, miss: 0}, pitcherlist: {hit: 0, miss: 0}}")
    assert pg.locator(RECORD + " .mu-recl-k").count() == 3 and pg.locator(".mu-fun").count() == 0


@pytest.mark.render
def test_smash_rows_lead_with_the_main_line_and_the_td_price(view):
    """SMASH is the calls card's first kind, MU_PAGE_ROWS a page on a phone (draft A); the fixture's ten fill two."""
    pg = view()
    first = smash_rows(pg)
    assert len(first) == PAGE_ROWS
    assert pg.evaluate("[...document.querySelectorAll('.mu-calls .mu-sm')].every(e => e.offsetHeight >= 52)")
    pg.click("[data-mupg='1']")
    second = smash_rows(pg)
    rows = first + second
    assert len(rows) == 10 and len(second) == 10 - PAGE_ROWS
    assert rows[0] == ["J. Allen", "QB1 · BUF vs MIA · Sun 10:00 AM", ["251.5 pass yds", "TD -105"]]
    assert rows[5] == ["P. Nacua", "WR2 · LA @ PHI · Sun 1:25 PM", ["72.0 rec yds", "TD +135"]]
    assert rows[6][0] == "A. St. Brown"                                   # initials, a two-word surname stays whole
    assert rows[9][2] == []                                               # no book prices Kittle: the row stands alone
    assert pg.locator(".mu-calls [data-mukind='smash'][aria-pressed='true']").count() == 1     # still SMASH's page


@pytest.mark.render
def test_the_smash_card_ends_in_a_link_to_slips(view):
    pg = view()
    assert pg.inner_text(".mu-calls .mu-cf .mu-go").strip() == words("matchups.smash.build")
    pg.click("[data-mukind='start']")
    assert pg.locator(".mu-calls .mu-cf").count() == 0                   # only SMASH's page builds a slip
    pg.click("[data-mukind='smash']")
    pg.click(".mu-calls [data-ssgo]")
    assert pg.evaluate("SURFACE") == "parlay"


@pytest.mark.render
def test_bold_calls_are_a_start_page_then_a_sit_page_ours_over_his_average(view):
    """The kind switch says START or SIT (its pressed button is the tag), so a row wears no tag of its own (draft A).
    Each page: our rank over his season average; 52px, or a second meta line (the kickoff wraps), never taller."""
    pg = view()
    pressed = lambda: pg.evaluate("document.querySelector('.mu-calls .mu-kd[aria-pressed=\"true\"]').firstChild.textContent.trim()")
    pg.click("[data-mukind='start']")
    rows = take_rows(pg)
    assert pressed() == CALL["start"] and len(rows) == 4
    assert rows[0] == ["R. Stevenson", "NE @ BUF · Sun 10:00 AM", "RB15", "avg RB36", False]
    assert rows[1][2:4] == ["WR16", "avg WR41"]
    assert pg.evaluate(ROW_FITS)
    pg.click("[data-mukind='sit']")
    rows = take_rows(pg)
    assert pressed() == CALL["sit"] and len(rows) == 5
    assert rows[1] == ["E. Engram", "DEN @ SF · Sun 1:25 PM", "TE20", "avg TE8", False]
    assert [r[2:] for r in rows[2:]] == [["RB31", "avg RB8", False], ["QB19", "avg QB9", False], ["WR31", "avg WR18", False]]
    assert pg.evaluate(ROW_FITS)


@pytest.mark.render
def test_a_take_opens_to_its_reasons_one_at_a_time_and_links_to_the_profile(view):
    pg = view()
    pg.click("[data-mukind='start']")
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
@pytest.mark.parametrize("kind, page", [("smash", 0), ("smash", 1), ("start", 0), ("sit", 0)])   # every page: 10, 4 and 5 calls
def test_no_call_is_close_or_expert_led_and_no_old_block_is_left(view, kind, page):
    pg = view("MU_KIND = %s; MU_PAGE = %d" % (json.dumps(kind), page))
    pg.evaluate("() => document.querySelectorAll('.mu-call').forEach(r => muSetOpen(r, true))")
    # the whole calls card (head, record, rows, kind switch, pager) and last week; the lineup and the picker keep their own coin flip
    text = " ".join(pg.locator(".mu-calls, .mu-last").all_inner_texts())
    still_there = [gone for gone in ("Close call", "CLOSE", "Coin flip", "More takes", "Most confident", "Higher than", "Lower than", "Splits",
                                     "Backed", "Gut", "Pitcher List's column", "Claude's read") if gone in text]
    assert text != "" and still_there == []
    assert "FantasyPros" in text and text.count("FantasyPros") == 1               # only the for-fun line names them
    assert pg.locator(".mu-top, .mu-more, .mu-ps, .mu-read, .mu-rb, .mu-spt, .mu-list").count() == 0


@pytest.mark.render
def test_a_kind_with_no_calls_is_one_quiet_line_and_counts_zero(view):
    pg = view("LIVE_SS3.takes = LIVE_SS3.takes.filter(r => r.call === 'SIT')")
    counts = pg.evaluate("Object.fromEntries([...document.querySelectorAll('[data-mukind]')].map(b => [b.dataset.mukind, b.querySelector('b').textContent]))")
    assert counts == {"smash": "10", "start": "0", "sit": "5"}
    pg.click("[data-mukind='start']")
    assert pg.inner_text(".mu-calls .mu-empty") == words("matchups.calls.none").format(kind=words("matchups.call.start"))
    pg = view("LIVE_SS3.takes.length = 0")
    assert pg.locator(".mu-calls .mu-sm").count() == PAGE_ROWS             # SMASH stands, its first page


@pytest.mark.render
def test_no_calls_at_all_is_blip_not_an_error(view):
    pg = view("LIVE_SS3.takes.length = 0; LIVE_SS3.smash.length = 0")
    assert pg.locator(".mu-blip q").inner_text() == words("matchups.blip.none")
    assert pg.locator(".mu-calls, .mu-empty").count() == 0
    assert pg.locator(".mu-blip [data-testid='matchups-record']").count() == 1     # the record stands under Blip
    assert pg.locator(".mu-lineup [data-mucmp]").count() == 1                         # and the lineup keeps its compare


@pytest.mark.render
def test_a_missing_block_renders_the_empty_states(view):
    """The producer has not written startsit_v3: the build's empty week (week null, no rows, zero record)."""
    empty = startsit_v3.live_ss3(None, slugify)
    pg = view("for (const k of Object.keys(LIVE_SS3)) delete LIVE_SS3[k]; Object.assign(LIVE_SS3, %s)" % json.dumps(empty))
    assert pg.locator(".mu-blip").count() == 1
    assert words("matchups.record.none") in pg.inner_text(".mu-blip [data-testid='matchups-record']")
    assert pg.locator(".mu-last, .mu-calls").count() == 0


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
    pg.click("[data-mukind='start']")
    pg.evaluate("() => document.querySelectorAll('.mu-call').forEach(r => muSetOpen(r, true))")
    assert pg.evaluate("document.documentElement.scrollWidth") <= 360


@pytest.mark.render
def test_desktop_sets_the_two_cards_side_by_side_ending_level(view):
    """The lineup and the calls share a top edge and end level: beside a full lineup the calls card holds as many
    rows as fit (muFitCalls). The fixture's own roster is short, so a 15-man one is planted."""
    pg = view("TEAMS[VIEW].roster = Array.from({length: 15}, (_, i) => P('Test Player ' + i, ['QB', 'RB', 'WR', 'TE'][i % 4],"
              " 'CIN', 'test-player-' + i, {slot: i < 8 ? 'RB' : 'BN', start: i < 8}))", w=1400, h=900)
    box = lambda sel: pg.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top + scrollY, r.bottom + scrollY, r.width]; }", sel)
    a, b = box(".mu-lineup"), box(".mu-calls")
    assert abs(a[1] - b[1]) < 4 and a[0] < b[0]                            # one top edge, the lineup on the left
    assert abs(a[2] - b[2]) <= 150                                         # STYLE.md: sections side by side end within 150px
    assert a[3] <= 600 and b[3] <= 600                                     # a label stays within 560px of its value, give or take the card's own padding
    assert pg.evaluate("document.documentElement.scrollWidth") <= 1400


@pytest.mark.render
@pytest.mark.parametrize("h", ["#matchups", "#startsit", "#takes"])
def test_the_hash_still_opens_the_view_and_the_lineup_calls_and_board_keep_their_place(view, h):
    pg = view(hash_=h)
    assert pg.evaluate("SURFACE") == "matchups" and pg.locator("[data-mucmp]").count() == 1 and pg.locator(".ssv-pick").count() == 0
    assert pg.evaluate("""() => { const q = s => document.querySelector(s);
      return [q('.mu-lineup').compareDocumentPosition(q('.mu-calls')) & 4, q('.mu-calls').compareDocumentPosition(q('.ssv')) & 4]; }""") == [4, 4]
