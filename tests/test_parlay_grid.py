"""Bets (2026-09-25): Build as one column of lines; Slips as a research board (2026-10-03: per
kickoff, a card per game, its players by work rising, a tap opens every line he has); the slip as a
tray that counts what lands in it, saves it, and opens into a sheet; one kickoff for both views. A
new view's cards arrive once, and a tap that only adds a leg pops that line without replaying the
arrival of everything else.

The fixture's slate: CIN @ NYJ in the morning (Tee Higgins out, Chase Brown questionable, Burrow),
SEA @ SF on Sunday night (Kittle: TD, receiving yards, Longest reception; no game log), DET @ GB on
Monday night (St. Brown: TD, yards, Longest reception, with a log; Gibbs a depth-2 back whose
rushing line the book moved)."""
import re

import pytest

from test_render import SEED, open_page  # noqa: F401

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


def board(browser, page_file, win, size=(390, 844), book="underdog"):
    """Slips on one kickoff window ('morning', 'evening-sun', 'evening-mon' or a day)."""
    ctx, page, errors = open_page(browser, page_file, size)
    page.evaluate(f"SURFACE='parlay'; PARLAY_BOOK='{book}'; GAL_WIN='{win}'; render()")
    return ctx, page, errors


def names(page):
    return page.locator(".sl-row .sl-who b").all_inner_texts()


def idx(page, name, mkt):
    return page.evaluate(f"PROPS.findIndex(p => p.n === {name!r} && p.mkt === {mkt!r})")


def test_the_board_is_games_of_players_with_no_line_and_no_chance(browser, page_file):
    """A card per game at the kickoff; a row per player: name, position and club, his work, "N lines"
    -- and no line, no side and no model % (those wait in the player sheet; the row's one pick is a
    label, never a button)."""
    ctx, page, errors = board(browser, page_file, "day-2026-09-13")
    assert page.locator(".sl-game").count() == 2, "Sunday: CIN @ NYJ and SEA @ SF"
    assert page.locator(".sl-game h3").all_inner_texts() == ["CIN @ NYJ", "SEA @ SF"], "kickoff order"
    rows = page.locator(".sl-row")
    assert rows.count() > 0
    assert page.locator(".sl-row [data-slpick], .sl-row .sl-md").count() == 0
    for k in range(rows.count()):
        slug = rows.nth(k).get_attribute("data-slplayer")
        n = page.evaluate(f"slPlayerRows({slug!r}).length")
        assert rows.nth(k).locator(".sl-go").inner_text().startswith(f"{n} line"), slug
    assert "model" not in page.locator(".sl-board").inner_text()
    assert errors == []
    ctx.close()


def test_out_and_moved_lines_leave_the_board_and_a_backup_stays(browser, page_file):
    """Out (Higgins) and a moved line (Gibbs' rushing yards) leave; a questionable starter (Chase
    Brown) and a depth-2 back (Gibbs, on his touchdown line) stay -- David's wins were role players."""
    ctx, page, errors = board(browser, page_file, "morning")
    page.locator("[data-slchip='all']").first.click()
    assert "T. Higgins" not in names(page) and "C. Brown" in names(page)
    page.evaluate("GAL_WIN='evening-mon'; render()")
    page.locator("[data-slchip='all']").first.click()
    assert "J. Gibbs" in names(page)
    gibbs = page.evaluate("slPlayerRows('jahmyr-gibbs').map(i => PROPS[i].mkt)")
    assert gibbs == ["TD"], "his moved rushing line is not one of his lines"
    assert page.evaluate("slPlayerRows('amonra-st-brown').map(i => PROPS[i].mkt)") == ["TD", "REC"], "a LONG row is no line"
    page.locator("[data-slchip='role']").first.click()
    assert names(page) == ["J. Gibbs"], "Role guys: a WR2 or deeper, a backup back"
    page.locator("[data-slchip='te']").first.click()
    assert page.locator(".sl-row").count() == 0 and page.locator(".sl-none").count() == 1
    assert page.locator("[data-slchip='all']").first.inner_text() == "All 2"
    assert errors == []
    ctx.close()


