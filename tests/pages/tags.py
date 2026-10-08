"""Player tags as drawn (js/ui/tags.js, 2026-10-08): the one pill on a Roster row and a Ranks row, and the profile's
list. Every tag locator lives here (`roster-row-tag`, `ranks-row-tag`, `profile-tag*`, test hooks only). The rows and
the profile themselves are pages/roster.py's, pages/ranks.py's and pages/profile.py's.
"""


class TagsPage:
    def __init__(self, page):
        self.page = page

    def roster_tags(self):
        """{player name: the row's tag (its data-tag) or None}, for every Roster row drawn."""
        return self.page.get_by_test_id("roster-row").evaluate_all("""rs => Object.fromEntries(rs.map(r => {
          const tg = r.querySelector('[data-testid="roster-row-tag"]');
          return [r.querySelector('.nm-full').textContent, tg ? tg.dataset.tag : null];
        }))""")

    def roster_pill(self, name):
        """The pill on `name`'s row: its word, its hover text."""
        pill = self.page.get_by_test_id("roster-row").filter(has_text=name).first.get_by_test_id("roster-row-tag")
        return {"text": pill.inner_text().strip(), "title": pill.get_attribute("title")}

    def roster_layout(self):
        """Per starter row: its height, whether it has a pill and the pill's height, and whether the pill sits wholly above
        the bars and inside the row (None without a pill)."""
        return self.page.get_by_test_id("roster-row").evaluate_all("""rs => rs.filter(r => r.classList.contains('start')).map(r => {
          const tg = r.querySelector('[data-testid="roster-row-tag"]'), bars = r.querySelector('[data-testid="roster-row-bars"]');
          const box = r.getBoundingClientRect(), t = tg && tg.getBoundingClientRect(), b = bars && bars.getBoundingClientRect();
          return {h: Math.round(box.height), tagged: !!tg, pill: t ? Math.ceil(t.height) : null,
                  above: tg && b ? t.bottom <= b.top + 0.5 : null,
                  inside: tg ? t.top >= box.top && t.bottom <= box.bottom && t.right <= box.right : null};
        })""")

    def roster_heights_without_pills(self):
        """Each starter row's height with its pills taken out, in roster_layout's order; the pills come back after."""
        return self.page.evaluate("""() => {
          const pills = [...document.querySelectorAll('[data-testid="roster-row-tag"]')];
          pills.forEach(p => { p.style.display = 'none'; });
          const hs = [...document.querySelectorAll('[data-testid="roster-row"].start')].map(r => Math.round(r.getBoundingClientRect().height));
          pills.forEach(p => { p.style.display = ''; });
          return hs;
        }""")

    def ranks_tags(self):
        """{slug: the row's tag or None} for every Ranks row drawn."""
        return self.page.get_by_test_id("ranks-row").evaluate_all("""rs => Object.fromEntries(rs.map(r => {
          const tg = r.querySelector('[data-testid="ranks-row-tag"]');
          return [r.dataset.rkopen, tg ? tg.dataset.tag : null];
        }))""")

    def ranks_name_line_fits(self, slug):
        """True when the row's name line (name, MINE, tag) stays one line inside its row."""
        return self.page.locator(f"[data-rkopen='{slug}'] .rk-nm").evaluate(
            "el => el.scrollWidth <= el.clientWidth + 1 && el.getBoundingClientRect().height < 24")

    def profile_list(self):
        """The profile's tags in order: (word, the plain line), and every other text in the item, which should be none."""
        rows = self.page.get_by_test_id("profile-tag-item").evaluate_all("""items => items.map(li => [
          li.querySelector('[data-testid="profile-tag"]').textContent,
          li.querySelector('[data-testid="profile-tag-lines"]').textContent,
          li.textContent.length - li.querySelector('[data-testid="profile-tag"]').textContent.length
            - li.querySelector('[data-testid="profile-tag-lines"]').textContent.length])""")
        return [tuple(r) for r in rows]

    def profile_has_list(self):
        return self.page.get_by_test_id("profile-tags-list").count() == 1

    def plant_verdict(self, verdict):
        """Every player gets watch's verdict `verdict` (data/signals.js signalsFor), as a refresh that flagged him would."""
        self.page.evaluate("v => { window.signalsFor = () => ({verdict: v, why: ''}); }", verdict)

    def verdict_shown(self):
        return self.page.get_by_test_id("profile-verdict").count() == 1
