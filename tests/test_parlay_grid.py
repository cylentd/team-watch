"""Bets (2026-09-25): the Build market as a card grid, two to a row on a phone; the Slips view as a
stack; the slip as a tray that counts what lands in it and opens into a sheet; one kickoff for both
views. A new view's cards arrive once, and a tap that only adds a leg pops that line without
replaying the arrival of everything else."""
import re

import pytest

from test_render import SEED, browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render


def columns(page, sel):
    return len(page.evaluate(f"getComputedStyle(document.querySelector('{sel}')).gridTemplateColumns").split())


@pytest.mark.parametrize("book, grid", [("underdog", ".pgrid"), ("dk", ".lgrid")])
def test_the_market_is_two_cards_a_row_on_a_phone(browser, page_file, book, grid):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(f"SURFACE='build'; PARLAY_BOOK='{book}'; MKT_PAGE=1; render()")
    assert columns(page, grid) == 2
    card = page.locator(f"{grid} > *").first
    card.locator(".more").first.click()
    page.wait_for_timeout(50)
    opened = page.locator(f"{grid} > *:has(.legx)").first
    assert opened.bounding_box()["width"] > 300, "an open card spans the row"
    assert errors == []
    ctx.close()


def test_a_new_view_enters_once_and_a_tap_pops_only_its_line(browser, page_file):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="no-preference")
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.route(re.compile(r"^https?://"), lambda route: route.abort())
    page.add_init_script(SEED)
    page.goto(page_file.as_uri() + "#build")
    page.wait_for_function("document.getElementById('view').children.length > 0")
    assert page.evaluate("document.getElementById('view').classList.contains('enter')")
    page.locator(".pgrid .udline").first.click()
    assert not page.evaluate("document.getElementById('view').classList.contains('enter')")
    assert page.locator(".udline.just").count() == 1
    assert page.locator(".slip .sliphead .pill.bump").count() == 1
    page.wait_for_function("document.querySelector('.tray .tray-n').textContent === '1'")
    assert errors == []
    ctx.close()


@pytest.mark.parametrize("book", ["underdog", "dk"])
def test_a_slip_is_one_row_per_pick_read_as_a_sentence(browser, page_file, book):
    """A pick'em entry (2026-09-25): one row per pick, its game and kickoff on the why line rather
    than a header per game (nearly every pick is its own game, so the header cost 31px a leg)."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate(f"SURFACE='parlay'; PARLAY_BOOK='{book}'; render()")
    slip = page.locator(".ticket").first
    if slip.count() == 0:
        pytest.skip("the fixture's market builds no gallery slip for this book")
    legs = slip.locator(".tk-leg")
    assert legs.count() >= 2 and slip.locator(".tk-game").count() == 0
    assert legs.first.locator("img, .fallback").count() == 1, "every leg carries his photo"
    call = legs.first.locator(".tk-call").inner_text()
    assert call != call.upper(), "the call is sentence case, not capitals"
    game = page.evaluate(f"PROPS[GALLERIES['{book}'][0].legs[0]].game")
    assert game in legs.first.locator(".why").inner_text(), "the pick names its game"
    assert slip.locator(".tk-stub .tk-head b").inner_text().strip() not in ("", "—")
    assert slip.locator(".tk-stub [data-loadslip]").count() == 1, "Load sits on the stub"
    assert errors == []
    ctx.close()


def test_every_underdog_slip_draws_its_verdict(browser, page_file):
    """Each Underdog slip draws its verdict on the stub (2026-09-25), so nobody works out whether a
    slip beats its payout: the meter's bar is the chance and its tick is 1/x, on one 0-50% scale;
    the note says what x needs and "Beats it" at a quarter or more over 1/x, "Short" under it.
    The chance is graded, so a receptions leg never counts above 57.3%."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='underdog'; render()")
    slips = page.locator(".ticket")
    if slips.count() == 0:
        pytest.skip("the fixture's market builds no gallery slip")
    board = {2: 3, 3: 6, 4: 10, 5: 20}
    for i in range(slips.count()):
        s = slips.nth(i)
        pct = float(s.locator(".tk-head b").inner_text().rstrip("%"))
        if s.locator(".tk-pays").count() == 0:   # a stack: the app quotes its payout
            assert "Type the app's payout" in s.locator(".tk-note").inner_text()
            assert s.locator(".tk-meter").count() == 0
            continue
        x = board[s.locator(".tk-leg").count()]
        assert s.locator(".tk-pays").inner_text() == f"{x}×"
        note = s.locator(".tk-note span[title]")
        assert note.count() == 1
        ratio = pct / 100 * x
        want = "Beats it" if ratio >= 1.25 else "Near" if ratio >= 1 else "Short"
        assert note.inner_text().endswith(f"{x}× needs {100 / x:.1f}% · {want}")
        tick = s.locator(".tk-meter u").evaluate("u => parseFloat(u.style.left)")
        assert abs(tick - min(100 / x / 50, 1) * 100) < 0.01
    assert page.evaluate("PROPS.filter(p => p.mkt === 'RECS' && udPick(p)).every(p => legHit(p) <= 57.3)")
    assert page.locator(".tk-grid").evaluate("() => GALLERIES.dk.length") == 0 or \
        page.evaluate("PARLAY_BOOK='dk'; render(); document.querySelectorAll('.ticket .tk-meter, .ticket .tk-note [title]').length") == 0, \
        "DraftKings slips carry no verdict: graded, the model's +EV overs lost"
    assert errors == []
    ctx.close()