def test_rising_work_comes_first_and_is_the_default(browser, page_file):
    """Work rising is the chip a game opens on when anyone's work rose (ff-jarvis's reason, else the
    log's usage); a game where nobody's did opens on All, never empty."""
    ctx, page, errors = board(browser, page_file, "evening-mon")
    rising = page.evaluate("slGames(slWin())[0].players.filter(slRising).map(x => x.slug)")
    chip = page.locator("[aria-pressed='true'][data-slchip]").first.get_attribute("data-slchip")
    assert chip == ("rise" if rising else "all")
    if rising:
        assert [r.get_attribute("data-slplayer") for r in page.locator(".sl-row").all()] == rising
        assert page.locator(".sl-row .sl-why").count() == 0, "no sentence under the work (2026-10-05)"
        assert page.locator(".sl-row .sl-spark i").count() >= 3
    assert errors == []
    ctx.close()


def test_the_player_sheet_holds_every_line_with_its_last_four(browser, page_file):
    """St. Brown's sheet: his touchdown (Yes) and receiving yards (Higher / Lower), each with his
    last four games against today's line; the touchdown "N% to score", the yards the model's tier
    (tests/test_prop_picks.py); then his longest catch in those
    games, history only (plan update 2026-10-03: no Longest reception line, so no sides, no count;
    the fixture's LONG prop rows are ignored, a game with no catch logged is a dash). Two legs from
    one sheet."""
    ctx, page, errors = board(browser, page_file, "evening-mon")
    page.evaluate("LIVE_MARKET.logs['amonra-st-brown'].v.LONG.splice(-1, 1, null); playerSheetOpen('amonra-st-brown')")
    sheet = page.locator("#legsheet.on")
    assert sheet.count() == 1 and page.evaluate("LEG_SHEET") == "amonra-st-brown"
    lines = sheet.locator(".sl-ln:not(.sl-long)")
    assert lines.count() == 2
    mk = sheet.locator(".sl-ln:not(.sl-long) .sl-mk").all_inner_texts()
    assert mk[0].startswith("Anytime TD") and mk[1].startswith(page.evaluate("MKT.REC"))
    assert lines.nth(0).locator(".sl-side").all_inner_texts() == ["Yes"]
    for k in range(2):
        hist = lines.nth(k).locator(".sl-hist")
        assert hist.locator("i").count() == 4 and hist.locator("em").count() == 0, "no N of 4 any more"
    assert sheet.locator(".sl-md").all_inner_texts() == ["28% to score"], "only the touchdown keeps a %"
    long = sheet.locator(".sl-long")
    assert long.count() == 1 and long.locator(".sl-mk").inner_text() == "Longest catch"
    assert long.locator(".sl-side, em, .sl-md, .sl-conf").count() == 0, "history only"
    cells = long.locator(".sl-hist i").all_inner_texts()
    assert len(cells) == 4 and cells[-1] == "–", "no catch logged reads as a dash"
    rec, tdi = idx(page, "Amon-Ra St. Brown", "REC"), idx(page, "Amon-Ra St. Brown", "TD")
    sheet.locator(f"[data-slpick='{rec}'][data-side='higher']").click()
    sheet.locator(f"[data-slpick='{tdi}'][data-side='higher']").click()
    assert page.evaluate("SLIP.map(i => [i, slipSide(i)])") == [[rec, "higher"], [tdi, "higher"]]
    assert page.locator("#legsheet.on").count() == 1, "the sheet stays up for the next leg"
    assert sheet.locator(f"[data-slpick='{rec}'][data-side='higher'][aria-pressed='true']").count() == 1
    sheet.locator(f"[data-slpick='{rec}'][data-side='lower']").click()
    assert page.evaluate(f"slipSide({rec})") == "lower" and page.evaluate("SLIP.length") == 2, "the other side swaps it"
    assert page.locator(".tray .tray-n").inner_text() == "2"
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")
    assert page.locator(".sl-row[data-slplayer='amonra-st-brown'] .sl-on").count() == 1
    assert errors == []
    ctx.close()


