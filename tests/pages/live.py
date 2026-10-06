"""Live (design/src/js/surface/live/): its tabs and the TDs feed with its TD clips reel.

Every Live locator lives here, data-testid first (`live-*`, test hooks only). The clip card, its Play n
pill and its arrows are Roster's shared rail (surface/teams/cliprail.js), which carries no test id; they
are found by the rail's own attributes, inside the Live reel's test id, and nowhere else.

The planted game day (`plant_td_day`) is what a TDs test starts from: SF at KC on (kicked off 20:25Z, the
page's clock 22:25Z), LAR at WSH on, DET at MIN final, MIA at BUF days old; four scorers; a window.fetch
that answers per channel from `replies`; and the build's names (jersey numbers, nicknames) for two of them.
The fixture clips (`REPLIES`) and the order the reel draws them in (`ORDER`) are here, so the component
tests and the Node tests (tests/test_js_tdclips.py) read the same day.

Reads return plain data; no method asserts. A method that plants state draws again, the way the page's
own poll does (`paintLive`).
"""
from test_render import LIVE_PLANT

PHONE = (360, 800)


def clip(id, title, posted, embed=True):
    return {"id": id, "title": title, "posted": posted, "secs": 30, "shape": "wide", "embed": embed}


def at(hhmm, day=13):
    return f"2026-09-{day:02d}T{hhmm}:00Z"


# Test Rusher is SF (jersey 22, "The Rocket"), Test Catcher is KC, Detroit Grabber is DET, Test Passer is SF.
# The games: SF-KC (kicked off 20:25Z) and LAR-WSH (20:00Z) are on, DET-MIN (17:00Z) is final, MIA-BUF is days old.
REPLIES = {
    "SF": [
        clip("f1", "Test Rusher punches it in", at("22:10")),          # last name
        clip("f2", "TD! #TestRusher again", at("21:40")),               # hashtag
        clip("f3", "No. 22 breaks free for six", at("21:50")),         # jersey, on his own club's channel
        clip("f4", "The Rocket lights up the board", at("21:55")),     # nickname
        clip("f5", "Catcher hauls it in", at("21:30")),                # a KC player on SF's channel
        clip("f6", "Rusher highlights", at("19:00")),                  # posted before kickoff
        clip("f7", "22-17 final, 1:22 left, 4th-and-22", at("22:23")),  # 22 inside a score and times
        clip("o1", "Rusher scores", at("21:00")),                      # also in LIVE_CLIPS, which has no time
    ],
    "KC": [
        clip("g1", "Catcher with the grab", at("22:00")),
        clip("g2", "No. 22 for the win", at("22:05")),                 # Rusher's number on another club's channel
        clip("g3", "Grabber scores", at("22:06")),                     # a DET player on KC's channel
    ],
    "NFL": [
        clip("h1", "Test Rusher and Test Catcher both score", at("22:28")),
        clip("h2", "No. 22 scores", at("22:21")),                      # a jersey number counts only on his own channel
        clip("p1", "Test Passer throws his third", at("22:15")),       # a passer: only under the Pass chip; the NFL's channel names whole players
    ],
    "DET": [clip("d1", "Grabber catches it", at("19:00"), embed=False)],
}
ORDER = ["h1", "f1", "g1", "f4", "f3", "f2", "o1", "d1", "o2"]    # newest first; o2 has no time, so it is last

# The day's scorers (api/stats `lead`) and the build's names, as the SETUP below plants them; Node tests use both.
LEAD = {
    "9001": {"n": "Test Rusher", "pos": "RB", "team": "SF", "s": {"rush_td": 2}, "pts": 20},
    "9002": {"n": "Test Passer", "pos": "QB", "team": "SF", "s": {"pass_td": 3}, "pts": 24},
    "9003": {"n": "Test Catcher", "pos": "WR", "team": "KC", "s": {"rec_td": 1}, "pts": 12},
    "9004": {"n": "Detroit Grabber", "pos": "WR", "team": "DET", "s": {"rec_td": 1}, "pts": 11}}
NAMES = {"test-rusher": {"n": 22, "t": "SF", "k": ["the rocket"]}, "test-catcher": {"n": None, "t": "KC", "k": []}}

