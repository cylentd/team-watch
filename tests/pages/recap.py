"""This week > Recap (leaf `weekrecap`, design/src/js/surface/recap/): what a reader can do there and what they see.

Every Recap locator lives here, data-testid first (`recap-*`, test hooks only). Three reads name a class
because no test id can say it: a mark's `hit` / `miss` colour, a list panel's `data-off` state (the
attribute the page itself sets), and `labels_far_from_values`, which measures the row parts by the class
each carries. A game's Preview dossier and a player's profile are other views': a tap on them is made
here, what they draw is read through their own page objects.

Plant methods set what the page would hold (a story, a preview week), then draw again the way the page does.
`RecapNav` is the nav chrome's sub-row as the Recap tests read it, for the one journey that needs the nav.
"""
import re

SIDEWAYS = "document.scrollingElement.scrollWidth - innerWidth"
STORY = ("() => { LIVE_DIGEST.week = LIVE_RECAP.week; LIVE_DIGEST.story = {head: 'Allen torches the Bills for 285 yards <3', "
         "fact: 'Josh Allen threw four scores.', kind: 'result', asof: '2099-01-01 00:00:00', club: 'BUF', "
         "player: {n: 'Josh Allen', slug: LIVE_RECAP.top.slug, pos: 'QB', team: 'BUF'}}; render(); }")
CARDS = re.compile(r"^recap-(leaders|lists|tds|games|claude)$")
FAR = """limit => [...document.querySelectorAll('.wr-r, .wr-lr, .wr-g')].filter(r => {
  const n = r.querySelector('.wr-n, .wr-ln, .wr-sc'), v = r.querySelector('.wr-pts, .wr-nums, .wr-dots, .wr-pk');
  return n && v && v.getBoundingClientRect().right - n.getBoundingClientRect().left > limit; }).length"""
CLIPPED = """[...document.querySelectorAll('#view *')].filter(e =>
  /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4).map(e => String(e.className).slice(0, 40))"""