def test_a_board_row_opens_its_sheet_and_back_closes_it(browser, page_file):
    ctx, page, errors = board(browser, page_file, "evening-sun", (360, 780))
    before = page.evaluate("location.href")
    page.locator("[data-slchip='all']").first.click()
    page.locator(".sl-row[data-slplayer='george-kittle']").click()
    assert page.locator("#legsheet.on .sl-ln").count() == 2, "Kittle: TD and yards; no log, so no longest-catch row"
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.go_back()
    page.wait_for_function("LEG_SHEET === null")
    assert page.evaluate("location.href") == before and page.evaluate("SURFACE") == "parlay"
    assert errors == []
    ctx.close()


def test_a_saved_slip_survives_a_reload_and_marks_its_players(browser, page_file):
    """Save keeps the tray's slip on the device for the slate week; the same legs twice is one slip;
    a reload keeps it and its players carry "on slip"; a saved slip loads back with its sides; the
    x deletes it."""
    ctx, page, errors = board(browser, page_file, "evening-mon")
    rec = idx(page, "Amon-Ra St. Brown", "REC")
    page.evaluate("playerSheetOpen('amonra-st-brown')")
    page.locator(f"#legsheet [data-slpick='{rec}'][data-side='lower']").click()
    page.keyboard.press("Escape")
    page.wait_for_function("LEG_SHEET === null")
    page.locator("[data-slsave]").click()
    assert page.locator("[data-slsave]").is_disabled(), "saved: nothing new to save"
    key = page.evaluate("SAVED_KEY")
    assert key.startswith("tw.slips.saved.")
    assert len(page.evaluate(f"JSON.parse(localStorage.getItem({key!r}))")) == 1
    page.reload()
    page.evaluate("SURFACE='parlay'; GAL_WIN='evening-mon'; render()")
    assert page.evaluate("SLIP.length") == 0 and page.evaluate("SAVED.length") == 1
    assert page.locator(".sl-row[data-slplayer='amonra-st-brown'] .sl-on").count() == 1
    page.locator("[data-tray]").click()
    assert page.locator(".slipsheet .sv-row").count() == 1
    page.locator(".sv-load").click()
    assert page.evaluate("SLIP.map(i => [i, slipSide(i)])") == [[rec, "lower"]]
    assert page.locator(".slipsheet.on .slipleg").count() == 1, "the sheet stays up, the slip in it"
    page.locator(".sv-drop").click()
    assert page.evaluate("SAVED.length") == 0 and page.locator(".slipsheet .sv-row").count() == 0
    assert errors == []
    ctx.close()


def test_a_slip_with_longest_reception_has_no_chance_and_copies(browser, page_file):
    """A LONG prop row is tolerated though never offered (Build can still add one from the fixture):
    with no model chance, a slip holding it prints none rather than a wrong one, and its copied text
    names the side and Underdog's line."""
    ctx, page, errors = board(browser, page_file, "evening-mon")
    long, rec = idx(page, "Amon-Ra St. Brown", "LONG"), idx(page, "Amon-Ra St. Brown", "REC")
    page.evaluate(f"slipSet({rec}, 'higher'); slipSet({long}, 'higher'); render()")
    assert page.evaluate("betsSlipPct()") is None
    page.locator("[data-tray]").click()
    assert page.locator(".slipsheet .odds-row").count() == 0
    assert page.locator(".slipsheet .slipleg").count() == 2
    text = page.evaluate("slipText()")
    assert "Amon-Ra St. Brown Higher 28.5 Longest rec" in text and "Amon-Ra St. Brown Higher 75.5" in text
    assert errors == []
    ctx.close()


def test_the_board_fits_a_phone_and_spreads_on_a_desktop(browser, page_file):
    """360px: nothing scrolls sideways and the first player sits on the first screen. 1280px: the
    day's two games side by side, sharing a top edge."""
    ctx, page, errors = board(browser, page_file, "day-2026-09-13", (360, 800))
    assert page.evaluate("document.documentElement.scrollWidth") <= 360
    y = page.evaluate("document.querySelector('.sl-row').getBoundingClientRect().top")
    assert y < 800, f"first row at {y}px"
    ctx.close()
    ctx, page, errors = board(browser, page_file, "day-2026-09-13", (1280, 900))
    a, b = (page.locator(".sl-game").nth(k).bounding_box() for k in (0, 1))
    assert abs(a["y"] - b["y"]) < 1 and b["x"] > a["x"] + a["width"]
    assert columns(page, ".sl-board") >= 2
    assert errors == []
    ctx.close()