SETUP = """(cfg) => {
  const week = GD.leagues[0].week;
  window.__now = Date.parse("2026-09-13T20:25:00Z") + cfg.hours * 3600e3;
  Date.now = () => window.__now;
  GD_GAMES.splice(0, GD_GAMES.length,
    {home: "SF", away: "KC", kickoff: "2026-09-13T20:25:00Z", week},
    {home: "DET", away: "MIN", kickoff: "2026-09-13T17:00:00Z", week},
    {home: "LAR", away: "WSH", kickoff: "2026-09-13T20:00:00Z", week},
    {home: "MIA", away: "BUF", kickoff: "2026-09-10T00:20:00Z", week});      // over 30 hours before
  const on = cfg.post ? "post" : "in";
  const g = (clubs, state) => ({state, q: state === "in" ? 3 : 4, clock: state === "in" ? "4:12" : "0:00", half: false, detail: "", clubs});
  GD_CLOCK = {};
  for (const [clubs, state] of [[["SF", "KC"], on], [["LAR", "WSH"], on], [["DET", "MIN"], "post"]]) for (const c of clubs) GD_CLOCK[c] = g(clubs, state);
  GD_STATS = {week, games: {}, stats: {}, lead: cfg.lead};
  GD_AT = Date.now(); GD_ERR = "";
  LIVE_CLIPS.week = cfg.clipsWeek === null ? week : cfg.clipsWeek;
  LIVE_CLIPS.players["test-rusher"] = [{id: "o1", title: "Rusher scores", kind: "play", secs: 20, embed: true, shape: "wide"}];
  LIVE_CLIPS.players["test-catcher"] = [{id: "o2", title: "Catcher's grab", kind: "play", secs: 20, embed: true, shape: "wide"}];
  tdcServed = () => true;
  clipEmbedOk = () => true;
  tdcNameRow = slug => cfg.names[slug] || null;
  window.__realOpen = clipTheaterOpen;
  window.__opened = null;
  window.clipTheaterOpen = (items, i, el) => { window.__opened = {ids: items.map(it => it.c.id), i, el: !!el}; };
  window.clipWarm = () => {};
  window.__replies = cfg.replies; window.__calls = []; window.__fly = 0; window.__peak = 0; window.__gate = null; window.__fail = [];
  window.fetch = async (url) => {
    const ch = /ch=([^&]+)/.exec(url)[1];
    window.__calls.push(ch);
    window.__fly++; window.__peak = Math.max(window.__peak, window.__fly);
    try {
      if (window.__gate) await window.__gate;
      if (window.__fail.includes(ch)) throw new Error("network");
      return {ok: true, json: async () => ({ch, clips: window.__replies[ch] || []})};
    } finally { window.__fly--; }
  };
}"""

ADVANCE = "(s) => { window.__now += s * 1000; GD_AT = Date.now(); paintLive(); }"
SETTLED = "TDC.at > 0 && !TDC.busy"
REEL_CARD = """cs => cs.map(c => ({id: c.dataset.clipid,
  nm: c.querySelector('.reel-nm').textContent, cap: c.querySelector('.reel-cap').textContent, tag: c.tagName,
  disc: !!c.querySelector('.reel-disc')}))"""
SCROLL_REST = """(s) => { const t = document.querySelector('[data-testid="live-reel"] .reel-track').scrollLeft;
  const same = window.__sl === t; window.__sl = t; return same && t >= s; }"""


