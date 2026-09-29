"""Bets (2026-09-25): Build as one column of lines; Slips as a deal table (2026-09-29: deal a slip
of a kind and length from the kickoff's pool, lock picks, keep slips); the slip as a tray that
counts what lands in it and opens into a sheet; one kickoff for both views. A new view's cards arrive once, and a tap that only adds a leg pops that line without
replaying the arrival of everything else."""
import re

import pytest

from test_render import OPEN_POOL, SEED, browser, open_page  # noqa: F401  (browser is a fixture)

pytestmark = pytest.mark.render


def columns(page, sel):
    return len(page.evaluate(f"getComputedStyle(document.querySelector('{sel}')).gridTemplateColumns").split())


@pytest.mark.parametrize("book", ["underdog", "dk"])
def test_build_is_one_column_of_lines_that_fits_a_phone(browser, page_file, book):
    """Build (2026-09-29): one column under a heading per kickoff, a row per line -- the line, his
    games against it, the call. At 360px the six chips and every row stay on screen; the line and
    its bars open the leg sheet, the call adds the pick."""
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate(f"SURFACE='build'; PARLAY_BOOK='{book}'; MKT_PAGE=1; render()")
    assert page.locator(".blist .bplayer").count() > 0
    right = page.evaluate("Math.max(...[...document.querySelectorAll('.bets-bar > *, .bline')].map(e => e.getBoundingClientRect().right))")
    assert right <= 360
    assert page.locator(".bets-bar > *").count() <= 6, "STYLE.md: up to ~6 siblings in the row"
    lefts = page.evaluate("[...document.querySelectorAll('.bline .bl-call')].map(e => Math.round(e.getBoundingClientRect().left))")
    assert len(set(lefts)) == 1, "every call sits in one column"
    page.locator(".bline[data-prop] .bl-ev").first.click()
    assert page.locator("#legsheet.on").count() == 1 and page.evaluate("SLIP.length") == 0
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")
    page.locator(".bline[data-prop] .bl-call").first.click()
    assert page.evaluate("SLIP.length") == 1
    assert errors == []
    ctx.close()


def test_a_moved_line_shows_no_chance_and_sorts_last(browser, page_file):
    """A line the book moved far from the model (build.py `stale`) shows "Line moved", no chance,
    and adds nothing on a tap: on 2026-09-29 every Underdog pick at 80%+ was one."""
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate("""SURFACE='build'; PARLAY_BOOK='underdog'; MKT_SORT='conf'; MKT_PAGE=1;
      const p = PROPS.filter(p => udPick(p) && !udPick(p).synthetic).sort(SORTS.conf)[0];
      p.books.Underdog.stale = 1; window._moved = PROPS.indexOf(p); render()""")
    i = page.evaluate("_moved")
    lines = page.evaluate("buildLines().map(p => PROPS.indexOf(p))")
    assert lines.index(i) > 0 and all(page.evaluate(f"lineMoved(PROPS[{j}], 'underdog')") for j in lines[lines.index(i):]), \
        "the top of the confidence sort sinks below every unmoved line"
    page.evaluate("buildLines = () => [PROPS[_moved]]; render()")
    row = page.locator(".bline")
    assert row.count() == 1 and "moved" in row.get_attribute("class")
    assert "%" not in row.inner_text() and row.get_attribute("data-prop") is None
    row.locator(".bl-call").click()
    assert page.evaluate("LEG_SHEET") == i and page.evaluate("SLIP.length") == 0
    assert errors == []
    ctx.close()


