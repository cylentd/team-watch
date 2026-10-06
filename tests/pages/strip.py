"""The drive strip (design/src/js/surface/strip/): a game's drives acted out on a tilted field.

The strip has no leaf of its own. A component test mounts the view that opens it (Live) and mounts the
strip into that page's view slot, as the dialogs do; a journey opens it from a player's game log.
Every strip locator lives here, data-testid first (`strip-*`, test hooks only).

Some reads go through the strip's own controller (`window.__ctl`, set by `open`): the strip is a pure
function of (t, hold), so a test asks it to draw one frame and reads what the browser did with it.

Motion: the strip's paint reads `prefers-reduced-motion` once at load (hit-stops, slow motion, the
moments), and `mount` loads with it on. A strip test is about the motion, so `StripPage.open_on` turns
it off for the page and reloads once; the page keeps that for its later mounts.

The profile and Roster controls a journey needs to open a game are here for now (`open_roster`,
`open_profile`, `tap_week`); they move to pages/roster.py and pages/profile.py when those exist.
"""
from component import DRAWN
from test_render import LOAD_MS

DESK = (1400, 900)
PHONE = (360, 800)
MOTION = "window.__stripMotion = true;"      # only a context key: motion tests get a context of their own

MOUNT = """
([data, at, who]) => {
  const host = document.createElement("div");
  document.getElementById("view").innerHTML = "";
  document.getElementById("view").appendChild(host);
  window.__ctl = stripMount(host, data, at, who);
  return window.__ctl.n;
}
"""

# Where a figure's measure is: the box is already centred on its anchor (.stactor carries
# translate(-50%,-100%)), so the middle of the box is the number to read.
RECT = "e => { const r = e.getBoundingClientRect(); return {left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height}; }"

LEG = """host => { const h = host.querySelector('.stfig.run [data-testid="strip-near-hip"]');
                   return h ? getComputedStyle(h).rotate : null; }"""
FRAMES = "() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))"


