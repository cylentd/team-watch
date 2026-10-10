"""Slips by kickoff window (2026-10-08, ledger #33): the record line, the windows, each game's row with its best
pick, an opened game, the window's Split fold, and our pick on the player sheet's line rows.

Every locator lives here, `parlay-*` test ids first. The player sheet is the static `#legsheet` (no hook of its
own); a line row's outlined side is the `.pick` class it wears.
"""
from component import DRAWN  # noqa: F401  (the same mount contract as ParlayPage)


class SlipsPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._windows, self._win_names = tid("parlay-window"), tid("parlay-window-name")
        self._games, self._titles = tid("parlay-game"), tid("parlay-game-title")
        self._toggles, self._counts = tid("parlay-game-toggle"), tid("parlay-game-count")
        self._picks, self._pick_names, self._pick_sides = tid("parlay-pick"), tid("parlay-pick-name"), tid("parlay-pick-side")
        self._adds, self._rows = tid("parlay-pick-add"), tid("parlay-row")
        self._split, self._split_lines = tid("parlay-split"), tid("parlay-split-line")
        self._record, self._record_note = tid("parlay-record"), tid("parlay-record-note")
        self._sheet = page.locator("#legsheet")

    @classmethod
    def open(cls, mount, win, size=(360, 800), book="dk"):
        page, errors = mount("parlay", size=size)
        s = cls(page)
        s.show(win, book)
        return s, errors

    def show(self, win, book="dk"):
        self.page.evaluate("([w, b]) => { SURFACE = 'parlay'; PARLAY_BOOK = b; GAL_WIN = w; SL_OPEN = {}; SL_SPLIT = {};"
                           " SLIP = []; SLIP_SIDE = {}; render(); }", [win, book])

    def forget_claude(self):
        """Claude has called no line yet this week."""
        self.page.evaluate("() => { for (const k of Object.keys(LIVE_CLAUDE_PROPS.calls)) delete LIVE_CLAUDE_PROPS.calls[k]; render(); }")

    def grade_ours(self, graded):
        self.page.evaluate("g => { Object.assign(LIVE_CLAUDE_RECORD, g); render(); }", graded)

    # ---- what a reader does ----

    def toggle_game(self, game):
        self._toggles.and_(self.page.locator(f"[data-slopen='{game}']")).click()

    def toggle_split(self):
        # The fold sits at the page foot once the Anytime TDs card leads (2026-10-09), where the tray covers it in a
        # 360x800 test page, so the test presses it from the keyboard. Open question in the 2026-10-09 report.
        self._split.first.press("Enter")

    def add_first_pick(self):
        self._adds.first.click()

    def open_sheet(self, slug):
        self.page.evaluate("s => playerSheetOpen(s)", slug)

    def close_sheet(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_function("LEG_SHEET === null")

    # ---- what a reader sees ----

    def window_names(self):
        return self._win_names.all_inner_texts()

    def game_titles(self):
        return self._titles.all_inner_texts()

    def game_counts(self):
        return self._counts.all_inner_texts()

    def picks(self):
        """Each pick row drawn: name, the side and line, the chance and tier word."""
        return self._picks.evaluate_all("""ps => ps.map(p => ({name: p.querySelector('[data-testid="parlay-pick-name"]').innerText,
          side: p.querySelector('[data-testid="parlay-pick-side"]').innerText,
          tier: p.querySelector('.sl-tp').innerText.replace(/\\s+/g, ' ').trim()}))""")

    def expanded(self, game):
        return self._toggles.and_(self.page.locator(f"[data-slopen='{game}']")).get_attribute("aria-expanded")

    def player_row_count(self):
        return self._rows.count()

    def split_label(self):
        return self._split.first.inner_text().replace("\n", " ")

    def split_lines(self):
        return self._split_lines.all_inner_texts()

    def split_sides_drawn(self):
        """Side buttons or tier words inside the Split fold: none, a split has no side."""
        return self.page.locator(".sl-split [data-slpick], .sl-split .sl-conf, .sl-split .sl-pick").count()

    def slip(self):
        return self.page.evaluate("SLIP.map(i => [PROPS[i].n, PROPS[i].mkt, slipSide(i)])")

    def add_pressed(self):
        return self._adds.first.get_attribute("aria-pressed")

    def record_text(self):
        return self._record.locator(".pr-rec-r").first.inner_text().replace("\n", " ")

    def record_note(self):
        return self._record_note.inner_text()

    def claude_badges(self):
        return self.page.locator(".sl-cb, .sl-cwhy, .pr-cb").count()

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")

    def sheet_line(self, label):
        """One line row of the open sheet: its outlined side, the words under the sides, and the labelled side."""
        ln = self._sheet.locator(f"[data-testid='parlay-line-item']:has([data-testid='parlay-line-market']:has-text('{label}'))").first
        return ln.evaluate("""l => ({pick: [...l.querySelectorAll('.sl-side.pick')].map(b => b.innerText),
          under: l.querySelector('.sl-sides').innerText.split('\\n').slice(2).join(' ').replace(/\\s+/g, ' ').trim(),
          named: [...l.querySelectorAll('.sl-side[aria-label]')].map(b => b.getAttribute('aria-label'))})""")
