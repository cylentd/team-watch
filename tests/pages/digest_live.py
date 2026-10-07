"""This week > Digest, after the week's first kickoff and the Recap row (surface/digest/now.js, mnf.js,
tonight.js, recaprow.js): the same page object plus what Live's poll and the clock plant, and what Right now,
Tonight's card, the last game and the Recap row print. See pages/digest.py.
"""
from pages.digest import DigestPage
from test_render import LIVE_PLANT

SUN, MON = "2026-10-04T12:00:00Z", "2026-10-05T15:00:00Z"


def _scorer(n, pos, team, pts, **s):
    return {"n": n, "pos": pos, "team": team, "pts": pts, "s": s}


# Seven scorers, league-wide, as GD_STATS.lead (api/stats.py lead=1); five have TDs worth counting.
LEAD = {
    "7547": _scorer("Amon-Ra St. Brown", "WR", "DET", 31.4, rec=10, rec_tgt=12, rec_yd=180, rec_td=2),
    "9226": _scorer("De'Von Achane", "RB", "MIA", 27.1, rush_att=18, rush_yd=130, rush_td=1, rec=4, rec_tgt=5, rec_yd=40),
    "8183": _scorer("Brock Purdy", "QB", "SF", 24.0, pass_cmp=22, pass_att=30, pass_yd=290, pass_td=3),
    "12481": _scorer("Cam Skattebo", "RB", "NYG", 19.2, rush_att=20, rush_yd=90, rush_td=2),
    "6801": _scorer("Tee Higgins", "WR", "CIN", 17.8, rec=6, rec_tgt=8, rec_yd=98),
    "4217": _scorer("George Kittle", "TE", "SF", 15.5, rec=6, rec_tgt=7, rec_yd=85, rec_td=1),
    "12526": _scorer("Tetairoa McMillan", "WR", "CAR", 12.0, rec=5, rec_tgt=7, rec_yd=70),
}

# Plants week 2 of both leagues (tests/fixtures/gameday.json), keeps the ESPN one, and gives every club
# a game: Sunday's, or the Monday pair `mon` ([home, away]). cfg: at, sunState, monState, mon, lead, stats, clock.
PLANT_WEEK = """(cfg) => {
  PLANT
  GD.leagues.splice(1);
  const lineup = Object.values(GD.leagues[0].teams).flatMap(tm => tm.lineup.map(r => r.team));
  const clubs = [...new Set(lineup)].filter(c => !cfg.mon.includes(c));
  const games = clubs.map(c => ({home: c, away: 'O' + c, kickoff: cfg.sun, week: 2}));
  if (cfg.mon.length) games.push({home: cfg.mon[0], away: cfg.mon[1], kickoff: cfg.monKick, week: 2});
  GD_GAMES.splice(0, GD_GAMES.length, ...games);
  Date.now = () => Date.parse(cfg.at);
  GD_STATS.games = {};
  for (const g of games) for (const c of [g.home, g.away]) GD_STATS.games[c] = cfg.mon.includes(c) ? cfg.monState : cfg.sunState;
  GD_STATS.lead = cfg.lead;
  Object.assign(GD_STATS.stats, cfg.stats || {});
  GD_AT = Date.now(); GD_CLOCK = cfg.clock || {};
  if (cfg.noHurt) { LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = []; }
  DG_CUT = null; render();
}""".replace("PLANT", LIVE_PLANT())

# Three games on the last day make it the main slate, not the standalone last game: no card, and the
# packet's own lead stands between windows.
EXTRA_LATE = """() => {
  for (const [h, a] of [['XA', 'XB'], ['XC', 'XD']]) GD_GAMES.push({home: h, away: a, kickoff: GD_GAMES[GD_GAMES.length - 1].kickoff, week: 2});
  const h = LIVE_DIGEST.hurt[0];
  h.game = {away: 'XA', home: 'XB', ko: '2026-10-06T00:30:00Z', kick: 'Mon 5:15 PM'};
  LIVE_DIGEST.lead = {rule: 'hurt', index: 0};
  DG_CUT = null; render();
}"""
BANNER_AT = """([at, state]) => {
  Date.now = () => Date.parse(at);
  for (const g of GD_GAMES) if (['NYG', 'DAL', 'XA', 'XB', 'XC', 'XD'].includes(g.home)) GD_STATS.games[g.home] = GD_STATS.games[g.away] = state;
  paintDigestLive();
}"""


