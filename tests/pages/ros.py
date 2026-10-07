"""Stats > Ranks > Rest of season (design/src/js/surface/ranks/ros.js) and the profile's Rest of season block
(surface/profile/ros.js): what a reader does there and what they see.

Every locator lives here, data-testid first (`ros-*` on the view, `profile-ros*` in the profile; test hooks only).
The two view tabs are the phone's tab-row segments (`#subnav .tr-seg`, chrome/nav.js) or, from 760px, the view's own
bar (`ranks-view-tab`): `pick_view` taps whichever is drawn. The positions are Ranks' own chips (`ranks-pos-tab`) on a
desktop and Stats' strip above the bottom bar (`stats-pos-seg`, pages/statspos.py) on a phone, since 2026-10-06.
"""
from pages.profile import ProfilePage

VIEWS = {"week": "This week", "ros": "Rest of season"}


class RosPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._rows, self._chart, self._sub = tid("ros-row"), tid("ros-chart"), tid("ros-sub")
        self._chips = tid("ranks-pos-tab").or_(tid("stats-pos-seg"))

    # ---- what a reader does ----

    def pick_view(self, view):
        """Tap the tab for "week" or "ros"; waits until the page says it is the open one."""
        seg = self.page.locator(f"#subnav [data-tseg='{view}']")
        (seg if seg.count() and seg.is_visible() else self.page.locator(f"[data-testid='ranks-view-tab'][data-rkview='{view}']")).click()
        self.page.wait_for_function("v => RK_VIEW === v", arg=view)

    def pick(self, pos):
        self._chips.and_(self.page.locator(f"[data-rkpos='{pos}']")).click()
        self.page.wait_for_function("p => RK_POS === p", arg=pos)

    def open_row(self, slug):
        """Tap a list row; returns his profile (pages/profile.py)."""
        self._rows.and_(self.page.locator(f"[data-rosopen='{slug}']")).click()
        self.page.wait_for_selector("#modal.on [data-testid='profile-title']")
        return ProfilePage(self.page)

    def open_label(self, slug):
        """Tap a name at a chart line's right end."""
        self.page.locator(f"[data-testid='ros-label'][data-rosopen='{slug}']").click()
        self.page.wait_for_selector("#modal.on [data-testid='profile-title']")
        return ProfilePage(self.page)

    def pick_team(self, key):
        self.page.evaluate("k => pickTeam(k)", key)

    # ---- what a reader sees ----

    def view_tabs(self):
        """The two view tabs as drawn: [(label, pressed)], from the tab row on a phone, else the view's bar."""
        seg = self.page.locator("#subnav .tr-seg")
        loc = seg if seg.count() and seg.first.is_visible() else self.page.get_by_test_id("ranks-view-tab")
        return [(t.strip(), p == "true") for t, p in zip(loc.all_text_contents(), loc.evaluate_all("els => els.map(e => e.getAttribute('aria-pressed'))"))]

    def has_view_tabs(self):
        return self.page.locator("#subnav .tr-seg").count() + self.page.get_by_test_id("ranks-view-tab").count() > 0

    def chips(self):
        return [s.strip() for s in self._chips.all_inner_texts()]

    def pressed_chip(self):
        return self._chips.and_(self.page.locator("[aria-pressed='true']")).inner_text().strip()

    def sub(self):
        return self._sub.inner_text().strip()

    def rows(self):
        """List rows in order: slug, rank, name, team, points, whether it is the reader's."""
        return self._rows.evaluate_all("""rs => rs.map(r => {
          const get = id => r.querySelector(`[data-testid="${id}"]`).textContent.trim();
          return {slug: r.dataset.rosopen, rank: +get("ros-rank"), name: get("ros-name"), team: get("ros-team"),
                  pts: get("ros-pts"), text: r.innerText.replace(/\\s+/g, " ").trim(), mine: r.classList.contains("mine")};
        })""")

    def chart(self):
        """The bump chart: each line's slug, whether it leads, its point count, whether it draws a line, its hollow dots;
        the labels and week names; the box on screen. None when there is no chart."""
        if not self._chart.count():
            return None
        return self._chart.evaluate("""c => {
          const box = c.getBoundingClientRect();
          return {box: {x: box.x, y: box.y + scrollY, w: box.width, h: box.height},
            lines: [...c.querySelectorAll('[data-testid="ros-line"]')].map(g => ({slug: g.dataset.slug, lead: g.classList.contains('lead'),
              points: g.querySelectorAll('.ros-dot').length, line: !!g.querySelector('polyline'),
              hollow: g.querySelectorAll('.ros-dot.over').length})),
            labels: [...c.querySelectorAll('[data-testid="ros-label"]')].map(l => l.textContent.trim()),
            weeks: [...c.querySelectorAll('[data-testid="ros-week"]')].map(w => w.textContent.trim()),
            axis: [...c.querySelectorAll('[data-testid="ros-axis"]')].map(w => w.textContent.trim())};
        }""")

    def empty(self):
        """The no-rows state's title, or None."""
        loc = self.page.get_by_test_id("ros-empty")
        return loc.inner_text().strip() if loc.count() else None

    def chart_top(self):
        """y of the chart's top edge in the page, as the phone's first data."""
        return round(self._chart.evaluate("c => c.getBoundingClientRect().y + scrollY"))

    def first_row_top(self):
        return round(self._rows.first.evaluate("r => r.getBoundingClientRect().y + scrollY"))

    def fits(self):
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    def surface(self):
        return self.page.evaluate("SURFACE")

    def tiers(self):
        """The This week list's tier labels: non-empty only on the This week view."""
        return self.page.get_by_test_id("ranks-tier").count()

    # ---- the profile's block ----

    def profile_block(self):
        """The open profile's Rest of season block, or None: points, points a game, games, rank, the chart's points."""
        loc = self.page.locator("#modal [data-testid='profile-ros']")
        if not loc.count():
            return None
        return loc.evaluate("""b => {
          const get = id => { const e = b.querySelector(`[data-testid="${id}"]`); return e ? e.textContent.trim().replace(/\\s+/g, " ") : null; };
          const svg = b.querySelector('[data-testid="profile-ros-chart"]');
          return {pts: get("profile-ros-pts"), lead: get("profile-ros-lead"), pg: get("profile-ros-pg"), games: get("profile-ros-games"),
            note: get("profile-ros-note"),
            chart: svg ? {dots: svg.querySelectorAll('.pfr-dot').length, line: !!svg.querySelector('polyline'),
                          axis: [...svg.querySelectorAll('[data-testid="ros-axis"]')].map(e => e.textContent.trim()),
                          weeks: [...svg.querySelectorAll('[data-testid="ros-week"]')].map(e => e.textContent.trim())} : null};
        }""")
