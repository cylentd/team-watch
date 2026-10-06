"""The roster surface (design/src/js/surface/teams/): the Sheet's rows and the Cards.

Every locator lives here, data-testid first (`roster-*`, test hooks only: no CSS or JS reads them). State a
test needs is a class on a testid'd element (`.back`, `.inj-alert`, `.tier-*`), read with `.and_()`; a few
reads go past a testid because the element is drawn outside surface/teams/ (the matchup clause on a row,
`.mu-meta`) or is retired and asserted gone (the red bar across a card's foot, `.tc-inj`).

The week's pack (the gate, the stage, Rip again) and the virtual clock its motion runs on are
pages/roster_pack.py's `RosterPack`, which `RosterPage` extends: one object, one API for a test.

The profile has no leaf: its tests mount the roster and open it from a row (`on_roster`, `RosterRows`),
so this file builds a `ProfilePage` for them (pages/profile.py).
"""
import re

from pages.roster_pack import RosterPack

MOTION = "window.__rosterMotion = true;"      # only a context key: motion tests get a context of their own
NEW_READER = "try { localStorage.removeItem('tw-roster-mode'); } catch (e) {}"   # SEED chose the Sheet; this reader never did


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


class RosterRows:
    """The roster rows a profile opens from, and the matchup clause on each (a row's `.mu-meta`, drawn by
    the profile's matchup block, not the roster)."""

    def __init__(self, page):
        self.page = page
        self._rows = page.get_by_test_id("roster-row")

    def _row(self, name):
        return self._rows.filter(has_text=name).first

    def open(self, name):
        self._row(name).click()

    def open_nth(self, i):
        self._rows.nth(i).click()

    def count(self):
        return self._rows.count()

    def texts(self):
        """The text of every row drawn."""
        return self._rows.evaluate_all("rs => rs.map(r => r.textContent)")

    def show_team(self, key):
        """The roster of one of the reader's teams ("yahoo", "espn"), as the page's own switch draws it."""
        self.page.evaluate("k => { VIEW = k; render(); }", key)

    def matchup(self, name):
        """The row's matchup clause, or None when it has none (a bye, a player with no profile)."""
        meta = self._row(name).locator(".mu-meta")
        if meta.count() == 0:
            return None
        n = meta.locator(".mu-n")
        return {"text": squash(meta.first.inner_text()), "visible": meta.first.is_visible(),
                "n_class": n.get_attribute("class") if n.count() else None,
                "n_title": n.get_attribute("title") if n.count() else None,
                "n_visible": n.is_visible() if n.count() else False}

    def phone_matchup(self, name):
        """What a phone row shows: the old Matchup column (hidden), the clause in the name block, the projection."""
        row = self._row(name)
        meta = row.locator(".nm-2 .mu-meta")
        return {"column_visible": row.locator(".match").is_visible(),
                "clause": {"visible": meta.is_visible(), "text": squash(meta.inner_text()),
                           "n_visible": meta.locator(".mu-n").is_visible()},
                "projection_visible": row.locator(".rproj").is_visible()}

    def chip_count(self):
        return self.page.locator(".mchip").count()

    def column_clauses(self):
        """Matchup clauses drawn in the old Matchup column (`.match .mu-n`): none once a profile file is missing."""
        return self.page.locator(".match .mu-n").count()

    def page_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")


def on_roster(mount, size=(1400, 900), team=None):
    """The roster mounted at a size: (ProfilePage, errors). `team` switches to that team's roster first."""
    from pages.profile import ProfilePage      # the profile opens from the roster; it imports RosterRows from here
    page, errors = mount("roster", size=size)
    profile = ProfilePage(page)
    if team:
        profile.roster.show_team(team)
    return profile, errors


