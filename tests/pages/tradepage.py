"""League > Trades, a player's trade page (design/src/js/surface/finder/tpage.js, 2026-10-08, ledger #51), and the
profile footer that opens it (surface/profile/tradefoot.js).

Every locator for the page lives here, `data-testid` first (`tpg-*`, `profile-foot*`, test hooks only). Methods return
plain data and never assert. `trade_page(mount, pick, hash)` opens the Trades view straight on a page's hash, as a
shared link does, with the fixture's offers served (pages/finder.py) and, when given, a pinned file."""

from pages.finder import finder

# Answers the page's fetch of an owner's pinned file from window.__tpFiles (a {url: file} map, set after the load);
# any other pinned file is a 404. One script for every test, so the module keeps one context per reader and size.
PINS = """(() => {
  const real = window.fetch.bind(window);
  window.__tpFiles = {}; window.__tpFetches = [];
  window.fetch = (url, ...rest) => {
    const u = String(url), files = window.__tpFiles;
    if (!u.startsWith("trade_pins/")) return real(url, ...rest);
    window.__tpFetches.push(u);
    return Promise.resolve(u in files ? new Response(JSON.stringify(files[u]), {status: 200}) : new Response("", {status: 404}));
  };
})();"""


def pins():
    """The init script that answers the page's trade_pins fetches (see PINS)."""
    return PINS


def at(hash_):
    """An init script that opens the page on `hash_` instead of the view's own, as a shared link would."""
    return f'history.replaceState(null, "", "#{hash_}");'


SET_FILES = "f => { window.__tpFiles = f; }"


PLANT_TEAMS = "names => { const lg = LIVE_TEAMS.leagues.find(l => l.key === 'espn'); names.forEach(n => lg.teams.push({key: 'espn-' + n, name: n})); }"


def trade_page(mount, pick, hash_, size=(360, 740), files=None, linked=False, teams=()):
    """(TradePage, errors): the page at `hash_` for the reader `pick`, once its rows or its one line are drawn. The
    Trades view loads first and the hash then moves, as a tap inside the page does; `linked` loads the page straight on
    the hash instead, as a shared link does. `files` are the pinned files served (none: every pinned fetch is a 404).
    `teams` are names added to the fixture's ESPN league (it has only the two teams with offers) before the page draws."""
    init = (pins(), at(hash_)) if linked else (pins(),)
    page, errors = finder(mount, pick, size=size, init=init)
    page.evaluate(SET_FILES, files or {})
    if teams:
        page.evaluate(PLANT_TEAMS, list(teams))
    tp = TradePage(page)
    if not linked:
        tp.go(hash_)
    tp.wait()
    return tp, errors


ROWS = """rows => rows.map(r => {
  const text = e => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  const g = r.querySelector('[data-testid="tpg-gains"]');
  return {main: text(r.querySelector('[data-testid="tpg-main"]')), sub: text(r.querySelector('[data-testid="tpg-sub"]')),
    me: text(g.querySelector('b')), them: text(g.querySelector('small')), tone: g.querySelector('b').className,
    open: r.getAttribute('aria-expanded') === 'true'};
})"""


