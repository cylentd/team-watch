"""The stat line under a name on the Roster's Week plays card (design/src/js/surface/teams/reel.js, data/weekstat.js),
read as a reader sees it: the words and whether they fit the card whole. Built on `ClipsPage` (pages/clips.py)."""
from pages.clips import ClipsPage


class ReelStatPage(ClipsPage):
    def plant_box_scores(self, rows):
        """The week's box score rows for the players in `rows` ({slug: fields}), replacing any the page had for the
        clips' week, then draw the Roster again."""
        self.page.evaluate("""(rows) => {
          const wk = LIVE_CLIPS.week;
          LIVE_GAMELOG.rows = LIVE_GAMELOG.rows.filter(r => !(r.slug in rows && r.wk === wk));
          for (const [slug, f] of Object.entries(rows)) LIVE_GAMELOG.rows.push({slug, wk, pts: 10, ...f});
          render();
        }""", rows)

    def lines(self):
        """Each card's stat line, in rail order: {nm, text, fits}. `fits` is true when the words are not wider
        than their box, so nothing is cut (the box ellipsizes what overflows) once the fonts are in."""
        return self.page.evaluate("""async () => {
          await document.fonts.ready;
          return [...document.querySelectorAll('[data-testid="clips-card"]')].map(c => {
            const l2 = c.querySelector('[data-testid="clips-l2"]');
            return {nm: c.querySelector('[data-testid="clips-nm"]').textContent, text: l2.textContent,
                    fits: l2.scrollWidth <= l2.clientWidth, w: l2.clientWidth};
          });
        }""")

    def narrow_to(self, px):
        """Make every card's line box `px` wide: a card narrower than any a phone draws, and the rail fits again."""
        self.page.evaluate("""(px) => {
          document.querySelectorAll('[data-testid="clips-l2"]').forEach(e => { e.style.width = px + 'px'; });
          window.dispatchEvent(new Event('resize'));
        }""", px)
