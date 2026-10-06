"""Claude's row under the Slips record line (2026-10-05, LIVE_CLAUDE_RECORD, design/slips.py): how often
Claude's frozen prop call hit where he took the model's side ("agrees") and where he took the other one ("alone").
The data cut needs no browser; the row and its pair of tiles are checked in Slips at 360px in both states:
no graded week yet (the fixture's `record` is null) and graded."""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
import contract  # noqa: E402  (before slips: slips puts api/ first on sys.path, where another clips.py lives)
import slips  # noqa: E402
from test_render import open_page  # noqa: E402

FIRST_CARD_MAX = 212   # design/STYLE.md: the first data starts by ~200px; this row spends 14 of the spare px

GRADED = {"season": 2026, "week": 5, "through_week": 4,
          "agree": {"w": 7, "l": 5, "push": 1, "void": 0}, "alone": {"w": 8, "l": 9, "push": 0, "void": 2}}


def block(built):
    m = re.search(r"^const LIVE_CLAUDE_RECORD = (.*);$", built.fragment, re.M)
    assert m, "LIVE_CLAUDE_RECORD not injected"
    return json.loads(m.group(1))


# ---------------------------------------------------------------- data (no browser)
def test_the_fixture_has_calls_but_nothing_graded(built):
    b = block(built)
    assert b == {"season": 2026, "week": 4, "through_week": None, "agree": None, "alone": None}
    assert contract.problems("LIVE_CLAUDE_RECORD", b) == []


def test_only_the_record_is_cut_out():
    raw = {"season": 2026, "week": 5, "calls": [{"name": "must not ride along"}], "games": {},
           "record": {"agree": {"w": 7, "l": 5, "push": 1, "void": 0, "n": 12, "hit": 0.583},
                      "disagree": {"claude": {"w": 8, "l": 9, "push": 0, "void": 2, "n": 17, "hit": 0.471},
                                   "model": {"w": 9, "l": 8, "push": 0, "void": 2}},
                      "claude": {"w": 15, "l": 14}, "weeks": [{"week": 3}, {"week": 4}]}}
    assert slips.claude_record(raw) == GRADED
    assert contract.problems("LIVE_CLAUDE_RECORD", GRADED) == []


def test_no_file_or_no_record_is_optional():
    assert slips.claude_record(None) is None, "no file: no row at all"
    assert contract.problems("LIVE_CLAUDE_RECORD", None) == []
    assert slips.claude_record({"season": 2026, "week": 4, "record": None})["agree"] is None


def test_the_contract_names_a_missing_field():
    assert contract.problems("LIVE_CLAUDE_RECORD", {"season": 2026, "week": 4, "agree": None, "alone": None}) == ["LIVE_CLAUDE_RECORD.through_week"]
    assert contract.problems("LIVE_CLAUDE_RECORD", {**GRADED, "agree": {"w": 1}}) == ["LIVE_CLAUDE_RECORD.agree.l"]
    assert contract.problems("LIVE_CLAUDE_RECORD", {**GRADED, "alone": None}) == ["LIVE_CLAUDE_RECORD.agree and .alone are both there or both null"]


# ---------------------------------------------------------------- the page
RESET = """() => { 'use strict';
  Object.assign(LIVE_CLAUDE_RECORD, JSON.parse(__CLR));
  SLIP.length = 0; SL_CHIP = {}; SL_FOCUS = null; SL_REC_OPEN = false; PV_OPEN = false; PV_I = null;
  PARLAY_BOOK = 'dk'; GAL_WIN = 'evening-mon'; SURFACE = 'parlay'; render(); }"""

GRADE = "g => { Object.assign(LIVE_CLAUDE_RECORD, g); render(); }"


@pytest.fixture(scope="module")
def shared(browser, page_file):
    ctx, pg, errors = open_page(browser, page_file, (360, 780))
    pg.evaluate("() => { window.__CLR = JSON.stringify(LIVE_CLAUDE_RECORD); }")
    assert errors == []
    yield pg, errors
    ctx.close()


@pytest.fixture
def page(shared):
    pg, errors = shared
    left, errors[:] = list(errors), []
    assert left == []
    pg.evaluate(RESET)
    yield pg
    assert errors == [], errors


def first_card_top(page):
    """Where the first data starts: Top calls since 2026-10-05, the game cards follow it."""
    return page.locator(".tpc").bounding_box()["y"] + page.evaluate("window.scrollY")


def one_line(page, selector):
    """The row's pieces share a middle line and do not overflow the button."""
    mids = page.evaluate("""s => [...document.querySelectorAll(s)].map(e => { const r = e.getBoundingClientRect(); return r.top + r.height / 2; })""", selector)
    assert max(mids) - min(mids) < 3, f"one line: {mids}"
    assert page.evaluate("(() => { const b = document.querySelector('.pr-rec-b'); return b.scrollWidth <= b.clientWidth; })()"), "overflows its button"


