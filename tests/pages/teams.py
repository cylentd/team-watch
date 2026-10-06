"""League > Teams, the roster cards (design/src/js/surface/lboard/lbcard.js, 2026-10-06).

Every locator for the board lives here, data-testid first (`teams-*`, test hooks only). A card is one
team: header, the strength strip, one row per starter, the bench as one line, and a foot that is empty
unless there is something to do. Methods return plain data and never assert.
"""

import re

CARD = """cards => cards.map(c => {
  const q = (id, root = c) => root.querySelector(`[data-testid="${id}"]`);
  const all = (id, root = c) => [...root.querySelectorAll(`[data-testid="${id}"]`)];
  const text = e => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  return {
    key: c.dataset.lbcard, name: text(q("teams-name")), record: text(q("teams-record")), total: text(q("teams-total")),
    mine: c.classList.contains("mine"),
    strip: all("teams-cell").map(e => ({col: e.dataset.col, value: text(q("teams-cell-v", e)),
      tone: e.classList.contains("up") ? "up" : e.classList.contains("dn") ? "dn" : "", spare: !!e.querySelector(".lb-plus")})),
    starters: all("teams-starter").map(e => ({slot: text(q("teams-slot", e)), name: text(q("teams-player", e)), pts: text(q("teams-pts", e))})),
    bench: all("teams-bench-item").map(e => ({pos: text(q("teams-slot", e)), name: text(q("teams-player", e)), pts: text(q("teams-pts", e))})),
    foot: q("teams-foot") ? text(q("teams-foot")) : null,
    yours: !!q("teams-yours", c), setButton: !!q("teams-mine", c), tradeLink: !!q("teams-trades", c),
  };
})"""


class TeamsPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._cards, self._sorts = tid("teams-card"), tid("teams-sort")

    # ---- what a reader does ----

    def sort(self, label):
        """Tap a sort chip by its label (Total, QB, RB, WR, TE) and wait for it to be the pressed one."""
        self._chip(label).click()
        self.page.wait_for_function("l => [...document.querySelectorAll('[data-testid=teams-sort]')]"
                                    ".some(b => b.textContent.trim() === l && b.getAttribute('aria-pressed') === 'true')", arg=label)

    def sort_with_keyboard(self, label):
        self._chip(label).focus()
        self.page.keyboard.press("Enter")

    def set_as_mine(self, key):
        """Tap "This is my team" in a card's foot."""
        self._card(key).get_by_test_id("teams-mine").click()

    def tap_card(self, key):
        self._card(key).get_by_test_id("teams-name").click()

    def open_trades_with(self, key):
        """Tap "Trades with them ›" in a card's foot."""
        self._card(key).get_by_test_id("teams-trades").click()

    def foot_box(self, key):
        """The foot's link or chip as a box: x, y, width, height of its button, and the colour of its background."""
        return self._card(key).get_by_test_id("teams-foot").locator("button").first.evaluate(
            "e => { const r = e.getBoundingClientRect(), c = getComputedStyle(e); return {x: r.left, y: r.top + scrollY, w: r.width, h: r.height, bg: c.backgroundColor}; }")

    # ---- what a reader sees ----

    def cards(self):
        return self._cards.evaluate_all(CARD)

    def names(self):
        return [c["name"] for c in self.cards()]

    def sorts(self):
        """The sort chips in order: label, pressed."""
        return self._sorts.evaluate_all("bs => bs.map(b => ({label: b.textContent.trim(), pressed: b.getAttribute('aria-pressed') === 'true'}))")

    def key_swatches(self):
        return self.page.get_by_test_id("teams-key").locator(".lb-k").count()

    def box(self, key=None):
        """x, y, width, height of a card (the first when no key), in page pixels."""
        loc = self._card(key) if key else self._cards.first
        return loc.evaluate("e => { const r = e.getBoundingClientRect(); return {x: r.left, y: r.top + scrollY, w: r.width, h: r.height}; }")

    def card_lefts(self):
        """The distinct left edges of the cards: how many columns the grid has."""
        return sorted({round(b) for b in self._cards.evaluate_all("cs => cs.map(c => c.getBoundingClientRect().left)")})

    def fits(self):
        """Nothing wider than the screen."""
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    def outline(self, key):
        """The computed box-shadow of a card (a lime outline reads rgb(200, 255, 46))."""
        return self._card(key).evaluate("e => getComputedStyle(e).boxShadow")

    def is_empty_state(self):
        return self.page.locator(".lb-empty").is_visible() and self._cards.count() == 0

    def _chip(self, label):
        return self._sorts.filter(has_text=re.compile(f"^{label}$"))

    def _card(self, key):
        return self._cards.and_(self.page.locator(f"[data-lbcard='{key}']"))
