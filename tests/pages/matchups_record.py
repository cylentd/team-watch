"""The season record on Start/Sit, as the reader reads it (S9, 2026-11-01).

`RecordPage(page)` wraps the record line that sits in the calls card (test id `matchups-record`). Reads return plain
data; none asserts. Open the view with `pages.matchups.MatchupsPage(page).open(plant)` first; `plant` sets the record.
"""


class RecordPage:
    def __init__(self, page):
        self.page = page
        self._record = page.get_by_test_id("matchups-record")
        self._line = self._record.locator("p:not(.mu-fun)")

    def head(self):
        """The line's words before the figures: "Record since week 5"."""
        return self._line.inner_text().split(":")[0]

    def tiles(self):
        """{kind: {wl, word, void}} for SMASH, START and SIT as drawn: hit-miss, the call's word, the void note or ""."""
        return self._record.locator(".mu-recl-k").evaluate_all(
            """ks => Object.fromEntries(ks.map(k => [k.classList[1], {wl: k.querySelector('b').textContent,
              word: k.childNodes[1].textContent.trim(), void: (k.querySelector('small') || {}).textContent || ''}]))""")

    def after_head(self):
        """The line's words after the head and its colon: the figures, or the no-week-graded sentence."""
        return self._line.inner_text().split(": ", 1)[1]

    def fun(self):
        """The for-fun line under the figures, or ""."""
        line = self._record.locator(".mu-fun")
        return line.inner_text() if line.count() else ""

    def on_screen(self):
        """True when the line is drawn and sits inside the page's width."""
        box = self._record.bounding_box()
        return bool(box) and box["x"] >= 0 and box["x"] + box["width"] <= self.page.evaluate("innerWidth")