class TradePage:
    def __init__(self, page):
        self.page = page
        self._rows = page.get_by_test_id("tpg-row")

    # ---- what a reader does ----

    def wait(self):
        """The page is out of its loading shapes: rows, one line why, or the error."""
        self.page.wait_for_selector("[data-testid=tpg-row], [data-testid=tpg-why], [data-testid=tpg-error], [data-testid=finder-need]")

    def go(self, hash_):
        """A link inside the page to another trade page (or the finder): the hash moves, the page draws."""
        self.page.evaluate("h => { location.hash = h; }", hash_)
        self.page.wait_for_function("h => location.hash === '#' + h && document.querySelector('.tpg')", arg=hash_)

    def tap_row(self, i):
        self._rows.nth(i).click()

    def add(self, slug):
        """Add a player to shop: the picker under Add a player."""
        self.page.get_by_test_id("tpg-add").select_option(slug)
        self.page.wait_for_selector("[data-testid=tpg-drop]")      # the page drew the pair, not just moved its hash

    def drop(self, i):
        self.page.get_by_test_id("tpg-drop").nth(i).click()

    def back(self):
        self.page.get_by_test_id("tpg-back").click()
        self.page.wait_for_function("location.hash === '#trades'")

    def own(self):
        """Make your own offer with him: the edit page."""
        self.page.get_by_test_id("tpg-own").click()
        self.page.wait_for_selector(".tb-edfoot")

    def copy(self):
        self.page.get_by_test_id("finder-copy").first.click()

    # ---- what a reader sees ----

    def hash(self):
        return self.page.evaluate("location.hash")

    def title(self):
        return self.page.get_by_test_id("tpg-title").inner_text()

    def line(self):
        loc = self.page.locator(".tpg-id")
        return loc.inner_text() if loc.count() else None

    def heads(self):
        """The column heads as written (the page sets them in capitals)."""
        return self.page.locator(".tpg-lh span").evaluate_all("ss => ss.map(s => s.textContent.trim())")

    def rows(self):
        return self._rows.evaluate_all(ROWS)

    def none(self):
        n = self.page.get_by_test_id("tpg-none")
        return n.inner_text().replace("\n", " | ") if n.count() else None

    def why(self):
        w = self.page.get_by_test_id("tpg-why")
        return w.inner_text() if w.count() else None

    def cards(self):
        """The offer cards open under rows: their partner names."""
        return self.page.get_by_test_id("finder-card").locator("[data-testid=finder-partner]").all_inner_texts()

    def card_buttons(self):
        return self.page.get_by_test_id("finder-card").locator("button").all_inner_texts()

    def own_text(self):
        o = self.page.get_by_test_id("tpg-own")
        return o.inner_text() if o.count() else None

    def add_options(self):
        return self.page.get_by_test_id("tpg-add").locator("option[value]:not([value=''])").evaluate_all("os => os.map(o => o.value)")

    def shopped(self):
        return self.page.get_by_test_id("tpg-drop").all_inner_texts()

    def has_add(self):
        return self.page.get_by_test_id("tpg-add").count() == 1

    def error(self):
        return self.page.get_by_test_id("tpg-error").count() == 1

    def need(self):
        n = self.page.get_by_test_id("finder-need")
        return n.inner_text() if n.count() else None

    def pin_fetches(self):
        return self.page.evaluate("window.__tpFetches")

    def locked(self):
        """In the edit page: the package's locked rows, and the roster rows that cannot be tapped."""
        return {"package": self.page.get_by_test_id("finder-locked").evaluate_all(
                    "rs => rs.map(r => [...r.children].map(c => c.textContent.trim()).filter(Boolean).join(' '))"),
                "disabled": self.page.locator(".tb-r[disabled]").evaluate_all("bs => bs.map(b => b.dataset.tbpick)")}

    def column_box(self):
        """The page's column, in page pixels."""
        return self.page.locator(".tpg-list").evaluate("e => { const r = e.getBoundingClientRect(); return {x: r.left, w: r.width}; }")

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")


class ProfileFoot:
    """The footer of the player profile (#modal)."""

    def __init__(self, page):
        self.page = page
        self._foot = page.get_by_test_id("profile-foot")

    def open(self, player):
        """Open the profile for `player` ({n, pos, team, slug}), as a row's tap does."""
        self.page.evaluate("p => openProfile(p, null)", player)
        self.page.wait_for_selector("#modal.on [data-testid=profile-foot]")

    def buttons(self):
        """The footer's visible buttons, left to right."""
        return self._foot.locator("button:visible").all_inner_texts()

    def trade(self):
        self.page.get_by_test_id("profile-trade").click()

    def close(self):
        self.page.get_by_test_id("profile-foot-close").click()

    def is_open(self):
        return self.page.evaluate("document.getElementById('modal').classList.contains('on')")

    def foot_box(self):
        """The footer and the modal, in viewport pixels: the footer sits on the modal's bottom edge."""
        return self.page.evaluate("""() => { const f = document.querySelector('[data-testid=profile-foot]').getBoundingClientRect(),
          m = document.getElementById('modal').getBoundingClientRect(); return {foot_bottom: f.bottom, modal_bottom: m.bottom, h: f.height}; }""")