@pytest.mark.parametrize("book", ["underdog", "dk"])
def test_best_odds_keeps_only_lines_that_pay_more(browser, page_file, book):
    """Best odds (2026-09-29): Underdog keeps a pick paying better than its -107 on the model's
    side, or at a line easier than DraftKings'; DraftKings keeps an over easier than the
    BettingPros consensus. Each kept row prints why."""
    ctx, page, errors = open_page(browser, page_file, (360, 780))
    page.evaluate(f"SURFACE='build'; PARLAY_BOOK='{book}'; MKT_BEST=true; MKT_PAGE=1; render()")
    kept = page.evaluate(f"""buildLines().map(p => {{
      const u = p.books && p.books.Underdog, d = p.books && p.books.DraftKings, r = p.ref;
      if ('{book}' === 'underdog') {{
        const lo = u.pick === 'lower', price = lo ? u.under : u.over;
        return !u.stale && (price > -107 || (d && d.line != null && (lo ? u.line > d.line : u.line < d.line)));
      }}
      return !p.stale && !!r && (d.line < r.line || (d.line === r.line && d.over > r.over));
    }})""")
    assert all(kept)
    everyone = page.evaluate("(MKT_BEST=false, buildLines().length)")
    assert len(kept) < everyone
    page.evaluate("MKT_BEST=true; render()")
    if kept:
        assert page.locator(".bline").count() == page.locator(".bline .bl-ln em").count(), "every kept row says why"
    else:
        assert page.locator(".state-empty").count() == 1
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
    page.locator(".bline[data-prop] .bl-call").first.click()
    assert not page.evaluate("document.getElementById('view').classList.contains('enter')")
    assert page.locator(".bline.just").count() == 1
    assert page.locator(".slip .sliphead .pill.bump").count() == 1
    page.wait_for_function("document.querySelector('.tray .tray-n').textContent === '1'")
    assert errors == []
    ctx.close()



def slips(browser, page_file, size=(390, 844), book="underdog"):
    ctx, page, errors = open_page(browser, page_file, size)
    page.evaluate(f"SURFACE='parlay'; PARLAY_BOOK='{book}'; GAL_WIN='ALL'; render()")
    page.evaluate(OPEN_POOL)
    return ctx, page, errors


def dealt(page):
    return page.evaluate("TABLE.legs.slice()")


def test_the_pool_holds_tds_at_30_and_yards_called_lower_at_58(browser, page_file):
    """David's floors (2026-09-29): an anytime TD at 30%+ P(score); a yards or receptions leg at
    Underdog's own line, called lower at 58%+ (higher picks graded 42.3%), receptions at 2.5+. Each
    fixture pick is tried as a starter with 8 games, before its kickoff."""
    ctx, page, errors = open_page(browser, page_file, (390, 844))
    bad = page.evaluate("""PROPS.map(p => ({...p, flag: null, stale: false, moved: false, games: 10})).filter(p => udPick(p)).filter(p => {
      const u = udPick(p), td = p.mkt === 'TD';
      const want = {td: td && u.conf >= 30,
                    safe: !td && !u.synthetic && !u.stale && u.pick === 'lower' && u.conf >= 58 && (p.mkt !== 'RECS' || u.line >= 2.5)};
      return ['td', 'safe'].some(k => tableLegOK(p, k, 'underdog') !== want[k]) || tableLegOK(p, 'mix', 'underdog') !== (want.td || want.safe);
    }).map(p => p.n + ' ' + p.mkt)""")
    assert bad == []
    assert page.evaluate("PROPS.filter(p => tableLegOK({...p, flag: 'backup'}, 'mix', 'underdog')).length") == 0, "a backup is news, not a pick"
    assert errors == []
    ctx.close()


def test_a_deal_is_the_kind_and_length_asked_for(browser, page_file):
    """TDs deals only TDs, Safe only yards, Mix splits them (the TDs rounding down); the length
    runs 3 to 6; never two legs of one player; a game of its own for each leg while games last."""
    ctx, page, errors = slips(browser, page_file)
    kinds = page.evaluate("PROPS.map(p => p.mkt === 'TD')")
    for kind in ("td", "safe", "mix"):
        page.click(f"[data-tkind='{kind}']")
        for n in (3, 4, 5, 6):
            page.click(f"[data-tlegs='{n}']")
            legs, pool = dealt(page), page.evaluate(f"tablePool('{kind}')")
            assert len(legs) == min(n, len({page.evaluate(f'PROPS[{i}].n') for i in pool})), (kind, n)
            assert set(legs) <= set(pool)
            assert len({page.evaluate(f"PROPS[{i}].n") for i in legs}) == len(legs), "one leg per player"
            if kind == "td":
                assert all(kinds[i] for i in legs)
            if kind == "safe":
                assert not any(kinds[i] for i in legs)
            if kind == "mix":
                # Half TDs, rounding down, unless a player's TD and yards legs compete for his one seat.
                tds = sum(kinds[i] for i in legs)
                assert tds <= n // 2 or len(legs) - tds < n - n // 2, "mix: half TDs, rounding down"
            assert page.locator(".dt-slip .tk-leg").count() == len(legs)
    assert errors == []
    ctx.close()


