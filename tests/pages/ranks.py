"""Stats > Ranks (design/src/js/surface/ranks/): what a reader can do there and what they see.

Every Ranks locator lives here, data-testid first (`ranks-*`, test hooks only). The "No line" tag is
drawn by data/rbrules.js for several views, so it is found by its class inside a Ranks row. A row opens
the profile, which pages/profile.py owns: `open_player` returns its ProfilePage. The Waivers link is the
one way out of Ranks a test needs; it moves to pages/waivers.py when that exists.
"""
from pages.profile import ProfilePage

POSITIONS = {"D/ST": "DST"}       # a chip's label -> its data-rkpos, where they differ
# The position row as drawn: Ranks' own chips on a desktop, Stats' strip above the bottom bar on a phone
# (pages/statspos.py, 2026-10-06). The strip's host is always in the page, hidden off a phone.
POS_ROW = "[data-testid='ranks-pos-row'], [data-testid='stats-pos-strip']:not([hidden])"


class RanksPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._tabs, self._tab_row = tid("ranks-pos-tab").or_(tid("stats-pos-seg")), page.locator(POS_ROW)
        self._rows, self._dst_rows, self._sub = tid("ranks-row"), tid("ranks-dst-row"), tid("ranks-sub")

    # ---- what a reader does ----

    def pick(self, pos):
        """Tap a position: "QB", "RB", "WR", "TE", "FLEX", "DST" (or "D/ST"), "K". A chip on a desktop, the
        strip's segment on a phone."""
        pos = POSITIONS.get(pos, pos)
        self._tabs.and_(self.page.locator(f"[data-rkpos='{pos}']")).click()
        self.page.wait_for_function("p => RK_POS === p", arg=pos)

    def open_player(self, slug):
        """Tap a player's row; returns his profile (pages/profile.py) once it is open."""
        self._row(slug).click()
        self.page.wait_for_selector("#modal.on [data-testid='profile-lede']")
        return ProfilePage(self.page)

    def open_first_row(self):
        self._rows.first.click()
        self.page.wait_for_selector("#modal.on")
        return ProfilePage(self.page)

    def pick_team(self, key):
        """Switch the reader's team (the one chip, chrome/teamswitch.js) as a tap would."""
        self.page.evaluate("k => pickTeam(k)", key)

    # ---- what a reader sees ----

    def chips(self):
        return [s.strip() for s in self._tabs.all_inner_texts()]

    def pressed(self):
        return self._tabs.and_(self.page.locator("[aria-pressed='true']")).inner_text().strip()

    def rows(self):
        """Player rows in order: slug, points shown, matchup tag (or None), FLEX position, mine."""
        return self._rows.evaluate_all("""rs => rs.map(r => {
          const get = id => r.querySelector(`[data-testid="${id}"]`);
          return {slug: r.dataset.rkopen, pts: get("ranks-pts").firstChild.textContent,
                  mx: get("ranks-mx") ? get("ranks-mx").textContent : null,
                  mx_up: get("ranks-mx") ? get("ranks-mx").classList.contains("up") : null,
                  pos: get("ranks-row-pos") ? get("ranks-row-pos").textContent : null,
                  mine: r.classList.contains("mine")};
        })""")

    def tiers(self):
        return [s.strip() for s in self.page.get_by_test_id("ranks-tier").all_inner_texts()]

    def sub(self):
        """The line under the heading: scoring, the notes, the teams left off."""
        return self._sub.first.inner_text()

    def dst_rows(self):
        """D/ST or K rows in order: team, streamer tag shown, MINE tag shown."""
        return self._dst_rows.evaluate_all("""rs => rs.map(r => ({team: r.dataset.rkteam,
          streamer: !!r.querySelector('[data-testid="ranks-dst-streamer"]'),
          mine: r.classList.contains('mine') && !!r.querySelector('.rk-dhold.mine')}))""")

    def dst_mine_teams(self):
        """The D/ST or K rows wearing the MINE tag, by club."""
        return {r["team"] for r in self.dst_rows() if r["mine"]}

    def schedule_link(self):
        link = self.page.get_by_test_id("ranks-schedule")
        return {"text": link.inner_text().strip(), "goes": link.get_attribute("data-rkgo")}

    def fits(self):
        """Nothing wider than the screen."""
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    def chips_fit(self):
        """The position chips (or strip segments) on one row, none cut off, its words included."""
        return self._tab_row.evaluate("e => e.scrollWidth <= e.clientWidth && [...e.querySelectorAll('button')].every(b => b.scrollWidth <= b.clientWidth)")

    def own_slugs(self):
        """Every player on the reader's own teams (never a leaguemate's)."""
        return set(self.page.evaluate(
            "[...new Set(Object.values(TEAMS).filter(t => !t.mate).flatMap(t => t.roster.map(p => p.slug)))]"))

    def mine_slugs(self):
        """The players in view wearing the MINE tag."""
        return {r["slug"] for r in self.rows() if r["mine"]}

    def shown_slugs(self):
        return {r["slug"] for r in self.rows()}

    def held_by(self, keys):
        """Every player on the rosters of these teams (TEAMS keys), as the page holds them."""
        return set(self.page.evaluate(
            "ks => [...new Set(ks.flatMap(k => (TEAMS[k] ? TEAMS[k].roster : []).map(p => p.slug)))]", keys))

    def first_mate(self):
        """The first leaguemate's team key, or None."""
        return self.page.evaluate("MATES.length ? MATES[0].key : null")

    def first_mate_in(self, league):
        """The first leaguemate's team key in a league, or None."""
        return self.page.evaluate("lg => (MATES.find(m => m.league === lg) || {}).key || null", league)

    def put_on_roster(self, key, slug):
        """Put a player on a team's roster, as the build would (the fixture's leaguemates hold none of the list's)."""
        self.page.evaluate("([k, s]) => TEAMS[k].roster.push({n: s, slug: s})", [key, slug])

    def put_pos_on_roster(self, key, pos, club):
        """Put a D/ST or K of an NFL club on a team's roster, as the build would (the fixture's rosters hold none)."""
        self.page.evaluate("([k, pos, club]) => TEAMS[k].roster.push({n: club, pos, team: club, slug: null})", [key, pos, club])

    def follow(self, key):
        """Follow a team the way a star in the team switch does, and draw the view again."""
        self.page.evaluate("k => { followToggle(k); render(); }", key)

    def surface(self):
        return self.page.evaluate("SURFACE")

    # ---- the ways in from elsewhere ----

    def waivers_dst_link(self):
        """Waivers' "Stream a D/ST" link, the one way in from Waivers: its text and height, or None."""
        link = self.page.locator("[data-wvdst]")
        if link.count() != 1:
            return None
        return {"text": link.inner_text().strip(), "height": link.bounding_box()["height"]}

    def follow_waivers_dst_link(self):
        self.page.locator("[data-wvdst]").click()

    def open_dst_from_elsewhere(self):
        """rkOpenDst(), the call a link in another view makes."""
        self.page.evaluate("rkOpenDst()")

    def _row(self, slug):
        return self._rows.and_(self.page.locator(f"[data-rkopen='{slug}']"))
