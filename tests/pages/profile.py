"""The player profile modal (design/src/js/surface/profile/): its head, panes, Season table, market, bio and owners.

Every locator lives here, data-testid first (`profile-*`, test hooks only: no CSS or JS reads them). A
few reads go past a testid because the element is drawn by a file outside surface/profile/: the leg
sheet's bars (`.ls-*`), the Leaders card's fields (`.bd-*`), the "No line" tag (`.pf-noline`, rbrules.js),
the weather icon (`.pf-wx-i`). The profile has no leaf, so a test mounts the roster (pages/roster.py
`on_roster`) and opens it from there; the roster's own rows are `profile.roster`.

The head and strip (name block, verdict, injury, rail, strip cells, grid link, owners) are
pages/profile_head.py's `ProfileHead`; the stat sheet (the sphere's layer), its radar and ladder, the elite
marks and Compare are pages/profile_sheet.py's `ProfileSheet`, which `ProfileHead` extends. `ProfilePage`
extends `ProfileHead`: one object, one API for a test.
"""
import re

from pages.profile_head import ProfileHead
from pages.roster import RosterRows

VISIBLE = "e => { const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0 && getComputedStyle(e).visibility !== 'hidden'; }"
SETTLE = "new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"


class ProfilePage(ProfileHead):
    def __init__(self, page):
        super().__init__(page)
        self.roster = RosterRows(page)

    # ---- opening and closing ----

    def open_from_roster(self, name):
        """Tap a roster row by the player's name."""
        self.roster.open(name)
        self._opened()

    def open_roster_row(self, i):
        self.roster.open_nth(i)
        self._opened()

    def open_player(self, player):
        """openProfile({n, pos, team[, slug]}), the call every other view makes."""
        self.page.evaluate("p => openProfile(p)", player)
        self._opened()

    def open_starter(self, team, name):
        """The profile of a starter on one of the reader's rosters, as the roster's own row opens it."""
        self.page.evaluate("""([team, name]) => openProfile(findPlayer(team, TEAMS[team].roster.filter(p => p.start)
          .findIndex(p => p.n === name)))""", [team, name])
        self._opened()

    def open_injured_player(self):
        """Open the first hurt player the search index knows; returns what the page says about him."""
        got = self.page.evaluate("""() => {
          const hurt = Object.entries(LIVE_INJURY.players).map(([slug, r]) => ({slug, r}))
            .map(x => ({...x, e: searchIndex().find(e => e.slug === x.slug)})).find(x => x.e);
          openProfile(searchPlayer(hurt.e));
          return {slug: hurt.slug, want: injFor({slug: hurt.slug})}; }""")
        self._opened()
        return got

    def open_healthy_player(self):
        self.page.evaluate("""() => { const well = searchIndex().find(e => !injFor({slug: e.slug}) && !e.status);
          openProfile(searchPlayer(well)); }""")
        self._opened()

    def _opened(self):
        self._tid("profile-title").wait_for()      # a locator wait, not wait_for_function: a test may hold the page's frames

    def is_open(self):
        return self.page.evaluate("document.getElementById('modal').classList.contains('on')")

    def close(self):
        """Escape on the profile, then wait for the dialog to go and its history step to land."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_function("!document.querySelector('#modal.on')")
        self.settle()

    def press_escape(self):
        """Escape with a layer (the stat sheet, Compare) open: it closes the layer alone."""
        self.page.keyboard.press("Escape")

    def settle(self):
        """Let a closed layer's history.back() land (LAYER_SKIP, layers.js) so the next layer does not race it."""
        self.page.wait_for_function("LAYER_SKIP.length === 0")
        self.page.evaluate(SETTLE)

    def back(self):
        self.page.go_back()

    def wait_hash(self, hash_):
        self.page.wait_for_function("h => location.hash === h", arg=hash_)

    def wait_surface(self, leaf):
        self.page.wait_for_function("s => SURFACE === s", arg=leaf)

    def wait_closed(self):
        self.page.wait_for_function("!document.getElementById('modal').classList.contains('on')")

    def wait_compare_closed(self):
        self.page.wait_for_function("!document.querySelector('#modal [data-testid=\"profile-cmp-layer\"]')")

    def anything_open(self):
        """A profile, a stat sheet or a Compare layer is up."""
        return self.page.evaluate("!!document.querySelector('.modal.on, .pf-orblayer, .cmp-layer')")

    def snapshot(self):
        """The page's view and storage, for a journey's shared page to be put back to."""
        return self.page.evaluate("({view: VIEW, ls: Object.entries(localStorage)})")

    def restore(self, snap):
        self.page.evaluate("""(snap) => {
          'use strict';
          localStorage.clear();
          for (const [k, v] of snap.ls) localStorage.setItem(k, v);
          VIEW = snap.view; render(); window.scrollTo(0, 0);
        }""", snap)

    def focus_on_roster_row(self):
        return self.page.evaluate("document.activeElement.classList.contains('row')")

    # ---- panes ----

    def tab_labels(self):
        return [b.inner_text() for b in self._tid("profile-tab").all()]

    def tab_ids(self):
        return [b.get_attribute("data-pftab") for b in self._tid("profile-tab").all()]

    def _tab(self, name):
        return self._tid("profile-tab").and_(self.page.locator(f"[data-pftab='{name}']"))

    def tab(self, name):
        """Open one pane. Only the open pane is in the DOM, so a test asks for the pane it wants."""
        self._tab(name).click()

    def tab_all(self):
        """Open every pane in turn, yielding its id after each."""
        for tid in self.tab_ids():
            self._tab(tid).click()
            yield tid

    def has_tab(self, name):
        return self._tab(name).count() == 1

    def selected_tab(self):
        return self.page.evaluate("document.querySelector('#modal [data-pftab][aria-selected=true]').dataset.pftab")

    def empty_notice(self):
        return self._tid("profile-empty").count()

    def season_blocks(self):
        return self._tid("profile-season").count()

    def zone_blocks(self):
        return self._tid("profile-zones").count()

    def zones_in(self, label):
        return self._tid("profile-sec").filter(has_text=label).get_by_test_id("profile-zone").count()

    def sections(self, kind=None):
        """How many sections of one kind (team, prop, arch, rz, zones, drafts), or all, are drawn."""
        return self._secs(kind).count()

    def pane_sections(self):
        """The kinds of the open pane's sections, in order."""
        return self._pane_children("section")

    def pane_blocks(self):
        """The top and bottom edge of each block of the open pane."""
        return self._tid("profile-pane").evaluate("""p => [...p.children].map(e => { const b = e.getBoundingClientRect(); return [b.top, b.bottom]; })""")

    def _pane_children(self, tag):
        return self._tid("profile-pane").evaluate("(p, tag) => [...p.children].filter(e => e.matches(tag)).map(e => e.dataset.sec || '')", tag)

    def _secs(self, kind=None):
        s = self._tid("profile-sec")
        return s.and_(self.page.locator(f"[data-sec='{kind}']")) if kind else s

    def section_text(self, label):
        return self._tid("profile-sec").filter(has_text=label).inner_text()

    def rank(self):
        """The matchup rank sentence, or None."""
        r = self._tid("profile-rank")
        return r.inner_text().strip() if r.count() else None

    def rank_class(self):
        return self._tid("profile-rank").get_attribute("class")

    def marks(self):
        """The tooltips on the open profile that say a flag is untested or failed its test (2026-10-06)."""
        return self._modal.locator("[title], title").evaluate_all(
            """els => els.map(e => e.getAttribute('title') || e.textContent)
                 .filter(s => /^(Untested|Failed test)/.test(s))""")

    def columns(self):
        """The matchup pane's cards: top and bottom edge of each."""
        return self._tid("profile-col").evaluate_all("cs => cs.map(e => { const b = e.getBoundingClientRect(); return [b.top, b.bottom]; })")

    def caps(self, text):
        """The matchup pane's lines containing `text`, each with how many change arrows it carries."""
        return self._tid("profile-cap").filter(has_text=text).evaluate_all(
            "cs => cs.map(c => ({text: c.innerText, deltas: c.querySelectorAll('[data-testid=\"profile-delta\"]').length}))")

    def weathers(self, section=None):
        """The forecast blocks drawn, optionally inside the matchup section whose head contains `section`."""
        root = self._tid("profile-sec").filter(has_text=section) if section else self._modal
        # the icons are ui/weather.js's (`svg.pf-wx-i`), which carries no testid
        return root.get_by_test_id("profile-weather").evaluate_all(
            "ws => ws.map(w => ({text: w.innerText, icons: w.querySelectorAll('svg.pf-wx-i').length}))")

    # ---- the season table ----

    def season_rows(self):
        """Every row of the Season table in order: classes after `ss-row`, then each cell's text (None if absent)."""
        return self._tid("profile-ss-row").evaluate_all("""rs => rs.map(r => {
          const cell = id => r.querySelector(`[data-testid="profile-${id}"]`);
          const txt = id => { const e = cell(id); return e ? e.innerText : null; };
          const stat = cell('ss-stat'), pts = cell('ss-pts');   // an absent stat cell reads as not visible
          return {classes: [...r.classList].slice(1), wk: txt('ss-wk'), opp: txt('ss-opp'), rk: txt('ss-rk'), date: txt('ss-date'),
                  pts: txt('ss-pts'), pts_main: pts && pts.firstChild ? pts.firstChild.textContent : null, note: txt('ss-note'),
                  line: txt('ss-line'), stat_visible: stat ? (${VISIBLE})(stat) : false};
        })""".replace("${VISIBLE}", VISIBLE))

    def season_row(self, kind):
        return next((r for r in self.season_rows() if kind in r["classes"]), None)

    def season_week(self, wk):
        """The first row whose week cell holds `wk`."""
        return next(r for r in self.season_rows() if r["wk"] and str(wk) in r["wk"])

    def week_rows(self):
        """The week-number buttons of the Season table (a played week with a replay): a locator, to count or tap."""
        return self._tid("profile-wk")

    def open_log_row_cell(self):
        """The last cell of the first Season row that opens a game replay: a locator, to read or tap (not the week number)."""
        row = self._tid("profile-ss-row").and_(self.page.locator(".gl-open")).first      # `gl-open` is a class season.js adds, no testid
        return row.locator(":scope > [data-testid^='profile-ss-']").last

    def open_log_row_text(self):
        return self.open_log_row_cell().inner_text()

    def season_date_lefts(self):
        return self._tid("profile-ss-date").evaluate_all("els => els.map(e => Math.round(e.getBoundingClientRect().left))")

    def season_pts_rights(self, n=3):
        return self._tid("profile-ss-row").evaluate_all(
            "(rs, n) => rs.slice(0, n).map(r => Math.round(r.querySelector('[data-testid=\"profile-ss-pts\"]').getBoundingClientRect().right))", n)

    def season_icons(self):
        return self._tid("profile-ss-row").locator("svg").count()

    def modal_overflows(self):
        return self.page.evaluate("document.querySelector('#modal').scrollWidth > document.querySelector('#modal').clientWidth")

    def season_live_game(self):
        """Plant a kicked-off week 3 for SF with Kittle scored in the poll's leaders (no log row for it)."""
        self.page.evaluate("""() => {
          const g = LIVE_SCHEDULE.games.find(x => x.week === 3 && (x.home === 'SF' || x.away === 'SF'));
          const kick = Date.parse(g.kickoff);
          Date.now = () => kick + 3600000;
          if (GD.leagues.length) GD.leagues[0].week = 3; else GD.leagues.push({key: 'espn', week: 3, teams: {}, games: [], rules: {off: [], dst: []}});
          GD_CLOCK = {SF: {state: 'in', q: 3, clock: '4:12', half: false, detail: '', clubs: ['SF', 'KC']}};
          GD_STATS = {week: 3, games: {SF: 'in_game', KC: 'in_game'}, stats: {},
            lead: {'4881': {n: 'George Kittle', pos: 'TE', team: 'SF', pts: 16.2, s: {rec: 6, rec_tgt: 8, rec_yd: 82, rec_td: 1}}}};
          GD_AT = Date.now(); GD_ERR = '';
        }""")

    def poll_final(self):
        """The next poll: SF's game is over."""
        self.page.evaluate("""() => { GD_CLOCK = {SF: {state: 'post', q: 4, clock: '0:00', half: false, detail: '', clubs: ['SF', 'KC']}};
          GD_STATS.games = {SF: 'complete', KC: 'complete'}; document.dispatchEvent(new Event('gd:stats')); }""")

    def poll_without_stats(self):
        """A poll ten hours on that no longer lists him."""
        self.page.evaluate("""() => { const at = Date.now() + 36000000; Date.now = () => at;
          GD_STATS.lead = {}; document.dispatchEvent(new Event('gd:stats')); }""")

    def poll(self):
        self.page.evaluate("() => document.dispatchEvent(new Event('gd:stats'))")

    # ---- usage, props, bio ----

    def zones_rows(self):
        return self._tid("profile-zone").count()

    def team_share(self, team, key):
        """What the team-share block should say about St. Brown (read from the page's own game log)."""
        return self.page.evaluate("""([team, key]) => { const d = teamShareRows(team, key);
          const me = d.rows.findIndex(r => r.slug === 'amonra-st-brown');
          return {me, v: d.rows[me].v, total: d.total, n: d.rows.length}; }""", [team, key])

    def team_block(self):
        """The team-share block: {lead, label}, or None."""
        sec = self._secs("team")
        if sec.count() == 0:
            return None
        return {"lead": sec.first.get_by_test_id("profile-lead").first.inner_text(),
                "label": sec.get_by_test_id("profile-sec-label").inner_text()}

    def team_rows(self):
        """The team-share rows in order: {pct, me, rest, tag, slug}; `tag` is BUTTON when a tap opens him, DIV when it goes nowhere."""
        return self._tid("profile-tm").evaluate_all("""rs => rs.map(r => ({pct: parseInt(r.querySelector('[data-testid="profile-tm-pct"]').innerText),
          me: r.classList.contains('me'), rest: r.classList.contains('rest'), tag: r.tagName, slug: r.dataset.tmslug || null}))""")

    def tm_bar_colours(self):
        """His bar's colour and the first teammate's."""
        return self.page.evaluate("""() => { const c = e => getComputedStyle(e).backgroundColor;
          const me = document.querySelector('#modal [data-testid="profile-tm"].me [data-testid="profile-tm-bar"] i');
          const mate = document.querySelector('#modal button[data-testid="profile-tm"] [data-testid="profile-tm-bar"] i');
          return {me: c(me), mate: c(mate)}; }""")

    def open_teammate(self, slug):
        self._tid("profile-tm").and_(self.page.locator(f"[data-tmslug='{slug}']")).click()

    def gamelog_name(self, slug):
        return self.page.evaluate("s => LIVE_GAMELOG.rows.find(r => r.slug === s).n", slug)

    def splits(self):
        """Each red-zone split: {key, segments: [segment classes]}."""
        return self._tid("profile-split").evaluate_all("""ss => ss.map(s => ({
          key: s.querySelector('[data-testid="profile-split-key"]').innerText,
          segments: [...s.querySelectorAll('[data-testid="profile-split-seg"]')].map(i => i.className)}))""")

    def windows(self):
        """Each section's stated window, by the section's head: {"DET TARGETS": "2 wk"}."""
        return self._tid("profile-win").evaluate_all("""ws => Object.fromEntries(ws.map(w =>
          [w.closest('[data-testid="profile-sec"]').querySelector('[data-testid="profile-sec-label"]').innerText, w.innerText]))""")

    def archetype_players(self):
        """One player with both archetype words and one with a style and no role, from the page's own data."""
        return self.page.evaluate("""(() => {
          const arch = (LIVE_ARCHETYPE && LIVE_ARCHETYPE.players) || {};
          const row = slug => LIVE_GAMELOG.rows.find(r => r.slug === slug);
          const pick = f => { const s = Object.keys(arch).find(k => f(arch[k]) && row(k)); if (!s) return null;
            const r = row(s); return {n: r.n, pos: r.pos, team: r.team, slug: s, role: arch[s].role, style: arch[s].style,
                                      role_null: arch[s].role_null}; };
          return {both: pick(a => a.role && a.style), one: pick(a => !a.role && a.style)};
        })()""")

    def role_word(self, role):
        return self.page.evaluate("v => bdRoleWord(v)", role)

    def arch_slots(self):
        """The head's archetype tiles: {field, text, visible, y, svgs}."""
        return self._tid("profile-arch-slot").evaluate_all("""ss => ss.map(s => ({field: s.dataset.pfarch, text: s.innerText,
          visible: (${V})(s), y: s.getBoundingClientRect().y,
          svgs: s.querySelectorAll('[data-testid="profile-arch-tile"].pf-sk-' + s.dataset.pfarch + ' svg').length}))""".replace("${V}", VISIBLE))

    def open_arch_slot(self, i):
        self._tid("profile-arch-slot").nth(i).click()

    def arch_block(self):
        """The Usage block that says what each word means (the card's `.bd-*` fields come from board/): or None."""
        sec = self._secs("arch")
        if sec.count() == 0:
            return None
        return sec.evaluate("""e => { const f = [...e.querySelectorAll('[data-testid="profile-arch-two"] > .bd-fld')];
          return {means: e.querySelectorAll('.bd-mean').length, evidence: e.querySelectorAll('.bd-ev').length,
                  starts_row: [...e.parentNode.children].indexOf(e) % 2 === 0,
                  side_by_side: f[0].getBoundingClientRect().y === f[1].getBoundingClientRect().y,
                  why: e.querySelector('.bd-why') ? e.querySelector('.bd-why').innerText : null}; }""")

    def prop_player(self):
        """A player with a market log and a posted line, with his bars' values; and one with no log."""
        return self.page.evaluate("""(() => {
          const logs = (LIVE_MARKET && LIVE_MARKET.logs) || {};
          const p = PROPS.find(r => ['WR', 'TE', 'RB'].includes(r.pos) && r.mkt !== 'TD' && logs[r.slug || slugOf(r.n)]);
          const none = LIVE_GAMELOG.rows.find(r => !logs[r.slug] && r.pos !== 'QB');
          return {p: {n: p.n, pos: p.pos, team: p.team, slug: p.slug || slugOf(p.n)}, mkt: p.mkt,
                  line: legSide(p).line, vals: logs[p.slug || slugOf(p.n)].v[p.mkt],
                  none: none && {n: none.n, pos: none.pos, team: none.team, slug: none.slug}};
        })()""")

    def market_name(self, mkt):
        return self.page.evaluate("m => MKT[m]", mkt)

    def prop_heads(self):
        return [s.inner_text() for s in self._secs("prop").get_by_test_id("profile-sec-label").all()]

    def prop_chart(self, name):
        """One market's chart: bars drawn, bars over the line, the caption (the leg sheet's `.ls-*`, no testid)."""
        sec = self._secs("prop").filter(has=self.page.get_by_test_id("profile-sec-label").filter(has_text=re.compile(f"^{re.escape(name)}$", re.I)))
        return {"bars": sec.locator(".ls-bar").count(), "hits": sec.locator(".ls-bar.hit").count(),
                "caption": sec.locator(".ls-cap b").inner_text()}

    def bio_facts(self):
        return self._tid("profile-facts").inner_text()

    def bio_rows(self, ped):
        """bioBlockHTML for a stub pedigree record, as "label value" strings (the page is left as found)."""
        return self.page.evaluate("""(ped) => {
          LIVE_PEDIGREE.players['stub'] = ped;
          const d = document.createElement('div');
          d.innerHTML = bioBlockHTML({slug: 'stub'});
          const out = [...d.querySelectorAll('[data-testid="profile-fact-label"]')].map((k, i) =>
            k.textContent + ' ' + d.querySelectorAll('[data-testid="profile-fact-value"]')[i].textContent);
          delete LIVE_PEDIGREE.players['stub'];
          return out; }""", ped)

    def draft_labels(self):
        return [d.inner_text().upper() for d in self._tid("profile-facts").get_by_test_id("profile-fact-label").all()]

    def draft_leagues(self):
        return self._tid("profile-facts").get_by_test_id("profile-fact-label").evaluate_all(
            "ds => ds.map(d => d.dataset.league).filter(Boolean)")

    def draft_row_span(self):
        return self.page.evaluate("""(() => { const r = document.querySelector('#modal [data-testid="profile-facts"] > div');
          return r.querySelector('dd').getBoundingClientRect().right - r.querySelector('dt').getBoundingClientRect().left; })()""")
