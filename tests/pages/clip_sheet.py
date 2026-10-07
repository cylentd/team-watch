"""The clip theater (design/src/js/surface/teams/clipsheet.js, clipplayer.js): a player's official clips full
screen over the Roster, and the one YouTube player behind it.

Its markup is in shell.html, which marks the fixed parts with `data-clip*` attributes (no test ids: the shell is
not this file's source) and leaves `.clip-main`, `.clip-nav`, `.clip-top` and `.clip-end` to their classes; what
clipsheet.js draws into it is a `clipsheet-*` data-testid (test hooks only: no CSS or JS reads them). The ring on a
roster head is board.js's `roster-row-head`, marked a ring by clipsheet.js's `data-clips`.

The page is a file here, where the embed cannot load, so `ClipSheet` stands in for an http(s) page
(`clipEmbedOk`), and `YT_STUB` (an init script: pass it to `mount(..., init=(YT_STUB,))`) replaces `window.YT`
with a player that records what the page asks of it and lets a test fire its events, so nothing leaves the
machine. The rail that opens the theater is `ClipsPage` (pages/clips.py), composed here as `.rail`.

Items 0-5 of `__items`: Purdy's three (the second also Kittle's), Brown's two, a Short YouTube refuses; 2, 3 and 4
play.
"""
import contextlib

from pages.clips import ClipsPage
from pages.roster_pack import VCLOCK

YT_STUB = """
window.__yt = {players: [], calls: []};
window.YT = {Player: class {
  constructor(target, opts){ this.opts = opts; this.muted = false; __yt.players.push(this); __yt.calls.push(['new', target]); }
  loadVideoById(id){ __yt.calls.push(['load', id]); }
  cueVideoById(id){ __yt.calls.push(['cue', id]); }
  stopVideo(){ __yt.calls.push(['stop']); }
  playVideo(){ __yt.calls.push(['play']); }
  mute(){ this.muted = true; __yt.calls.push(['mute']); }
  unMute(){ this.muted = false; __yt.calls.push(['unmute']); }
  isMuted(){ return this.muted; }
}};
"""
# The rail's items for Purdy's three, Kittle's one (the touchdown pass is Purdy's second too: one item
# naming both) and Chase Brown's two, plus a Short YouTube refuses.
ITEMS = """() => {
  const r = TEAMS.espn.roster, by = n => r.find(p => p.n === n), p = by('Brock Purdy');
  const cards = ['Brock Purdy', 'George Kittle', 'Chase Brown'].map(n => ({p: by(n), clips: clipItemsOf(by(n))}));
  window.__items = [...reelItems(cards),
    {c: {id: 'tallblock01', title: 'A Short YouTube refuses', shape: 'tall', embed: false}, p, ps: [p]}];
}"""
OPEN = "document.getElementById('clipsheet').classList.contains('on')"
BOX = """(() => { const b = document.querySelector('[data-clipbox]').getBoundingClientRect(),
  m = document.querySelector('.clip-main').getBoundingClientRect(), n = document.querySelector('.clip-nav').getBoundingClientRect(),
  c = document.querySelector('.clip-cap').getBoundingClientRect();
  return {w: b.width, h: b.height, top: b.top, bottom: b.bottom, mid: (m.top + m.bottom) / 2, mainMid: (b.top + c.bottom) / 2,
    capTop: c.top, navTop: n.top, navH: n.height, vh: innerHeight, vw: innerWidth};
})()"""
TAPS_UNDER_VIDEO = """(() => { const bx = document.querySelector('[data-clipbox]').getBoundingClientRect(),
  nav = document.querySelector('.clip-nav');
  return [...document.querySelectorAll('#clipsheet button, #clipsheet a[href], #clipsheet [tabindex]')]
    .filter(e => e.getClientRects().length && !nav.contains(e) && e.getBoundingClientRect().top >= bx.bottom - 1)
    .map(e => e.className); })()"""
MONO = """(() => { const s = document.createElement('span'); s.style.fontFamily = 'var(--mono)';
  document.body.appendChild(s); const f = getComputedStyle(s).fontFamily; s.remove(); return f; })()"""
REAL_CLOCK = "window.__real = {st: window.setTimeout, ct: window.clearTimeout, an: Element.prototype.animate}"
PUT_CLOCK_BACK = """() => { Object.assign(window, {setTimeout: __real.st, clearTimeout: __real.ct});
  Element.prototype.animate = __real.an; delete window.__vc; delete window.__real; }"""