def test_the_kickoff_tabs_pick_what_the_board_shows(browser, page_file):
    """Slips' kickoff is its row of tabs (a whole day by its weekday, then its parts); a tab shows
    that kickoff's games, and Build opens with it."""
    ctx, page, errors = open_page(browser, page_file, (360, 800))
    page.evaluate("SURFACE='parlay'; render()")
    tabs = page.locator(".bets-tabsrow [data-gwin]")
    if tabs.count() == 0:
        pytest.skip("the fixture has no kickoff windows")
    assert tabs.all_inner_texts() == page.evaluate("KICK_CHIPS.map(kickChipLabel)")
    k = tabs.nth(1).get_attribute("data-gwin")
    tabs.nth(1).click()
    assert page.evaluate("GAL_WIN") == k and page.evaluate("slWin().k") == k
    games = page.evaluate("slGames(slWin()).map(g => g.game)")
    assert page.locator(".sl-game h3").all_inner_texts() == games
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
    ctx, page, errors = board(browser, page_file, "morning")
    page.evaluate("""PROPS.map((p, i) => [p, i]).filter(([p]) => udPick(p) && !udPick(p).synthetic && p.flag !== 'out' && p.mkt !== 'PASS')
      .slice(0, 3).forEach(([p, i]) => slipSet(i, udPick(p).pick)); render()""")
    n = page.evaluate("SLIP.length")
    assert n == 3
    page.locator("[data-tray]").click()
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


def test_a_leg_counts_at_the_graded_rate_of_its_side(browser, page_file):
    """A higher pick counts at most 42.3% (ff-jarvis 12.51), a lower at most 56.3% (57.3% at the
    model's own lower at 65%+); a pick against the model's call at what the model leaves for it."""
    ctx, page, errors = board(browser, page_file, "morning")
    got = page.evaluate("""(() => {
      const i = PROPS.findIndex(p => udPick(p) && !udPick(p).synthetic && p.mkt !== 'TD');
      const u = udPick(PROPS[i]);
      slipSet(i, 'higher'); const hi = legHit(PROPS[i]);
      slipSet(i, 'lower'); const lo = legHit(PROPS[i]);
      return {hi, lo, conf: u.conf, pick: u.pick};
    })()""")
    conf_hi = got["conf"] if got["pick"] == "higher" else 100 - got["conf"]
    assert got["hi"] == min(conf_hi, 42.3) and got["lo"] == min(100 - conf_hi, 56.3)
    assert page.evaluate("legHit(PROPS.find(p => p.mkt === 'LONG'))") is None
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


def test_a_saved_slip_loads_into_the_sheet(browser, page_file):
    """A saved slip fills the tray with every leg at its side, and the tray opens the sheet: one bar
    per leg, then the all-hit bar, then the slip itself, then the saved list."""
    ctx, page, errors = board(browser, page_file, "morning")
    page.evaluate("PROPS.forEach((p, i) => { const u = udPick(p); if (u && !u.synthetic && p.flag !== 'out') slipSet(i, 'higher'); }); render()")
    legs = page.evaluate("SLIP.length")
    page.locator("[data-slsave]").click()
    page.evaluate("SLIP = []; SLIP_SIDE = {}; render()")
    page.locator("[data-tray]").click()
    page.locator(".sv-load").first.click()
    assert page.evaluate("SLIP.length") == legs and page.evaluate("SLIP.every(i => slipSide(i) === 'higher')")
    assert page.locator(".slipsheet.on").count() == 1
    assert page.locator(".slipsheet .odds-row").count() == legs + 1
    assert page.locator(".slipsheet .slip .slipleg").count() == legs
    page.keyboard.press("Escape")
    page.wait_for_function("!BETS_SHEET")
    assert errors == []
    ctx.close()