@pytest.mark.render
def test_no_graded_week_says_where_the_numbers_start(page):
    row = page.locator(".pr-rec-cl")
    assert row.count() == 1 and row.locator(".pr-rec-l").text_content() == "Claude"
    assert row.locator(".pr-rec-from").text_content() == "from week 5"
    assert row.locator(".pr-cq, .pr-cb").count() == 0, "no numbers and no badge before a graded game"
    assert row.locator(".pr-rec-from").evaluate("e => getComputedStyle(e).color") == page.locator(".pr-rec-l").first.evaluate("e => getComputedStyle(e).color"), "muted like the label"
    one_line(page, ".pr-rec-cl > *")
    page.locator(".pr-rec-b").click()
    assert page.locator(".pr-cts").count() == 0, "no tiles to open yet"
    page.locator(".pr-rec-b").click()
    top = first_card_top(page)
    print("first game card top, no graded week:", top)
    assert page.locator(".pr-rec-b").bounding_box()["height"] <= 44 and top <= FIRST_CARD_MAX, top


@pytest.mark.render
def test_graded_row_has_both_hit_rates_and_the_badge(page):
    page.evaluate(GRADE, GRADED)
    row = page.locator(".pr-rec-cl")
    assert row.locator(".pr-cq i").all_inner_texts() == ["agrees", "alone"]
    assert row.locator(".pr-cq b").all_inner_texts() == ["58%", "47%"]
    assert row.locator(".pr-rec-from").count() == 0
    assert row.locator(".pr-cq b").first.evaluate("e => getComputedStyle(e).fontFamily").lower().endswith("monospace")
    badge = row.locator(".pr-cb")
    assert badge.count() == 1 and row.locator(".pr-cq.agree .pr-cb").count() == 1, "the C sits before agrees only"
    assert badge.text_content() == "C" and badge.get_attribute("aria-hidden") == "true"
    box = badge.bounding_box()
    assert (round(box["width"]), round(box["height"])) == (18, 18)
    style = badge.evaluate("e => { const s = getComputedStyle(e); return [s.borderRadius, s.fontWeight, s.backgroundColor, s.color, s.fontFamily]; }")
    assert style[0] == "50%" and style[1] == "800" and "Bricolage" in style[4], style
    root = page.evaluate("[getComputedStyle(document.documentElement).getPropertyValue('--lime'), getComputedStyle(document.documentElement).getPropertyValue('--on-lime')]")
    probe = page.evaluate("""l => { const e = document.createElement('i'); e.style.color = l[0]; e.style.backgroundColor = l[1]; document.body.append(e);
      const s = getComputedStyle(e); const v = [s.color, s.backgroundColor]; e.remove(); return v; }""", root)
    assert (style[2], style[3]) == (probe[0], probe[1]), "lime on on-lime, from the tokens"
    one_line(page, ".pr-rec-cl > *, .pr-rec-cl .pr-cq > *")
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    top = first_card_top(page)
    print("first game card top, graded:", top)
    assert page.locator(".pr-rec-b").bounding_box()["height"] <= 44 and top <= FIRST_CARD_MAX, top


@pytest.mark.render
def test_graded_tiles_pair_agrees_and_alone(page):
    page.evaluate(GRADE, GRADED)
    page.locator(".pr-rec-b").click()
    assert page.locator(".pr-rt b").all_inner_texts() == ["205-165", "305-275", "241-182"], "the tier tiles are untouched"
    assert page.locator(".pr-ct b").all_inner_texts() == ["7-5", "8-9"]
    assert page.locator(".pr-ct span").all_text_contents() == ["Cagrees", "alone"]
    assert page.locator(".pr-ct small").all_inner_texts() == ["58%", "47%"]
    assert page.locator(".pr-ct .pr-cb").count() == 1
    assert page.locator(".pr-rec-cs").inner_text() == "Claude, through week 4"
    a, b = (page.locator(".pr-ct").nth(i).bounding_box() for i in (0, 1))
    assert abs(a["y"] - b["y"]) < 1 and abs(a["height"] - b["height"]) < 1, "a pair on one row, one size"
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    page.evaluate("render()")
    assert page.locator(".pr-ct").count() == 2 and page.locator("#pr-rec-more").is_visible(), "a re-render keeps it open"


@pytest.mark.render
def test_one_graded_side_has_no_percent_not_a_dash(page):
    page.evaluate(GRADE, {**GRADED, "alone": {"w": 0, "l": 0, "push": 1, "void": 0}})
    page.locator(".pr-rec-b").click()
    assert page.locator(".pr-cq b").all_inner_texts() == ["58%"]
    assert page.locator(".pr-ct small").all_inner_texts() == ["58%", ""]
