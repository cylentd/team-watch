"""League > Trade history's top row: the Best and Worst trader cards and the heists beside them
(design/src/js/surface/trades/trades.js trTopHTML, trFormHTML). Added 2026-11-01, when the two lead cards stopped
showing a trade. Methods return plain data and never assert. Class selectors for the cards until trades.js gives
them `data-testid`s; the strip has its own.
"""

STRIP = "[data-testid='trades-form']"
MARK = "[data-testid='trades-form-mark']"


class TradeHistoryLead:
    def __init__(self, page):
        self.page = page

    def card(self, kind):
        """A lead card ("best" or "worst") as drawn: its headline, deck, strip and anything of a trade inside it."""
        return self.page.evaluate("""([kind, strip, mark]) => {
            const c = document.querySelector(`#view .tr-top-row > .tr-lead-card.${kind}`);
            const s = c.querySelector(strip);
            return {head: c.querySelector('h3').textContent.trim(), deck: c.querySelector('.tr-deck').textContent.trim(),
                    n: c.querySelector('.tr-bx-hd > span:last-child').textContent.trim(),
                    marks: [...c.querySelectorAll(mark)].map(e => e.textContent.trim()),
                    aria: s && s.getAttribute('aria-label'), role: s && s.getAttribute('role'),
                    tradeRows: c.querySelectorAll('.tr-sc').length, faces: c.querySelectorAll('.tr-face').length,
                    foot: c.querySelectorAll('.tr-bx-ft').length};
        }""", [kind, STRIP, MARK])

    def has_strip(self, kind):
        return self.page.locator(f"#view .tr-lead-card.{kind} {STRIP}").count() == 1

    def mark_kinds(self, kind):
        """Each mark's result as its colour class and its letter: the mark may not lean on colour alone."""
        return self.page.eval_on_selector_all(f"#view .tr-lead-card.{kind} {MARK}",
                                              "els => els.map(e => [e.className.split(' ').pop(), e.textContent.trim()])")

    def strip_lines(self, kind):
        """How many lines the marks take, how far any runs past the strip's right edge, a mark's size and the
        px between one line's marks and the next's, in px."""
        return self.page.evaluate("""([kind, strip, mark]) => {
            const s = document.querySelector(`#view .tr-lead-card.${kind} ${strip}`), r = s.getBoundingClientRect();
            const m = [...s.querySelectorAll(mark)].map(e => e.getBoundingClientRect());
            const tops = [...new Set(m.map(b => Math.round(b.top)))].sort((a, b) => a - b);
            return {lines: tops.length, over: Math.max(...m.map(b => b.right - r.right)), width: m[0].width, height: m[0].height,
                    between: tops.length > 1 ? tops[1] - tops[0] - m[0].height : 0};
        }""", [kind, STRIP, MARK])

    def strip_room(self, kind):
        """Where a lead card spends its spare height (STYLE.md "Gaps": the top and bottom hold their edges, the
        middle block centres), in px; `marksBottom` and `keyTop` are from the viewport's top."""
        return self.page.evaluate("""([kind, strip]) => {
            const c = document.querySelector(`#view .tr-lead-card.${kind}`), f = c.querySelector('.tr-form').getBoundingClientRect();
            const hd = c.querySelector('.tr-bx-hd').getBoundingClientRect(), name = c.querySelector('.tr-deck').parentElement.getBoundingClientRect();
            const key = c.querySelector('.tr-form-key').getBoundingClientRect(), s = c.querySelector(strip).getBoundingClientRect();
            return {aboveName: name.top - hd.bottom, underName: f.top - name.bottom, toCardFoot: c.getBoundingClientRect().bottom - f.bottom,
                    marksBottom: s.bottom, keyTop: key.top};
        }""", [kind, STRIP])

    def top_row(self):
        """The cards left to right: each one's kind, its players as drawn, its box and the free space under it."""
        return self.page.evaluate("""() => [...document.querySelectorAll('#view .tr-top-row > .tr-bx')].map(c => {
            const r = c.getBoundingClientRect(), last = c.lastElementChild.getBoundingClientRect();
            return {lead: c.classList.contains('tr-lead-card'), players: [...c.querySelectorAll('.tr-pls b')].map(b => b.textContent.trim()),
                    top: Math.round(r.top), height: Math.round(r.height), under: Math.round(r.bottom - last.bottom)};
        })""")

    def card_clips(self):
        """Top-row cards with something past their right edge."""
        return self.page.evaluate("""() => [...document.querySelectorAll('#view .tr-top-row > .tr-bx')].filter(c => [...c.querySelectorAll('*')]
            .some(e => e.getBoundingClientRect().right > c.getBoundingClientRect().right + 0.5)).length""")
