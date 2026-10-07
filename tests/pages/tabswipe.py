"""The swipe between tabs (chrome/tabswipe.js, 2026-10-06): a sideways swipe on the view taps the next thing
in the phone's top tab row. `TabSwipe` wraps any mounted page: it swipes on the view and reads the row.

The row is chrome/nav.js's (`#subnav`, `.mode-sub`, `.tr-seg`), which has no test ids, so it is found by
class here, the one place. Reads return plain data; no method asserts.
"""

# A one-finger touch through `pts` ([x, y] each: start, moves, end) on `sel`, as a reader's thumb makes it.
# `scroll` px, when given, is how far the page scrolls while the finger is down (before it lifts).
TOUCH = """([sel, pts, scroll]) => {
  const el = document.querySelector(sel);
  const at = ([cx, cy]) => new Touch({identifier: 1, target: el, clientX: cx, clientY: cy});
  const fire = (type, p, down) => el.dispatchEvent(new TouchEvent(type, {touches: down ? [at(p)] : [], changedTouches: [at(p)], bubbles: true}));
  fire('touchstart', pts[0], true);
  for (const p of pts.slice(1, -1)) fire('touchmove', p, true);
  if (scroll) window.scrollBy(0, scroll);
  fire('touchend', pts[pts.length - 1], false);
}"""
FRAME = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"

# Something in the view that keeps its own sideways touch: a surface with its own swipe, or a row that scrolls sideways.
OWNERS = {
    "own swipe": "<div id='tsw-owner' data-ownswipe style='height:120px'></div>",
    "sideways scroll": "<div id='tsw-owner' style='overflow-x:auto;height:120px'><div style='width:2000px;height:100px'></div></div>",
}

# The page's chrome around the view, where a swipe is never the tab swipe's.
CHROME = {"header": ".navbar .navrow", "tab row": "#subnav", "bottom bar": "#tabbar"}

# Long enough that the page can scroll under a touch, whatever the view holds.
TALL = "document.getElementById('view').insertAdjacentHTML('beforeend', \"<div id='tsw-tall' style='height:3000px'></div>\")"


class TabSwipe:
    def __init__(self, page):
        self.page = page

    # ---- what a reader does ----

    def touch(self, pts, on="#view", scroll=0):
        self.page.evaluate(TOUCH, [on, [list(p) for p in pts], scroll])
        self.page.evaluate(FRAME)

    def swipe(self, dx, x=200, on="#view", scroll=0):
        """Swipe `dx` px sideways (negative is a swipe left: the next tab), starting `x` px from the left edge."""
        self.touch([(x, 400), (x + dx / 2, 402), (x + dx, 404)], on=on, scroll=scroll)

    def swipe_on_owner(self, kind, dx):
        """Put an OWNERS element at the top of the view, then swipe on it."""
        self.page.evaluate("html => document.getElementById('view').insertAdjacentHTML('afterbegin', html)", OWNERS[kind])
        self.swipe(dx, on="#tsw-owner")

    def swipe_on_background(self, dx):
        """Swipe on the page itself, below a view shorter than the screen: the touch lands on the body."""
        self.swipe(dx, on="body")

    def swipe_on_chrome(self, part, dx):
        self.swipe(dx, on=CHROME[part])

    def swipe_on_leaders_card(self, dx):
        """Stats > Leaders: the #1's card, which turned the stat on a swipe until 2026-10-06."""
        self.swipe(dx, on=".bd-card")

    def scroll_while_swiping(self, dx, scroll):
        """A sideways swipe during which the page scrolls `scroll` px (a flick whose drift looks sideways)."""
        self.page.evaluate(TALL)
        self.swipe(dx, scroll=scroll)

    def open(self, leaf):
        self.page.evaluate("leaf => navGo(leaf)", leaf)

    def tap_seg(self, seg):
        self.page.locator(f"#subnav .tr-seg[data-tseg='{seg}']").click()

    def open_search(self):
        self.page.locator("#navsearch").click()
        self.page.locator("#search:not([hidden])").wait_for()

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

    def pressed_seg_overhang(self):
        """How many px of the pressed tab fall outside the row's box: [left, right], 0 when it shows whole."""
        return self.page.evaluate("""() => { const r = document.querySelector('#subnav .modes-sub').getBoundingClientRect(),
            s = document.querySelector('#subnav .tr-seg[aria-pressed=true]').getBoundingClientRect();
            return [Math.max(0, Math.round(r.left - s.left)), Math.max(0, Math.round(s.right - r.right))]; }""")

    def hash(self):
        return self.page.evaluate("location.hash")

    def width_at_slide_start(self, dx):
        """Swipe with motion on, freeze the slide at its first frame: [the page's width, the screen's]. The
        mounted page runs with reduced motion, so motion is switched on for this swipe and back off after."""
        self.page.emulate_media(reduced_motion="no-preference")
        try:
            self.swipe(dx)
            return self.page.evaluate("""() => { document.getAnimations().forEach(a => { a.pause(); a.currentTime = 0; });
                return [document.documentElement.scrollWidth, innerWidth]; }""")
        finally:
            self.page.evaluate("document.getAnimations().forEach(a => a.finish())")
            self.page.emulate_media(reduced_motion="reduce")

    def sliding(self):
        """#view's children: [their first class, position, whether the swipe's slide moves them]."""
        return self.page.evaluate("""[...document.getElementById('view').children].map(c => [c.classList[0] || c.tagName,
            getComputedStyle(c).position, c.classList.contains('tab-in-r') || c.classList.contains('tab-in-l')])""")
