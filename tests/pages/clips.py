"""The Roster's Week plays rail (design/src/js/surface/teams/reel.js): one card per starter with clips, the
header, the page arrows, and the "This week" list that folds under it.

Every rail locator is a `clips-*` data-testid (test hooks only: no CSS or JS reads them). The "This week" list
under it is `roster-brief-*` (brief.js; its own reads are pages/roster_brief.py). One thing is not the rail's
and is found by class until its owner gets a hook: the Roster's page layout (`.rl-reel`, `.rl-rows`, render.js).
The League's team line is
pages/league_chip.py, and the roster's rows and cards are `RosterPage` (pages/roster.py).

The clip theater is clipsheet.js's: `show(stubs=True)` puts stubs on the page, and `opened()` reads what the
rail asked the theater to open.
"""
STUBS = """() => {
  window.__opened = null; window.__warm = 0;
  window.clipTheaterOpen = (items, i, el) => { window.__opened = {ids: items.map(it => it.c.id), who: items.map(it => it.p.n), ps: items.map(it => it.ps.map(p => p.n)), i, el: !!el && el.tagName}; };
  window.clipWarm = () => { window.__warm++; };
}"""
NO_NAV = "document.addEventListener('click', e => { if (e.target.closest('a.reel-card')) e.preventDefault(); }, true)"
RECT = "e => { const r = e.getBoundingClientRect(); return {l: r.left, r: r.right, t: r.top, w: r.width, h: r.height}; }"
FITS_TRACK = "(() => { const t = document.querySelector('[data-testid=\"clips-track\"]'); return t.scrollWidth <= t.clientWidth + 1; })()"


