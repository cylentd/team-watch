"""This week > Digest (design/src/js/surface/digest/): what a reader can do there and what they see.

Every Digest locator lives here, data-testid first (`digest-*`, test hooks only). A few absence checks
name a class a retired part used to wear (`.dg-bd`, `.dg-wait`, `.dg-fact`): there is nothing to hang a
test id on, and the class is the thing proven gone. The way out of the Digest, a profile, is read through
pages/profile.py's `ProfilePage` (`DigestPage.profile`), never re-implemented here.

Plant methods set what the page would hold at a clock (`Date.now`, which the suite pins before every
fixture kickoff) or after a Live poll (`plant_live`), then draw again, the way the page's own tick does.
"""
import re

from pages.profile import ProfilePage

# The clock before the fixture's first ranked kickoff, so every Ranks row is still ahead of it.
EARLY = """(() => { const ks = LIVE_RANKS.rows.map(r => Date.parse(r.kick)).filter(Boolean);
  const at = Math.min(...ks) - 3600e3; Date.now = () => at; DG_CUT = null; render(); return at; })()"""


class DigestPage:


    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._rows, self._row_head, self._ticker = tid("digest-row"), tid("digest-row-head"), tid("digest-ticker")
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
          DG_CUT = null; DG_OPEN = null; render(); }""", [at, nobody_out, packet_week])

    def plant_results_lead(self, at):
        """An old packet that still says its lead is the week's results: it must not draw one."""
        self.page.evaluate("""(at) => { Date.now = () => Date.parse(at); DG_CUT = null; DG_OPEN = null;
          LIVE_DIGEST.lead = {rule: 'results', index: 0}; render(); }""", at)

    def plant_not_live(self):
        self.page.evaluate("() => { dgLiveMode = () => false; render(); }")

    def early(self):
        """The clock just before Ranks' first kickoff."""
        return self.page.evaluate(EARLY)

    def plant_one_call(self):
        self.page.evaluate("() => { LIVE_DIGEST.calls = 1; LIVE_DIGEST.best = []; DG_CUT = null; render(); }")

    def plant_sleeper_adds(self, at):
        self.page.evaluate("""(at) => { Object.assign(LIVE_DIGEST, {adds_source: "sleeper", adds_hours: 24, adds_weeks: [], adds: [
          {n: "Ollie Gordon II", slug: "ollie-gordon-ii", pos: "RB", team: "MIA", count: 4039301, was: null, now: null, delta: null},
          {n: "Kenyon Sadiq", slug: "kenyon-sadiq", pos: "TE", team: "NYJ", count: 832977, was: null, now: 35.2, delta: null}]});
          DG_CUT = null; Date.now = () => Date.parse(at); render(); }""", at)

    def plant_news_without_a_player(self):
        self.page.evaluate("""() => { LIVE_DIGEST.news = [{n: null, rest: null, headline: 'Jalen Davis placed on IR',
          slugs: ['jalen-davis'], when: '9:08 PM', kind: 'out'}, ...LIVE_DIGEST.news]; DG_CUT = null; render(); }""")

    def plant_sunday_top5_kickoff(self):
        """The fixture schedule holds one week-3 game, so one top-5 row gets a Sunday kickoff by hand."""
        self.page.evaluate("() => { LIVE_DIGEST.top5.find(r => !r.ko).ko = '2026-09-27T17:00:00Z'; DG_CUT = null; }")

    def plant_weather_moves(self, moves):
        """The Weather view's rows: one game that moves scoring (`moves`), or none (False)."""
        self.page.evaluate("""(on) => { const g = LIVE_SCHEDULE.games.find(x => Date.parse(x.kickoff) > Date.now());
          wtRows = () => ({week: 4, moves: on ? [{g, done: false, conds: ['precip'], effects: [{pos: 'WR', pts: -0.5}],
            fc: {precip_pct: 60, temp_f: 65}, mph: 6}] : [], indoor: [], open: []}); DG_CUT = null; render(); }""", moves)

    def plant_no_start_take(self):
        self.page.evaluate("""() => { LIVE_SS3.takes = LIVE_SS3.takes.filter(r => r.call !== 'START');
          Object.assign(LIVE_SS3.record, {weeks: [], smash: {hit: 0, miss: 0, void: 0}, start: {hit: 0, miss: 0, void: 0},
          sit: {hit: 0, miss: 0, void: 0}}); DG_CUT = null; render(); }""")

    def start_games_of_new_starters(self):
        self.page.evaluate("""() => { LIVE_DIGEST.starters.forEach(r => { r.ko = "2026-09-20T17:00:00Z"; });
          Date.now = () => Date.parse("2026-09-20T17:01:00Z"); DG_CUT = null; render(); }""")

    def plant_need_clock(self, at):
        self.page.evaluate("(at) => { Date.now = () => Date.parse(at); DG_CUT = null; DG_NEED_ALL = false; render(); }", at)

    def plant_wall_clock(self, at, hide_recap):
        """A clock, and the recap link shown (its fixture n_final) or hidden (0 games final)."""
        return self.page.evaluate("""([at, hide]) => { Date.now = () => Date.parse(at); DG_CUT = null;
          window.__nf = window.__nf ?? LIVE_RECAP.n_final; LIVE_RECAP.n_final = hide ? 0 : window.__nf; render();
          const tk = document.querySelector('[data-testid="digest-ticker"]'), cs = getComputedStyle(tk);
          const names = new Set(cs.gridTemplateAreas.replace(/"/g, ' ').split(/\\s+/).filter(Boolean));
          const rows = [...tk.children].filter(e => getComputedStyle(e).display !== 'none');
          return {cls: tk.className, missing: rows.map(e => [e.dataset.dgrow || e.className, getComputedStyle(e).gridRowStart])
            .filter(([, a]) => !names.has(a)), cols: cs.gridTemplateColumns.split(' ').length}; }""", [at, hide_recap])

    # ---- what a reader does ----

    def tap_head(self, row_id):
        self._row(row_id).get_by_test_id("digest-row-head").click()

    def open_row(self, row_id):
        """Open a row the way a tap does, when it has a head to tap (a wall has none to spare)."""
        head = self._row(row_id).get_by_test_id("digest-row-head")
        if head.count():
            head.click()

    def tap_lead(self):
        self._lead_go.click()

    def tap_lead_and_close(self):
        """The banner opens its player's profile; Escape closes it again."""
        self._lead_go.click()
        self.page.wait_for_selector("#modal.on")
        self.close_profile()

    def pick_t5(self, position):
        """Top 5's tab for a position (its label, FLEX's too)."""
        self._t5_tabs().filter(has_text=re.compile(f"^{position}$")).click()

    def tap_top5_first_row(self):
        """The first Top 5 mover; returns his name as the row prints it."""
        first = self.page.get_by_test_id("digest-rk").first
        name = first.get_by_test_id("digest-rk-name").inner_text()
        first.click()
        return name

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

    def lead_when(self):
        return self.page.get_by_test_id("digest-lead-when").inner_text()

    def lead_pills(self):
        """The retired result pills under the banner."""
        return self.page.locator(".dg-lead .dg-lpill").count()

    def lead_slug(self):
        return self._lead_go.get_attribute("data-dgslug")

    def lead_buttons(self):
        """How the banner opens its player: `slug` (wired once at render) and `live` (the page's one listener)."""
        return {"slug": self._lead_go.and_(self.page.locator("[data-dgslug]")).count(),
                "live": self._lead_go.and_(self.page.locator("[data-dglv]")).count(),
                "all": self._lead_go.count()}

    def ghost(self):
        return self.page.get_by_test_id("digest-ghost").inner_text()

    # ---- the ticker ----

    def row_ids(self):
        """The ticker's rows, top to bottom."""
        return self._rows.evaluate_all("rs => rs.map(r => r.dataset.dgrow)")

    def row_count(self, row_id):
        return self._row(row_id).count()

    def row_label(self, row_id):
        return self._row(row_id).get_by_test_id("digest-row-label").inner_text()

    def row_count_text(self, row_id):
        return self._row(row_id).get_by_test_id("digest-row-count").inner_text()

    def row_line(self, row_id):
        return self._row(row_id).get_by_test_id("digest-row-line").inner_text()

    def row_line_text(self, row_id):
        return self._row(row_id).get_by_test_id("digest-row-line").text_content().strip()

    def recap_note(self):
        """The Recap row's note ("Final tomorrow") and whether it opens the row's text; None when there is none."""
        note = self._row("recap").get_by_test_id("digest-recap-note")
        if not note.count():
            return None
        first = self._row("recap").get_by_test_id("digest-row-line").locator(":scope > :first-child")
        return {"text": note.inner_text(), "first": first.inner_text()}

    def recap_text_geometry(self):
        """The Recap row's text area and its who part, in px, and whether the page scrolls sideways."""
        return self.page.evaluate("""() => { const r = document.querySelector('[data-testid="digest-row"][data-dgrow="recap"]'),
          s = r.querySelector('[data-testid="digest-row-line"]').getBoundingClientRect(),
          w = r.querySelector('[data-testid="digest-recap-who"]').getBoundingClientRect();
          return {text: Math.round(s.width), who: Math.round(w.width), overflow: document.documentElement.scrollWidth > innerWidth}; }""")

    def row_foot(self, row_id):
        return self._row(row_id).get_by_test_id("digest-foot").inner_text()

    def row_foot_text(self, row_id):
        return self._row(row_id).get_by_test_id("digest-foot-text").inner_text()

    def row_go(self, row_id):
        """Where the row's foot link goes (the leaf it names)."""
        return self._row(row_id).get_by_test_id("digest-go").get_attribute("data-dggo")

    def row_go_text(self, row_id):
        return self._row(row_id).get_by_test_id("digest-go").text_content().strip()

    def row_plus(self, row_id):
        return self._row(row_id).get_by_test_id("digest-plus").all_inner_texts()

    def row_body_count(self, row_id):
        return self._row(row_id).get_by_test_id("digest-row-body").count()

    def row_is_open(self, row_id):
        return self._row(row_id).get_attribute("data-open") is not None

    def row_display(self, row_id):
        return self._row(row_id).evaluate("e => getComputedStyle(e).display")

    def open_row_count(self):
        return self._rows.and_(self.page.locator("[data-open]")).count()

    def panel_row_count(self):
        """Rows that open in place: not the empty ones, not the Recap link."""
        return self._rows.and_(self.page.locator(":not(.empty):not(.link)")).count()

    def link_row_count(self):
        return self._rows.and_(self.page.locator(".link")).count()

    def open_link_row_count(self):
        return self._rows.and_(self.page.locator(".link[data-open]")).count()

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

    def retired_highlights(self):
        return self.page.locator(".dg-facts, .dg-fact, [data-dgfact]").count()

    def retired_wait_card(self):
        return self.page.locator(".dg-wait").count() + self.page.locator(".dg svg.blip").count()

    def icons_match_labels(self):
        """Per row, its id and whether its icon is stroked in the label's own colour."""
        return self._rows.evaluate_all("""rs => rs.map(r => {
          const l = r.querySelector('[data-testid="digest-row-label"]'), i = l.querySelector('[data-testid="digest-icon"]');
          return [r.dataset.dgrow, !!i && getComputedStyle(i).stroke === getComputedStyle(l).color];
        })""")

    def fits(self):
        """Nothing wider than the screen."""
        return self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    # ---- the page's own state, read where a test needs the expected value ----

    def packet_lead(self):
        return self.page.evaluate("dgD().lead")

    def packet_first_headline(self):
        return self.page.evaluate("(() => { const d = dgD(); return d.news.length ? d.news[0].headline : null; })()")

    def packet_hurt_games(self):
        return self.page.evaluate("dgD().hurt.map(r => r.game && r.game.away + '@' + r.game.home)")

    def packet_top5_count(self):
        return self.page.evaluate("dgD().top5.length")

    def weekday(self):
        return self.page.evaluate("new Date(Date.now()).getDay()")

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

    def blip_jokes(self):
        """Matchups' line with nothing to call (Blip's voice): the three it may be, and the one drawn."""
        return self.page.evaluate("""() => ({jokes: [t('digest.wait.mu1', {week: 4}), t('digest.wait.mu2'), t('digest.wait.mu3')],
          drawn: dgMuNone(4)})""")

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

    def news_new_starter_blocks(self):
        """News no longer carries the new starters."""
        return self.page.locator(".dg-nw.start").count()

    # ---- News ----

    def news_lines(self):
        """Per headline line: its link's href, target and rel (None for a line with no link)."""
        return self.page.get_by_test_id("digest-news").locator("li").evaluate_all("""lis => lis.map(li => {
          const a = li.querySelector('a'); return a && {href: a.getAttribute('href'), target: a.target, rel: a.rel}; })""")

    def news_expected_hrefs(self):
        """Each headline's story, or a search for it when ff-jarvis kept no link."""
        return self.page.evaluate("""() => dgD().news.map(it => it.link || 'https://www.google.com/search?tbm=nws&q=' + encodeURIComponent(it.headline))""")

    def news_nested_controls(self):
        """A link inside a button, or a button inside a link."""
        return self.page.locator(".dg-nws button a, .dg-nws a button").count()

    def news_names_open_profiles(self):
        return self.page.get_by_test_id("digest-news-who").evaluate_all("bs => bs.every(b => b.dataset.dgslug)")

    def news_block_with(self, text):
        """The block that holds `text`: its tag name and its text."""
        return self.page.get_by_test_id("digest-news-block").evaluate_all(
            """(bs, text) => { const b = bs.find(b => b.textContent.includes(text));
              return b ? {tag: b.tagName, text: b.textContent.trim()} : null; }""", text)

    # ---- Matchups, Top 5, Weather ----

    def first_ln(self, row_id):
        """The row's first player line: its tag, the player and what it says at the right."""
        ln = self._row(row_id).get_by_test_id("digest-ln").first
        return {"slug": ln.get_attribute("data-dgslug"),
                "sotw": ln.get_by_test_id("digest-sotw").inner_text() if ln.get_by_test_id("digest-sotw").count() else None,
                "right": ln.get_by_test_id("digest-ln-right").inner_text().replace("\n", " ")}

    def sotw_count(self):
        return self.page.get_by_test_id("digest-sotw").count()

    def sotw_color(self):
        return self.page.get_by_test_id("digest-sotw").evaluate("e => getComputedStyle(e).color")

    def sotw_title(self):
        return self.page.get_by_test_id("digest-sotw").get_attribute("title")

    def lime(self):
        """The brand lime, resolved to the colour string getComputedStyle gives."""
        return self.page.evaluate("""() => { const i = document.createElement('i'); i.style.color = 'var(--lime)';
          document.body.appendChild(i); const c = getComputedStyle(i).color; i.remove(); return c; }""")

    def start_take(self):
        """The take Start of the week must show: our boldest START."""
        return self.page.evaluate("LIVE_SS3.takes.find(r => r.call === 'START')")

    def weather_games(self):
        """The opened Weather row's games: how many."""
        return self._row("wx").get_by_test_id("digest-wx").count()

    def weather_readings(self):
        """What each game of the opened Weather row says at the right."""
        return self._row("wx").get_by_test_id("digest-wx").get_by_test_id("digest-ln-right").all_inner_texts()

    def t5_tabs(self):
        return [s.strip() for s in self._t5_tabs().all_inner_texts()]

    def t5_expected(self):
        """Ranks' own top five per position and FLEX, as slugs: what every tab must show."""
        return self.page.evaluate("""Object.fromEntries(DG_T5_POS.map(p => [p, rkList(p).slice(0, 5).map(r => r.slug)])
          .filter(([, s]) => s.length))""")

    def t5_slugs(self, position):
        """The slugs the open panel of a position shows, top to bottom."""
        return self._t5_panel(position).get_by_test_id("digest-rk").evaluate_all("els => els.map(e => e.dataset.dgslug)")

    def t5_first_pts(self, position):
        return self._t5_panel(position).get_by_test_id("digest-rk-pts").first.inner_text()

    def ranks_first_pts(self, position):
        """Ranks' own first row's points for a position, to one decimal."""
        return self.page.evaluate("p => rkList(p)[0].pts.toFixed(1)", position)

    def t5_tiers(self):
        """The open Top 5 panel's tier chips: label, background, text colour."""
        return self.page.locator("[data-dgset='t5'] [data-dgpanel]:not([data-off])").get_by_test_id("digest-rk-tier").evaluate_all(
            "els => els.map(e => [e.textContent, getComputedStyle(e).backgroundColor, getComputedStyle(e).color])")

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

    def _row(self, row_id):
        return self._rows.and_(self.page.locator(f"[data-dgrow='{row_id}']"))

    def _t5_tabs(self):
        return self.page.get_by_test_id("digest-tabset").and_(self.page.locator("[data-dgset='t5']")).get_by_test_id("digest-tab")

    def _t5_panel(self, position):
        return (self.page.get_by_test_id("digest-tabset").and_(self.page.locator("[data-dgset='t5']"))
                .get_by_test_id("digest-tabpanel").and_(self.page.locator(f"[data-dgpanel='{position}']:not([data-off])")))
