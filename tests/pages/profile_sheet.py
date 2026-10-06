"""The profile's stat sheet and Compare (design/src/js/surface/profile/orb.js, orbsheet.js, radarkit.js,
ladder.js, cmp*.js): the sphere that opens the sheet, its radar and ladder, the elite marks, and the
Compare layer.

`ProfileSheet` is the base of `ProfilePage` (pages/profile.py), so a test reaches all of it through the one
object. Every locator is a `profile-*` data-testid (test hooks only), through the modal's `_tid`; a few
reads go past one because the element is drawn outside surface/profile/ (`.pf-lr`, `.pf-cap`, `.cmp-sheet`).
"""
from pages.roster import squash

FRAMES = "n => new Promise(r => { const f = () => --n > 0 ? requestAnimationFrame(f) : r(); f(); })"


class ProfileSheet:
    def __init__(self, page):
        self.page = page
        self._modal = page.locator("#modal")        # the shell's dialog, shared with the game sheet: no testid
        self._tid = self._modal.get_by_test_id

    # ---- the stat sheet (the sphere's layer) ----

    def orb_text(self):
        return squash(self._tid("profile-orb").inner_text())

    def orb_count(self):
        return self._tid("profile-orb").count()

    def orb_focused(self):
        return self.page.evaluate("document.activeElement.classList.contains('pf-orb')")

    def orb_tint(self):
        """The position tint class on the sphere (`pos-rb`) and on the sheet, or None."""
        pick = "e => [...e.classList].find(c => c.startsWith('pos-')) || null"
        sheet = self._tid("profile-sheet")
        return {"orb": self._tid("profile-orb").evaluate(pick), "sheet": sheet.evaluate(pick) if sheet.count() else None}

    def orb_yaw(self):
        return self.page.evaluate("ORB_STATE.get(document.querySelector('#modal [data-testid=\"profile-orb\"]')).yaw")

    def wait_orb_turning(self, past=0):
        self.page.wait_for_function(
            "p => ORB_STATE.get(document.querySelector('#modal [data-testid=\"profile-orb\"]')).yaw > p", arg=past)

    def wait_orb(self):
        self._tid("profile-orb").wait_for()

    def frames(self, n):
        self.page.evaluate(FRAMES, n)

    def allow_motion(self, on):
        self.page.emulate_media(reduced_motion="no-preference" if on else "reduce")

    def hold_frames(self):
        """Queue the page's animation frames so a test runs them on its own clock."""
        self.page.evaluate("""() => { const real = window.requestAnimationFrame.bind(window), q = [];
          window.__rafReal = real; window.__rafQ = q; window.requestAnimationFrame = cb => q.push(cb); }""")

    def run_frames(self, n, step=16.7):
        self.page.evaluate("""([n, step]) => { let t = performance.now();
          for (let i = 0; i < n; i++) { t += step; window.__rafQ.splice(0).forEach(cb => cb(t)); } }""", [n, step])

    def release_frames(self):
        self.page.evaluate("""() => { if (!window.__rafReal) return; window.requestAnimationFrame = window.__rafReal;
          window.__rafQ.splice(0).forEach(cb => window.__rafReal(cb)); window.__rafReal = null; }""")

    def rank_mark(self, pos, axis, slug):
        return self.page.evaluate("([p, a, s]) => rankMark(sheetRank(p, a, s))", [pos, axis, slug])

    def stat_rank(self, pos, axis, slug):
        """[rank, of, tied] of a player on a stat among his position."""
        return self.page.evaluate("([p, a, s]) => sheetRank(p, a, s)", [pos, axis, slug])

    def sheet_axes(self, pos=None):
        if pos:
            return self.page.evaluate("p => USAGE.sheet.axes[p].map(a => a.id)", pos)
        return self.page.evaluate("Object.fromEntries(Object.entries(USAGE.sheet.axes).map(([k, v]) => [k, v.map(a => a.id)]))")

    def open_sheet(self):
        self._tid("profile-orb").click()

    def layers(self):
        return self._tid("profile-orblayer").count()

    def layer_radars(self):
        return self._tid("profile-orblayer").get_by_test_id("profile-radar").count()

    def radars(self):
        return self._tid("profile-radar").count()

    def sheet_stat(self):
        """The stat the sheet's ladder has lit."""
        return self._tid("profile-orbsheet").get_by_test_id("profile-lr").and_(self.page.locator(".on")).get_by_test_id("profile-lr-name").inner_text()

    def fold_last_stat(self):
        self._tid("profile-orbsheet").get_by_test_id("profile-lr-toggle").last.click()

    def open_folds(self):
        return self._tid("profile-orbsheet").get_by_test_id("profile-lr").and_(self.page.locator("[open]")).count()

    def radar_top(self):
        return self._tid("profile-orbsheet").get_by_test_id("profile-radar").bounding_box()["y"]

    def scroll_state(self):
        """What lies under the sheet: the profile's scroll and the page's."""
        return self.page.evaluate("[document.querySelector('#modal .dr-body').scrollTop, scrollY]")

    def wheel_over_scrim(self):
        box = self._tid("profile-orbscrim").bounding_box()
        self.page.mouse.move(box["x"] + 4, box["y"] + 4)
        self.page.mouse.wheel(0, 600)
        self.page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => requestAnimationFrame(r))))")

    def swipe_over_scrim(self):
        """A sideways swipe that starts and ends on the scrim."""
        self.page.evaluate("""(() => { const el = document.querySelector('#modal [data-testid="profile-orbscrim"]');
          const at = x => [new Touch({identifier: 1, target: el, clientX: x, clientY: 20})];
          el.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, touches: at(300), changedTouches: at(300)}));
          el.dispatchEvent(new TouchEvent('touchend', {bubbles: true, touches: [], changedTouches: at(120)})); })()""")

    def elite(self, kind):
        """The stats flagged elite on the open sheet, sorted: kind is "row" (ladder), "label" or "dot"."""
        tid = {"row": "profile-lr", "label": "profile-radar-label", "dot": "profile-radar-dot"}[kind]
        return sorted(self._tid("profile-orbsheet").get_by_test_id(tid).evaluate_all(
            "els => els.filter(e => e.classList.contains('elite')).map(e => e.dataset.col)"))

    def elite_expected(self, slug):
        """The axes the page's own rule (sheetElite) calls elite for a player."""
        return self.page.evaluate("""s => { const sh = sheetFor({slug: s});
          return sh.axes.filter(a => sheetElite(sh, a, sheetRank(sh.pos, a.id, sh.row.slug))).map(a => a.id).sort(); }""", slug)

    def elite_glow(self):
        return self._tid("profile-orbsheet").locator(".pf-lr.elite .pf-lr-bar i").first.evaluate("e => getComputedStyle(e).boxShadow")

    def radar_counts(self):
        return {"shape": self._tid("profile-radar-shape").count(), "rings": self._tid("profile-radar-ring").count(),
                "labels": self._tid("profile-radar-label").count(), "dots": self._tid("profile-radar-dot").count(),
                "notes": self._tid("profile-radar-note").count()}

    def radar_note(self):
        return self._tid("profile-radar-note").text_content().strip()

    def radar_text(self):
        return self._tid("profile-radar").text_content()

    def radar_box_text(self):
        return self._tid("profile-radar-box").text_content()

    def radar_labels_named(self, name):
        return self._tid("profile-radar-label").filter(has_text=name).count()

    def label_lit(self, name):
        return "on" in self._tid("profile-radar-label").filter(has_text=name).get_attribute("class").split()

    def tap_label(self, name):
        self._tid("profile-radar-label").filter(has_text=name).click()

    def lit_dot(self):
        return self._tid("profile-radar-dot").and_(self.page.locator(".on")).get_attribute("data-col")

    def wait_lit_dot(self, col):
        self._tid("profile-radar-dot").and_(self.page.locator(f".on[data-col='{col}']")).wait_for()

    def sheet_caps(self):
        return self._tid("profile-sheet").locator(".pf-cap").count()

    def bar_provisional(self, col):
        return "prov" in self._tid("profile-radar-bar").and_(self.page.locator(f"[data-col='{col}']")).get_attribute("class").split()

    def _lr(self, col):
        return self._tid("profile-lr").and_(self.page.locator(f"[data-col='{col}']"))

    def ladder_cols(self):
        return [r.get_attribute("data-col") for r in self._tid("profile-lr").all()]

    def ladder_percentiles(self, cols):
        return self.page.evaluate("""cols => cols.map(c => { const rk = sheetRank('WR', c, 'amonra-st-brown');
          return rk ? ladderPct(rk) : -1; })""", cols)

    def lr(self, col):
        """One ladder row: {on, open, elite, rank: [words], rank_note, def_visible, gap, gap_up, def, why, text}."""
        r = self._lr(col)
        gap, d, why, note = (r.get_by_test_id(t) for t in ("profile-lr-gap", "profile-lr-def", "profile-lr-why", "profile-lr-rank"))
        return {"on": "on" in r.get_attribute("class").split(), "open": r.get_attribute("open") is not None,
                "elite": "elite" in r.get_attribute("class").split(), "rank": note.inner_text().split(),
                "rank_small": note.locator("small").inner_text() if note.locator("small").count() else None,
                "def_visible": d.is_visible() if d.count() else None, "def": d.inner_text() if d.count() else None,
                "why": why.inner_text() if why.count() else None,
                "gap": gap.inner_text() if gap.count() else None,
                "gap_up": "up" in gap.get_attribute("class").split() if gap.count() else None, "text": r.inner_text()}

    def toggle_ladder(self, col):
        self._lr(col).get_by_test_id("profile-lr-toggle").click()

    def wait_dot(self, col):
        self.wait_lit_dot(col)

    def ladder_facts(self, col):
        """The spans of a ladder row's fold (sample, gap, source, window), last one last."""
        return self._lr(col).get_by_test_id("profile-lr-facts").locator("span").all_inner_texts()

    def plant_stat_weeks(self, slug, stat, weeks):
        """Give a player's usage rows these weeks (as heatradar publishes them); returns the ladder's window text."""
        return self.page.evaluate("""([slug, stat, weeks]) => {
          const row = USAGE.rows.find(r => r.slug === slug);
          USAGE.rows = USAGE.rows.filter(r => r.slug !== slug);
          weeks.forEach(wk => USAGE.rows.push({...row, wk, v: {...row.v, [stat]: 1.5 + wk}}));
          const s = sheetFor({slug});
          return ladderWindow(s, statWeeks(slug, stat)); }""", [slug, stat, weeks])

    def strip_axes(self, slug, stats):
        """Null some of a player's measured stats on the sheet, as a player heatradar has not covered yet."""
        self.page.evaluate("""([slug, stats]) => {
          const r = USAGE.sheet.rows.find(x => x.slug === slug);
          stats.forEach(k => { r.v[k] = null; });
          for (const k in SHEET_BY) delete SHEET_BY[k];   // memoised per position+axis
        }""", [slug, stats])

    def floor_probe(self):
        """A rate under its floor: what the ladder, the radar and Leaders say about L. Jackson (1 of 4) and J. Allen (3 of 5)."""
        return self.page.evaluate("""(() => {
          const s = sheetFor({slug: 'lamar-jackson'}), a = s.axes.find(x => x.id === 'gl_pct');
          const lad = (who) => { const d = document.createElement('div'); d.innerHTML = ladderHTML(who, 'gl_pct'); return d; };
          const q = (d, id) => d.querySelector('[data-col="gl_pct"] [data-testid="' + id + '"]');
          const d = lad(s), row = d.querySelector('[data-col="gl_pct"]');
          const d2 = lad(sheetFor({slug: 'josh-allen'}));
          const ranked = [...d.querySelectorAll('[data-testid="profile-lr"]')].map(r => !!sheetRank('QB', r.dataset.col, 'lamar-jackson'));
          return {rank: sheetRank('QB', 'gl_pct', 'lamar-jackson'), allen: sheetRank('QB', 'gl_pct', 'josh-allen'),
                  facts: q(d, 'profile-lr-facts').textContent, floor: q(d, 'profile-lr-floor').textContent,
                  dim: q(d, 'profile-lr-value').className, have: q(d, 'profile-lr-rank').textContent,
                  last: ranked.slice(ranked.indexOf(false)).every(x => !x),
                  allenFacts: q(d2, 'profile-lr-facts').textContent,
                  allenFloor: d2.querySelectorAll('[data-col="gl_pct"] [data-testid="profile-lr-floor"]').length,
                  allenRk: q(d2, 'profile-lr-rank').querySelector('b').textContent,
                  held: bdThinOut('QB', 'gl_pct', -1).map(r => sampleShort(r, a))};
        })()""")

    # ---- Compare ----

    def compare_open(self):
        self._tid("profile-compare-open").click()

    def compare_layers(self):
        return self._tid("profile-cmp-layer").count()

    def compare_rows(self):
        return self._tid("profile-cmp-row").count()

    def compare_go_disabled(self):
        return self._tid("profile-cmp-go").is_disabled()

    def compare_pick(self, i):
        self._tid("profile-cmp-row").nth(i).click()

    def compare_picked(self, name=None):
        picked = self._tid("profile-cmp-row").and_(self.page.locator(".on"))
        return (picked.filter(has_text=name) if name else picked).count()

    def compare_go(self):
        self._tid("profile-cmp-go").click()

    def compare_search(self, q):
        self._tid("profile-cmp-search").fill(q)

    def compare_query(self):
        return self._tid("profile-cmp-search").input_value()

    def compare_rows_named(self, name):
        return self._tid("profile-cmp-row").filter(has_text=name).count()

    def compare_pick_named(self, name, fresh=False):
        """Tap the first list row containing `name`; fresh skips the ones already ticked."""
        rows = self._tid("profile-cmp-row").filter(has_text=name)
        (rows.and_(self.page.locator(":not(.on)")) if fresh else rows).first.click()

    def compare_pick_two(self, q):
        """Search `q` twice and tick the first two results, as a reader sets three players side by side."""
        self.compare_open()
        self.compare_search(q)
        self.compare_pick_named(q.upper())
        self.compare_search(q)
        self.compare_pick_named(q.upper(), fresh=True)
        self.compare_go()

    def compare_cards(self):
        return self._tid("profile-cmp-card").count()

    def compare_strips(self):
        return self._tid("profile-cmp-strip").count()

    def compare_shapes(self):
        return self._tid("profile-cmp-shape").count()

    def compare_graphs(self):
        return self._tid("profile-cmp-graph").count()

    def compare_focus(self):
        return self._tid("profile-cmp-card").and_(self.page.locator(".on")).get_attribute("data-i")

    def compare_focus_in_sheet(self):
        return self.page.evaluate("!!document.activeElement.closest('.cmp-sheet')")

    def compare_card(self, i):
        self._tid("profile-cmp-card").and_(self.page.locator(f"[data-i='{i}']")).click()

    def compare_graph_class(self):
        return self._tid("profile-cmp-graph").get_attribute("class")

    def compare_front_shapes(self, i):
        return self._tid("profile-cmp-shape").and_(self.page.locator(f".front.cmp-s{i}")).count()

    def compare_graph_ranks(self):
        return self._tid("profile-cmp-graph").get_by_test_id("profile-radar-value").all_inner_texts()

    def compare_graph_buttons(self):
        return self._tid("profile-cmp-graph").locator("button").count()

    def compare_sheet_overflow(self):
        """Pixels the Compare sheet scrolls by (0 when it fits)."""
        sh, ch = self._tid("profile-cmp-sheet").evaluate("e => [e.scrollHeight, e.clientHeight]")
        return sh - ch
