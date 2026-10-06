"""League > Recap's League section (surface/league/back.js, lead.js): its type, read for STYLE.md "Type: one voice
per line". Class selectors until surface/league/ has test ids, as in pages/league_chip.py."""

NAMES = ".lg-league .bp2-w b, .lg-league .bp2-l b, .bp2-ag b, .lg-luck-l li > b"


class LeagueRecapPage:
    def __init__(self, page):
        self.page = page

    def name_faces(self):
        """The font family of every manager's name in the section."""
        return self.page.evaluate("q => [...document.querySelectorAll(q)].map(e => getComputedStyle(e).fontFamily)", NAMES)

    def score_sides(self):
        """Per side of every score line: does its score share its name's face, with fixed-width digits?"""
        return self.page.evaluate("""() => [...document.querySelectorAll('.lg-league .bp2-w, .lg-league .bp2-l')].map(s => {
            const n = getComputedStyle(s.querySelector('.bp2-n')), b = getComputedStyle(s.querySelector('b'));
            return n.fontFamily === b.fontFamily && n.fontVariantNumeric.includes('tabular-nums'); })""")

    def stamps(self):
        """Every award and luck stamp: {case, face, px}."""
        return self.page.evaluate("""() => [...document.querySelectorAll('.lg-league .lg-stamp')].map(e => {
            const s = getComputedStyle(e); return {case: s.textTransform, face: s.fontFamily, px: parseFloat(s.fontSize)}; })""")

    def headline_face(self):
        """The face of the lead's headline, the section's display face."""
        return self.page.evaluate("getComputedStyle(document.querySelector('.lg-league .lg-hl')).fontFamily")

    def body_face(self):
        """The face of the lead's report, the section's body text."""
        return self.page.evaluate("getComputedStyle(document.querySelector('.bp2-report')).fontFamily")

    def drop_game_stamps(self):
        """Take every game's own stamp (the Nail-biter) off the cards, to lay out a card that has none."""
        self.page.evaluate("() => document.querySelectorAll('.lg-league .bp2-sgame').forEach(e => e.remove())")

    def card_rows(self):
        """Per game card, per team row: [name top, score top, every stamp's vertical centre] in px."""
        return self.page.evaluate("""() => [...document.querySelectorAll('.lg-league .lg-row')].map(card =>
            [...card.querySelectorAll('.bp2-sr')].map(r => {
              const top = e => Math.round(e.getBoundingClientRect().top), mid = e => { const b = e.getBoundingClientRect(); return Math.round((b.top + b.bottom) / 2); };
              return [top(r.querySelector('b')), top(r.querySelector('.bp2-n')), ...[...r.querySelectorAll('.lg-stamp')].map(mid)];
            }))""")

    def bottom_row_ends(self):
        """The bottom edge of each section in the bottom row (standings, luck, grudge), in px."""
        return self.page.evaluate("() => [...document.querySelectorAll('.lg-after > *')].map(e => Math.round(e.getBoundingClientRect().bottom))")

    def record_edges(self):
        """The distinct right edges of the standings' records, in px."""
        return sorted(set(self.page.evaluate(
            "() => [...document.querySelectorAll('.bp2-ag em')].map(e => Math.round(e.getBoundingClientRect().right))")))
