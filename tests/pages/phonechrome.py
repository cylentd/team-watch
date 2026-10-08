"""The phone's chrome at the top of the screen (css/chrome/phonenav.css): the header bar (`chrome-header`,
holding #hdrteam and Ask) and the tab row under it (`chrome-tabrow`, #subnav). Test hooks only.
"""
HEADER, TABROW = "chrome-header", "chrome-tabrow"
# Scroll events (and so any class they set on the body) land in the next rendering step: two frames.
FRAMES = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"


class PhoneChrome:
    def __init__(self, page):
        self.page = page

    def lengthen(self, px):
        """Hang a block `px` tall under the view, so a fixture view too short to scroll has room to."""
        self.page.evaluate("""px => { const d = document.createElement('div'); d.style.height = px + 'px';
          document.getElementById('view').append(d); }""", px)

    def scroll_through(self, ys, step=60):
        """Scroll from where the page is to each y in turn, `step` px a frame, as a finger does. Returns
        scrollY at the end."""
        return self.page.evaluate("""async ([ys, step]) => {
          const frame = () => new Promise(r => requestAnimationFrame(r));
          for (const y of ys) {
            const dir = Math.sign(y - scrollY);
            for (let at = scrollY; dir && (at - y) * dir < 0; ) { at = dir > 0 ? Math.min(y, at + step) : Math.max(y, at - step); scrollTo(0, at); await frame(); }
          }
          return Math.round(scrollY);
        }""", [list(ys), step])

    def edges(self):
        """Screen y of the header's top and bottom and of the tab row's top, once the scroll has landed."""
        self.page.evaluate(FRAMES)
        return self.page.evaluate("""([h, t]) => {
          const top = id => document.querySelector(`[data-testid="${id}"]`).getBoundingClientRect();
          const a = top(h), b = top(t);
          return {header_top: Math.round(a.top), header_bottom: Math.round(a.bottom), row_top: Math.round(b.top)};
        }""", [HEADER, TABROW])


# The bottom tab bar (#tabbar): on a phone the groups and search; on a desktop display:contents, no box.
TABBAR = "chrome-tabbar"
CHROME_PARTS = {"header": HEADER, "tab row": TABROW, "bottom bar": TABBAR}
# Which side of each part meets the content: the header and tab row end at their bottom, the bar starts at its top.
EDGE_SIDE = {"header": "bottom", "tab row": "bottom", "bottom bar": "top"}


class PhoneBar:
    """The bottom bar's words and where Search sits (2026-10-08, nav regroup to Team · Matchup · Players · League ·
    Bets): Search left the bar for the header, beside Ask."""

    def __init__(self, page):
        self.page = page

    def words(self):
        """The bottom bar's visible words, left to right."""
        return self.page.evaluate("""id => [...document.querySelectorAll(`[data-testid="${id}"] button`)]
          .filter(b => b.getBoundingClientRect().width > 0).map(b => b.innerText.trim())""", TABBAR)

    def search_place(self):
        """{in_header, in_bar, beside_ask, on_screen} for the Search button (#navsearch, the shell's id)."""
        return self.page.evaluate("""([h, bar]) => {
          const s = document.getElementById('navsearch'), ask = document.getElementById('chatfab');
          const r = s.getBoundingClientRect(), a = ask.getBoundingClientRect(), head = document.querySelector(`[data-testid="${h}"]`).getBoundingClientRect();
          return {in_header: r.top >= head.top && r.bottom <= head.bottom && r.width > 0,
                  in_bar: !!s.closest(`[data-testid="${bar}"]`),
                  beside_ask: Math.round(a.left - r.right) >= 0 && Math.round(a.left - r.right) <= 8,
                  on_screen: r.left >= 0 && r.right <= innerWidth};
        }""", [HEADER, TABBAR])


class ChromeSurface:
    """The chrome's own surface (2026-10-08, TODO "chrome stands apart from content"): what each part of the
    chrome paints, beside a card's and the page's, all as computed by the browser."""

    def __init__(self, page):
        self.page = page

    def paint(self, card_row):
        """{part: {bg, edge}} for every chrome part, plus "card" (the first box with a background around
        the first `card_row` test id) and "page" (the body). `edge` is the border on the side that meets
        the content, or None when that border is not drawn."""
        return self.page.evaluate("""([parts, sides, row]) => {
          const paint = (el, side) => {
            const cs = getComputedStyle(el), w = parseFloat(cs[`border-${side}-width`]);
            return {bg: cs.backgroundColor, edge: w > 0 && cs[`border-${side}-style`] !== 'none' ? cs[`border-${side}-color`] : null};
          };
          const out = {};
          for (const [name, id] of Object.entries(parts))
            out[name] = paint(document.querySelector(`[data-testid="${id}"]`), sides[name]);
          let card = document.querySelector(`[data-testid="${row}"]`);
          while (card && /rgba\\(0, 0, 0, 0\\)|transparent/.test(getComputedStyle(card).backgroundColor)) card = card.parentElement;
          out.card = paint(card, 'top');
          out.page = paint(document.body, 'top');
          return out;
        }""", [CHROME_PARTS, EDGE_SIDE, card_row])