class RecapPage:

    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._tabs, self._body = tid("recap-tab"), tid("recap-body")
        self._lead, self._head, self._pills = tid("recap-lead"), tid("recap-lead-head"), tid("recap-lead-pills")
        self._pos, self._pos_head, self._leaders = tid("recap-pos"), tid("recap-pos-head"), tid("recap-leader")
        self._list_tabs, self._panels = tid("recap-list-tab"), tid("recap-list-panel")
        self._tds, self._td_more = tid("recap-td-row"), tid("recap-td-more")
        self._games, self._marks = tid("recap-game"), tid("recap-mark")
        self._tiles, self._calls = tid("recap-tile-value"), tid("recap-call")

    # ---- planting ----

    def plant_story(self):
        """Claude's story about the week's top scorer, as the Digest packet would carry it, drawn again."""
        self.page.evaluate(STORY)

    def plant_preview_week(self):
        """Preview holds the recap's week (the page week is still another one), drawn again."""
        self.page.evaluate("LIVE_PREVIEW.week = LIVE_RECAP.week; wrPaint(document.getElementById('view'))")

    def plant_page_week(self):
        """The page week is the recap's week too, drawn again."""
        self.page.evaluate("LIVE_SCHEDULE.week = LIVE_RECAP.week; wrPaint(document.getElementById('view'))")

    # ---- what a reader does ----

    def pick_tab(self, tab):
        """Tap a tab where the reader sees it: the view's own bar on a desktop, the tab row in the nav
        (chrome/tabrow.js, no test id of its own) on a phone; both carry data-wrtab."""
        self.page.locator(f"[data-wrtab='{tab}']:visible").first.click()

    def reload(self):
        """Load the page again, as a reader's refresh does."""
        self.page.reload()
        self._body.wait_for()

    def tap_lead(self):
        """The banner opens its player's profile."""
        self.page.get_by_test_id("recap-go").click()
        self.page.wait_for_selector("#modal.on")

    def pick_list(self, key):
        """Smashed / Busts / Left hurt on a phone: `smashed`, `busts` or `left`."""
        self._list_tabs.and_(self.page.locator(f"[data-wrlist='{key}']")).click()

    def toggle_touchdowns(self):
        self._td_more.click()

    def open_first_touchdown(self):
        self._tds.first.click()
        self.page.wait_for_selector("#modal.on")

    def open_game(self, text):
        """Tap the game whose line holds `text` (a button only when Preview holds the week)."""
        self._games.filter(has_text=text).and_(self.page.locator("button")).click()
        self.page.wait_for_function("SURFACE === 'preview'")

    def open_every_week(self):
        self.page.get_by_test_id("recap-every-week").click()

    # ---- what a reader sees: the bar and the body ----

    def tabs(self):
        return self._tabs.all_inner_texts()

    def tab_count(self):
        return self._tabs.count()

    def pressed_tab(self):
        return self._tabs.and_(self.page.locator("[aria-pressed='true']")).get_attribute("data-wrtab")

    def body_tab(self):
        return self._body.get_attribute("data-wrtabname")

    def stored_tab(self):
        return self.page.evaluate("localStorage.getItem('tw-recap-tab')")

    def sections(self):
        """How many of each card the body draws."""
        tid = self.page.get_by_test_id
        return {k: tid(f"recap-{k}").count() for k in ("leaders", "lists", "tds", "games", "claude")}

    def cards(self):
        return self.page.get_by_test_id(CARDS).count()

    def empty_title(self):
        return self.page.get_by_test_id("recap-empty-title").inner_text()

    def empty_count(self):
        """How many empty-state blocks the view draws: none while a tab has something to show."""
        return self.page.locator(".state-empty").count()

    def surface(self):
        return self.page.evaluate("SURFACE")

    def opened_preview_game(self):
        """The game Preview has open after a recap game opened it, as away + home ("PITCLE")."""
        return self.page.evaluate("pvGames()[PV_I].away + pvGames()[PV_I].home")

    def preview_record_open(self):
        """Whether Preview opened on its record (Past games), as "Every week" asks for."""
        return self.page.evaluate("PV_REC")

    # ---- the banner ----

    def lead_count(self):
        return self._lead.count()

    def headline(self):
        return self._head.inner_text()

    def lead_fact(self):
        return self.page.get_by_test_id("recap-lead-fact").inner_text()

    def lead_when(self):
        return self.page.get_by_test_id("recap-when").inner_text()

    def lead_pills(self):
        """The box line under the headline: one text per pill."""
        return self._pills.locator(":scope > *").all_inner_texts()

    # ---- Players ----

    def pos_heads(self):
        return self._pos_head.all_inner_texts()

    def leader_counts(self):
        """Rows in each position's block, in order."""
        return self._pos.evaluate_all("bs => bs.map(b => b.querySelectorAll('[data-testid=\"recap-leader\"]').length)")

    def _block(self, pos):
        return self._pos.filter(has=self._pos_head.filter(has_text=re.compile(f"^{pos}$")))

    def first_day(self, pos):
        """The first row's day line in a position's block (a kicker's is his box line)."""
        return self._block(pos).get_by_test_id("recap-day").first.inner_text()

    def openable(self, pos):
        """Rows in a position's block that open a player's page."""
        return self._block(pos).locator("button").count()

    def list_tab_labels(self):
        return self._list_tabs.all_inner_texts()

    def list_counts(self):
        return [s.strip() for s in self.page.get_by_test_id("recap-list-count").all_inner_texts()]

    def list_tab_count(self):
        return self._list_tabs.count()

    def open_panels(self):
        """The panels showing, by name: one on a phone."""
        shown = self._panels.and_(self.page.locator(":not([data-off])"))
        return [shown.nth(i).get_attribute("data-wrpanel") for i in range(shown.count())]

    def panel_text(self, key):
        return self._panels.and_(self.page.locator(f"[data-wrpanel='{key}']")).inner_text()

    def touchdown_rows(self):
        return self._tds.count()

    def touchdown_more(self):
        return self._td_more.inner_text()

    def touchdown_dots(self):
        """A dot per rushing, receiving or return score, row by row."""
        return self._tds.evaluate_all("rs => rs.map(r => r.querySelectorAll('[data-testid=\"recap-td-dots\"] i').length)")

    def touchdown_note(self):
        return self.page.get_by_test_id("recap-td-note").inner_text()

    # ---- Players on a desktop ----

    def list_tabs_hidden(self):
        return self.page.get_by_test_id("recap-list-tabs").is_hidden()

    def panels(self):
        """The three lists laid out: how many, whether all show, each one's top and left edge."""
        return {"count": self._panels.count(),
                "shown": self._panels.evaluate_all("ps => ps.every(p => p.offsetParent !== null)"),
                "tops": self._panels.evaluate_all("ps => ps.map(p => Math.round(p.getBoundingClientRect().top))"),
                "lefts": self._panels.evaluate_all("ps => ps.map(p => Math.round(p.getBoundingClientRect().left))")}

    def list_head_visible(self):
        return self.page.get_by_test_id("recap-list-head").first.is_visible()

    def leader_columns(self):
        """How many columns the leaders' board lays its positions in."""
        return self.page.get_by_test_id("recap-board").evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length")

    def labels_far_from_values(self, limit):
        """Rows (leader, list, touchdown, game) whose name sits more than `limit` px from its value."""
        return self.page.evaluate(FAR, limit)

    # ---- Scores ----

    def window_names(self):
        return self.page.get_by_test_id("recap-window-name").all_inner_texts()

    def first_window_times(self):
        return self.page.get_by_test_id("recap-window-times").first.inner_text()

    def game_count(self):
        return self._games.count()

    def game_buttons(self):
        return self._games.and_(self.page.locator("button")).count()

    def marks(self):
        """Claude's graded picks on the games: how many hit, how many missed."""
        return {"hit": self._marks.and_(self.page.locator(".hit")).count(),
                "miss": self._marks.and_(self.page.locator(".miss")).count(), "all": self._marks.count()}

    def strip(self):
        return self.page.get_by_test_id("recap-strip").inner_text()

    def strip_count(self):
        return self.page.get_by_test_id("recap-strip").count()

    def _game(self, text):
        return self._games.filter(has_text=text)

    def winner_of(self, text):
        """The bold side of the final score on the game whose line holds `text`."""
        return self._game(text).get_by_test_id("recap-score").locator("b").inner_text()

    def pick_of(self, text):
        return self._game(text).get_by_test_id("recap-pick").inner_text()

    def marks_in(self, text):
        return self._game(text).get_by_test_id("recap-mark").count()

    # ---- Claude ----

    def tile_values(self):
        return self._tiles.all_inner_texts()

    def tile_labels(self):
        return self.page.get_by_test_id("recap-tile-label").all_inner_texts()

    def call(self, n):
        """Claude's best call (0) or worst (1), as the card prints it."""
        return self._calls.nth(n).inner_text()

    # ---- fit ----

    def sideways(self):
        """How far the page scrolls sideways: 0 or less is none."""
        return self.page.evaluate(SIDEWAYS)

    def clipped_scrollers(self):
        """Elements inside the view that scroll sideways inside themselves."""
        return self.page.evaluate(CLIPPED)


class RecapNav:
    """The nav chrome around Recap: the This week sub-row and the hash, for the journey that crosses views."""

    def __init__(self, page):
        self.page = page

    def sub_row(self):
        return [s.strip() for s in self.page.locator("#subnav .mode-sub").all_inner_texts()]

    def sub_row_fits(self):
        return self.page.evaluate("document.querySelector('#subnav .subnav-in').scrollWidth <= document.querySelector('#subnav .subnav-in').clientWidth")

    def open_by_hash(self, leaf):
        self.page.evaluate("l => { location.hash = '#' + l; }", leaf)
        self.page.wait_for_function("l => document.getElementById('view').dataset.view === l", arg=leaf)

    def group(self):
        return self.page.evaluate("document.querySelector('#nav .navitem[aria-current=true]').dataset.s")

    def pressed_subs(self):
        return self.page.locator("#subnav .mode-sub[aria-pressed='true']").count()

    def go(self, leaf):
        self.page.evaluate("l => navGo(l)", leaf)

    def pressed_sub(self):
        return self.page.locator("#subnav .mode-sub[aria-pressed='true']").inner_text().strip()