class RosterPage(RosterPack):
    def __init__(self, page):
        super().__init__(page)
        self.rows = RosterRows(page)
        self._modal = page.locator("#modal")
        self._cards = page.get_by_test_id("roster-cards")
        self._grid = self._cards.get_by_test_id("roster-cardgrid")
        self._starters, self._bench = page.get_by_test_id("roster-cards-starters"), page.get_by_test_id("roster-cards-bench")

    def _at(self, i):
        """The i-th card of the first grid (the starters', where `add_card` puts a card)."""
        return self._grid.first.get_by_test_id("roster-card").nth(i)

    # ---- driving: the team, the Sheet / Cards switch, the page ----

    def show(self, team):
        self.page.evaluate("k => { VIEW = k; render(); }", team)

    def mode(self, m):
        self.page.get_by_test_id("roster-mode").and_(self.page.locator(f"[data-rmode='{m}']")).click()

    def show_cards(self, team="espn"):
        """A team's roster in Cards view (an ESPN team is followed, so its pack waits in the starters' place)."""
        self.show(team)
        self.mode("cards")

    def redraw(self):
        self.page.evaluate("render()")

    def roster_mode(self):
        return self.page.evaluate("ROSTER_MODE")

    def stored_mode(self):
        return self.page.evaluate("localStorage.getItem('tw-roster-mode')")

    def mode_switch(self):
        """The Sheet / Cards switch: its box, and each button as [mode, label, pressed, text, has an icon]."""
        buttons = self.page.get_by_test_id("roster-mode").evaluate_all("""bs => bs.map(e =>
          [e.dataset.rmode, e.getAttribute('aria-label'), e.getAttribute('aria-pressed'), e.textContent.trim(), !!e.querySelector('svg')])""")
        box = self.page.locator(".rmode").first.evaluate(
            "e => { const r = e.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, w: r.width, h: r.height}; }")
        return {"rect": box, "buttons": buttons}

    def mode_switch_count(self):
        """Sheet / Cards switches drawn: 1 on the roster, 0 on every other leaf."""
        return self.page.locator(".rmode").count()

    def sheet_pressed(self):
        return self.page.get_by_test_id("roster-mode").and_(self.page.locator("[data-rmode=sheet]")).get_attribute("aria-pressed")

    def first_starter_y(self):
        """Page y of the first starter's row."""
        return (self.page.get_by_test_id("roster-row").and_(self.page.locator(".start")).first
                .evaluate("e => e.getBoundingClientRect().top + scrollY"))

    def card_grid_count(self):
        return self.page.get_by_test_id("roster-cardgrid").count()

    # ---- what the roster holds ----

    def roster_size(self, team="espn"):
        return self.page.evaluate("k => TEAMS[k].roster.length", team)

    def support_size(self, team="espn"):
        return self.page.evaluate("k => TEAMS[k].roster.filter(p => p.pos === 'K' || p.pos === 'DST').length", team)

    def starters_size(self, team="espn"):
        return self.page.evaluate("k => TEAMS[k].roster.filter(p => p.start).length", team)

    def has_packs(self):
        """Both followed teams have a pack this week."""
        return self.page.evaluate("packHas(TEAMS.yahoo) && packHas(TEAMS.espn)")

    def dual_counts(self, team):
        """How many of the reader's leagues roster each player of `team` (0 when only this one): {name: n}."""
        return self.page.evaluate("k => Object.fromEntries(TEAMS[k].roster.map(p => [p.n, p.dual || 0]))", team)

    def dual_of(self, team, name):
        return self.page.evaluate("([k, n]) => TEAMS[k].roster.find(p => p.n === n).dual || 0", [team, name])

    def owners_html(self, player):
        """The owners line a player shows anywhere (`ownersHTML`), for `player` ({n, slug})."""
        return self.page.evaluate("p => ownersHTML(p)", player)

    def search_leagues(self, name):
        """The reader's leagues the search index says rostering `name`."""
        return self.page.evaluate("n => searchIndex().find(e => e.n === n).leagues", name)

    def prop_leagues(self, name):
        """The leagues listed on each of `name`'s props."""
        return self.page.evaluate("n => PROPS.filter(p => p.n === n).map(p => p.leagues)", name)

    def signed_block_is_null(self):
        return self.page.evaluate("LIVE_SIGNED === null")

    def signed_week(self):
        return self.page.evaluate("LIVE_SIGNED.wk")

    def espn_row_starts(self, rows):
        """Which of ESPN-shaped rows (`{n, pos, team, slug, slot}`) the page starts."""
        return self.page.evaluate("rows => espnRows(rows).map(p => p.start)", rows)

    # ---- cards ----

    def card_count(self):
        return self._card.count()

    def support_card_count(self):
        return self._where(".tier-k, .tier-dst").count()

    def autograph_count(self):
        return self._cards.get_by_test_id("roster-card-auto").count()

    def add_card(self, player, rank=None):
        """Draw one more card for `player` ({n, pos, team, slot, start, slug}) at the end of the starters'
        grid, with his projection rank when given; returns its index there."""
        return self.page.evaluate("""([p, rank]) => { const g = document.querySelector('[data-testid="roster-cardgrid"]');
          if (rank !== null) LIVE_PROJECTIONS.players[p.slug] = {...(LIVE_PROJECTIONS.players[p.slug] || {pts: 12}), rank};
          g.insertAdjacentHTML('beforeend', cardHTML(p, 0, 'espn')); fitSig(document); fitBanner(document);
          return g.querySelectorAll('[data-testid="roster-card"]').length - 1; }""", [player, rank])

    def add_support_cards(self):
        """A defense and a kicker, drawn directly at the end of the starters' grid."""
        self.page.evaluate("""document.querySelector('[data-testid="roster-cardgrid"]').insertAdjacentHTML('beforeend',
          cardHTML({n:'Bengals', pos:'DST', team:'CIN', slot:'DST', start:true, slug:null}, 0, 'espn') +
          cardHTML({n:'Cam Little', pos:'K', team:'JAX', slot:'K', start:true, slug:null}, 0, 'espn'))""")

    def add_support_and_signed_cards(self):
        """A defense, a kicker and a signed skill player the Grid has a row for, at the end of the starters'
        grid (a signed back is the tallest one a 360px card holds)."""
        self.page.evaluate("""(() => {
          const sk = TEAMS.espn.roster.find(p => p.slug && WV_PROOF[p.pos] && USAGE.rows.some(r => r.slug === p.slug));
          LIVE_SIGNED.players[sk.slug] = {rank: 2, pts: 22.6};
          document.querySelector('[data-testid="roster-cardgrid"]').insertAdjacentHTML('beforeend',
            cardHTML({n:'Bengals', pos:'DST', team:'CIN', slot:'DST', start:true, slug:null}, 0, 'espn') +
            cardHTML({n:'Cam Little', pos:'K', team:'JAX', slot:'K', start:true, slug:null}, 0, 'espn') + cardHTML(sk, 0, 'espn'));
        })()""")

    def support_faces(self):
        """The last defense's and the last kicker's face: {holo, banner, badge}."""
        def face(card):
            return {"holo": card.get_by_test_id("roster-card-holo").count(),
                    "banner": card.get_by_test_id("roster-card-ban").text_content().strip(),
                    "badge": card.get_by_test_id("roster-card-badge").text_content().strip()}
        return {"dst": face(self._where(".tier-dst").last), "k": face(self._where(".tier-k").last)}

    def defense_abbr(self):
        return self._where(".tier-dst").last.get_by_test_id("roster-card-abbr").inner_text()

    def metal_look(self, i):
        """What the border and badge of card i say: {tier, background, ring, holo, badge}."""
        card = self._at(i)
        got = card.evaluate("""tc => ({tier: [...tc.classList].find(c => c.startsWith('tier-')),
          background: getComputedStyle(tc).backgroundImage.split('(')[0], ring: getComputedStyle(tc).getPropertyValue('--ring').trim()})""")
        badge = card.get_by_test_id("roster-card-badge")
        got["holo"] = card.get_by_test_id("roster-card-holo").count() > 0
        got["badge"] = badge.get_by_test_id("roster-card-badge-pos").text_content() + badge.get_by_test_id("roster-card-badge-rank").text_content()
        return got

    def name_fit(self, i):
        """Card i's banner name, whether it ends before the badge, and its font size."""
        card = self._at(i)
        return {"name": card.get_by_test_id("roster-card-name").text_content(),
                "clear_of_badge": card.evaluate("""tc => { const s = tc.querySelector('[data-testid="roster-card-name"]'),
                  b = tc.querySelector('[data-testid="roster-card-badge"]'); return s.offsetLeft + s.offsetWidth <= b.offsetLeft; }"""),
                "font": card.get_by_test_id("roster-card-name").evaluate("s => parseFloat(getComputedStyle(s).fontSize)")}

    def backs_overflowing(self):
        """The class names of every card back whose content is taller than the back."""
        return self._cards.get_by_test_id("roster-card-back").evaluate_all(
            "bs => bs.filter(b => b.scrollHeight > b.clientHeight + 1).map(b => b.className)")

    def signed_backs(self):
        return self._cards.get_by_test_id("roster-card-back").and_(self.page.locator(".signed")).count()

    def back_facts(self, player, rank, signed):
        """A card drawn off screen for `player`, planted at `rank` and signed (rank, pts): the back's first
        line, the game, the signed row, and the front's text."""
        return self.page.evaluate("""([p, rank, sg]) => {
          LIVE_PROJECTIONS.players[p.slug] = {pts: 12, rank};
          LIVE_SIGNED.players[p.slug] = sg;
          const d = document.createElement('div'); d.innerHTML = cardHTML(p, 0, 'espn');
          delete LIVE_SIGNED.players[p.slug];
          const q = id => d.querySelector('[data-testid="' + id + '"]');
          return {first: q('roster-back-rank').textContent, matchup: cardMatchup('JAX', cardGame('JAX')),
                  signed: q('roster-back-signed')?.textContent, front: q('roster-card-front').textContent};
        }""", [player, rank, signed])

    def sign(self, slug, rank, pts):
        self.page.evaluate("([s, r, p]) => { LIVE_SIGNED.players[s] = {rank: r, pts: p}; }", [slug, rank, pts])

    def autographs_of_two_skill_players(self):
        """The first two rostered skill players, the first signed, the second not (the nobody-hurt, drawn
        off screen): how many autographs each face carries, or None without two."""
        return self.page.evaluate("""(() => {
          const ps = TEAMS.espn.roster.filter(p => p.slug && ['QB','RB','WR','TE'].includes(p.pos)).slice(0, 2);
          if (ps.length < 2) return null;
          LIVE_SIGNED.players = {[ps[0].slug]: {rank: 2, pts: 30}};
          if (typeof LIVE_INJURY !== 'undefined' && LIVE_INJURY) LIVE_INJURY.players = {};
          ps.forEach(p => { p.status = null; });
          const sig = p => { const d = document.createElement('div'); d.innerHTML = cardHTML(p, 0, 'espn');
            return d.querySelectorAll('[data-testid="roster-card-auto"]').length; };
          return [sig(ps[0]), sig(ps[1])];
        })()""")

    def autograph(self, i):
        """Card i's autograph: its parts, what shows, whether it fits the card, and its words."""
        card = self._at(i)
        auto = card.get_by_test_id("roster-card-auto")
        opacity = lambda id: card.get_by_test_id(id).evaluate("e => getComputedStyle(e).opacity")
        got = card.evaluate("""tc => { const a = tc.querySelector('[data-testid="roster-card-auto"]'),
          c = tc.querySelector('[data-testid="roster-card-auto-cool"]').getBoundingClientRect(), r = tc.getBoundingClientRect(),
          wrap = a.querySelector('[data-testid="roster-card-auto-wrap"]');
          return {inside: c.left >= r.left && c.right <= r.right && c.top >= r.top && c.bottom <= r.bottom,
                  fits: wrap.offsetWidth <= a.clientWidth, font: parseFloat(getComputedStyle(a).fontSize),
                  shaped: !!a.querySelector(':scope > [data-testid="roster-card-auto-wrap"] > [data-testid="roster-card-auto-cool"] + [data-testid="roster-card-auto-hot"] + [data-testid="roster-card-auto-tip"]')}; }""")
        got.update({"count": auto.count(), "cool": card.get_by_test_id("roster-card-auto-cool").text_content(),
                    "hot": card.get_by_test_id("roster-card-auto-hot").text_content(),
                    "opacity": (opacity("roster-card-auto-cool"), opacity("roster-card-auto-hot"), opacity("roster-card-auto-tip")),
                    "back": card.get_by_test_id("roster-back-signed").text_content(), "title": auto.get_attribute("title")})
        return got

    def fronts_with_at_most_one_autograph(self):
        return self._cards.get_by_test_id("roster-card-front").evaluate_all(
            "fs => fs.every(f => f.querySelectorAll('[data-testid=\"roster-card-auto\"]').length <= 1)")

    def plant_out_player(self, slug):
        self.page.evaluate("""s => { LIVE_INJURY.players[s] = {s: 'OUT', code: 'IR', note: 'Knee'};
          LIVE_PROJECTIONS.players[s] = {pts: null, rank: null, out: 'IR'}; }""", slug)

    def out_card(self, i):
        """An OUT card: the bar across its foot (none), its number, the number's colour, the colour the page
        calls `down`, and the photo's filter."""
        card = self._at(i)
        down = self.page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--down-rgb')").strip().replace(" ", ", ")
        return {"bar": card.locator(".tc-inj").count(),      # retired: a red bar across the foot
                "num": card.get_by_test_id("roster-card-num").text_content(),
                "num_color": card.get_by_test_id("roster-card-num").evaluate("e => getComputedStyle(e).color"),
                "down": f"rgb({down})",
                "photo_filter": card.get_by_test_id("roster-card-head").evaluate("e => getComputedStyle(e).filter")}

    def plant_chip_scene(self):
        """Rain at JAX's stadium and a Questionable and a Doubtful receiver."""
        self.page.evaluate("""(() => { const g = cardGame('JAX'); LIVE_WEATHER.teams[g.venue] = {roof: 'outdoor', wind: '22 mph', precip_pct: 60, short: 'Rain'};
          LIVE_INJURY.players['test-q-wr'] = {s: 'Q', code: 'Questionable', note: null};
          LIVE_INJURY.players['test-d-wr'] = {s: 'D', code: 'Doubtful', note: 'Hamstring'}; })()""")

    def chip_layout(self, indexes):
        """For each card: how many chips it carries, whether one covers the projection, badge or banner, and
        whether all sit inside the face."""
        return [self._at(i).evaluate("""tc => {
          const box = id => { const e = tc.querySelector('[data-testid="' + id + '"]'); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
          const hit = (a, b) => a && b && a[0] < b[2] && b[0] < a[2] && a[1] < b[3] && b[1] < a[3];
          const chips = [...tc.querySelectorAll('[data-testid="roster-card-flags"] > [data-testid="roster-card-chip"]')].map(e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; });
          const face = tc.querySelector('[data-testid="roster-card-front"]').getBoundingClientRect();
          return {n: chips.length, clash: chips.some(c => hit(c, box('roster-card-num')) || hit(c, box('roster-card-badge')) || hit(c, box('roster-card-ban'))),
                  inside: chips.every(c => c[0] >= face.left && c[2] <= face.right)}; }""") for i in indexes]

    def border_animation(self):
        """The first card's border light: [animation name, iteration count]."""
        return self._card.first.get_by_test_id("roster-card-fx").evaluate(
            "e => { const s = getComputedStyle(e, '::after'); return [s.animationName, s.animationIterationCount]; }")

    def border_mask(self):
        return self._card.first.get_by_test_id("roster-card-fx").evaluate(
            "e => { const s = getComputedStyle(e); return s.maskComposite + ' ' + s.webkitMaskComposite; }")

    def shine_first_card(self, on):
        self._card.first.evaluate("(el, on) => el.classList.toggle('shine', on)", on)

    def plant_one_out_one_questionable(self):
        """On every team: the first starter out, a bench player questionable, everyone else healthy; drawn again."""
        self.page.evaluate("""(() => { LIVE_INJURY.players = {};
          for (const tm of Object.values(TEAMS)){
            const s = tm.roster.find(p => p.start && p.slug && !['K','DST'].includes(p.pos));
            const b = tm.roster.find(p => !p.start && p.slug);
            tm.roster.forEach(p => { p.status = null; });
            if (s) LIVE_INJURY.players[s.slug] = {s: 'OUT', code: 'IR', note: 'Knee'};
            if (b) LIVE_INJURY.players[b.slug] = {s: 'Q', code: 'Questionable', note: null};
          }
          render(); })()""")

    def sit_pill(self):
        """The red pill in the "This week" row: {count, text, title}."""
        warn = self.page.get_by_test_id("roster-brief-head").get_by_test_id("roster-inj-warn")
        n = warn.count()
        return {"count": n, "text": warn.inner_text() if n == 1 else None, "title": warn.get_attribute("title") if n == 1 else None}

    def sit_strips(self):
        """The retired full-width strip above the roster (`div.inj-warn`; the pill is a span): none."""
        return self.page.locator("div.inj-warn").count()

    def alert_cards(self):
        """Cards marked as a starter who will likely sit: {count, bars} (the retired red bar across the foot)."""
        alert = self._where(".inj-alert")
        return {"count": alert.count(), "bars": alert.locator(".tc-inj").count()}

    def questionable_cards(self):
        """{chips: Q chips on Q cards, alerts: Q cards marked as sitting}."""
        q = self._where(".inj-q")
        return {"chips": q.get_by_test_id("roster-card-chip").and_(self.page.locator(".q")).count(),
                "alerts": q.and_(self.page.locator(".inj-alert")).count()}

    def alert_rows(self):
        return self.page.get_by_test_id("roster-row").and_(self.page.locator(".inj-alert")).count()

    def flip(self, i=0):
        self._card.nth(i).click()

    def flipped(self, i=0):
        return "back" in (self._card.nth(i).get_attribute("class") or "").split()

    def open_profile_from_back(self, i=0):
        self._card.nth(i).get_by_test_id("roster-back-open").click()

    def profile_open(self):
        return self._modal.is_visible()

    def role_sheet_back(self):
        """The back of the first rostered skill player the Grid has a row for, drawn off screen while healthy
        and dry: {stats, bars, week, spark}, or None without one."""
        return self.page.evaluate("""(() => {
          const p = TEAMS.espn.roster.find(p => WV_PROOF[p.pos] && USAGE.rows.some(r => r.slug === p.slug));
          if (!p) return null;
          // Healthy and dry, so the heading's second line is the week (an injury or the weather outranks it).
          if (typeof LIVE_INJURY !== 'undefined' && LIVE_INJURY) LIVE_INJURY.players = {};
          p.status = null; if (typeof LIVE_WEATHER !== 'undefined' && LIVE_WEATHER) LIVE_WEATHER.teams = {};
          const d = document.createElement('div'); d.innerHTML = cardHTML(p, 0, 'espn');
          const q = id => [...d.querySelectorAll('[data-testid="' + id + '"]')];
          const last = Math.max(...USAGE.rows.filter(r => r.slug === p.slug).map(r => r.wk));
          return {stats: q('roster-back-stat').length, bars: q('roster-back-bar').map(b => b.querySelector('i').style.getPropertyValue('--p')),
                  week: q('roster-back-why')[0].textContent.includes(String(last)), spark: d.querySelectorAll('.tc-back .spark').length};
        })()""")

    def head_sources(self):
        """The photo a card takes for a player with a 256px head, then for one with only the 96px."""
        return self.page.evaluate("""(() => {
          HEADS_LG['a-sharp-one'] = 'heads/lg/a-sharp-one.webp'; HEADS['a-sharp-one'] = 'heads/a-sharp-one.webp';
          HEADS['a-soft-one'] = 'heads/a-soft-one.webp';
          const src = slug => { const d = document.createElement('div'); d.innerHTML = cardHeadHTML({n: 'A One', slug, pos: 'WR'});
            return d.querySelector('img').getAttribute('src'); };
          return [src('a-sharp-one'), src('a-soft-one')];
        })()""")

    def photo_geometry(self):
        """The first headshot, its art, the first face and the first banner, as boxes; and whether there is a photo."""
        img = self._cards.get_by_test_id("roster-card-head").locator(":scope > img").first
        return {"has_photo": img.count() > 0,
                "face": self._cards.get_by_test_id("roster-card-front").first.bounding_box(),
                "art": img.locator("xpath=../..").bounding_box() if img.count() else None,
                "banner": self._cards.get_by_test_id("roster-card-ban").first.bounding_box(),
                "photo": img.bounding_box() if img.count() else None}

    def grid_columns(self):
        """How many columns each card grid lays out."""
        return self._grid.evaluate_all("gs => gs.map(g => getComputedStyle(g).gridTemplateColumns.split(' ').length)")

    def starters_box(self):
        return self._starters.bounding_box()

    def bench_box(self):
        return self._bench.bounding_box()

