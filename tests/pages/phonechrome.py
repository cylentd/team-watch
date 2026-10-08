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
