"""The swipe between tabs (chrome/tabswipe.js, 2026-10-06): a sideways swipe on the view taps the next thing
in the phone's top tab row. `TabSwipe` wraps any mounted page: it swipes on the view and reads the row.

The row is chrome/nav.js's (`#subnav`, `.mode-sub`, `.tr-seg`), which has no test ids, so it is found by
class here, the one place. Reads return plain data; no method asserts.
"""

# A one-finger touch from (x, 400) to (x + dx, 404) on `sel`, as a reader's thumb makes it: start, one move, end.
SWIPE = """([sel, x, dx]) => {
  const el = document.querySelector(sel);
  const at = (cx, cy) => new Touch({identifier: 1, target: el, clientX: cx, clientY: cy});
  el.dispatchEvent(new TouchEvent('touchstart', {touches: [at(x, 400)], changedTouches: [at(x, 400)], bubbles: true}));
  el.dispatchEvent(new TouchEvent('touchmove', {touches: [at(x + dx / 2, 402)], changedTouches: [at(x + dx / 2, 402)], bubbles: true}));
  el.dispatchEvent(new TouchEvent('touchend', {touches: [], changedTouches: [at(x + dx, 404)], bubbles: true}));
}"""
FRAME = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"

# Something in the view that keeps its own sideways touch: a surface with its own swipe, or a row that scrolls sideways.
OWNERS = {
    "own swipe": "<div id='tsw-owner' data-ownswipe style='height:120px'></div>",
    "sideways scroll": "<div id='tsw-owner' style='overflow-x:auto;height:120px'><div style='width:2000px;height:100px'></div></div>",
}


class TabSwipe:
    def __init__(self, page):
        self.page = page

    # ---- what a reader does ----

    def swipe(self, dx, x=200, on="#view"):
        """Swipe `dx` px sideways (negative is a swipe left: the next tab), starting `x` px from the left edge."""
        self.page.evaluate(SWIPE, [on, x, dx])
        self.page.evaluate(FRAME)

    def swipe_on_owner(self, kind, dx):
        """Put an OWNERS element at the top of the view, then swipe on it."""
        self.page.evaluate("html => document.getElementById('view').insertAdjacentHTML('afterbegin', html)", OWNERS[kind])
        self.swipe(dx, on="#tsw-owner")

    def open(self, leaf):
        self.page.evaluate("leaf => navGo(leaf)", leaf)

    # ---- what a reader sees ----

    def pills(self):
        """The row's views, left to right."""
        return self.page.locator("#subnav .mode-sub").evaluate_all("bs => bs.map(b => b.dataset.leaf)")

    def pressed_pill(self):
        return self.page.locator("#subnav .mode-sub[aria-pressed='true']").get_attribute("data-leaf")

    def segs(self):
        """The open pill's own tabs, left to right."""
        return self.page.locator("#subnav .tr-seg").evaluate_all("bs => bs.map(b => b.dataset.tseg)")

    def pressed_seg(self):
        return self.page.locator("#subnav .tr-seg[aria-pressed='true']").get_attribute("data-tseg")

    def hash(self):
        return self.page.evaluate("location.hash")
