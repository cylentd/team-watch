"""Team > Trades > Value (design/src/js/surface/finder/value.js, 2026-11-03): what a reader does there and sees.

Every locator lives here, data-testid first (`value-*` on the view, `trades-tab` for the desktop's Offers / Value bar;
test hooks only). The two tabs are the phone's tab-row segments (`#subnav .tr-seg`, chrome/nav.js) or, from 760px,
the view's own bar: `pick_tab` taps whichever is drawn. Methods return plain data and never assert.
"""
from pages.profile import ProfilePage

ROWS = """rows => rows.map(r => {
  const q = id => r.querySelector(`[data-testid="${id}"]`), text = e => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  return {slug: r.dataset.tvopen, rank: text(q("value-rank")), name: text(q("value-name")), holder: text(q("value-holder")),
    par: text(q("value-par")), rate: text(q("value-rate")), healthy: text(q("value-healthy")), sees: text(q("value-sees")),
    mine: r.classList.contains("mine")};
})"""


class ValuePage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._rows, self._chips, self._cap, self._more = tid("value-row"), tid("value-chip"), tid("value-cap"), tid("value-more")

    # ---- what a reader does ----

    def pick_tab(self, tab):
        """Tap "offers" or "value"; waits until the page says it is the open one."""
        seg = self.page.locator(f"#subnav [data-tseg='{tab}']")
        (seg if seg.count() and seg.is_visible() else self.page.locator(f"[data-testid='trades-tab'][data-tvtab='{tab}']")).click()
        self.page.wait_for_function("v => tvTab() === v", arg=tab)

    def pick(self, chip):
        self._chips.and_(self.page.locator(f"[data-tvchip='{chip}']")).click()
        self.page.wait_for_function("c => TV_CHIP === c", arg=chip)

    def pick_span(self, span):
        self.page.get_by_test_id("value-span").and_(self.page.locator(f"[data-tvspan='{span}']")).click()
        self.page.wait_for_function("s => TV_SPAN === s", arg=span)

    def spans(self):
        return [(c.get_attribute("data-tvspan"), c.inner_text(), c.get_attribute("aria-pressed") == "true")
                for c in self.page.get_by_test_id("value-span").all()]

    def show_all(self):
        self._more.click()
        self.page.wait_for_function("() => TV_ALL")

    def open_row(self, slug):
        """Tap a row; returns his profile (pages/profile.py)."""
        self._rows.and_(self.page.locator(f"[data-tvopen='{slug}']")).click()
        self.page.wait_for_selector("#modal.on [data-testid='profile-title']")
        return ProfilePage(self.page)

    # ---- what a reader sees ----

    def tabs(self):
        """[(tab id, pressed)] from the phone's tab row, else the desktop's bar; [] when neither is drawn."""
        segs = self.page.locator("#subnav .tr-seg[data-tvtab]")
        if segs.count() and segs.first.is_visible():
            return [(s.get_attribute("data-tvtab"), s.get_attribute("aria-pressed") == "true") for s in segs.all()]
        bar = self.page.get_by_test_id("trades-tab")
        return [(b.get_attribute("data-tvtab"), b.get_attribute("aria-pressed") == "true") for b in bar.all() if b.is_visible()]

    def chips(self):
        return [(c.get_attribute("data-tvchip"), c.get_attribute("aria-pressed") == "true") for c in self._chips.all()]

    def rows(self):
        return self._rows.evaluate_all(ROWS)

    def caption(self):
        return self._cap.inner_text()

    def more(self):
        return self._more.inner_text() if self._more.count() else None

    def first_row_top(self):
        return self._rows.first.bounding_box()["y"]

    def scroll_width(self):
        return self.page.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
