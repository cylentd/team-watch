"""League > Trades, the finder (design/src/js/surface/finder/, 2026-10-06), and the offer cards it draws.

Every locator for the finder lives here, `data-testid` first (`finder-*`, test hooks only); the offer card's own
parts (columns, rows, pills) keep the class names the edit page shares (`.tb-*`). Methods return plain data and never
assert. `finder(mount, pick)` opens the Trades view for a reader with the fixture's offers served in place of the real
fetch, which from file:// the browser refuses.
"""
import json
import re

from conftest import FIXTURES

FIXTURE = json.loads((FIXTURES / "data" / "trade_offers.json").read_text(encoding="utf-8"))

# Replaces the page's fetch of the offers. window.__tb is the mode ("ok", "fail", "hold" until __tbRelease()),
# __tbFetches how many times the page asked.
PLANT = """(() => {
  window.__tb = "ok"; window.__tbFetches = 0;
  const real = window.fetch.bind(window), body = %s;
  window.fetch = (url, ...rest) => {
    if (!String(url).includes("trade_offers.json")) return real(url, ...rest);
    window.__tbFetches++;
    const reply = () => window.__tb === "ok" ? new Response(JSON.stringify(body), {status: 200}) : Promise.reject(new TypeError("Failed to fetch"));
    if (window.__tb !== "hold") return Promise.resolve(reply());
    return new Promise(res => { window.__tbRelease = () => { window.__tb = "ok"; res(reply()); }; });
  };
})();"""
COPY_REFUSED = "navigator.clipboard.writeText = () => Promise.reject(new DOMException('no', 'NotAllowedError'));"


def serve(body):
    """An init script that makes the page fetch `body` for trade_offers.json."""
    return PLANT % json.dumps(body)


def reader(key):
    """An init script for a reader whose team is `key` (a TEAMS key), or nobody's with None."""
    if key is None:
        return 'try { localStorage.removeItem("tw-team"); } catch (e) {}'
    return f'try {{ localStorage.setItem("tw-team", "{key}"); }} catch (e) {{}}'


def finder(mount, pick, size=(360, 740), init=(), body=None):
    """(page, errors): the Trades view at `size` for the reader `pick`, offers from `body` (the fixture's by default)."""
    page, errors = mount("trades", size=size, init=(reader(pick), serve(body or FIXTURE), *init))
    ctx = page.context
    if not getattr(ctx, "tw_clipboard_granted", False):     # a permission outlasts the page's reloads: once per kept context
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])
        ctx.tw_clipboard_granted = True
    return page, errors


TAP_ALL = """([scope, names]) => names.forEach(n => {
  const el = [...document.querySelectorAll(scope)].find(e => e.dataset.tbpick === n);
  if (!el) throw new Error("no " + scope + " for " + n);
  el.click();
})"""


def tap_all(page, names, scope=".tb-r"):
    """Tap each named player in the edit page in turn, in one round trip: `scope` is `.tb-r` for a roster row and
    `.tb-pkg [data-tbpick]` for a package row. For setup taps a test does not itself assert on; a tap a test is about
    goes through `page.locator(...).click()`, with its checks that the row can be reached. A missing row throws."""
    page.evaluate(TAP_ALL, [scope, list(names)])


def builder(page, key):
    """The finder filtered to team `key`, from the Who's deep list: every offer with him, the way the old builder page showed them."""
    page.locator(f"[data-tfwho='{key}']").click()
    page.wait_for_selector("[data-testid=finder-with]")
    page.wait_for_selector("[data-testid=finder-card], [data-testid=finder-empty], [data-testid=finder-error]")


CARDS = """cards => cards.map(c => {
  const text = e => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  const q = id => c.querySelector(`[data-testid="${id}"]`);
  const side = i => [...c.querySelectorAll(".tb-col")[i].querySelectorAll(".tb-p")].map(r => text(r));
  return {partner: text(q("finder-partner")), record: text(q("finder-record")), send: side(0), get: side(1),
    gain: text(q("finder-gain")), ir: text(c.querySelector(".tb-ir")), drop: text(c.querySelector(".tb-drop"))};
})"""

DEEP = """rows => rows.map(r => {
  const text = e => e ? e.textContent.replace(/\\s+/g, " ").trim() : null;
  const q = id => r.querySelector(`[data-testid="${id}"]`), v = q("finder-deepval");
  return {key: q("finder-deepname").dataset.tfwho, name: text(q("finder-deepname").querySelector("b")), record: text(q("finder-deepname").querySelector("small")),
    val: text(v), tone: v.classList.contains("up") ? "up" : v.classList.contains("dn") ? "dn" : "", starters: text(q("finder-deepstarters"))};
})"""


class FinderPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._chips, self._cards, self._deep = tid("finder-chip"), tid("finder-card"), tid("finder-deeprow")

    # ---- what a reader does ----

    def pick(self, pos):
        """Tap a position chip and wait for it to be the pressed one."""
        self._chip(pos).click()
        self.page.wait_for_function("p => [...document.querySelectorAll('[data-testid=finder-chip]')]"
                                    ".some(b => b.dataset.tfpos === p && b.getAttribute('aria-pressed') === 'true')", arg=pos)

    def open_partner(self, name):
        """Tap a team's name in Who's deep: the finder filtered to him."""
        self.page.get_by_test_id("finder-deepname").filter(has=self.page.locator("b", has_text=re.compile(f"^{re.escape(name)}$"))).click()
        self.page.wait_for_selector("[data-testid=finder-with]")

    def all_positions(self):
        self.page.get_by_test_id("finder-all").click()
        self.page.wait_for_selector("[data-testid=finder-chip]")

    def wait_offers(self):
        """The offers section is out of its skeleton: cards, an empty state or an error."""
        self.page.wait_for_selector("[data-testid=finder-card], [data-testid=finder-empty], [data-testid=finder-error]")

    def pick_team(self, name):
        """With no team picked: tap a team in the picker."""
        self.page.locator(".tp-team", has_text=re.compile(f"^{re.escape(name)}$")).click()

    # ---- what a reader sees ----

    def chips(self):
        """The chip row in order: position, signed gap, pressed, tone."""
        return self._chips.evaluate_all("""bs => bs.map(b => ({pos: b.dataset.tfpos, gap: b.querySelector('b').textContent.trim(),
          pressed: b.getAttribute('aria-pressed') === 'true', tone: b.querySelector('b').className}))""")

    def pressed(self):
        return [c["pos"] for c in self.chips() if c["pressed"]]

    def cards(self):
        return self._cards.evaluate_all(CARDS)

    def partners(self):
        return [c["partner"] for c in self.cards()]

    def deep(self):
        return self._deep.evaluate_all(DEEP)

    def deep_title(self):
        return self.page.get_by_test_id("finder-deep").locator("h2").inner_text()

    def offers_heading(self):
        return self.page.get_by_test_id("finder-offers").locator("h2").inner_text()

    def with_title(self):
        t = self.page.get_by_test_id("finder-with")
        return t.inner_text() if t.count() else None

    def is_filtered(self):
        return self.page.get_by_test_id("finder-with").count() == 1

    def empty_text(self):
        e = self.page.get_by_test_id("finder-empty")
        return e.inner_text() if e.count() else None

    def need_text(self):
        n = self.page.get_by_test_id("finder-need")
        return n.inner_text() if n.count() else None

    def picker_teams(self):
        return self.page.locator(".tp-team").all_inner_texts()

    def has_own(self):
        return self.page.get_by_test_id("finder-own").count() == 1

    def first_card_y(self):
        """Where the first offer card starts, in page pixels."""
        return self._cards.first.evaluate("e => e.getBoundingClientRect().top + scrollY")

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    # ---- where things sit (x, y, w, h in page pixels; for the desktop layout) ----

    def frame_box(self):
        """The page's frame, as the team line spans it: what every League leaf fills."""
        return self._box(self.page.locator(".lgchip").first)

    def chips_box(self):
        return self._box(self.page.locator(".tf-chips"))

    def card_boxes(self):
        return self._boxes(self._cards)

    def deep_boxes(self):
        return self._boxes(self._deep)

    def picker_boxes(self):
        """With no team picked: one box per league's list of teams."""
        return self._boxes(self.page.locator(".tp-lg"))

    def open_edit(self, i=0):
        """Tap Edit on offer card `i`: the edit page, with its tray."""
        self.page.locator(f"[data-tbedit='{i}']").click()
        self.page.wait_for_selector(".tb-edfoot")

    def edit_boxes(self):
        """The edit page's tray and, inside it, the gain and the Reset / Copy offer pair."""
        return {"tray": self._box(self.page.locator(".tb-edfoot")), "gain": self._box(self.page.locator(".tb-edfoot .tb-gain")),
                "acts": self._box(self.page.locator(".tb-edfoot .tb-acts")), "package": self._box(self.page.locator(".tb-pkg"))}

    def empty_box(self):
        return self._box(self.page.get_by_test_id("finder-empty"))

    @staticmethod
    def _box(loc):
        return loc.evaluate("e => { const r = e.getBoundingClientRect(); return {x: r.left, y: r.top + scrollY, w: r.width, h: r.height}; }")

    @staticmethod
    def _boxes(loc):
        return loc.evaluate_all("es => es.map(e => { const r = e.getBoundingClientRect(); return {x: r.left, y: r.top + scrollY, w: r.width, h: r.height}; })")

    def _chip(self, pos):
        return self._chips.and_(self.page.locator(f"[data-tfpos='{pos}']"))
