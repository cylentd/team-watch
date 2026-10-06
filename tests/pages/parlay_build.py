"""Build (design/src/js/surface/parlay/lines.js): the line market, one column of lines.

BuildPage extends ParlayPage (tests/pages/parlay.py), which holds the slip, the tray and the leg sheet
Build shares. A Build test mounts "build": the view is a leaf of its own and its lines.css is fenced to
it, so a mount of "parlay" has no Build CSS. Every method only reads or acts; what a number should be
is the test's to say.

Motion: `mount` loads with prefers-reduced-motion on, and the entrance and the pop read it at the time
they run. A motion test takes `open_with_motion`, which turns it off for a context of its own (a
context key, MOTION) so no other test inherits it, and reloads once.
"""
from component import DRAWN
from pages.parlay import ParlayPage
from test_render import LOAD_MS


MOTION = "window.__parlayMotion = true;"      # only a context key: motion tests get a context of their own

STAMP = "e => Math.round(e.getBoundingClientRect().right)"

# every fact of a listed line the Best odds rule reads; the rule itself is the test's
LINE_FACTS = """() => buildLines().map(p => {
  const u = p.books && p.books.Underdog, d = p.books && p.books.DraftKings, r = p.ref;
  return {stale: !!p.stale,
          ref: r ? {line: r.line, over: r.over} : null,
          underdog: u ? {stale: !!u.stale, pick: u.pick, line: u.line, over: u.over, under: u.under} : null,
          draftkings: d ? {line: d.line, over: d.over} : null};
})"""


class BuildPage(ParlayPage):
    def __init__(self, page):
        super().__init__(page)
        tid = page.get_by_test_id
        self._bar, self._lines = tid("parlay-bar"), tid("parlay-line")
        self._build_list, self._why, self._build_empty = tid("parlay-build-list"), tid("parlay-line-why"), tid("parlay-build-empty")

    # ---- opening it ----

    @classmethod
    def open(cls, mount, book=None, size=(360, 780), best=False, sort=None):
        """Build on `book` (the page's own when None), at `size`. (BuildPage, errors)."""
        page, errors = mount("build", size=size)
        lines = cls(page)
        if book:
            lines.show_build(book, best=best, sort=sort)
        return lines, errors

    @classmethod
    def open_with_motion(cls, mount, size=(390, 844)):
        """Build with the reader's motion on: the page reloads once, so its first draw is the entrance."""
        page, errors = mount("build", size=size, init=(MOTION,))
        if page.evaluate("REDUCED()"):
            page.emulate_media(reduced_motion="no-preference")
            page.reload(timeout=LOAD_MS)
            page.wait_for_function(DRAWN, timeout=LOAD_MS)
        return cls(page), errors

    def show_build(self, book, best=False, sort=None):
        self.page.evaluate("([b, best, sort]) => { SURFACE = 'build'; PARLAY_BOOK = b; if (sort) MKT_SORT = sort;"
                           " MKT_PAGE = 1; if (best) MKT_BEST = true; render(); }", [book, best, sort])

    def build_with_settings_panel(self):
        self.page.evaluate("() => { SURFACE = 'build'; BETS_PANEL = true; render(); }")

    # ---- what a reader does ----

    def tap_first_line_evidence(self):
        """The line and its bars, on the first line a reader can pick: they open the leg sheet."""
        self._pickable().first.get_by_test_id("parlay-line-ev").click()

    def tap_first_call(self):
        """The call on the first line a reader can pick: it puts the pick in the slip."""
        self._pickable().first.get_by_test_id("parlay-line-call").click()

    def tap_call_of_only_line(self):
        self._lines.get_by_test_id("parlay-line-call").click()

    def move_most_confident_line(self):
        """The book moves its most confident Underdog line far from the model's (build.py `stale`);
        the page redraws. Returns that line's index in PROPS."""
        return self.page.evaluate("""() => {
          const p = PROPS.filter(p => udPick(p) && !udPick(p).synthetic).sort(SORTS.conf)[0];
          p.books.Underdog.stale = 1; window._moved = PROPS.indexOf(p); render(); return window._moved;
        }""")

    def list_only(self, i):
        """Build shows PROPS[i] alone."""
        self.page.evaluate("i => { buildLines = () => [PROPS[i]]; render(); }", i)

    def reapply_best_odds(self):
        self.page.evaluate("() => { MKT_BEST = true; render(); }")

    def wait_for_tray_count(self, n):
        """The tray counts n: a pick flies in, then lands."""
        self.page.wait_for_function(
            "n => document.querySelector('[data-testid=\"parlay-tray-count\"]').textContent === n", arg=str(n))

    # ---- what a reader sees ----

    def player_blocks(self):
        return self._build_list.get_by_test_id("parlay-bplayer").count()

    def right_edge(self):
        """The furthest right edge of the bar's controls and every line."""
        return max(self._bar.locator(":scope > *").evaluate_all(f"es => es.map({STAMP})")
                   + self._lines.evaluate_all(f"es => es.map({STAMP})"))

    def bar_controls(self):
        return self._bar.locator(":scope > *").count()

    def call_lefts(self):
        """Where each line's call starts, in px: one column when they all agree."""
        return self.page.get_by_test_id("parlay-line-call").evaluate_all(
            "es => es.map(e => Math.round(e.getBoundingClientRect().left))")

    def line_count(self):
        return self._lines.count()

    def lines_saying_why(self):
        return self._why.count()

    def only_line(self):
        """The one line on screen: whether it wears 'moved', its text, and its data-prop (None: a tap adds nothing)."""
        line = self._lines
        return {"moved": "moved" in line.get_attribute("class"), "text": line.inner_text(),
                "prop": line.get_attribute("data-prop")}

    def build_order(self):
        """The PROPS index of every line Build lists, in order."""
        return self.page.evaluate("buildLines().map(p => PROPS.indexOf(p))")

    def is_moved(self, i, book="underdog"):
        return self.page.evaluate("([i, b]) => lineMoved(PROPS[i], b)", [i, book])

    def listed_line_facts(self):
        """For each line Build lists: the prices and flags the Best odds rule reads (`ref` is the
        BettingPros consensus; `underdog` and `draftkings` None when the book has no line)."""
        return self.page.evaluate(LINE_FACTS)

    def lines_without_best_odds(self):
        """How many lines the book has in all: Best odds is switched off to count them."""
        return self.page.evaluate("(MKT_BEST = false, buildLines().length)")

    def empty_shown(self):
        return self._build_empty.count()

    def view_enters(self):
        """Whether the view is marked as arriving: its cards come in staggered."""
        return self.page.evaluate("document.getElementById('view').classList.contains('enter')")

    def lines_just_tapped(self):
        return self._lines.and_(self.page.locator(".just")).count()

    def slip_count_bumped(self):
        return self.page.get_by_test_id("parlay-slip-pill").and_(self.page.locator(".bump")).count()

    def kickoff_setting(self):
        """The kickoff select in Build's settings panel."""
        return self.page.get_by_test_id("parlay-select").and_(self.page.locator("[data-msel='gwin']")).input_value()

    def _pickable(self):
        """Lines a tap can add: the ones the book has not moved carry data-prop."""
        return self._lines.and_(self.page.locator("[data-prop]"))