def test_a_locked_pick_stays_through_a_deal(browser, page_file):
    """A lock keeps a pick on the slip through Deal again; a pool pick tapped locks it onto the
    slip in a free leg's place; its lock does not open the leg sheet."""
    ctx, page, errors = slips(browser, page_file)
    page.click("[data-tkind='mix']")
    page.click("[data-tlegs='3']")
    first = dealt(page)[0]
    page.click(f".dt-slip [data-tlock='{first}']")
    assert page.evaluate("LEG_SHEET") is None, "the lock is not the row"
    assert page.locator(f".dt-slip [data-tlock='{first}'][aria-pressed='true']").count() == 1
    for _ in range(3):
        page.click("[data-tdeal]")
        assert first in dealt(page)
    off = page.evaluate("tablePool('mix').find(i => !TABLE.legs.includes(i) && PROPS[i].n !== PROPS[TABLE.locks[0]].n)")
    if off is None:
        pytest.skip("the fixture pool has no pick off the slip")
    page.click(f".dt-pick[data-tpool='{off}']")
    legs = dealt(page)
    assert off in legs and first in legs and len(legs) == 3
    assert page.locator(f".dt-pick[data-tpool='{off}'][aria-pressed='true']").count() == 1
    assert errors == []
    ctx.close()


def test_the_stub_says_one_in_n_and_what_the_payout_needs(browser, page_file):
    """The headline is "1 in N" of the graded chance (a 3% slip reads as zero in percent); the note
    names Underdog's board and whether the slip beats it."""
    ctx, page, errors = slips(browser, page_file)
    page.click("[data-tkind='safe']")
    page.click("[data-tlegs='3']")
    p = page.evaluate("udChance(TABLE.legs.map(i => PROPS[i]))")
    n = len(dealt(page))
    assert page.locator(".dt-slip .tk-head b").inner_text() == f"1 in {max(1, round(1 / p))}"
    x = {2: 3, 3: 6, 4: 10, 5: 20}[n]
    want = "Beats it" if p * x >= 1.25 else "Near" if p * x >= 1 else "Short"
    assert page.locator(".dt-slip .tk-note").inner_text() == f"Pays {x}x · needs 1 in {x} · {want}"
    assert page.evaluate("PROPS.filter(p => p.mkt === 'RECS' && udPick(p)).every(p => legHit(p) <= 57.3)")
    assert errors == []
    ctx.close()


def test_kept_slips_list_load_and_survive_a_reload(browser, page_file):
    """Keep adds the slip to Kept once; a kept slip loads into the tray, counted; the list is
    stored on the device for the slate week, so a reload keeps it; the x drops it."""
    ctx, page, errors = slips(browser, page_file)
    page.click("[data-tlegs='3']")
    legs = dealt(page)
    assert page.locator(".dt-kept-row").count() == 0
    page.click("[data-tkeep]")
    page.click("[data-tkeep]")
    assert page.locator(".dt-kept-row").count() == 1, "the same legs twice is one slip"
    page.click("[data-tkind='safe']")
    page.click("[data-tkeep]")
    assert page.locator(".dt-kept-row").count() == 2
    page.locator(".dt-kept-load").nth(1).click()
    assert sorted(page.evaluate("SLIP")) == sorted(legs), "newest first: the TD slip is second"
    page.wait_for_function(f"document.querySelector('.tray .tray-n').textContent === '{len(legs)}'")
    page.reload()
    page.evaluate("SURFACE='parlay'; render()")
    assert page.locator(".dt-kept-row").count() == 2, "kept slips live on the device"
    page.locator(".dt-kept-drop").first.click()
    assert page.locator(".dt-kept-row").count() == 1
    assert errors == []
    ctx.close()