def test_a_near_copy_slip_is_dropped(browser, page_file):
    """A slip of 3+ that shares all but one leg with a kept slip of its own kind is a copy
    (2026-09-25: Sunday morning's receptions slip reused 2 of the whole day's 3)."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    near = page.evaluate("""() => Object.values(GALLERIES).flatMap(g => g.flatMap((a, i) => g.slice(i + 1)
        .filter(b => a.scope === b.scope && a.scope !== 'stack' && b.legs.length >= 3 &&
          b.legs.filter(l => a.legs.includes(l)).length >= b.legs.length - 1)
        .map(b => [a.scope, a.legs, b.legs])))""")
    assert near == []
    assert errors == []
    ctx.close()


def test_the_typed_payout_decides_the_verdict(browser, page_file):
    """The sheet takes the multiplier the Underdog app quotes (2026-09-25): it starts at the
    standard board, the verdict follows what is typed without the field losing focus, and the
    number belongs to that slip only."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("SURFACE='parlay'; PARLAY_BOOK='underdog'; render()")
    if page.locator(".ticket").count() == 0:
        pytest.skip("the fixture's market builds no gallery slip")
    page.locator(".ticket .ticket-cta").first.click()
    page.locator("[data-tray]").click()
    n = page.evaluate("SLIP.length")
    box = page.locator("[data-bpay]")
    assert box.input_value() == str({2: 3, 3: 6, 4: 10, 5: 20}[n])
    box.fill("1.5")
    assert page.locator("[data-bpayv]").inner_text().startswith("Short of the 1.5× payout")
    assert page.evaluate("document.activeElement.hasAttribute('data-bpay')")
    box.fill("500")
    assert page.locator("[data-bpayv]").inner_text().startswith("Beats the 500× payout")
    page.evaluate("SLIP = SLIP.slice(0, -1)")
    assert page.evaluate("betsPayout(betsSlipLegs())") == {1: None, 2: 3, 3: 6, 4: 10}[n - 1], \
        "a changed slip goes back to the board"
    assert errors == []
    ctx.close()


def test_a_stack_counts_at_its_graded_joint_rate(browser, page_file):
    """A QB and his top two receivers, all lower, hit together 23.1% (ff-jarvis 12.32), not the
    product of three legs, and a stack gets no standard payout."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    got = page.evaluate("""(() => {
      const qb = PROPS.find(p => p.mkt === 'PASS' && isLower(p) && stackOf(p) && stackOf(p).every(isLower));
      if (!qb) return null;
      const s = stackOf(qb);
      return {chance: udChance(s), pay: betsPayout(s), inside: stackIn(s) !== null};
    })()""")
    if got is None:
        pytest.skip("the fixture has no all-lower stack")
    assert abs(got["chance"] - 0.231) < 1e-9
    assert got["pay"] is None and got["inside"]
    assert errors == []
    ctx.close()


def test_reduced_motion_never_marks_an_entrance(browser, page_file):
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("SURFACE='build'; render()")
    assert not page.evaluate("document.getElementById('view').classList.contains('enter')")
    page.locator(".pgrid .udline").first.click()
    assert page.locator(".udline.just").count() == 0
    assert errors == []
    ctx.close()


def test_slips_stack_and_load_into_the_tray(browser, page_file):
    """Slips stack down the page (no sideways rail), "Load slip" fills the tray with every leg, and
    the tray opens the sheet: one bar per leg, then the all-hit bar, then the slip itself."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    page.evaluate("SURFACE='parlay'; render()")
    if page.locator(".ticket").count() == 0:
        pytest.skip("the fixture's market builds no gallery slip")
    assert page.locator("#view .railscroll").count() == 0, "the slips no longer scroll sideways"
    assert columns(page, ".tk-grid") == 1
    legs = page.locator(".ticket").first.locator(".tk-leg").count()
    page.locator(".ticket .ticket-cta").first.click()
    assert page.evaluate("SLIP.length") == legs
    assert page.locator(".tray .tray-n").inner_text() == str(legs)
    page.locator("[data-tray]").click()
    assert page.locator(".slipsheet.on").count() == 1
    assert page.locator(".slipsheet .odds-row").count() == legs + 1
    assert page.locator(".slipsheet .slip .slipleg").count() == legs
    page.keyboard.press("Escape")
    page.wait_for_function("!BETS_SHEET")
    assert errors == []
    ctx.close()


def test_one_kickoff_for_both_views(browser, page_file):
    """Slips and Build share one kickoff: there is one select for it, and a choice made on Slips is
    the filter Build opens with."""
    ctx, page, errors = open_page(browser, page_file, (1280, 900))
    page.evaluate("SURFACE='parlay'; BETS_PANEL=true; render()")
    assert page.locator("[data-msel='gwin']").count() == 1
    assert page.locator("[data-msel='mwin']").count() == 0
    if page.evaluate("GAL_WINDOWS.length") == 0:
        pytest.skip("the fixture has no kickoff windows")
    k = page.evaluate("GAL_WINDOWS[0].k")
    page.locator("[data-msel='gwin']").select_option(k)
    page.evaluate("SURFACE='build'; render()")
    assert page.evaluate("buildLines().every(p => inWin(p, GAL_WINDOWS[0]))")
    assert errors == []
    ctx.close()
