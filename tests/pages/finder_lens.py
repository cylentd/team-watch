"""League > Trades, the lens parts of an offer card (ledger #44, 2026-10-08; design/src/js/surface/finder/lenses.js): each
side's judge (You / Them, the gain on the lens that judges it, "For a contender: Playoff run"), the bye notes, and the
All four lenses table behind its disclosure. FinderPage (pages/finder.py) reads the rest of the card; this is its own
class because that one is frozen. Methods return plain data and never assert."""

TEXT = "e => e ? e.textContent.replace(/\\s+/g, ' ').trim() : null"

SIDES = """cards => cards.map(c => [...c.querySelectorAll('[data-testid=finder-side]')].map(s => {
  const text = %s, q = id => s.querySelector(`[data-testid="${id}"]`);
  return {who: text(q('finder-side-who')), gain: text(q('finder-side-gain')), judge: text(q('finder-side-judge'))};
}))""" % TEXT

NOTES = """cards => cards.map(c => [...c.querySelectorAll('[data-testid=finder-note]')].map(%s))""" % TEXT

ROWS = """d => [...d.querySelectorAll('[data-testid=finder-lens-row]')].map(r => {
  const text = %s, td = [...r.querySelectorAll('td')];
  return {lens: text(r.querySelector('th b')), weeks: text(r.querySelector('th small')), me: text(td[0]), them: text(td[1]),
    on: td.map(c => c.classList.contains('on'))};
})""" % TEXT

LOOK = """cards => cards.map(c => [...c.querySelectorAll('[data-testid=finder-side-gain] b')].map(b => {
  const s = getComputedStyle(b), r = b.getBoundingClientRect();
  return {size: s.fontSize, weight: s.fontWeight, colour: s.color, top: Math.round(r.top)};
}))"""


class FinderLens:
    def __init__(self, page):
        self.page = page
        self._cards = page.get_by_test_id("finder-card")

    def sides(self):
        """Per card, its two sides in order (You, Them): who, the gain with its unit, the judge line. [] on a ROS card."""
        return self._cards.evaluate_all(SIDES)

    def notes(self):
        """Per card, its bye notes' text in order."""
        return self._cards.evaluate_all(NOTES)

    def gain_looks(self):
        """Per card, each side's gain number: font size, weight, colour and top edge."""
        return self._cards.evaluate_all(LOOK)

    def lenses_open(self, i=0):
        return self._details(i).evaluate("d => d.open")

    def open_lenses(self, i=0):
        """Tap All four lenses on card `i`."""
        self._details(i).locator("summary").click()
        self.page.wait_for_function("i => document.querySelectorAll('[data-testid=finder-lenses]')[i].open", arg=i)

    def lens_rows(self, i=0):
        """Card `i`'s lens table: lens, its weeks, both gains, and which cell judges its side."""
        return self._details(i).evaluate(ROWS)

    def has_lenses(self):
        return self.page.get_by_test_id("finder-lenses").count() > 0

    def _details(self, i):
        return self.page.get_by_test_id("finder-lenses").nth(i)