class ClipSheet:
    def __init__(self, page):
        """The ESPN roster drawn as a page that can embed, with the six items to open the theater on."""
        self.page = page
        self.rail = ClipsPage(page)
        self.rail.show(then=ITEMS)
        tid = page.get_by_test_id
        self._sheet = page.locator("#clipsheet")
        self._btn = {"prev": page.locator("[data-clipprev]"), "next": page.locator("[data-clipnext]"),
                     "close": page.locator("[data-clipclose]")}
        self._count, self._cap, self._up = (page.locator(f"[data-clip{k}]") for k in ("count", "cap", "up"))
        self._end, self._link, self._sound = (page.locator(f"[data-clip{k}]") for k in ("end", "link", "sound"))
        self._who, self._who_name, self._title = tid("clipsheet-who"), tid("clipsheet-who-name"), tid("clipsheet-title")
        self._done, self._rows, self._ring = tid("clipsheet-done"), tid("clipsheet-row"), tid("roster-row-head").and_(page.locator("[data-clips]"))
        self._anchor = self._link.get_by_test_id("clipsheet-link")

    # ---- opening and driving the theater ----

    def open(self, start=2):
        """Ask for the theater on the items, at item `start` (-1: the end card)."""
        self.page.evaluate(f"clipTheaterOpen(__items, {start}, null)")

    def play_all(self, start=2):
        """Open at item `start` and have the player report ready (one round trip: opening builds the player in
        the same call, so its event can fire at once)."""
        self.page.evaluate(f"() => {{ clipTheaterOpen(__items, {start}, null); __yt.players[0].opts.events.onReady({{}}); }}")

    def open_items(self, name):
        """Open the theater on one starter's own items (his game's video when he has none), at the end card."""
        self.page.evaluate("""(n) => { const p = TEAMS.espn.roster.find(p => p.n === n);
          const items = clipItemsOf(p).map(c => ({c, p})); clipTheaterOpen(items, -1, null); }""", name)

    def open_second_item_embeddable(self):
        """The shared touchdown pass plays too: opened at it, among four that play."""
        self.page.evaluate("""() => { const x = __items[1]; x.c = {...x.c, embed: true}; clipTheaterOpen(__items, 1, null); }""")

    def fire(self, name, arg=None):
        """One of the player's events, the way YouTube's script would."""
        self.page.evaluate("([name, a]) => __yt.players[0].opts.events[name](a)", [name, arg or {}])

    def state(self, code):
        self.fire("onStateChange", {"data": code})

    def error(self, code):
        self.fire("onError", {"data": code})

    def step(self, which):
        """"prev" or "next": the round buttons."""
        self._btn[which].click()

    def press(self, key):
        self.page.keyboard.press(key)

    def close_button(self):
        self._btn["close"].click()

    def go_back(self):
        self.page.go_back()

    def close(self):
        self.page.evaluate("clipClose()")

    def embed_ok(self, ok):
        self.page.evaluate(f"clipEmbedOk = () => {'true' if ok else 'false'}")

    def forget_player(self):
        """As if no player was ever built."""
        self.page.evaluate("() => { CP.player = null; CP.ready = false; __yt.players.length = 0; }")

    def warm(self, times=1):
        self.page.evaluate("clipWarm();" * times)

    def api_fails(self):
        """No `window.YT`: the page asks for the API script, whose request is aborted (its onerror fires)."""
        self.page.evaluate("delete window.YT")

    def player_muted_by_browser(self):
        self.page.evaluate("__yt.players[0].muted = true")

    def tap_sound(self):
        self._sound.click()

    def settle_layers(self):
        """The history steps the theater's close took back are done."""
        self.page.wait_for_function("LAYER_SKIP.length === 0")

    def wait_open(self):
        self.page.wait_for_function(OPEN)

    def wait_closed(self):
        self.page.wait_for_function(f"!({OPEN})")

    def wait_for_load(self, clip_id, timeout=4000):
        self.page.wait_for_function(f"__yt.calls.some(c => c[0] === 'load' && c[1] === '{clip_id}')", timeout=timeout)

    def wait_for_link_stage(self):
        self._anchor.wait_for(state="visible")

    @contextlib.contextmanager
    def virtual_clock(self):
        """The page's timers on its virtual clock (`run_virtual`) inside the block, the real ones put back after:
        the page's later taps run on real timers."""
        self.page.evaluate(REAL_CLOCK)
        self.page.evaluate(VCLOCK)
        try:
            yield self
        finally:
            self.page.evaluate(PUT_CLOCK_BACK)

    def run_virtual(self, ms):
        self.page.evaluate("ms => window.__vc.run(ms)", ms)

    # ---- what the player was asked ----

    def loads(self):
        """The clip ids sent to the player, in order."""
        return self.page.evaluate("__yt.calls.filter(c => c[0] === 'load').map(c => c[1])")

    def calls(self, kind):
        """How many times the player was sent `kind` ("new", "load", "cue", "stop", "play", "mute", "unmute")."""
        return self.page.evaluate("k => __yt.calls.filter(c => c[0] === k).length", kind)

    def cues_and_loads(self):
        return self.page.evaluate("__yt.calls.filter(c => c[0] === 'cue' || c[0] === 'load')")

    def last_call(self):
        return self.page.evaluate("__yt.calls.slice(-1)[0]")

    def player_count(self):
        return self.page.evaluate("__yt.players.length")

    def own_iframes(self):
        return self.page.evaluate("document.querySelectorAll('#clipsheet iframe').length")

    def preconnects(self):
        return self.page.evaluate("[...document.head.querySelectorAll('link[rel=preconnect]')].map(l => l.href)")

    def blocked(self):
        return self.page.evaluate("CLIP_BLOCKED")

    def waiting_clip(self):
        """The clip the player will play when it is ready, or None."""
        return self.page.evaluate("CP.load")

    # ---- the rail's items, and what the rail and a ring open ----

    def items(self):
        """Each item: [clip id, the names of every starter credited]."""
        return self.page.evaluate("__items.map(it => [it.c.id, it.ps.map(p => p.n)])")

    def press_rail_card(self):
        """Press the first playable card of the Week plays rail, without releasing."""
        self.rail.press_card()

    def release(self):
        self.page.mouse.up()

    def ring_pointerdown(self, name):
        self._ring.and_(self.page.get_by_label(name)).first.dispatch_event("pointerdown")

    def ring_click(self, name):
        self._ring.and_(self.page.get_by_label(name)).first.click()

    def focus_inside_theater(self):
        return self.page.evaluate("document.getElementById('clipsheet').contains(document.activeElement)")

    def focus_on_ring(self):
        return self.page.evaluate("document.activeElement.matches('[data-testid=\"roster-row-head\"][data-clips]')")

    # ---- what the theater shows ----

    def is_open(self):
        return self.page.evaluate(OPEN)

    def aria_hidden(self):
        return self._sheet.get_attribute("aria-hidden")

    def counter(self):
        return self._count.inner_text()

    def who(self):
        """The caption's first line, and the names in bold in it."""
        return {"text": self._who.inner_text(), "names": self._who_name.inner_text()}

    def title(self):
        return self._title.inner_text()

    def title_white_space(self):
        return self._title.evaluate("e => getComputedStyle(e).whiteSpace")

    def up_next(self):
        return self._up.inner_text()

    def old_parts_drawn(self):
        """The retired bars, list and next card (`.clip-bars`, `.clip-list`, `.clip-next`): none."""
        return self.page.locator(".clip-bars, .clip-list, .clip-next").count()

    def is_disabled(self, which):
        return self._btn[which].is_disabled()

    def is_enabled(self, which):
        return self._btn[which].is_enabled()

    def end_visible(self):
        return self._end.is_visible()

    def end_hidden(self):
        return self._end.is_hidden()

    def done_text(self):
        return self._done.inner_text()

    def done_count(self):
        return self._done.count()

    def end_row_count(self):
        return self._rows.count()

    def end_hrefs(self):
        return self._rows.evaluate_all("els => els.map(e => e.getAttribute('href'))")

    def end_row(self, n):
        """The n-th end-card row: its address, target, rel, words, names, YouTube chip and picture."""
        row = self._rows.nth(n)
        return {"href": row.get_attribute("href"), "target": row.get_attribute("target"), "rel": row.get_attribute("rel"),
                "text": row.inner_text(), "names": row.get_by_test_id("clipsheet-row-names").inner_text(),
                "chip": row.get_by_test_id("clipsheet-row-chip").inner_text(),
                "img": row.get_by_test_id("clipsheet-row-thumb").get_attribute("src")}

    def ends_text(self):
        return self.page.get_by_test_id("clipsheet-ends").inner_text()

    def link_stage(self):
        """The stage that stands in for a clip the page cannot play: its address, words and picture."""
        return {"href": self._anchor.get_attribute("href"), "text": self._anchor.inner_text(),
                "img": self._link.get_by_test_id("clipsheet-link-thumb").get_attribute("src")}

    def link_stage_hidden(self):
        return self._link.is_hidden()

    def link_stage_visible(self):
        return self._anchor.is_visible()

    def sound_visible(self):
        return self._sound.is_visible()

    def sound_hidden(self):
        return self._sound.is_hidden()

    def sound_text(self):
        return self._sound.inner_text()

    def sound_background(self):
        return self._sound.evaluate("e => getComputedStyle(e).backgroundColor")

    # ---- layout ----

    def box(self):
        """The video box and what it sits among: {w, h, top, bottom, mid, mainMid, capTop, navTop, navH, vh, vw}."""
        return self.page.evaluate(BOX)

    def box_is_tall(self):
        return self.page.evaluate("document.querySelector('[data-clipbox]').classList.contains('tall')")

    def top_height(self):
        return self.page.evaluate("document.querySelector('.clip-top').getBoundingClientRect().height")

    def taps_under_video(self):
        """The classes of every control that sits under the video and is not in the bottom row."""
        return self.page.evaluate(TAPS_UNDER_VIDEO)

    def control_size(self, which):
        """"prev", "next" or "close": its box, {x, y, width, height}."""
        return self._btn[which].bounding_box()

    def page_width(self):
        return self.page.evaluate("document.documentElement.scrollWidth")

    def sheet_rect(self):
        return self._sheet.bounding_box()

    def sheet_background(self):
        return self._sheet.evaluate("e => getComputedStyle(e).backgroundColor")

    def covers_the_screen_at(self, x, y):
        """Whether the theater is what sits at that point."""
        return self.page.evaluate("([x, y]) => document.elementFromPoint(x, y).closest('#clipsheet') !== null", [x, y])

    def counter_font(self):
        return self._count.evaluate("e => getComputedStyle(e).fontFamily")

    def mono_font(self):
        return self.page.evaluate(MONO)
