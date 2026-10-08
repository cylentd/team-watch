"""This week > Digest (design/src/js/surface/digest/): what a reader can do there and what they see.

Every Digest locator lives here, data-testid first (`digest-*`, test hooks only). A few absence checks
name a class a retired part used to wear (`.dg-bd`, `.dg-wait`, `.dg-fact`, `.dg-row`): there is nothing to
hang a test id on, and the class is the thing proven gone. The way out of the Digest, a profile, is read
through pages/profile.py's `ProfilePage` (`DigestPage.profile`), never re-implemented here. The day's
banner, cards, rows and strip (2026-10-06, Digest by day) are pages/digest_day.py.

Plant methods set what the page would hold at a clock (`Date.now`, which the suite pins before every
fixture kickoff) or after a Live poll (`plant_live`), then draw again, the way the page's own tick does.
"""
from pages.profile import ProfilePage


class DigestPage:

    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._ticker = tid("digest-ticker")
        self._lead_go, self._head = tid("digest-lead-go"), tid("digest-lead-head")
        self._now, self._need, self._tn = tid("digest-now"), tid("digest-need"), tid("digest-tn")
        self.profile = ProfilePage(page)

    # ---- planting: what the page would hold at a clock, drawn again ----

    def set_clock(self, at, nobody_out=False, packet_week=False):
        """The page's clock at an ISO instant; `nobody_out` empties Hurt and the new starters;
        `packet_week` sets the page week to the packet's, as it is live (the fixture's page week is 2,
        the packet's 3)."""
        self.page.evaluate("""([at, none, pw]) => { Date.now = () => Date.parse(at);
          if (none) { LIVE_DIGEST.hurt = []; LIVE_DIGEST.starters = []; }
          if (pw) LIVE_SCHEDULE.week = LIVE_DIGEST.week;
          DG_CUT = null; render(); }""", [at, nobody_out, packet_week])

    def plant_empty(self, *keys):
        """Empty packet lists (`adds`, `gains`; `usage` is LIVE_USAGE_MOVERS' rows, `tiers` LIVE_RANKS' lists): the day
        cards fed by them draw nothing, so a test about Need to know or a planted card is not about the cards the
        fixtures now feed."""
        self.page.evaluate("""(keys) => { keys.forEach(k => { if (k === 'usage') LIVE_USAGE_MOVERS.rows = [];
            else if (k === 'tiers') { LIVE_RANKS.rows = []; LIVE_RANKS.flex = []; } else LIVE_DIGEST[k] = []; });
          DG_CUT = null; render(); }""", list(keys))

    def plant_results_lead(self, at):
        """An old packet that still says its lead is the week's results: it must not draw one."""
        self.page.evaluate("""(at) => { Date.now = () => Date.parse(at); DG_CUT = null;
          LIVE_DIGEST.lead = {rule: 'results', index: 0}; render(); }""", at)

    def plant_not_live(self):
        self.page.evaluate("() => { dgLiveMode = () => false; render(); }")

    def plant_sleeper_adds(self, at):
        self.page.evaluate("""(at) => { Object.assign(LIVE_DIGEST, {adds_source: "sleeper", adds_hours: 24, adds_weeks: [], adds: [
          {n: "Ollie Gordon II", slug: "ollie-gordon-ii", pos: "RB", team: "MIA", count: 4039301, was: null, now: null, delta: null},
          {n: "Kenyon Sadiq", slug: "kenyon-sadiq", pos: "TE", team: "NYJ", count: 832977, was: null, now: 35.2, delta: null}]});
          DG_CUT = null; Date.now = () => Date.parse(at); render(); }""", at)

    def plant_news_lead_without_a_player(self, at):
        """A headline that names no player but carries a slug (a defender's IR move) leads the packet."""
        self.page.evaluate("""(at) => { Date.now = () => Date.parse(at);
          LIVE_DIGEST.news = [{n: null, rest: null, headline: 'Jalen Davis placed on IR',
          slugs: ['jalen-davis'], when: '9:08 PM', kind: 'out'}, ...LIVE_DIGEST.news];
          LIVE_DIGEST.lead = {rule: 'news', index: 0}; LIVE_DIGEST.adds = []; DG_CUT = null; render(); }""", at)

    def plant_sunday_top5_kickoff(self):
        """The fixture schedule holds one week-3 game, so one top-5 row gets a Sunday kickoff by hand."""
        self.page.evaluate("() => { LIVE_DIGEST.top5.find(r => !r.ko).ko = '2026-09-27T17:00:00Z'; DG_CUT = null; }")

    def start_games_of_new_starters(self):
        self.page.evaluate("""() => { LIVE_DIGEST.starters.forEach(r => { r.ko = "2026-09-20T17:00:00Z"; });
          Date.now = () => Date.parse("2026-09-20T17:01:00Z"); DG_CUT = null; render(); }""")

    def plant_need_clock(self, at):
        self.page.evaluate("(at) => { Date.now = () => Date.parse(at); DG_CUT = null; DG_NEED_ALL = false; render(); }", at)

    # ---- what a reader does ----

    def tap_lead(self):
        self._lead_go.click()

    def tap_lead_and_close(self):
        """The banner opens its player's profile; Escape closes it again."""
        self._lead_go.click()
        self.page.wait_for_selector("#modal.on")
        self.close_profile()

    def close_profile(self):
        self.page.keyboard.press("Escape")
        self.page.wait_for_selector("#modal.on", state="detached")

    # ---- what a reader sees: the banner ----

    def headline(self):
        return self._head.inner_text()

    def headline_text(self):
        return self._head.text_content()

    def lead_fact(self):
        return self.page.get_by_test_id("digest-lead-fact").inner_text()

    def lead_pills(self):
        """The retired result pills under the banner."""
        return self.page.get_by_test_id("digest-lead").locator(".dg-lpill").count()

    def lead_slug(self):
        return self._lead_go.get_attribute("data-dgslug")

    def lead_buttons(self):
        """How the banner opens its player: `slug` (wired once at render) and `live` (the page's one listener)."""
        return {"slug": self._lead_go.and_(self.page.locator("[data-dgslug]")).count(),
                "live": self._lead_go.and_(self.page.locator("[data-dglv]")).count(),
                "all": self._lead_go.count()}

    # ---- the body ----

    def ticker_classes(self):
        return self._ticker.get_attribute("class")

    def section_titles(self):
        return self.page.get_by_test_id("digest-sec").all_inner_texts()

    def html(self):
        return self.page.get_by_test_id("digest-root").evaluate("e => e.outerHTML")

    def mark_root(self):
        self.page.get_by_test_id("digest-root").evaluate("e => { e.dataset.keep = '1'; }")

    def root_is_marked(self):
        return self.page.get_by_test_id("digest-root").evaluate("e => e.dataset.keep === '1'")

    def retired_parts(self):
        """Parts the Digest no longer draws (the results board, tabs, list and wait card, the banner's pills)."""
        return self.page.locator(".dg-rs, .dg-bd, .dg-rr, .dg-rlist, [data-dgset='res'], .dg-wait, .dg-lead-pills").count()

    def retired_rows(self):
        """The ticker's rows, its wall panels and Top 5's tabs, all gone on 2026-10-06."""
        return self.page.locator(".dg-row, .dg-head, [data-dgset], .dg-ghost").count()

    def retired_highlights(self):
        return self.page.locator(".dg-fact, [data-dgfact]").count()

    def retired_wait_card(self):
        return self.page.locator(".dg-wait").count() + self.page.locator(".dg svg.blip").count()

    def fits(self):
        """Nothing wider than the screen."""
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    # ---- the page's own state, read where a test needs the expected value ----

    def packet_lead(self):
        return self.page.evaluate("dgD().lead")

    def packet_hurt_games(self):
        return self.page.evaluate("dgD().hurt.map(r => r.game && r.game.away + '@' + r.game.home)")

    def packet_top5_count(self):
        return self.page.evaluate("dgD().top5.length")

    def hash(self):
        return self.page.evaluate("location.hash")

    def surface(self):
        return self.page.evaluate("SURFACE")

    # ---- the banner's parts, called as the Recap view calls them ----

    def recap_parts(self):
        """What the functions the Recap view draws with return, called from the Digest's own file."""
        return self.page.evaluate("""() => {
      const text = html => { const h = document.createElement('div'); h.innerHTML = html; return h.textContent.replace(/\\s+/g, ' ').trim(); };
      const R = LIVE_RECAP, top = R.top;
      const left = R.left_hurt.length ? R.left_hurt[0] : {injury: 'knee', later: 'suffers season-ending torn ACL', slug: 'x', n: 'Test Player', proj: 10, actual: null};
      const why = {kind: 'role', luck: 5, expected: 12, stat: 'targets', share: 31, delta: 10};
      const board = (() => { const h = document.createElement('div'); h.innerHTML = dgBoardHTML({stars: R.stars}); return h; })();
      return {board: board.querySelectorAll('.dg-bd-r').length, stars: R.stars.length,
              boardText: board.querySelector('.dg-bd-r') ? board.querySelector('.dg-bd-r').textContent.replace(/\\s+/g, ' ').trim() : '',
              first: R.stars.length ? dgShort(R.stars[0].n) + ' ' + dgStatLine(R.stars[0]) + ' ' + R.stars[0].actual.toFixed(1) : '',
              call: text(dgCall({n: 'Jahmyr Gibbs', line: {car: 20, rush_yd: 99, rec: 7, rec_yd: 65, td: 3, att: null}, actual: 30}, 4)),
              box: [...(() => { const h = document.createElement('div'); h.innerHTML = dgBoxPills({...top, actual: top.actual}); return h.querySelectorAll('.dg-lpill'); })()].map(e => e.textContent),
              topLine: dgTopLine({rush_yd: 99, rec_yd: 65, rush_td: 1, rec_td: 2}),
              why: text(dgWhy({why, diff: 9.7, slug: 'x'}, [])),
              leftRow: text(dgResRow(left, dgLeftPills(left), dgResNum(left))),
              out: [text(dgOutPill('Baker Mayfield expected to miss three weeks')), text(dgOutPill('suffers season-ending torn ACL'))],
              games: [dgGames(1), dgGames(15)]};
    }""")

    def calls(self):
        """dgCall for six box lines in week 3, one again, and one man across eight weeks."""
        return self.page.evaluate("""() => {
      const box = (o) => ({car: 0, rush_yd: 0, rec: 0, rec_yd: 0, td: 0, cmp: null, att: null, pass_yd: null, pass_td: null, int: null, ...o});
      const call = (n, line, week, actual) => { const h = document.createElement('i'); h.innerHTML = dgCall({n, line, actual: actual || 30}, week); return h.textContent; };
      const gibbs = box({car: 20, rush_yd: 99, rec: 7, rec_yd: 65, td: 3});
      return {calls: [call('Jahmyr Gibbs', gibbs, 3),
                      call('Jaxon Smith-Njigba', box({rec: 10, rec_yd: 128, td: 2, cmp: 1, att: 1, pass_yd: 14, pass_td: 0}), 3),
                      call('Brock Purdy', box({car: 2, rush_yd: 34, cmp: 15, att: 27, pass_yd: 297, pass_td: 4}), 3),
                      call('Konata Mumpfield', box({rec: 4, rec_yd: 93, td: 1}), 3),
                      call('Kyren Williams', box({car: 9, rush_yd: 31, td: 3}), 3),
                      call('Travis Etienne Jr.', null, 3, 21.4)],
              again: call('Jahmyr Gibbs', gibbs, 3),
              weeks: [...new Set([1, 2, 3, 4, 5, 6, 7, 8].map(w => call('Jahmyr Gibbs', gibbs, w)))].length};
    }""")

    # ---- Need to know ----

    def need_none(self):
        return self._need.get_by_test_id("digest-need-none").inner_text()

    def need_tags(self):
        return self._need.get_by_test_id("digest-need-what").evaluate_all(
            "ss => ss.map(s => s.firstElementChild.textContent.trim())")

    def need_lines(self):
        """Each line's second row: what happened, without the tag and without the rank at its end."""
        return self._need.get_by_test_id("digest-need-what").evaluate_all("""ss => ss.map(s => {
          const c = s.cloneNode(true); c.firstElementChild.remove(); c.querySelectorAll('i').forEach(i => i.remove());
          return c.textContent.replace(/\\s*·\\s*$/, '').trim(); })""")

    def need_faces_lead(self):
        """Every line starts with a face."""
        return self._need.get_by_test_id("digest-need-line").evaluate_all(
            "bs => bs.every(b => b.firstElementChild.classList.contains('dg-hd'))")

    def need_more(self):
        more = self._need.get_by_test_id("digest-need-more")
        return more.text_content() if more.count() else ""

    def need_has_questionable_line(self):
        return self._need.get_by_test_id("digest-need-q").count() > 0

    def need_questionable_taps_open_profiles(self):
        return self._need.get_by_test_id("digest-need-qp").evaluate_all("bs => bs.every(b => b.dataset.dgslug)")

    def need_tag_count(self):
        return self._need.get_by_test_id("digest-need-tag").count()

    def need_count(self):
        return self._need.count()

    def lime(self):
        """The accent as a computed `rgb(r, g, b)` body."""
        return self.page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--lime-rgb').trim().split(/\\s+/).join(', ')")

    # ---- the way out: a profile ----

    def profile_open(self):
        return self.profile.is_open()

    def profile_has_title(self):
        return self.profile.has_title()

    def profile_title(self):
        return self.profile.title()