def test_a_slip_pick_is_a_sentence_and_opens_its_sheet(browser, page_file):
    """A pick is two lines -- his face on his team's colour, his name, the call in sentence case --
    and a tap opens its leg sheet."""
    ctx, page, errors = slips(browser, page_file)
    leg = page.locator(".dt-slip .tk-leg").first
    assert leg.locator(".tk-face img, .tk-face .fallback").count() == 1, "every leg carries his photo"
    call = leg.locator(".tk-call").inner_text()
    assert call != call.upper(), "the call is sentence case, not capitals"
    i = int(leg.get_attribute("data-legsheet"))
    leg.locator(".tk-who").click()
    assert page.evaluate("LEG_SHEET") == i
    assert errors == []
    ctx.close()


def test_the_table_fits_a_phone_and_sits_beside_kept_on_a_desktop(browser, page_file):
    """On a phone the slip, then the pool, one column; an empty Kept hides. On a desktop the slip
    and Kept share a row and the pool runs under both, two picks across."""
    ctx, page, errors = slips(browser, page_file, (360, 800))
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    assert page.locator(".dt-kept").is_hidden()
    ctx.close()
    ctx, page, errors = slips(browser, page_file, (1280, 900))
    slip = page.locator(".dt-slip").bounding_box()
    kept = page.locator(".dt-kept").bounding_box()
    pool = page.locator(".dt-pool")
    assert abs(slip["y"] - kept["y"]) < 1 and kept["x"] > slip["x"] + slip["width"]
    if pool.count():
        assert pool.bounding_box()["y"] >= slip["y"] + slip["height"]
        assert columns(page, ".dt-picks") == 2
    assert errors == []
    ctx.close()


def test_the_kickoff_tabs_pick_what_the_table_deals_from(browser, page_file):
    """Slips' kickoff is its row of tabs (a whole day by its weekday, then its parts); a tab deals
    for that kickoff, and Build opens with it."""
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    page.evaluate("SURFACE='parlay'; render()")
    tabs = page.locator(".bets-tabsrow [data-gwin]")
    if tabs.count() == 0:
        pytest.skip("the fixture has no kickoff windows")
    assert tabs.all_inner_texts() == page.evaluate("KICK_CHIPS.map(kickChipLabel)")
    k = tabs.nth(1).get_attribute("data-gwin")
    tabs.nth(1).click()
    assert page.evaluate("GAL_WIN") == k and page.evaluate("TABLE.sig").split("|")[1] == k
    assert page.locator(f".bets-tabsrow [data-gwin='{k}'][aria-selected='true']").count() == 1
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    page.evaluate("SURFACE='build'; BETS_PANEL=true; render()")
    assert page.locator("[data-msel='gwin']").input_value() == k
    assert errors == []
    ctx.close()


def test_the_typed_payout_decides_the_verdict(browser, page_file):
    """The sheet takes the multiplier the Underdog app quotes (2026-09-25): it starts at the
    standard board, the verdict follows what is typed without the field losing focus, and the
    number belongs to that slip only."""
    ctx, page, errors = slips(browser, page_file)
    page.click("[data-tlegs='3']")
    page.click("[data-tkeep]")
    page.locator(".dt-kept-load").first.click()
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
    page.locator(".bline[data-prop] .bl-call").first.click()
    assert page.locator(".bline.just").count() == 0
    assert errors == []
    ctx.close()


def test_a_loaded_slip_opens_into_the_sheet(browser, page_file):
    """A kept slip fills the tray with every leg, and the tray opens the sheet: one bar per leg,
    then the all-hit bar, then the slip itself."""
    ctx, page, errors = slips(browser, page_file)
    page.click("[data-tlegs='4']")
    legs = len(dealt(page))
    page.click("[data-tkeep]")
    page.locator(".dt-kept-load").first.click()
    assert page.evaluate("SLIP.length") == legs
    page.locator("[data-tray]").click()
    assert page.locator(".slipsheet.on").count() == 1
    assert page.locator(".slipsheet .odds-row").count() == legs + 1
    assert page.locator(".slipsheet .slip .slipleg").count() == legs
    page.keyboard.press("Escape")
    page.wait_for_function("!BETS_SHEET")
    assert errors == []
    ctx.close()