class ClipsPage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._reel, self._track, self._card = tid("clips-reel"), tid("clips-track"), tid("clips-card")
        self._brief = tid("roster-brief")                        # brief.js, reel.js
        self._parts = {
            "track": self._track, "card": self._card, "head": tid("clips-head"), "title": tid("clips-title"),
            "count": tid("clips-count"), "all": tid("clips-all"), "prev": tid("clips-prev"), "next": tid("clips-next"),
            "thumb": tid("clips-thumb"), "ov": tid("clips-ov"), "nm": tid("clips-nm"), "pt": tid("clips-pt"),
            "l2": tid("clips-l2"), "n": tid("clips-n"),
            "button_card": self._card.and_(page.locator("button")), "link_card": self._card.and_(page.locator("a")),
            "end": self._card.and_(page.locator(".reel-end")),
            "rows": page.locator(".rl-rows"), "list": self._brief,      # render.js, brief.js
        }

    # ---- setting the page up ----

    def show(self, team="espn", mode="sheet", served=True, stubs=False, pack_opened=False, then=None):
        """A team's roster in Sheet or Cards. `served` stands in for an http(s) page (from file:// clipEmbedOk()
        is false and every card is a link); `stubs` replaces the theater and the warm-up; `pack_opened` marks
        this week's pack opened, so no stage covers the cards; `then` is one more arrow function of JS to run
        once the roster is drawn. All of it is one round trip but the pack's mark."""
        steps = []
        if served:
            steps.append("clipEmbedOk = () => true;")
        if stubs:
            steps.append(f"({STUBS})(); {NO_NAV};")
        if pack_opened:
            self.page.evaluate("packMark(TEAMS.espn, schedWeek())")    # its own call: test_layer_ratchet counts it
        steps.append(f"VIEW='{team}'; ROSTER_MODE='{mode}'; render();")
        if then:
            steps.append(f"({then})();")
        self.page.evaluate("() => { " + " ".join(steps) + " }")

    def drop_clips(self):
        """The page as built with no clips block: every reader of LIVE_CLIPS finds no week and no player."""
        self.page.evaluate("LIVE_CLIPS.players = {}; LIVE_CLIPS.week = null; LIVE_CLIPS.games = {}; LIVE_CLIPS.alias = {}")

    def disable_embedding(self):
        """YouTube refuses every clip on other sites; the rail draws again."""
        self.page.evaluate("for (const l of Object.values(LIVE_CLIPS.players)) l.forEach(c => { c.embed = false; }); render()")

    def redraw(self):
        self.page.evaluate("render()")

    def plant_week_row(self, name, pts, line):
        """The week's box score row for one player (the rest have none), then draw again."""
        self.page.evaluate("""([n, pts, line]) => { window.clipWeekRow = p => p.n === n ? {row: {}, pts, line} : {row: null, pts: null, line: null}; render(); }""",
                           [name, pts, line])

    def plant_starters(self, specs):
        """Add starters `(name, team, start)` to the ESPN roster; what the rail's model and markup say of them:
        {ends: names with no clip but a game video, line: the end card's words, items: clips in the queue}."""
        return self.page.evaluate("""(specs) => {
          const mk = ([n, team, start]) => ({n, slug: n.toLowerCase().replace(' ', '-'), pos: 'WR', team, start});
          const team = {key: 'x', roster: [...TEAMS.espn.roster, ...specs.map(mk)]};
          const m = reelModel(team), box = document.createElement('div');
          box.innerHTML = reelHTML(team);
          return {ends: m.ends.map(p => p.n), line: box.querySelector('.reel-endline').textContent, items: m.items.length};
        }""", [list(s) for s in specs])

    def add_cards(self, n):
        """Copy the first card n times onto the track and fit the rail again."""
        self.page.evaluate("""(n) => { const tr = document.querySelector('[data-testid="clips-track"]'), c = tr.querySelector('[data-testid="clips-card"]');
          for (let i = 0; i < n; i++) tr.appendChild(c.cloneNode(true));
          reelFit(document.querySelector('[data-testid="clips-reel"]')); }""", n)

    # ---- what the rail draws ----

    def reel_count(self):
        return self._reel.count()

    def reel_visible(self):
        return self._reel.is_visible()

    def reel_fits(self):
        """The rail's class when everything fits one page (the arrows then hide)."""
        return self._reel.evaluate("e => e.classList.contains('fits')")

    def fits_count(self):
        return self._reel.and_(self.page.locator(".fits")).count()

    def card_count(self):
        return self._card.count()

    def end_count(self):
        return self._parts["end"].count()

    def link_count(self):
        return self._parts["link_card"].count()

    def title(self):
        return self._parts["title"].inner_text()

    def count_label(self):
        return self._parts["count"].inner_text()

    def play_all_count(self):
        return self._parts["all"].count()

    def play_all_text(self):
        return self._parts["all"].inner_text()

    def chip_count(self):
        """The count chips (a card whose clips play wears one)."""
        return self._parts["n"].count()

    def kinds(self, end=True):
        """Each card's tag: "BUTTON" plays here, "A" opens YouTube. `end` False leaves the end card out."""
        cards = self._card if end else self._card.and_(self.page.locator(":not(.reel-end)"))
        return cards.evaluate_all("els => els.map(e => e.tagName)")

    def card_summaries(self):
        """Each card: [tag, the count chip's text or None, whether it wears YouTube's chip]."""
        return self._card.evaluate_all("""els => els.map(e => [e.tagName, (e.querySelector('[data-testid="clips-n"]') || {}).textContent || null,
          !!e.querySelector('[data-testid="clips-mark"]')])""")

    def names(self):
        """The starters' names on the clip cards, best scorer first (the end card has none)."""
        return self._card.and_(self.page.locator(":not(.reel-end)")).evaluate_all(
            "els => els.map(e => e.querySelector('[data-testid=\"clips-nm\"]').textContent)")

    def first_mark_text(self):
        return self.page.get_by_test_id("clips-mark").first.inner_text()

    def thumb_sources(self):
        return self._parts["thumb"].locator("img").evaluate_all("els => els.map(e => e.getAttribute('src'))")

    def first_clip_thumbs(self, slugs):
        """The picture the page itself takes for each player's first clip."""
        return self.page.evaluate("slugs => slugs.map(s => clipThumbOf(clipsOf(s)[0]))", slugs)

    def point_count(self):
        return self._parts["pt"].count()

    def text(self, part):
        """The first match's words: "nm", "pt", "l2"."""
        return self._parts[part].first.inner_text()

    def rect(self, part, n=0):
        """The n-th match's box: {l, r, t, w, h}."""
        return self._parts[part].nth(n).evaluate(RECT)

    def thumb_rects(self):
        """The first card's picture and the end card's, as boxes."""
        return {"first": self.rect("thumb"), "end": self._parts["end"].get_by_test_id("clips-thumb").evaluate(RECT)}

    def parts_inside_thumb(self, part):
        """Whether every part of the first match's picture sits inside it (the end card's words fit its box)."""
        return self._parts[part].get_by_test_id("clips-thumb").evaluate("""t => { const b = t.getBoundingClientRect();
          return [...t.children].every(e => { const r = e.getBoundingClientRect();
            return r.left >= b.left - .5 && r.right <= b.right + .5 && r.top >= b.top - .5 && r.bottom <= b.bottom + .5; }); }""")

    def inside_its_picture(self, parts=("ov", "nm", "pt", "l2", "n")):
        """Each part's box (first match), the picture's box, and whether the part sits inside it."""
        thumb = self.rect("thumb")
        out = {}
        for p in parts:
            r = self.rect(p)
            out[p] = {"rect": r, "inside": thumb["l"] <= r["l"] and r["r"] <= thumb["r"] + .5 and thumb["t"] <= r["t"]
                      and r["t"] + r["h"] <= thumb["t"] + thumb["h"] + .5}
        return out

    def end_card(self):
        """The end card: its tag, link target, address, "No clip" label, the starters' line and YouTube's chip."""
        end = self._parts["end"]
        return {"tag": end.evaluate("e => e.tagName"), "target": end.get_attribute("target"), "href": end.get_attribute("href"),
                "no": end.get_by_test_id("clips-no").inner_text(), "line": end.get_by_test_id("clips-endline").inner_text(),
                "mark": end.get_by_test_id("clips-mark").inner_text()}

    def link(self, n=0):
        """The n-th card that opens YouTube: its target, rel, address and label."""
        a = self._parts["link_card"].nth(n)
        return {"target": a.get_attribute("target"), "rel": a.get_attribute("rel"), "href": a.get_attribute("href"),
                "label": a.get_attribute("aria-label")}

    def sheet_address(self, slug):
        """The address the clip sheet itself gives a player's first clip (None where it has no such function)."""
        return self.page.evaluate("slug => typeof clipYtUrl === 'function' ? clipYtUrl(clipsOf(slug)[0]) : null", slug)

    def arrow(self, which):
        """"prev" or "next": {visible, hidden, enabled, disabled}."""
        a = self._parts[which]
        return {"visible": a.is_visible(), "hidden": a.is_hidden(), "enabled": a.is_enabled(), "disabled": a.is_disabled()}

    def first_arrow_hidden(self):
        return self._parts["prev"].first.is_hidden()

    # ---- the rail as a scroller ----

    def track_css(self):
        """overflow-x, snap type, touch action, overscroll and scrollbar width of the track."""
        return self._track.evaluate("e => { const s = getComputedStyle(e); return [s.overflowX, s.scrollSnapType, s.touchAction, s.overscrollBehaviorX, s.scrollbarWidth]; }")

    def every_card_snaps_to_start(self):
        return self._card.evaluate_all("els => els.every(e => getComputedStyle(e).scrollSnapAlign.startsWith('start'))")

    def track_room(self):
        """How much wider the track's content is than the track."""
        return self._track.evaluate("t => t.scrollWidth - t.clientWidth")

    def track_fits(self):
        return self.page.evaluate(FITS_TRACK)

    def scroll_left(self):
        return self._track.evaluate("e => e.scrollLeft")

    def scroll_to(self, px):
        self._track.evaluate("(e, px) => { e.scrollLeft = px; }", px)

    def scroll_card_into_view(self, n):
        self._parts["button_card"].nth(n).evaluate("e => e.scrollIntoView({inline: 'start'})")

    def wait_until_next_disabled(self):
        self.page.wait_for_function("document.querySelector('[data-testid=\"clips-next\"]').disabled")

    def wait_until_at_rest(self):
        """The rail's scroll has come to rest: the same scrollLeft on two frames running, so a snap is done."""
        self.page.evaluate("window.__sl = null")
        self.page.wait_for_function("() => { const t = document.querySelector('[data-testid=\"clips-track\"]').scrollLeft; const same = window.__sl === t; window.__sl = t; return same; }")

    def catch_scroll_by(self):
        """The track's scrollBy records its argument instead of scrolling."""
        self._track.evaluate("e => { e.scrollBy = o => { window.__by = o; }; }")

    def scrolled_by(self):
        return self.page.evaluate("__by")

    def page_overflow(self):
        """How far the document is wider than the screen."""
        return self.page.evaluate("document.scrollingElement.scrollWidth - innerWidth")

    def stray_scrollers(self):
        """Elements in the view, other than the track, that scroll sideways."""
        return self.page.evaluate("[...document.querySelectorAll('#view *')].filter(e => /(auto|scroll)/.test(getComputedStyle(e).overflowX) && e.scrollWidth > e.clientWidth + 4 && !e.matches('[data-testid=\"clips-track\"]')).length")

    # ---- what a reader does ----

    def step(self, which):
        self._parts[which].click()

    def play_all(self):
        self._parts["all"].click()

    def click_card(self, part="button_card", n=0):
        self._parts[part].nth(n).click()

    def click_end(self):
        self._parts["end"].click()

    def tap_at(self, part, n=0, dx=20, dy=20):
        """A mouse press and release at an offset into a part's box."""
        r = self.rect(part, n)
        self.page.mouse.move(r["l"] + dx, r["t"] + dy)
        self.page.mouse.down()
        self.page.mouse.up()

    def press_card(self, n=0, dx=20, dy=20):
        """Scroll a card that plays here into view and press the mouse down at an offset into it, unreleased
        (the page's `mouse.up` ends it)."""
        card = self._parts["button_card"].nth(n)
        card.scroll_into_view_if_needed()
        r = card.bounding_box()
        self.page.mouse.move(r["x"] + dx, r["y"] + dy)
        self.page.mouse.down()

    def drag(self, part, n, moves, dx=30, dy=40):
        """Press at an offset into a part, move sideways by each of `moves` from there, release."""
        r = self.rect(part, n)
        x, y = r["l"] + dx, r["t"] + dy
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        for m in moves:
            self.page.mouse.move(x + m, y)
        self.page.mouse.up()

    def unfold_list(self):
        self.page.get_by_test_id("roster-brief-unfold").click()

    # ---- what the theater was asked ----

    def opened(self):
        """What the rail asked the theater to open ({ids, who, ps, i, el}), or None."""
        return self.page.evaluate("__opened")

    def clear_opened(self):
        self.page.evaluate("__opened = null")

    def warm_count(self):
        return self.page.evaluate("__warm")

    def has_prime_step(self):
        return self.page.evaluate("typeof clipPrime") != "undefined"

    # ---- the "This week" list under the rail ----

    def folded(self):
        """How many lists are folded to their one row."""
        return self._brief.and_(self.page.locator(".done")).count()

    def fold_count_text(self):
        return self._brief.and_(self.page.locator(".done")).get_by_test_id("roster-brief-head").locator("small").inner_text()

    def list_lines(self):
        return self.page.get_by_test_id("roster-brief-line").count()

    def unfold_buttons(self):
        return self.page.get_by_test_id("roster-brief-unfold").count()

    def list_html(self):
        return self._brief.first.evaluate("e => e.outerHTML")

    def first_list_line_visible(self):
        return self.page.get_by_test_id("roster-brief-line").first.is_visible()

    def rail_count_in_layout(self):
        """The Roster's column wrapper when a rail is drawn (`.rl-reel`, render.js)."""
        return self.page.locator(".rl-reel").count()

    def columns(self):
        """The rail, the rows and the list, each as [left, top, width]."""
        box = "e => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width]; }"
        return {"reel": self._reel.evaluate(box), "rows": self._parts["rows"].first.evaluate(box),
                "brief": self._parts["list"].first.evaluate(box)}