class StripPage:
    def __init__(self, page):
        self.page = page
        self.root = page.get_by_test_id("strip")
        tid = self.root.get_by_test_id
        self._turf, self._chevrons, self._stage = tid("strip-turf"), tid("strip-chevrons"), tid("strip-stage")
        self._carrier, self._passer = tid("strip-carrier"), tid("strip-passer")
        self._tackler, self._tackler2, self._miss = tid("strip-tackler"), tid("strip-tackler2"), tid("strip-miss")
        self._caption, self._slider, self._play = tid("strip-caption"), tid("strip-slider"), tid("strip-play")
        self._rows, self._me, self._me_count = tid("strip-row"), tid("strip-me"), tid("strip-me-count")
        self._actors = {"passer": self._passer, "tackler": self._tackler, "tackler2": self._tackler2,
                        "carrier": self._carrier}

    @classmethod
    def open_on(cls, mount, data, drive=None, size=DESK, who=None):
        """Mount the strip over Live's page at `size`, on game `data`, opened at `drive` (None: the whole
        game from the kickoff) and narrowed to `who`'s plays when the reader came from his game log.
        Returns (StripPage, the page's errors)."""
        page, errors = mount("live", size=size, init=(MOTION,))
        strip = cls(page)
        strip._allow_motion()
        strip.page.evaluate(MOUNT, [data, drive, who])
        return strip, errors

    def _allow_motion(self):
        if not self.page.evaluate("ST_REDUCED"):
            return
        self.page.emulate_media(reduced_motion="no-preference")
        self.page.reload(timeout=LOAD_MS)
        self.page.wait_for_function(DRAWN, timeout=LOAD_MS)

    # ---- what a reader does ----

    def render(self, t, hold=None):
        """Draw the field at play-time t (3.5: halfway through the fourth play of the drive)."""
        self.page.evaluate("([t, h]) => h == null ? stRender(window.__ctl, t) : stRender(window.__ctl, t, h)", [t, hold])

    def seek(self, t):
        """Move the reel to t, changing drive when it crosses into the next."""
        self.page.evaluate("t => stSeek(window.__ctl, t)", t)

    def seek_into_throw_by(self, qb):
        """Halfway through the first play the reel has with `qb` as the passer."""
        k = self.page.evaluate("qb => window.__ctl.reel.findIndex(s => window.__ctl.data.drives[s.d].plays[s.i].qb === qb)", qb)
        self.seek(k + .5)

    def pose(self, i, f, hold=0):
        """Pose play i at fraction f straight from the figures' own placement (no list, no caption)."""
        self.page.evaluate("([i, f, hold]) => window.__ctl.pose(i, f, hold, false)", [i, f, hold])

    def scale_ancestor(self, s):
        """Scale the strip's parent as the dialog's open animation does, then redraw the last frame."""
        self.root.evaluate("""(host, s) => {
          const box = host.parentElement;
          box.style.transformOrigin = "0 0";
          box.style.transform = `scale(${s})`;
          window.__ctl.pose.bump();                       // the arc cache was measured at the old scale
          stRender(window.__ctl, 1);
        }""", s)

    def toggle_play(self):
        self._play.click()

    def follow_player(self):
        """Tap the player chip: the reel narrows to his plays, or widens again."""
        self._me.click()

    def pick_quarter(self, q):
        self.root.get_by_test_id("strip-quarter").and_(self.page.locator(f'[data-q="{q}"]')).click()

    def tap_row(self, k):
        self._rows.and_(self.page.locator(f'[data-k="{k}"]')).click()

    def draw_every_frame(self):
        """Every drive, every play, four frames of each, the way a replay reaches them; returns how many
        frames were drawn."""
        return self.page.evaluate("""() => {
          const ctl = window.__ctl; let n = 0;
          for (let d = 0; d < ctl.data.drives.length; d++){
            stShowDrive(ctl, d);
            for (let i = 0; i < ctl.data.drives[d].plays.length; i++)
              for (const f of [0, .35, .7, 1]){ stRender(ctl, i + f, f >= 1 ? .5 : 1); n++; }
          }
          return n;
        }""")

    def wait_for_a_runner(self):
        self.page.wait_for_function("""() => !!document.querySelector('.stfig.run [data-testid="strip-near-hip"]')""",
                                    timeout=6000)

    def wait_until_reel_at(self, t):
        self.page.wait_for_function("t => window.__ctl.T === t", arg=t, timeout=6000)

    def frames(self, n=1):
        """Let n frames of the page's own clock pass."""
        for _ in range(n):
            self.page.evaluate(FRAMES)

    # ---- what a reader sees ----

    def carrier_x_at(self, i, f, hold=0):
        """Screen x of the man with the ball, posed at play i, fraction f."""
        self.pose(i, f, hold)
        r = self._carrier.evaluate(RECT)
        return r["left"] + r["width"] / 2

    def carrier_on_field(self):
        """Where he stands as a fraction of the field: (across, down to his feet)."""
        t, c = self._turf.evaluate(RECT), self._carrier.evaluate(RECT)
        return [(c["left"] + c["width"] / 2 - t["left"]) / t["width"], (c["bottom"] - t["top"]) / t["height"]]

    def facing(self):
        """The horizontal scale of the carrier's and the tackler's figures: 1 faces right, -1 left."""
        return [loc.get_by_test_id("strip-pose").evaluate("e => getComputedStyle(e).scale.split(' ')[0]")
                for loc in (self._carrier, self._tackler)]

    def jerseys(self):
        """The colour the carrier and the tackler wear."""
        return [loc.evaluate("e => getComputedStyle(e).getPropertyValue('--jersey').trim()")
                for loc in (self._carrier, self._tackler)]

    def pile_on(self):
        """The second tackler's display, whether the carrier is down, and the tag the play wears."""
        return {"shown": self._tackler2.evaluate("e => getComputedStyle(e).display"),
                "down": "down" in (self._carrier.get_attribute("class") or "").split(),
                "tag": self._miss.text_content().strip()}

    def stage_classes(self):
        return self._stage.get_attribute("class")

    def chevrons_shown(self):
        return self._chevrons.evaluate("e => getComputedStyle(e).display") != "none"

    def chevron_box(self):
        """The chevron band, the turf and the ball, as left/right screen edges."""
        a, t, b = self._chevrons.evaluate(RECT), self._turf.evaluate(RECT), self._carrier.evaluate(RECT)
        return {"aL": a["left"], "aR": a["right"], "tL": t["left"], "tR": t["right"],
                "ball": b["left"] + b["width"] / 2}

    def broke_line(self):
        """The card's broken-tackles line, or None when the man has none."""
        line = self._caption.get_by_test_id("strip-broke")
        return line.text_content() if line.count() else None

    def caption_height(self):
        return self._caption.evaluate("e => e.offsetHeight")

    def goalposts(self):
        """The path of each upright's drawing."""
        return self.root.get_by_test_id("strip-post-path").evaluate_all("ps => ps.map(p => p.getAttribute('d'))")

    def post_depth(self):
        """How far above the near anchor the far one sits on screen (negative: higher up)."""
        far = self.root.get_by_test_id("strip-anchor-far-A").evaluate(RECT)
        near = self.root.get_by_test_id("strip-anchor-near-A").evaluate(RECT)
        return far["top"] - near["top"]

    def sideways(self):
        """What scrolls sideways inside the strip, how far the panel does, and its right edge. The one
        deliberate scroller (the field in Pan) and clipped text are left out."""
        return self.root.evaluate("""host => {
          const bad = [];
          for (const el of host.querySelectorAll("*")){
            if (el.closest(".stview")) continue;
            // the player's name may ellipsize inside its chip; that is clipping, not scrolling
            if (el.closest(".stme") && getComputedStyle(el).textOverflow === "ellipsis") continue;
            // Text hidden for sighted readers but kept for screen readers is a 1px box holding a
            // whole phrase on purpose. It is clipped, not scrollable, and clip-path is what says so.
            if (getComputedStyle(el).clipPath !== "none") continue;
            if (el.scrollWidth > el.clientWidth + 1) bad.push(el.className + " " + el.scrollWidth + ">" + el.clientWidth);
          }
          return {bad, wide: host.scrollWidth - host.clientWidth,
                  right: Math.round(host.getBoundingClientRect().right)};
        }""")

    def classes_used(self):
        """Every class name on anything the strip draws."""
        return self.root.evaluate("""host => {
          const out = new Set();
          for (const el of host.querySelectorAll("*")) for (const c of el.classList) out.add(c);
          return [...out];
        }""")

    def reel(self):
        """What the list and the transport run over: rows, the slider's top, the chip's count."""
        return {"rows": self._rows.count(), "max": self._slider.evaluate("e => +e.max"),
                "chip": self._me_count.text_content()}

    def ringed(self):
        """Who wears the lime ring: "carrier", "passer", "tackler" or "tackler2", in field order."""
        return [name for name, loc in self._actors.items()
                if "ring" in (loc.get_attribute("class") or "").split()]

    def ring_count(self):
        """How many actors on the field wear the ring, named or not."""
        return self.root.get_by_test_id("strip-actors").locator(".stactor.ring").count()

    def faces_on_field(self):
        """Headshots drawn on the field itself (the play card holds the faces)."""
        return self.root.get_by_test_id("strip-actors").get_by_test_id("strip-face").count()

    def looping_animations(self):
        """Names of the strip's animations that are running and never end."""
        return self.root.evaluate("""host => document.getAnimations()
          .filter(a => a.playState === "running" && a.effect && a.effect.target
                       && a.effect.getTiming().iterations === Infinity && host.contains(a.effect.target))
          .map(a => a.animationName || "?")""")

    def leg_angle(self):
        """A running figure's near hip rotation as drawn, or None while nobody runs."""
        return self.root.evaluate(LEG)

    def legs_after_moving(self, was):
        """The leg angle once it differs from `was` (up to 3 s of the replay), else whatever it reads."""
        try:
            return self.page.wait_for_function(
                f"([host, a]) => {{ const v = ({LEG})(host); return v !== a && v; }}",
                arg=[self.root.element_handle(), was], timeout=3000).json_value()
        except Exception:
            return self.leg_angle()

    def lit_row(self):
        """The list row marked as the one playing (its data-k), as a string."""
        return self._rows.and_(self.page.locator(".cur")).get_attribute("data-k")

    def row_count(self):
        return self._rows.count()

    def reel_clock(self):
        return self.page.evaluate("window.__ctl.T")

    def drive_on_field(self):
        return self.page.evaluate("window.__ctl.at")

    def walk_reel(self):
        """Every half-play point of the reel: did each draw on its own drive's field, and the caption's
        heights across all of them."""
        return self.page.evaluate("""() => {
          const ctl = window.__ctl, out = [], hs = new Set();
          for (let T = 0; T <= ctl.reel.length; T += .5){
            stSeek(ctl, T);
            out.push(ctl.at === ctl.reel[stSegAt(ctl, T)].d);
            hs.add(document.querySelector('[data-testid="strip-caption"]').offsetHeight);
          }
          return {ok: out.every(Boolean), heights: [...hs]};
        }""")

    def time_warp(self):
        """moments.js stWarp, the pure map from wall time to play time, for the plays a hit, an
        interception and a big gain stop or slow."""
        return self.page.evaluate("""() => {
          const g = stGeom(1), m = 1000, at = f => m * stEaseInv(f);
          const hit = stWarp({k: "rush", from: 20, to: 25, tk: "A"}, 1, m), h = at(g.hitOf({k: "rush"}));
          const pick = stWarp({k: "int", from: 20, to: 40}, 1, m);
          const big = stWarp({k: "rush", from: 20, to: 45}, 1, m);
          return {extra: hit.extra, held: [hit.map(h + 10), hit.map(h + 60)], after: hit.map(h + 170),
                  pick: [pick.extra, pick.map(m + 100)], big: big.extra > 0};
        }""")

    # ---- the second way in: a week in a player's game log (a journey, on the full page) ----

    def visit(self, url):
        """Load the whole page at `url` (the journeys' one full load)."""
        self.page.goto(url, timeout=LOAD_MS)

    def open_roster(self):
        """League, then Roster by name: the group's default has moved before."""
        self.page.locator(".navitem[data-s='league']").click()
        self.page.locator("[data-leaf='roster']").click()

    def open_profile(self, name):
        self.page.locator(f".row:has-text('{name}')").click()

    # ProfilePage has no read for a week that opens a game, so these go by its `profile-*` testids.
    def _week_buttons(self):
        """The week numbers of the Season table that are real buttons (a game the strip can draw)."""
        return self.page.get_by_test_id("profile-ss-wk").get_by_role("button")

    def weeks_in_game_log(self):
        return self._week_buttons().count()

    def tap_week(self):
        self._week_buttons().first.click()

    def tap_far_cell_of_a_week_row(self):
        """A stat cell at the far end of the row, not the week number."""
        row = self.page.get_by_test_id("profile-ss-row").and_(self.page.locator(".gl-open")).first
        row.locator(":scope > div").last.click()

    def wait_for_game(self):
        self.page.get_by_test_id("strip-turf").wait_for()

    def close_game(self):
        """Escape, then wait for the game's dialog to leave."""
        self.page.keyboard.press("Escape")
        self.page.wait_for_function("!document.getElementById('stripmodal').classList.contains('on')")

    def dialogs(self):
        """Which dialogs are open: the game, and the profile under it."""
        return self.page.evaluate("""() => ({
          strip: document.getElementById("stripmodal").classList.contains("on"),
          profile: document.getElementById("modal").classList.contains("on")})""")

    def game_title(self):
        return self.page.get_by_test_id("strip-title").text_content()

    def game_plays(self):
        return self._rows.count()

    def field_height(self):
        """The field's layout box (the dialog may still be growing out of scale(.2))."""
        return self.page.get_by_test_id("strip-box").evaluate("e => e.offsetHeight")
