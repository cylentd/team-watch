"""League > Teams, the roster cards (design/src/js/surface/lboard/lbcard.js, 2026-10-06).

Every locator for the board lives here, data-testid first (`teams-*`, test hooks only). A card is one
team: header, the strength strip, one row per starter, the bench as one line, and a foot that is empty
unless there is something to do. Methods return plain data and never assert.

The League's one team line is not this view's: it is surface/league/switch.js, read through `self.chip`
(pages/league_chip.py). The header's team switch and the nav row are chrome/, with no test id yet, so their few class
and data-attribute locators sit under "the chrome around it" and move when those get one. `open_teams` mounts the view
as a reader whose team is `team` (a TEAMS key), or the suite's own pick (SUITE).
"""

import re

from pages.league_chip import LeagueChip

SUITE = None       # the suite's own pick (SEED): the Madden Curse team


def pick_script(key):
    return f'try {{ localStorage.setItem("tw-team", "{key}"); }} catch (e) {{}}\n'


def open_teams(mount, team=SUITE, size=(360, 800)):
    """League > Teams on a kept context: (TeamsPage, errors). `team` is the TEAMS key the reader has picked;
    a key no team has ("nothing") is a reader with no team."""
    page, errors = mount("teams", size=size, init=() if team is SUITE else (pick_script(team),))
    return TeamsPage(page), errors


CARD = """cards => cards.map(c => {
  const q = (id, root = c) => root.querySelector(`[data-testid="${id}"]`);
  const all = (id, root = c) => [...root.querySelectorAll(`[data-testid="${id}"]`)];
  const text = e => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  return {
    key: c.dataset.lbcard, name: text(q("teams-name")), record: text(q("teams-record")), total: text(q("teams-total")),
    mine: c.classList.contains("mine"),
    strip: all("teams-cell").map(e => ({col: e.dataset.col, value: text(q("teams-cell-v", e)),
      tone: e.classList.contains("up") ? "up" : e.classList.contains("dn") ? "dn" : "", spare: !!q("teams-spare", e)})),
    starters: all("teams-starter").map(e => ({slot: text(q("teams-slot", e)), name: text(q("teams-player", e)), pts: text(q("teams-pts", e))})),
    bench: all("teams-bench-item").map(e => ({pos: text(q("teams-slot", e)), name: text(q("teams-player", e)), pts: text(q("teams-pts", e))})),
    foot: q("teams-foot") ? text(q("teams-foot")) : null,
    yours: !!q("teams-yours", c), setButton: !!q("teams-mine", c), tradeLink: !!q("teams-trades", c),
  };
})"""


class TeamsPage:
    def __init__(self, page):
        self.page = page
        self.chip = LeagueChip(page)
        tid = page.get_by_test_id
        self._cards, self._sorts, self._grid, self._empty = tid("teams-card"), tid("teams-sort"), tid("teams-grid"), tid("teams-empty")
        self._starters, self._names = tid("teams-starter"), tid("teams-name")

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

    def pick_team(self, key):
        """Switch the reader's team as the team switch does (pickTeam)."""
        self.page.evaluate("k => pickTeam(k)", key)

    def show_league(self, league):
        """Draw the cards of league `league` ("espn", "ayo", "yahoo") for a reader with no team: the league on screen."""
        self.page.evaluate("l => { VIEW = l; render(); }", league)

    def plant(self, block):
        """Gives a league its cards from an invented block (design/teams.py live_league), and draws it."""
        self.page.evaluate("b => { LIVE_TEAMS.leagues = LIVE_TEAMS.leagues.filter(l => l.key !== b.key); "
                           "LIVE_TEAMS.leagues.push(b); render(); }", block)

    def pick_in_header(self, league, key):
        """Choose a team in the header bar's switch (chrome, no test id): open it, the league, the team."""
        self.page.locator("#hdrswitch [data-tsbtn]").click()
        self.page.locator(f"#hdrswitch [data-tsleague='{league}']").click()
        self.page.locator(f"#hdrswitch .ts-item[data-k='{key}']").click()

    # ---- what a reader sees ----

    def league_group_count(self):
        """League buttons in the nav bar (chrome, no test id)."""
        return self.page.locator(".navitem[data-s='league']").count()

    def open_leaf(self):
        """The sub-row's pressed tab (chrome, no test id)."""
        return self.page.locator(".mode-sub[aria-pressed='true']").inner_text()

    def hash(self):
        return self.page.evaluate("location.hash")

    def stored_team(self):
        return self.page.evaluate("localStorage.getItem('tw-team')")

    def grid_count(self):
        return self._grid.count()

    def bench_count(self):
        """Bench lines drawn: one per card."""
        return self.page.get_by_test_id("teams-bench").count()

    def starter_heights(self):
        """The rounded height of every starter row on the page."""
        return self._starters.evaluate_all("rs => rs.map(e => Math.round(e.getBoundingClientRect().height))")

    def starter_name_font(self):
        """The computed font size of the first starter's name."""
        return self._starters.first.get_by_test_id("teams-player").evaluate("e => getComputedStyle(e).fontSize")

    def names_keep_room(self):
        """No team name is cut off."""
        return self._names.evaluate_all("bs => bs.every(b => b.scrollWidth <= b.clientWidth)")

    def card_heights(self, n):
        """The rounded heights of the first n cards."""
        return self._cards.evaluate_all("(cs, n) => cs.slice(0, n).map(c => Math.round(c.getBoundingClientRect().height))", n)

    def card_left_from_chip(self):
        """How far the first card's left edge is from the chip's, the frame's edge."""
        return self.box()["x"] - self.chip.left()

    def cards(self):
        return self._cards.evaluate_all(CARD)

    def names(self):
        return [c["name"] for c in self.cards()]

    def sorts(self):
        """The sort chips in order: label, pressed."""
        return self._sorts.evaluate_all("bs => bs.map(b => ({label: b.textContent.trim(), pressed: b.getAttribute('aria-pressed') === 'true'}))")

    def key_swatches(self):
        return self.page.get_by_test_id("teams-key-item").count()

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
        return self._empty.is_visible() and self._cards.count() == 0

    def _chip(self, label):
        return self._sorts.filter(has_text=re.compile(f"^{label}$"))

    def _card(self, key):
        return self._cards.and_(self.page.locator(f"[data-lbcard='{key}']"))
