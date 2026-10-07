"""Stats' position strip (design/src/js/chrome/statspos.js, 2026-10-06): the pill above a phone's bottom bar
that picks the one position every Stats view shares. Every strip locator lives here (`stats-pos-*`, test hooks
only). A view's own top chips, drawn on a desktop instead, are found by the data attribute each view gives
them (`data-rkpos`, `data-bdpos`, ...); a strip segment carries its view's attribute too.
"""
VIEW_CHIPS = "#view [data-rkpos], #view [data-bdpos], #view [data-rvpos], #view [data-upos], #view [data-sospos]"
# What each view says it draws: its heading or foot names the position; Leaders wears it as a class on its
# wrap; Work vs points names each row's position, so All reads "RB TE WR".
DRAWN = {
    "ranks": "() => document.querySelector('#view .rk-headline h2').textContent",
    "board": "() => [...document.querySelector('#view .wrap').classList].find(c => c.startsWith('pos-')).slice(4).toUpperCase()",
    "movers": "() => [...new Set([...document.querySelectorAll('#view .rv-pos')].map(e => e.textContent))].sort().join(' ')",
    "usage": "() => document.querySelector('#view .ufoot').textContent",
    "schedule": "() => document.querySelector('[data-testid=\"schedule-title\"]').textContent",
}


class StatsPosStrip:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._strip, self._segs, self._hl = tid("stats-pos-strip"), tid("stats-pos-seg"), tid("stats-pos-hl")

    # ---- what a reader does ----

    def open_view(self, leaf):
        """Go to another view the way the tab row does (navGo)."""
        self.page.evaluate("leaf => navGo(leaf)", leaf)

    def tap(self, pos):
        """Tap the segment for a position: "QB", "FLEX", "DST", "ALL" ..."""
        self._seg(pos).click()

    def slide(self, start, through, read):
        """Press the segment `start`, slide the finger over each of `through` in turn without lifting, then lift.
        After each move, `read()` is called; returns what it returned at each step, then once more after the lift."""
        y = self._centre(start)[1]
        self.page.mouse.move(*self._centre(start))
        self.page.mouse.down()
        seen = [read()]
        for pos in through:
            self.page.mouse.move(self._centre(pos)[0], y, steps=4)
            seen.append(read())
        self.page.mouse.up()
        seen.append(read())
        return seen

    def finger_drag(self, start, end):
        """A real one-finger drag (Chromium's own touch input, so the page gets touch and pointer events as from a
        phone) from the segment `start` to the segment `end`, in 8 moves, then lift. Needs a touch context."""
        (x0, y), (x1, _) = self._centre(start), self._centre(end)
        cdp = self.page.context.new_cdp_session(self.page)
        try:
            send = lambda kind, pts: cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": pts})
            send("touchStart", [{"x": x0, "y": y}])
            for i in range(1, 9):
                send("touchMove", [{"x": x0 + (x1 - x0) * i / 8, "y": y}])
            send("touchEnd", [])
        finally:
            cdp.detach()

    def tab(self):
        """The view and its own tab as the top row has them: SURFACE and the pressed pill's leaf."""
        return self.page.evaluate("[SURFACE, (document.querySelector('#subnav .mode-sub[aria-pressed=\"true\"]') || {dataset: {}}).dataset.leaf]")

    def focus(self, pos):
        """Move keyboard focus onto a segment (Tab from the page's last focus)."""
        self._seg(pos).focus()

    def scroll_to_end(self):
        self.page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")

    # ---- what a reader sees ----

    def shown(self):
        return self._strip.count() == 1 and self._strip.is_visible()

    def labels(self):
        return [s.strip() for s in self._segs.all_inner_texts()]

    def positions(self):
        return self._segs.evaluate_all("ss => ss.map(s => s.dataset.spseg)")

    def pressed(self):
        """The data position of every segment pressed (one, when the strip works)."""
        return self._segs.evaluate_all("ss => ss.filter(s => s.getAttribute('aria-pressed') === 'true').map(s => s.dataset.spseg)")

    def drawn(self):
        """What the open view says it draws (DRAWN): a heading, a class or the rows' positions."""
        return self.page.evaluate(DRAWN[self.surface()])

    def view_chip_count(self):
        """The open view's own position chips (its top row), drawn on a desktop only."""
        return self.page.locator(VIEW_CHIPS).count()

    def geometry(self):
        """The strip's box, each segment's width, the bottom bar's top, the screen, as numbers."""
        return self.page.evaluate("""() => {
          const s = document.querySelector('[data-testid="stats-pos-strip"]').getBoundingClientRect();
          const bar = document.getElementById('tabbar').getBoundingClientRect();
          const segs = [...document.querySelectorAll('[data-testid="stats-pos-seg"]')].map(b => b.getBoundingClientRect().width);
          return {left: s.left, right: s.right, top: s.top, bottom: s.bottom, height: s.height, segs,
                  bar_top: bar.top, width: innerWidth, height_screen: innerHeight};
        }""")

    def highlight_on(self):
        """The position whose segment the one sliding highlight sits over (its left edge within 1px), or None."""
        return self.page.evaluate("""() => {
          const hl = document.querySelector('[data-testid="stats-pos-hl"]');
          if (!hl) return null;
          const x = hl.getBoundingClientRect().left;
          const seg = [...document.querySelectorAll('[data-testid="stats-pos-seg"]')]
            .find(b => Math.abs(b.getBoundingClientRect().left - x) <= 1);
          return seg ? seg.dataset.spseg : null;
        }""")

    def highlight_count(self):
        return self._hl.count()

    def gesture(self):
        """How the strip takes a touch: its touch-action, and whether the tab swipe is told to leave it alone."""
        return self._strip.evaluate("s => ({touch: getComputedStyle(s).touchAction, own: s.hasAttribute('data-ownswipe')})")

    def group(self):
        """The strip's role and accessible label, and whether every segment is a button with aria-pressed."""
        return self._strip.evaluate("""s => ({role: s.getAttribute('role'), label: s.getAttribute('aria-label'),
          buttons: [...s.querySelectorAll('[data-spseg]')].every(b => b.tagName === 'BUTTON' && b.hasAttribute('aria-pressed'))})""")

    def focus_ring(self, pos):
        """The focused segment's outline width and style, while it holds keyboard focus."""
        return self._seg(pos).evaluate("b => { const c = getComputedStyle(b); return {focused: b.matches(':focus-visible'), width: c.outlineWidth, style: c.outlineStyle}; }")

    def lowest_content_bottom(self):
        """The bottom edge of the view's lowest drawn element, in screen terms."""
        return self.page.evaluate("""() => Math.max(...[...document.querySelectorAll('#view *')]
          .filter(e => e.getClientRects().length && getComputedStyle(e).position !== 'fixed')
          .map(e => e.getBoundingClientRect().bottom))""")

    def strip_top(self):
        return self._strip.bounding_box()["y"]

    def scrolls_sideways(self):
        return self.page.evaluate("document.documentElement.scrollWidth > innerWidth")

    def surface(self):
        return self.page.evaluate("SURFACE")

    def _seg(self, pos):
        return self._segs.and_(self.page.locator(f"[data-spseg='{pos}']"))

    def _centre(self, pos):
        b = self._seg(pos).bounding_box()
        return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
