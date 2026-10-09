"""Matchup > Start/Sit (leaf `matchups`, design/src/js/surface/matchups/): the lineup card that leads it, the paged
calls under it, the record, the board, and the Compare two page (ledger #94, draft A, 2026-10-09).

Every locator for the view lives here, data-testid first (`matchups-*`, test hooks only). The Compare two page is
the picker (surface/matchups/picker.js), found by its own controls. `tests/component.py` cannot mount `matchups`
yet (its SURFACES is frozen), so `open` mounts Ranks and goes to the view the way a tap would: the JS is the whole
app either way, and these checks read words, order and taps, never a size the view's own CSS sets.
"""


class MatchupsPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._lineup, self._noteam, self._swap = tid("matchups-lineup"), tid("matchups-noteam"), tid("matchups-swap")
        self._calls, self._kinds, self._record = tid("matchups-calls"), tid("matchups-kind"), tid("matchups-record")

    # ---- getting there ----

    def open(self, plant=""):
        """Go to Start/Sit, after `plant` (JS that sets the page's data, as the build would have) has run."""
        self.page.evaluate("js => { new Function(js)(); navGo('matchups'); }", plant)
        self.page.wait_for_function("SURFACE === 'matchups' && !!document.querySelector('.mu')")
        return self

    # ---- what a reader does ----

    def compare_the_two(self):
        self._swap.get_by_test_id("matchups-swap-compare").click()
        self.page.wait_for_selector(".mu.cmp")

    def compare_two(self):
        """The no-team card's way into the picker."""
        self._noteam.get_by_test_id("matchups-noteam-compare").click()
        self.page.wait_for_selector(".mu.cmp")

    def pick_team(self):
        """The no-team card's Pick your team: opens the visible team switch's menu."""
        self._noteam.get_by_test_id("matchups-noteam-pick").click()

    def kind(self, kind):
        """Tap a kind of call: "smash", "start" or "sit"."""
        self._kinds.and_(self.page.locator(f"[data-mukind='{kind}']")).click()
        self.page.wait_for_function("k => MU_KIND === k", arg=kind)

    def next_page(self):
        self.page.get_by_test_id("matchups-page-next").click()

    def prev_page(self):
        self.page.get_by_test_id("matchups-page-prev").click()

    # ---- what a reader sees ----

    def sections(self):
        """The view's blocks top down, by test id."""
        return self.page.evaluate("""[...document.querySelectorAll('.mu [data-testid^="matchups-"]')]
          .filter(e => e.parentElement.closest('[data-testid^="matchups-"]') === null).map(e => e.dataset.testid)""")

    def lineup(self):
        """{starters, bench}: each row's slug, slot word, call tag (or ""), points shown and its mark (in, out or "")."""
        def group(g):
            return self._lineup.locator(f"[data-mugroup='{g}'] [data-testid='matchups-lineup-row']").evaluate_all(
                """rs => rs.map(r => ({slug: r.dataset.mulu, slot: r.querySelector('.mu-lu-slot').textContent,
                  call: (r.querySelector('.mu-tag') || {}).textContent || '', pts: r.querySelector('.mu-lu-pts').textContent,
                  mark: r.dataset.mumark || ''}))""")
        return {"starters": group("starters"), "bench": group("bench")}

    def swap(self):
        """The swap: its kind, its words, the line under them (or ""), the number beside them (or "") and the
        compare button's words; None with no swap drawn."""
        if self._swap.count() == 0:
            return None
        sub, gain = self._swap.get_by_test_id("matchups-swap-sub"), self._swap.get_by_test_id("matchups-swap-gain").locator("b")
        return {"word": self._swap.get_by_test_id("matchups-swap-word").inner_text(),
                "sub": sub.inner_text() if sub.count() else "",
                "why": self._swap.get_by_test_id("matchups-swap-why").all_inner_texts(),
                "gain": gain.inner_text().strip() if gain.count() else "",
                "kind": self._swap.get_attribute("data-muswap"),
                "compare": self._swap.get_by_test_id("matchups-swap-compare").inner_text().strip()}

    def noteam(self):
        """The no-team card's line and its two buttons' words, or None when the lineup is drawn."""
        if self._noteam.count() == 0:
            return None
        tid = self._noteam.get_by_test_id
        return {"line": tid("matchups-noteam-line").inner_text(), "pick": tid("matchups-noteam-pick").inner_text().strip(),
                "compare": tid("matchups-noteam-compare").inner_text().strip()}

    def picked(self):
        """The picker's players, in its order (the Compare two page)."""
        return self.page.evaluate("[...document.querySelectorAll('[data-ssx]')].map(b => b.dataset.ssx)")

    def team_menu_open(self):
        return self.page.evaluate("[...document.querySelectorAll('[data-tsmenu]')].some(m => !m.hidden)")

    def calls(self):
        """The calls card: the kind pressed, each kind's count and label, the rows' slugs, the page line and the pager's state."""
        return {"kind": self._kinds.and_(self.page.locator("[aria-pressed='true']")).get_attribute("data-mukind"),
                "counts": dict(self._kinds.evaluate_all("bs => bs.map(b => [b.dataset.mukind, b.querySelector('b').textContent])")),
                "labels": dict(self._kinds.evaluate_all("bs => bs.map(b => [b.dataset.mukind, b.firstChild.textContent.trim()])")),
                "rows": self._calls.get_by_test_id("matchups-call-row").evaluate_all("rs => rs.map(r => r.dataset.murow)"),
                "page": self.page.get_by_test_id("matchups-page").inner_text().strip(),
                "prev": self.page.get_by_test_id("matchups-page-prev").is_enabled(),
                "next": self.page.get_by_test_id("matchups-page-next").is_enabled()}

    def record(self):
        return self._record.inner_text()

    def record_in_calls(self):
        return self._calls.get_by_test_id("matchups-record").count() == 1