def live_cfg(**over):
    """The after-kickoff plant: Sunday's games on at 14:00 UTC, no Monday game, LEAD as the poll's scorers."""
    cfg = {"at": "2026-10-04T14:00:00Z", "sun": SUN, "monKick": MON, "mon": [], "sunState": "in_game",
           "monState": "pre_game", "lead": LEAD, "stats": {}, "clock": {}, "noHurt": False}
    cfg.update(over)
    return cfg


class DigestLivePage(DigestPage):
    """DigestPage, with the planted poll, Right now, Tonight, the last game and the Recap row."""

    # ---- planting: Live's poll and the clock ----

    def plant_live(self, **over):
        """Week 2 of both leagues, a Sunday on or off, the poll's scorers: `live_cfg(**over)`."""
        self.page.evaluate(PLANT_WEEK, live_cfg(**over))

    def plant_extra_late_games(self):
        self.page.evaluate(EXTRA_LATE)

    def plant_banner_state(self, at, state):
        """The poll says the late games are `state` at `at`, and the Digest repaints in place."""
        self.page.evaluate(BANNER_AT, [at, state])

    def plant_scorer_pts(self, key, pts):
        self.page.evaluate("([k, p]) => { GD_STATS.lead[k].pts = p; }", [key, pts])

    def clear_scorers(self):
        self.page.evaluate("() => { GD_STATS.lead = {}; DG_CUT = null; render(); }")

    def start_monday_game(self):
        """Monday night's game kicks off 15 minutes before the clock."""
        self.page.evaluate("""() => { GD_GAMES.push({home: 'CHI', away: 'PHI', kickoff: '2026-09-29T00:15:00Z', week: GD.leagues[0].week});
          Date.now = () => Date.parse("2026-09-29T00:30:00Z"); DG_CUT = null; render(); }""")

    def plant_recap(self, at, edit=""):
        """The page at a clock, after `edit` (a JS statement) on the fixture's recap. Every call starts
        from the fixture's recap, so one case's edit never leaks into the next."""
        self.page.evaluate("""([at, js]) => { window.__r = window.__r ?? JSON.stringify(LIVE_RECAP); window.__s = window.__s ?? LIVE_SCHEDULE.games;
          Object.assign(LIVE_RECAP, JSON.parse(window.__r)); LIVE_SCHEDULE.games = window.__s;
          Date.now = () => Date.parse(at); DG_CUT = null; eval(js); render(); }""", [at, edit])

    # ---- what a reader does ----

    def tap_now_more(self):
        self._now.get_by_test_id("digest-now-more").click()

    def tap_now_row(self, n=0):
        self._now.get_by_test_id("digest-now-row").nth(n).click()

    def tap_recap_link(self):
        self._row("recap").get_by_test_id("digest-row-head").click()

    def tap_now_td(self):
        self._now.get_by_test_id("digest-now-td").click()

    def facts_panels(self):
        """The `.dg-facts` panels (Right now is the one)."""
        return self.page.locator(".dg-facts").count()

    def stored_live_tab(self):
        return self.page.evaluate("localStorage.getItem('tw-live-tab')")

    def live_tab(self):
        return self.page.evaluate("gdTab()")

    def block_storage(self):
        self.page.evaluate("""() => { const no = () => { throw new Error('blocked'); };
          Storage.prototype.setItem = no; Storage.prototype.getItem = no; }""")

    # ---- Right now, Tonight, the last game ----

    def now_title(self):
        return self._now.get_by_test_id("digest-sec").text_content()

    def now_rows(self):
        return self._now.get_by_test_id("digest-now-row").count()

    def now_first_row_text(self):
        return self._now.get_by_test_id("digest-now-row").first.inner_text().replace("\n", " ")

    def now_points(self):
        return self.page.get_by_test_id("digest-now-pts").all_inner_texts()

    def now_more(self):
        more = self._now.get_by_test_id("digest-now-more")
        return {"text": more.inner_text(), "expanded": more.get_attribute("aria-expanded")}

    def now_more_text(self):
        return self.page.get_by_test_id("digest-now-more").inner_text()

    def now_td_text(self):
        return self._now.get_by_test_id("digest-now-td").inner_text()

    def live_parts(self):
        """Right now and the last game's card: neither is drawn before the first kickoff."""
        return self._now.count() + self.page.locator("[data-dgmnf]").count()

    def tn_story(self):
        return self.page.get_by_test_id("digest-tn-story").inner_text()

    def tn_list_heads(self):
        """The headings of Tonight's short lists, in order."""
        return self._tn.locator("h4").all_inner_texts()

    def tn_foot(self):
        return self._tn.get_by_test_id("digest-foot-text").inner_text()

    def tn_block_count(self):
        """Tonight's card once it is on: the game's one block."""
        return self._tn.and_(self.page.locator(".on")).get_by_test_id("digest-mnf-block").count()

    def tn_when(self):
        return self._tn.and_(self.page.locator(".on")).get_by_test_id("digest-mnf-when").inner_text()

    def mnf_cards(self):
        return self._tn.and_(self.page.locator(".dg-mnf")).count()

    def paint_poll(self):
        """live.js's call after a poll."""
        self.page.evaluate("() => { paintDigestLive(); }")

    def paint_poll_off_the_digest(self, pts):
        """A poll lands while another view is on screen: the Digest keeps what it drew."""
        self.page.evaluate("""(p) => { SURFACE = 'ranks'; GD_STATS.lead['9226'].pts = p; paintDigestLive(); SURFACE = 'digest'; }""", pts)

    # ---- the Recap row ----

    def recap_facts(self):
        """What the Recap row prints (the label, the week, the top scorer's part and Claude's), or None
        when the ticker draws no such row."""
        row = self._row("recap")
        if not row.count():
            return None
        who, claude = row.get_by_test_id("digest-recap-who"), row.get_by_test_id("digest-recap-claude")
        return {"href": row.get_by_test_id("digest-row-head").get_attribute("href"),
                "arrows": row.get_by_test_id("digest-row-head").get_by_test_id("digest-arrow").count(),
                "label": row.get_by_test_id("digest-row-label").inner_text(),
                "week": row.get_by_test_id("digest-row-count").inner_text(),
                "bodies": row.get_by_test_id("digest-row-body").count(),
                "open": row.get_attribute("data-open"),
                "who": who.inner_text() if who.count() else None, "claude": claude.inner_text() if claude.count() else None,
                "whos": who.count(), "claudes": claude.count(), "bold": who.locator("b").count(),
                "line": row.get_by_test_id("digest-row-line").inner_text(), "text": row.inner_text()}

    def recap_row_geometry(self):
        """The row's height, whether the page scrolls sideways, and whether Claude's part sits inside its line."""
        return self.page.evaluate("""() => { const r = document.querySelector('[data-testid="digest-row"][data-dgrow="recap"]'),
          h = r.querySelector('[data-testid="digest-row-head"]').getBoundingClientRect();
          const c = r.querySelector('[data-testid="digest-recap-claude"]').getBoundingClientRect(),
                s = r.querySelector('[data-testid="digest-row-line"]').getBoundingClientRect();
          return {h: Math.round(h.height), overflow: document.documentElement.scrollWidth > innerWidth, claudeInside: c.right <= s.right + 1}; }""")

    def recap_row_wall_band(self):
        """On the wall: the row's grid area, whether it is as wide as the ticker, whether it opens, its line, its cursor."""
        return self.page.evaluate("""() => { const tk = document.querySelector('[data-testid="digest-ticker"]'),
          r = tk.querySelector('[data-testid="digest-row"][data-dgrow="recap"]');
          const cs = getComputedStyle(r), b = r.getBoundingClientRect(), t = tk.getBoundingClientRect();
          return {area: cs.gridRowStart, full: Math.abs(b.width - t.width) < 2, open: r.hasAttribute('data-open'),
                  line: getComputedStyle(r.querySelector('[data-testid="digest-row-line"]')).display,
                  cur: getComputedStyle(r.querySelector('[data-testid="digest-row-head"]')).cursor}; }""")
