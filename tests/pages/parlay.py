"""Bets (design/src/js/surface/parlay/): Slips, the research board; the tray and the slip sheet, which
both views fill; the Slips player sheet. Build, the line market, is tests/pages/parlay_build.py
(BuildPage extends ParlayPage, so it shares everything here).

Every Slips, tray and sheet locator lives here, data-testid first (`parlay-*`, test hooks only). Three
things have no hook of their own, so they are found by id or class: the leg sheet (`#legsheet`, static
markup in shell.html, outside every view), the Slips tab row a phone draws in the nav chrome
(`#subnav`), and the classes a state wears (`.on`, `.all`).

State a test needs that a tap cannot reach (which kickoff, which book) is set through the page's own
globals, in a method named for what it does; the page redraws as it would.
"""
from component import DRAWN
from test_render import LOAD_MS


GRADED = """() => {
  const i = PROPS.findIndex(p => udPick(p) && !udPick(p).synthetic && p.mkt !== 'TD');
  const u = udPick(PROPS[i]);
  slipSet(i, 'higher'); const hi = legHit(PROPS[i]);
  slipSet(i, 'lower'); const lo = legHit(PROPS[i]);
  return {hi, lo, conf: u.conf, pick: u.pick};
}"""

# the fixture holds no QB whose top two receivers are all on the lower side: plant one game
STACK = """() => {
  const ud = (line, conf) => ({books: {Underdog: {line, pick: 'lower', conf}}});
  const at = {team: 'ZZZ', game: 'ZZZ @ YYY', n: 'Planted', slug: 'planted'};
  PROPS.push({...at, pos: 'QB', mkt: 'PASS', ...ud(230.5, 60)},
             {...at, pos: 'WR', mkt: 'REC', ...ud(70.5, 60)},
             {...at, pos: 'WR', mkt: 'REC', ...ud(55.5, 60)});
  const qb = PROPS.find(p => p.mkt === 'PASS' && isLower(p) && stackOf(p) && stackOf(p).every(isLower));
  if (!qb) return null;
  const s = stackOf(qb);
  return {chance: udChance(s), pay: betsPayout(s), inside: stackIn(s) !== null};
}"""

SHEET_LINE = """ls => ls.map(l => ({
  market: l.querySelector('[data-testid="parlay-line-market"]').innerText,
  sides: [...l.querySelectorAll('[data-testid="parlay-side"]')].map(s => s.innerText),
  cells: l.querySelectorAll('[data-testid="parlay-hist-cell"]').length,
  notes: l.querySelectorAll('[data-testid="parlay-hist"] em').length}))"""

LONG_EXTRAS = ("l => l.querySelectorAll('[data-testid=\"parlay-side\"], [data-testid=\"parlay-model-pct\"], "
               "[data-testid=\"parlay-tier\"], em').length")


class ParlayPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._kick_tabs, self._kick_tab = tid("parlay-kick-tabs"), tid("parlay-kick-tab")
        self._games, self._titles, self._board = tid("parlay-game"), tid("parlay-game-title"), tid("parlay-board")
        self._rows, self._names, self._chips = tid("parlay-row"), tid("parlay-row-name"), tid("parlay-chip")
        self._none, self._bars = tid("parlay-none"), tid("parlay-spark-bar")
        self._tray, self._tray_open, self._count = tid("parlay-tray"), tid("parlay-tray-open"), tid("parlay-tray-count")
        self._save, self._slipsheet = tid("parlay-tray-save"), tid("parlay-slipsheet")
        self._pay, self._verdict = tid("parlay-pay-input"), tid("parlay-pay-verdict")
        self._sheet = page.locator("#legsheet")        # static markup in shell.html: no hook to put one on

    # ---- opening it ----

    @classmethod
    def slips(cls, mount, win, size=(390, 844), book="underdog"):
        """Slips on one kickoff window ('morning', 'evening-sun', 'evening-mon' or a day). (ParlayPage, errors)."""
        page, errors = mount("parlay", size=size)
        board = cls(page)
        board.show_slips(win, book)
        return board, errors

    def show_slips(self, win, book="underdog"):
        self.page.evaluate("([w, b]) => { SURFACE = 'parlay'; PARLAY_BOOK = b; GAL_WIN = w; render(); }", [win, book])

    def show_window(self, win):
        self.page.evaluate("w => { GAL_WIN = w; render(); }", win)

    def reload(self):
        """A reader reloads the tab: the page draws again, and what it keeps on the device comes back."""
        self.page.reload(timeout=LOAD_MS)
        self.page.wait_for_function(DRAWN, timeout=LOAD_MS)

    # ---- Slips: what a reader does ----

    def tap_chip(self, kind):
        """A chip on the first game's card: 'rise', 'te', 'role' or 'all'."""
        self._chips.and_(self.page.locator(f"[data-slchip='{kind}']")).first.click()

    def tap_row(self, slug):
        self._row(slug).click()

    def open_player_sheet(self, slug):
        self.page.evaluate("s => playerSheetOpen(s)", slug)

    def plant_no_catch_in_last_game(self, slug):
        """His last game has no catch logged (a null in the log's Longest reception)."""
        self.page.evaluate("s => LIVE_MARKET.logs[s].v.LONG.splice(-1, 1, null)", slug)

    def pick_in_sheet(self, i, side):
        self._sheet.get_by_test_id("parlay-side").and_(
            self.page.locator(f"[data-slpick='{i}'][data-side='{side}']")).click()

    def close_sheet(self):
        """Escape, then wait for the leg or player sheet to leave."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_function("LEG_SHEET === null")

    def go_back(self):
        """The phone's Back: it closes the sheet before it changes the view."""
        self.page.go_back()
        self.page.wait_for_function("LEG_SHEET === null")

    # ---- Slips: what a reader sees ----

    def game_count(self):
        return self._games.count()

    def game_titles(self):
        return self._titles.all_inner_texts()

    def row_count(self):
        return self._rows.count()

    def row_summaries(self):
        """Each player row in order: his slug and what its right edge says ('3 lines')."""
        return self._rows.evaluate_all("""rs => rs.map(r => ({slug: r.dataset.slplayer,
          go: r.querySelector('[data-testid="parlay-row-go"]').innerText}))""")

    def row_slugs(self):
        return self._rows.evaluate_all("rs => rs.map(r => r.dataset.slplayer)")

    def row_names(self):
        return self._names.all_inner_texts()

    def row_controls(self):
        """Pick buttons and model percentages drawn inside the rows: none, they wait in the player sheet."""
        return self._rows.locator("[data-slpick]").count() + self._rows.get_by_test_id("parlay-model-pct").count()

    def row_sentences(self):
        """A sentence under a player's work (retired 2026-10-05)."""
        return self._rows.locator(".sl-why").count()

    def spark_bars(self):
        return self._bars.count()

    def board_text(self):
        return self._board.inner_text()

    def none_notes(self):
        return self._none.count()

    def chip_text(self, kind):
        return self._chips.and_(self.page.locator(f"[data-slchip='{kind}']")).first.inner_text()

    def pressed_chip(self):
        return self._chips.and_(self.page.locator("[aria-pressed='true']")).first.get_attribute("data-slchip")

    def chip_kinds(self):
        """The first game card's chips, left to right."""
        return self._games.first.get_by_test_id("parlay-chip").evaluate_all("cs => cs.map(c => c.dataset.slchip)")

    def rising_bars(self):
        """Last bars drawn in the green of a rise (retired 2026-10-06)."""
        return self.page.locator(".sl-spark > span.up").count()

    def line_count_of(self, slug):
        """How many lines the model has for the player: what his row should say."""
        return self.page.evaluate("s => slPlayerRows(s).length", slug)

    def markets_of(self, slug):
        return self.page.evaluate("s => slPlayerRows(s).map(i => PROPS[i].mkt)", slug)

    def props_index(self, name, mkt):
        return self.page.evaluate("([n, m]) => PROPS.findIndex(p => p.n === n && p.mkt === m)", [name, mkt])

    def market_word(self, mkt):
        return self.page.evaluate("m => MKT[m]", mkt)

    def row_on_slip(self, slug):
        return self._row(slug).get_by_test_id("parlay-row-on").count()

    def scroll_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")

    def fits(self):
        """Nothing wider than the screen."""
        return self.page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    def first_row_top(self):
        return self._rows.first.evaluate("e => e.getBoundingClientRect().top")

    def game_box(self, k):
        return self._games.nth(k).bounding_box()

    def board_columns(self):
        return self._board.evaluate("e => getComputedStyle(e).gridTemplateColumns.trim().split(/\\s+/).length")

    def surface(self):
        return self.page.evaluate("SURFACE")

    def href(self):
        return self.page.evaluate("location.href")

    # ---- the leg sheet (a player's on Slips, or one Build line's) ----

    def sheet_open(self):
        return self.page.locator("#legsheet.on").count() == 1

    def sheet_key(self):
        """What the sheet is about: a player's slug, a PROPS index, or None when it is closed."""
        return self.page.evaluate("LEG_SHEET")

    def sheet_lines(self):
        """The player sheet's lines (not Longest catch): market, side buttons, last-four cells, 'N of 4' notes."""
        return self._sheet.get_by_test_id("parlay-line-item").evaluate_all(SHEET_LINE)

    def sheet_all_line_count(self):
        """Every row of lines in the sheet, Longest catch included."""
        return (self._sheet.get_by_test_id("parlay-line-item").count()
                + self._sheet.get_by_test_id("parlay-long").count())

    def sheet_model_pcts(self):
        return self._sheet.get_by_test_id("parlay-model-pct").all_inner_texts()

    def sheet_longest(self):
        """The Longest catch row: how many there are, and when one, its words, extras and cells."""
        long = self._sheet.get_by_test_id("parlay-long")
        if long.count() != 1:
            return {"count": long.count()}
        return {"count": 1, "market": long.get_by_test_id("parlay-line-market").inner_text(),
                "extras": long.evaluate(LONG_EXTRAS),
                "cells": long.get_by_test_id("parlay-hist-cell").all_inner_texts()}

    def side_pressed(self, i, side):
        return self._sheet.get_by_test_id("parlay-side").and_(
            self.page.locator(f"[data-slpick='{i}'][data-side='{side}'][aria-pressed='true']")).count()

    # ---- the slip and the tray ----

    def slip(self):
        """The slip in order: [PROPS index, side]."""
        return self.page.evaluate("SLIP.map(i => [i, slipSide(i)])")

    def slip_size(self):
        return self.page.evaluate("SLIP.length")

    def slip_side(self, i):
        return self.page.evaluate("i => slipSide(i)", i)

    def slip_all_on(self, side):
        return self.page.evaluate("s => SLIP.every(i => slipSide(i) === s)", side)

    def put_on_slip(self, legs):
        """[(PROPS index, side), ...] onto the slip, as taps would."""
        self.page.evaluate("legs => { legs.forEach(([i, s]) => slipSet(i, s)); render(); }", legs)

    def put_first_picks_on_slip(self, n):
        """The first n Underdog lines the model prices (no Out player, no passing yards), each at its own side."""
        self.page.evaluate("""n => { PROPS.map((p, i) => [p, i])
          .filter(([p]) => udPick(p) && !udPick(p).synthetic && p.flag !== 'out' && p.mkt !== 'PASS')
          .slice(0, n).forEach(([p, i]) => slipSet(i, udPick(p).pick)); render(); }""", n)

    def put_every_pick_on_slip(self, side):
        self.page.evaluate("""s => { PROPS.forEach((p, i) => { const u = udPick(p);
          if (u && !u.synthetic && p.flag !== 'out') slipSet(i, s); }); render(); }""", side)

    def clear_slip(self):
        self.page.evaluate("() => { SLIP = []; SLIP_SIDE = {}; render(); }")

    def drop_last_leg(self):
        self.page.evaluate("() => { SLIP = SLIP.slice(0, -1); }")

    def slip_chance(self):
        return self.page.evaluate("betsSlipPct()")

    def slip_text(self):
        """What Copy puts on the clipboard."""
        return self.page.evaluate("slipText()")

    def tray_count(self):
        return self._count.inner_text()

    def tray_drawn(self):
        """How many slip trays are drawn: one once a pick is in the slip, wherever it was picked."""
        return self._tray.count()

    def open_tray(self):
        self._tray_open.click()

    def close_slip_sheet(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_function("!BETS_SHEET")

    def save_slip(self):
        self._save.click()

    def save_disabled(self):
        return self._save.is_disabled()

    def saved_key(self):
        return self.page.evaluate("SAVED_KEY")

    def saved_on_device(self, key):
        """How many slips the device holds under `key`."""
        return self.page.evaluate("k => JSON.parse(localStorage.getItem(k)).length", key)

    def saved_count(self):
        return self.page.evaluate("SAVED.length")

    def saved_rows(self):
        return self._slipsheet.get_by_test_id("parlay-saved-row").count()

    def load_saved(self):
        self._slipsheet.get_by_test_id("parlay-saved-load").first.click()

    def drop_saved(self):
        self._slipsheet.get_by_test_id("parlay-saved-drop").first.click()

    def slip_sheet_open(self):
        return self._slipsheet.and_(self.page.locator(".on")).count()

    def slip_legs_in_open_sheet(self):
        return self._slipsheet.and_(self.page.locator(".on")).get_by_test_id("parlay-slip-leg").count()

    def sheet_odds_rows(self):
        return self._slipsheet.get_by_test_id("parlay-odds-row").count()

    def sheet_all_hit_rows(self):
        return self._slipsheet.get_by_test_id("parlay-odds-row").and_(self.page.locator(".all")).count()

    def sheet_slip_legs(self):
        return self._slipsheet.get_by_test_id("parlay-slip-leg").count()

    def joint_notes(self):
        return self._slipsheet.get_by_test_id("parlay-slip-corr").count()

    def joint_note(self):
        return self._slipsheet.get_by_test_id("parlay-slip-corr").inner_text().strip()

    def all_hit_chance(self):
        return self._slipsheet.get_by_test_id("parlay-slip-edge").inner_text()

    def payout_shown(self):
        return self._pay.input_value()

    def type_payout(self, x):
        self._pay.fill(x)

    def payout_verdict(self):
        return self._verdict.inner_text()

    def payout_box_focused(self):
        return self.page.evaluate("document.activeElement.hasAttribute('data-bpay')")

    def payout_for_slip(self):
        """The payout the slip is on now: typed for this exact slip, else the standard board's, else None."""
        return self.page.evaluate("betsPayout(betsSlipLegs())")

    def graded_rates(self):
        """The first priced non-touchdown line, put on the slip higher and then lower: the chance each side
        counts at, and the model's own confidence and pick."""
        return self.page.evaluate(GRADED)

    def longest_leg_rate(self):
        return self.page.evaluate("legHit(PROPS.find(p => p.mkt === 'LONG'))")

    def planted_stack(self):
        """A QB and his top two receivers, all lower, planted as one game: the stack's chance, its payout, and
        whether the stack is recognised; None when no all-lower stack can be found."""
        return self.page.evaluate(STACK)

    # ---- the phone's kickoff row, the desktop's tabs (journeys) ----

    def go_to_slips(self):
        self.page.evaluate("navGo('parlay')")

    def desktop_tabs_hidden(self):
        return self._kick_tabs.is_hidden()

    def phone_tab_labels(self):
        return self.page.locator("#subnav .tr-x [data-gwin]").all_inner_texts()

    def kick_chip_labels(self):
        """The labels the page's own kickoff list gives its tabs."""
        return self.page.evaluate("KICK_CHIPS.map(kickChipLabel)")

    def tap_phone_tab(self, n):
        """The n-th kickoff tab in the phone's tab row; returns its kickoff key."""
        tab = self.page.locator("#subnav .tr-x [data-gwin]").nth(n)
        key = tab.get_attribute("data-gwin")
        tab.click()
        return key

    def kickoff(self):
        """The kickoff in force: the page's choice and the board's."""
        return {"chosen": self.page.evaluate("GAL_WIN"), "board": self.page.evaluate("slWin().k")}

    def board_games(self):
        """The games the board should show for its kickoff."""
        return self.page.evaluate("slGames(slWin()).map(g => g.game)")

    def phone_tab_pressed(self, k):
        return self.page.locator(f"#subnav [data-gwin='{k}'][aria-pressed='true']").count()

    def desktop_tab_selected(self, k):
        return self._kick_tab.and_(self.page.locator(f"[data-gwin='{k}'][aria-selected='true']")).count()

    def _row(self, slug):
        return self._rows.and_(self.page.locator(f"[data-slplayer='{slug}']"))
