"""The roster as a lineup sheet (2026-09-25): full-size rows on a phone in the cards' frame (it was
squeezed to one screen, and David found it read small), the bench beside the starters on a
desktop. Runs on the ESPN fixture, the one with a bench."""
import re

import pytest

from test_render import drive, go, open_page  # noqa: F401


def espn_roster(browser, page_file, viewport):
    ctx, page, errors = open_page(browser, page_file, viewport)
    drive(page, go("roster"))
    page.evaluate("VIEW='espn'; render()")
    return ctx, page, errors


@pytest.mark.render
def test_a_phone_row_is_full_size(browser, page_file):
    ctx, page, errors = espn_roster(browser, page_file, (360, 660))
    heads = page.eval_on_selector_all(".row .head img, .row .head .fallback", "els => els.map(e => e.getBoundingClientRect().width)")
    assert heads and min(heads) >= 40, heads
    slots = page.eval_on_selector_all(".row.start .slot", "els => els.map(e => e.textContent)")
    assert slots and not any(re.search(r"\d", s) for s in slots), slots   # RB1 prints RB, FLX2 prints FLX
    # The bench is one to a row, like the starters: every bench row as wide as a starter row.
    widths = page.eval_on_selector_all(".row", "els => [...new Set(els.map(e => Math.round(e.getBoundingClientRect().width)))]")
    assert len(widths) == 1, widths
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_starter_row_shows_usage_and_a_td_chance(browser, page_file):
    """Usage by position where the snap-share line was, and the TD chance under the projection
    only from 25% up (2026-09-25, storyboard option A)."""
    ctx, page, errors = espn_roster(browser, page_file, (1280, 900))
    assert page.locator(".row .trend, .row .spark").count() == 0, "the snap-share line is gone"
    words = page.eval_on_selector_all(".row.start .ruse small", "els => els.map(e => e.textContent)")
    assert set(words) <= {"targets", "touches", "dropbacks"}, words
    shown = page.eval_on_selector_all(".rtd", "els => els.map(e => parseInt(e.textContent.replace(/\\D/g, '')))")
    assert all(n >= 25 for n in shown), shown
    assert page.evaluate("TEAMS.espn.roster.every(p => { const n = tdChanceFor(p); return n === null || n < 25 || projFor(p) === null"
                         " || !!document.querySelector(`.row[data-i='${briefOrder(TEAMS.espn).indexOf(p)}'] .rtd`); })")
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_an_early_projection_wears_a_label_and_a_lined_or_unstamped_one_does_not(browser, page_file):
    """ff-jarvis's `stage` (2026-10-05): "early" = no prop line for his game yet, drawn as an EARLY tag with
    its note; "lined" = the normal state, a hover note and no tag; no field = nothing, and no error.
    Fixture: Purdy early, Chase Brown lined, Kittle unstamped."""
    ctx, page, errors = espn_roster(browser, page_file, (1280, 900))
    got = page.evaluate("""() => Object.fromEntries(['brock-purdy', 'chase-brown', 'george-kittle'].map(slug => {
        const el = document.createElement('div');
        el.innerHTML = projNumHTML({slug});
        const tag = el.querySelector('.rstage');
        return [slug, {stage: projStage({slug}), tag: tag ? tag.textContent : null, tip: tag ? tag.title : null,
                       rowTip: el.firstElementChild.title}];
    }))""")
    assert got["brock-purdy"] == {"stage": "early", "tag": "EARLY", "rowTip": "",
                                  "tip": "No prop line for this game yet: model, opponent and game total."}, got
    assert got["chase-brown"] == {"stage": "lined", "tag": None, "tip": None,
                                  "rowTip": "Lines are up for this game; blended with his own line if he has one."}, got
    assert got["george-kittle"] == {"stage": None, "tag": None, "tip": None, "rowTip": ""}, got
    assert page.locator(".row .rstage").count() == page.evaluate(
        "TEAMS.espn.roster.filter(p => projStage(p) === 'early' && projFor(p) !== null).length")
    assert errors == []
    ctx.close()


def test_the_projection_cut_carries_stage_and_an_older_feed_without_it_is_no_error():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "design"))
    import projections
    slugify = lambda n: n.lower().replace(" ", "-")
    rows = [{"name": "A One", "pos": "QB", "pts": 10.0, "src": "model", "stage": "early"},
            {"name": "B Two", "pos": "QB", "pts": 9.0, "src": "model", "stage": "lined"},
            {"name": "C Three", "pos": "QB", "pts": 8.0, "src": "model"}]
    raw = {"players": rows, "stage": {"early": 1, "lined": 1}}
    out = projections.live_projections(raw, slugify, {"a-one", "b-two", "c-three"})
    assert [out["players"][s]["stage"] for s in ("a-one", "b-two", "c-three")] == ["early", "lined", None]
    assert out["meta"]["stage"] == {"early": 1, "lined": 1}
    assert projections.live_projections({"players": rows[2:]}, slugify, {"c-three"})["meta"]["stage"] is None


@pytest.mark.render
@pytest.mark.parametrize("width", [360, 1100, 1280])
def test_no_name_loses_its_end(browser, page_file, width):
    """A long name wraps to a second line, never ends in "..." (2026-09-25: "Tetairoa McMill..."
    at 1280, nearly every name at 1100). The check measures the text itself against its cell, so
    an ellipsis set on any ancestor counts."""
    ctx, page, errors = espn_roster(browser, page_file, (width, 900))
    # A third line is clamped away; scrollHeight past the box by more than a descender's 2px says so.
    cut = page.evaluate("""[...document.querySelectorAll('.row .nm')].filter(nm => {
      const b = nm.querySelector('.nm-1 b'), r = document.createRange(); r.selectNodeContents(b);
      return r.getBoundingClientRect().width > nm.getBoundingClientRect().width + 0.5 || b.scrollHeight > b.clientHeight + 2;
    }).map(nm => nm.querySelector('.nm-1 b').innerText)""")
    assert cut == []
    assert errors == []
    ctx.close()


@pytest.mark.render
def test_a_desktop_puts_the_bench_beside_the_starters(browser, page_file):
    ctx, page, errors = espn_roster(browser, page_file, (1280, 900))
    tops = page.eval_on_selector_all(".sheet-col", "els => els.map(e => Math.round(e.getBoundingClientRect().top))")
    lefts = page.eval_on_selector_all(".sheet-col", "els => els.map(e => Math.round(e.getBoundingClientRect().left))")
    assert len(tops) == 2 and tops[0] == tops[1] and lefts[1] > lefts[0]
    assert errors == []
    ctx.close()