class LivePage:
    def __init__(self, page):
        self.page = page
        tid = page.get_by_test_id
        self._tabs, self._reel = tid("live-tab"), tid("live-reel")
        self._chips, self._by_game = tid("live-td-chip"), tid("live-td-bygame")
        self._cards, self._gcards, self._rows = tid("live-td-card"), tid("live-td-gcard"), tid("live-td-row")
        self._clips = self._reel.locator("[data-clipid]")
        self._track = self._reel.locator(".reel-track")

    @classmethod
    def open_tds(cls, mount, hours=2, replies=REPLIES, clips_week=None, wait=True, post=False, size=PHONE):
        """Mount Live at `size`, plant the game day `hours` after the first kickoff and open the TDs tab.
        `wait` holds until the first round of clip requests has come back. Returns (LivePage, the page's errors)."""
        page, errors = mount("live", size=size)
        live = cls(page)
        live.plant_td_day(hours, replies, clips_week, post)
        live.open_tab("tds")
        if wait:
            live.wait_for_round()
            live.wait_for_reel()
        return live, errors

    # ---- planting: what the page would hold on the game day ----

    def plant_td_day(self, hours=2, replies=REPLIES, clips_week=None, post=False):
        """The leagues of week 2, then the game day (module docstring), the clock `hours` after SF's kickoff."""
        self.page.evaluate(LIVE_PLANT())
        self.page.evaluate(SETUP, {"hours": hours, "replies": replies, "clipsWeek": clips_week, "post": post,
                                   "lead": LEAD, "names": NAMES})

    def advance(self, seconds):
        """The clock moves on and Live's poll repaints; a request, if one is due, is made inside that call."""
        self.page.evaluate(ADVANCE, seconds)

    def set_tab_visible(self, visible):
        self.page.evaluate("v => Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => v})",
                           "visible" if visible else "hidden")

    def reply_with_more(self, channel, clips):
        """The channel answers with what it did, and `clips` as well (a reply joins, it never replaces)."""
        self.page.evaluate("([ch, c]) => { window.__replies = {...window.__replies, [ch]: [...(window.__replies[ch] || []), ...c]}; }",
                           [channel, clips])

    def reply_with_only(self, channel, clips):
        self.page.evaluate("([ch, c]) => { window.__replies = {...window.__replies, [ch]: c}; }", [channel, clips])

    def fail_channel(self, channel, reply_with_none_from=()):
        """`channel` fails from now on; the channels in `reply_with_none_from` (and the failing one) answer with no clips."""
        self.page.evaluate("""([ch, none]) => { window.__fail = [ch];
          const r = {...window.__replies}; for (const c of [ch, ...none]) r[c] = []; window.__replies = r; }""",
                           [channel, list(reply_with_none_from)])

    def hold_requests(self):
        """Ask again from a clean slate with every request held in flight until `release_requests`."""
        self.page.evaluate("""() => { window.__calls = []; window.__peak = 0;
          window.__gate = new Promise(r => { window.__open = r; }); TDC.at = 0; TDC.rounds = 0; paintLive(); }""")

    def release_requests(self):
        self.page.evaluate("() => window.__open()")

    def drop_every_clip(self):
        """Nobody the chips keep has a clip: no fresh ones, and the page's own are of another week."""
        self.page.evaluate("() => { window.__replies = {}; TDC.by = {}; paintLive(); }")
        self.page.evaluate("() => { LIVE_CLIPS.week = 99; paintLive(); }")

    def drop_fresh_clip(self, channel, clip_id):
        """The channel stops holding one clip, and Live repaints."""
        self.page.evaluate("([ch, id]) => { TDC.by[ch] = TDC.by[ch].filter(c => c.id !== id); paintLive(); }", [channel, clip_id])

    def use_the_real_theater(self):
        """The theater opens for real (no sound, no network): the module's stub of it goes."""
        self.page.evaluate("() => { clipTheaterOpen = __realOpen; clipPlayerPlay = () => {}; clipPlayerStop = () => {}; }")

    def repaint(self):
        """Live's 30 s poll."""
        self.page.evaluate("paintLive()")

    def forget_opened(self):
        self.page.evaluate("() => { __opened = null; }")

    # ---- what a reader does ----

    def open_tab(self, name):
        """Tap a Live tab: league, games or tds. A phone's is the tab row's segment (chrome/nav.js, no test id)
        and the board's own bar is hidden there, so the one on screen is the one tapped."""
        self.page.locator(f"[data-gdtab='{name}']").locator("visible=true").first.click()

    def toggle_chip(self, kind):
        """Mine, Pass, Rush or Rec (mine, pass, rush, rec): on, or off again."""
        self._chips.and_(self.page.locator(f'[data-tdchip="{kind}"]')).click()

    def toggle_by_game(self):
        self._by_game.click()

    def play_all(self):
        self._reel.locator("[data-reelall]").click()

    def tap_clip(self, clip_id):
        self._reel.locator(f"[data-clipid='{clip_id}']").click()

    def tap_first_scorer(self):
        """The profile a tap on the first scorer's row opens (the profile is stubbed to hand its argument back)."""
        self.page.evaluate("() => { window.__profile = null; openProfile = p => { window.__profile = p; }; }")
        self._rows.first.click()
        return self.page.evaluate("window.__profile")

    def scroll_reel_to(self, clip_id):
        """Scroll the rail so this card is at its left edge."""
        self._track.evaluate("""(t, id) => { t.scrollLeft = t.querySelector(`[data-clipid='${id}']`).offsetLeft - t.offsetLeft; }""", clip_id)

    def scroll_reel_to_start(self):
        self._track.evaluate("t => { t.scrollLeft = 0; }")

    def press_escape(self):
        self.page.keyboard.press("Escape")

    def theater_return_card_is_detached(self):
        """Live's repaint rebuilt the rail: the card that opened the theater is no longer in the page."""
        return self.page.evaluate("CLIP_RETURN.isConnected") is False

    # ---- waits (on a condition, never a duration) ----

    def wait_for_round(self):
        """The first (or latest) round of clip requests has come back."""
        self.page.wait_for_function(SETTLED)

    def wait_for_reel(self):
        self._reel.wait_for()

    def wait_for_calls(self, n):
        """Exactly `n` requests made in all, and the round that made them settled."""
        self.page.wait_for_function(f"__calls.length === {n} && {SETTLED}")

    def wait_for_requests_in_flight(self, n):
        self.page.wait_for_function(f"__calls.length === {n}")

    def wait_for_theater(self):
        self.page.wait_for_function("CT !== null")

    def wait_for_theater_closed(self):
        self.page.wait_for_function("CT === null")

    def wait_for_scroll_rest(self, at_least=0):
        """The rail's scroll has come to rest: the same scrollLeft on two frames running, and at least `at_least`."""
        self.page.evaluate("window.__sl = null")
        self.page.wait_for_function(SCROLL_REST, arg=at_least)

    # ---- what a reader sees: the reel ----

    def reel_count(self):
        return self._reel.count()

    def reel_ids(self):
        """The clip ids on the rail, left to right."""
        return self._clips.evaluate_all("cs => cs.map(c => c.dataset.clipid)")

    def reel_cards(self):
        """Each card: id, scorers (nm), second line (cap), element (BUTTON plays here, A is a link) and whether it wears a disc."""
        return self._clips.evaluate_all(REEL_CARD)

    def reel_heading(self):
        return self._reel.locator("h2").inner_text()

    def reel_count_label(self):
        return self._reel.locator(".reel-ti small").inner_text()

    def play_all_label(self):
        return self._reel.locator("[data-reelall]").inner_text()

    def thumb_size(self):
        """The first card's picture, width and height in px."""
        return self._reel.locator(".reel-thumb").first.evaluate("e => [e.offsetWidth, e.offsetHeight]")

    def reel_is_above_scored(self):
        """The reel comes before the first card of the feed in the page."""
        first = self._cards.first.element_handle()
        return self._reel.evaluate("(r, c) => !!(r.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING)", first)

    def page_scrolls_sideways(self):
        return not self.page.evaluate("document.documentElement.scrollWidth <= innerWidth")

    def opened_in_theater(self):
        """What the stubbed theater was last asked to open: {ids, i, el}, or None."""
        return self.page.evaluate("__opened")

    def card_left(self, clip_id):
        """How far the card's left edge is from the rail's."""
        return self._track.evaluate("""(t, id) => t.querySelector(`[data-clipid='${id}']`).getBoundingClientRect().left
                                       - t.getBoundingClientRect().left""", clip_id)

    def reel_scroll(self):
        return self._track.evaluate("t => t.scrollLeft")

    # ---- what a reader sees: the feed ----

    def scored_rows(self):
        """How many rows the first card of the feed (Scored) holds."""
        return self._cards.first.get_by_test_id("live-td-row").count()

    def row_count(self):
        """Every scorer and TD-chance row on the tab."""
        return self._rows.count()

    def game_card_count(self):
        return self._gcards.count()

    # ---- what the page asked for ----

    def calls(self):
        """The channels asked for so far, in the order the requests were made."""
        return self.page.evaluate("__calls")

    def call_count(self):
        return self.page.evaluate("__calls.length")

    def calls_since(self, n):
        return self.page.evaluate("n => __calls.slice(n)", n)

    def in_flight(self):
        return self.page.evaluate("__fly")

    def peak_in_flight(self):
        return self.page.evaluate("__peak")

    def channel_clip_ids(self, channel):
        """What the page holds for a channel, newest first."""
        return self.page.evaluate("ch => TDC.by[ch].map(c => c.id)", channel)

    # ---- focus ----

    def focused_clip(self):
        """The clip id on the element holding focus, or None."""
        return self.page.evaluate("document.activeElement.dataset.clipid || null")

    def focus_is_attached(self):
        return self.page.evaluate("document.activeElement.isConnected")

    def focus_is_on_first_card(self):
        return self._clips.first.evaluate("e => document.activeElement === e")
