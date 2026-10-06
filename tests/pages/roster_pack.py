"""The roster's week pack (design/src/js/surface/teams/pack*.js): the gate in the starters' place, the stage,
the Rip again chip, and the virtual clock the pack's motion runs on.

`RosterPack` is the base of `RosterPage` (pages/roster.py), so a test reaches the cards and the pack through
the one object. Every locator is a `roster-*` data-testid (test hooks only); a card's state is a class on
its testid'd element (`.down`, `.pk-slot`), read with `.and_()`; the retired pile count (`.pack-n`) is
asserted gone by its class.

Motion: the pack's wait, tear and deal run on `VCLOCK`, installed after the page loads, so a test waits on a
condition, never a duration. `mount` loads with reduced motion on; a test about the motion mounts with
`pages.roster.MOTION` in `init` (a context of its own) and calls `allow_motion` once.
"""
import contextlib

from component import DRAWN
from test_render import LOAD_MS

# A virtual clock for the pack's motion (2026-10-05). The stage times itself with setTimeout (pkSleep) and
# the Web Animations API (pkAnim), a dozen seconds of both per pack. Installed after the page loads, it
# replaces setTimeout and clearTimeout and parks every finite animation, then moves page time on only
# when a test asks, jumping from one event (a timer, an animation's end) to the next at the animation's
# own playbackRate. So a tap that hurries the deal (rate 6) still shortens the page's time, the best
# card's reveal is still not hurried, and a test reads how long the page says it took, not the host's
# wall clock. Infinite animations (the orbiting line) are left alone: nothing awaits them.
VCLOCK = """
(() => {
  if (window.__vc) return;
  const realST = window.setTimeout.bind(window);
  const yieldNow = () => new Promise(r => { const c = new MessageChannel(); c.port1.onmessage = () => r(); c.port2.postMessage(0); });
  const vc = window.__vc = {now: 0, seq: 0, timers: new Map(), anims: new Set()};
  window.setTimeout = (fn, ms, ...args) => {
    const id = ++vc.seq;
    vc.timers.set(id, {id, at: vc.now + Math.max(0, +ms || 0), fn: () => fn(...args)});
    return id;
  };
  window.clearTimeout = id => { vc.timers.delete(id); };
  const animate = Element.prototype.animate;
  Element.prototype.animate = function (frames, opts) {
    const a = animate.call(this, frames, opts);
    if (a.effect.getComputedTiming().endTime !== Infinity) { a.pause(); vc.anims.add(a); }
    return a;
  };
  const left = a => (a.effect.getComputedTiming().endTime - (a.currentTime ?? 0)) / a.playbackRate;
  const next = () => {
    let d = Infinity;
    for (const t of vc.timers.values()) d = Math.min(d, t.at - vc.now);
    for (const a of vc.anims) if (a.playState === "paused" && a.playbackRate > 0) d = Math.min(d, left(a));
    return d === Infinity ? null : Math.max(0, d);
  };
  const step = dt => {
    vc.now += dt;
    for (;;) {
      let n = null;
      for (const t of vc.timers.values()) if (t.at <= vc.now + 1e-6 && (!n || t.at < n.at || (t.at === n.at && t.id < n.id))) n = t;
      if (!n) break;
      vc.timers.delete(n.id);
      try { n.fn(); } catch (e) { realST(() => { throw e; }, 0); }
    }
    for (const a of [...vc.anims]) {
      if (a.playState === "idle" || a.playState === "finished") { vc.anims.delete(a); continue; }
      if (a.playbackRate <= 0) continue;
      const to = (a.currentTime ?? 0) + dt * a.playbackRate;
      if (to >= a.effect.getComputedTiming().endTime - 1e-6) a.finish(); else a.currentTime = to;
    }
  };
  vc.run = async ms => {
    const end = vc.now + ms;
    for (let i = 0; vc.now < end - 1e-6 && i < 100000; i++) {
      const d = next();
      step(d === null ? end - vc.now : Math.min(d, end - vc.now));
      await yieldNow();
    }
    return vc.now;
  };
  vc.until = async (cond, limit) => {
    const ok = new Function("return (" + cond + ")"), t0 = vc.now;
    let idle = 0;
    while (!ok()) {
      if (vc.now - t0 >= limit) return -1;
      const d = next();
      if (d === null) {   // nothing of ours is pending: something real (a decode, a frame) has to land
        if (++idle > 1500) return -2;
        await new Promise(r => realST(r, 10));
        continue;
      }
      idle = 0;
      step(Math.min(d, t0 + limit - vc.now));
      await yieldNow();
    }
    return vc.now - t0;
  };
})()
"""


def vc_install(page):
    page.evaluate(VCLOCK)


def vc_run(page, ms):
    """Move the page's time on by `ms`; returns the page clock in ms."""
    return page.evaluate("ms => window.__vc.run(ms)", ms)


def vc_until(page, cond, limit=60000):
    """Move the page's time on until the JS expression `cond` holds; raises TimeoutError if `limit` page-ms
    pass first. Returns the page-ms it took."""
    took = page.evaluate("([c, l]) => window.__vc.until(c, l)", [cond, limit])
    if took < 0:
        raise TimeoutError(f"the page's clock ran {limit} ms ({took}) and never saw: {cond}")
    return took


def vc_now(page):
    return page.evaluate("window.__vc.now")


SEAL = "[data-testid=\"roster-pack-stage\"] [data-testid=\"roster-pack-seal\"]"
STAGE_GONE = "!document.querySelector('[data-testid=\"roster-pack-stage\"]')"
GLOW_STILL = "!document.querySelector('[data-testid=\"roster-pack-center\"] [data-testid=\"roster-pack-glow\"]')?.getAnimations().length"


def rip(page, part=.9):
    """Drag along the stage pack's strip, `part` of its width. A tap no longer rips (2026-09-25).
    With motion on, the pack spins in first (2026-09-26); a finger waits for it to land. The pack
    stands turned, so its box is wider than its strip: the grip is the first point from the left
    that is on the strip. On a page with the virtual clock, the wait and the tear's own 220 ms
    are run on it."""
    clocked = page.evaluate("!!window.__vc")
    if clocked:
        vc_until(page, GLOW_STILL)
    else:
        page.wait_for_function(GLOW_STILL)
    box = page.get_by_test_id("roster-pack-stage").get_by_test_id("roster-pack-seal").bounding_box()
    y = box["y"] + box["height"] * .07
    x = page.evaluate("""([l, w, y]) => { for (let f = .02; f < .5; f += .02){
      const e = document.elementFromPoint(l + w * f, y); if (e && e.closest('[data-testid="roster-pack-top"]')) return l + w * (f + .02); } return l + w * .15; }""",
                      [box["x"], box["width"], y])
    part = min(part, .8)
    page.mouse.move(x, y)
    page.mouse.down()
    for k in range(1, 7):
        page.mouse.move(x + box["width"] * part * k / 6, y)
    page.mouse.up()
    if clocked:
        vc_run(page, 250)


class RosterPack:
    def __init__(self, page):
        self.page = page
        self._card = page.get_by_test_id("roster-cards").get_by_test_id("roster-card")
        self._rule = page.get_by_test_id("roster-cards").get_by_test_id("roster-rule")
        self._gate, self._stage = page.get_by_test_id("roster-pack-gate"), page.get_by_test_id("roster-pack-stage")
        self._seal = self._stage.get_by_test_id("roster-pack-seal")

    def _where(self, css):
        return self._card.and_(self.page.locator(css))

    def reload(self):
        self.page.reload(timeout=LOAD_MS)
        self.page.wait_for_function(DRAWN, timeout=LOAD_MS)

    def press_escape(self):
        self.page.keyboard.press("Escape")

    def allow_motion(self):
        """Motion on for this page (it was mounted under `MOTION`, a context of its own): the media query
        is read as the page runs, so one reload after the switch is all it takes."""
        if self.page.evaluate("REDUCED()"):
            self.page.emulate_media(reduced_motion="no-preference")
            self.reload()

    @contextlib.contextmanager
    def motion_allowed(self):
        """Motion on inside the block, reduced again after, so a page the module shares is as it was."""
        self.page.emulate_media(reduced_motion="no-preference")
        try:
            yield
        finally:
            self.page.emulate_media(reduced_motion="reduce")

    def reduced_motion(self):
        self.page.emulate_media(reduced_motion="reduce")

    def install_clock(self):
        vc_install(self.page)

    def run_clock(self, ms):
        return vc_run(self.page, ms)

    # ---- the pack: the gate, the stage, the chips ----

    def gates(self):
        return self._gate.count()

    def sealed_gates(self):
        return self._gate.get_by_test_id("roster-pack-seal").count()

    def stages(self):
        return self._stage.count()

    def skip_pack(self):
        self._gate.get_by_test_id("roster-pack-skip").click()

    def rip_gate(self):
        self._gate.get_by_test_id("roster-pack-rip").click()

    def open_stage(self):
        """Rip on the waiting pack, and wait for the stage."""
        self.rip_gate()
        self._stage.wait_for()

    def open_stage_on_the_clock(self):
        """Rip, not the pack: the pack turns by itself, and a turning target never holds still for a click."""
        self.rip_gate()
        vc_until(self.page, "!!document.querySelector('[data-testid=\"roster-pack-stage\"]')", 2000)

    def rip(self, part=.9):
        rip(self.page, part)

    def wait_stage_gone(self):
        self._stage.wait_for(state="detached")

    def stage_seals(self):
        return self._seal.count()

    def rerips(self):
        return self.page.get_by_test_id("roster-rerip").count()

    def rerip(self):
        self.page.get_by_test_id("roster-rerip").click()

    def slot_cards(self):
        """Cards left empty on the page while the stage holds their pack."""
        return self._where(".pk-slot").count()

    def dealt_cards(self):
        """Cards on the stage, risen out of the pack."""
        return self.page.get_by_test_id("roster-pack-card").count()

    def down_cards(self):
        return self._where(".down").count()

    def gate_away(self):
        """Gates whose pack is on the stage."""
        return self._gate.and_(self.page.locator(".away")).count()

    def pile_count(self):
        """Packs showing a retired count of the pack's size (`.pack-n`): none."""
        return self.page.locator(".pack-n").count()

    def center_count(self):
        return self.page.get_by_test_id("roster-pack-center").count()

    def stage_pack_scale(self):
        """The scale the stage's pack starts from (FLIP: small, where the page's was), or None."""
        return self.page.evaluate("""(() => { const a = document.querySelector('[data-testid="roster-pack-center"] [data-testid="roster-pack-glow"]').getAnimations()[0];
          return a ? +a.effect.getKeyframes()[0].scale : null; })()""")

    def empty_slots(self):
        """The indexes of the starters whose slot is left empty, sorted."""
        return self.page.evaluate("[...document.querySelectorAll('[data-testid=\"roster-card\"].pk-slot [data-testid=\"roster-back-open\"]')].map(b => +b.dataset.ci).sort((a, b) => a - b)")

    def pack_indexes(self):
        """The indexes of the cards the pack holds, sorted."""
        return self.page.evaluate("packCards(TEAMS.espn).map(c => c.i).sort((a, b) => a - b)")

    def art_share(self, where):
        """The photo's height over the card's, on the stage's card ("stage") or the first roster card ("roster")."""
        card = (self.page.get_by_test_id("roster-pack-card").get_by_test_id("roster-card") if where == "stage" else self._card).first
        return card.evaluate("el => el.querySelector('[data-testid=\"roster-card-art\"]').getBoundingClientRect().height / el.getBoundingClientRect().height")

    def seal_box(self):
        return self._seal.bounding_box()

    def tear_vars(self):
        """The stage pack's tear: [--ta, --tb, --tdir]."""
        return self._seal.evaluate("e => ['--ta', '--tb', '--tdir'].map(k => parseFloat(getComputedStyle(e).getPropertyValue(k)))")

    def tear_amount(self):
        return self._seal.evaluate("e => getComputedStyle(e).getPropertyValue('--tear').trim()")

    def wait_for_spring_back(self):
        """The spring back is eased, not a jump: wait for it to land."""
        self.page.wait_for_function("""() => { const s = document.querySelector('""" + SEAL + """');
          return !s.getAnimations().length && ['0', '0.000'].includes(getComputedStyle(s).getPropertyValue('--tear').trim()); }""")

    def tap_at(self, x, y):
        self.page.mouse.click(x, y)

    def press_at(self, x, y):
        self.page.mouse.move(x, y)
        self.page.mouse.down()

    def drag_to(self, x, y, steps=1):
        self.page.mouse.move(x, y, steps=steps)

    def release(self):
        self.page.mouse.up()

    def drag_between(self, x0, y0, x1, y1):
        self.press_at(x0, y0)
        self.drag_to(x1, y1)
        self.release()

    # ---- the chips, the switch, the starters' place ----

    def mode_chip_xs(self):
        return self.page.get_by_test_id("roster-mode").evaluate_all("bs => bs.map(b => Math.round(b.getBoundingClientRect().x))")

    def rule_rerips(self):
        """Rip again chips ending the Starters rule over the cards."""
        return self._rule.get_by_test_id("roster-rerip").count()

    def mode_switch_rerips(self):
        return self.page.locator(".rmode").get_by_test_id("roster-rerip").count()

    def open_week_chip(self):
        self.page.get_by_test_id("roster-open-week").click()

    def open_week_chips(self):
        return self._rule.get_by_test_id("roster-open-week").count()

    def waiting_open_week_chips(self):
        """Open-week chips drawn hidden (`.wait`), for Skip to shrink the pack into."""
        return self._rule.get_by_test_id("roster-open-week").and_(self.page.locator(".wait")).count()

    def open_week_chip_state(self):
        """The open-week chip: {count, text, waits}."""
        chip = self._rule.get_by_test_id("roster-open-week")
        one = chip.count() == 1
        return {"count": chip.count(), "text": chip.inner_text() if one else None,
                "waits": "wait" in (chip.get_attribute("class") or "") if one else None}

    def sched_week(self):
        return self.page.evaluate("schedWeek()")

    def starters_grid_edges(self):
        return self.page.get_by_test_id("roster-cards").get_by_test_id("roster-cardgrid").first.evaluate("e => (r => [r.top, r.bottom])(e.getBoundingClientRect())")

    def starters_grid_rect(self):
        return self.page.get_by_test_id("roster-cards-starters").get_by_test_id("roster-cardgrid").evaluate("e => (r => [r.left, r.top + scrollY, r.width, r.height])(e.getBoundingClientRect())")

    def viewport_height(self):
        return self.page.viewport_size["height"]

    def scroll_to_top(self):
        self.page.evaluate("scrollTo(0, 0)")

    def starter_cards(self):
        return self.page.get_by_test_id("roster-cards-starters").get_by_test_id("roster-card").count()

    def down_starters(self):
        return self.page.get_by_test_id("roster-cards-starters").get_by_test_id("roster-card").and_(self.page.locator(".down")).count()

    def bench_cards(self):
        return self.page.get_by_test_id("roster-cards-bench").get_by_test_id("roster-card").count()

    def down_bench_cards(self):
        return self.page.get_by_test_id("roster-cards-bench").get_by_test_id("roster-card").and_(self.page.locator(".down")).count()

    def zone_boxes(self):
        """The waiting pack's place: boxes of the zone, its grid, its pack, and the Rip and Skip buttons."""
        zone = self.page.get_by_test_id("roster-pack-zone")
        return {"zone": zone.bounding_box(), "grid": zone.get_by_test_id("roster-cardgrid").bounding_box(),
                "pack": self._gate.get_by_test_id("roster-pack-gpack").get_by_test_id("roster-pack-seal").bounding_box(),
                "rip": self._gate.get_by_test_id("roster-pack-rip").bounding_box(),
                "skip": self._gate.get_by_test_id("roster-pack-skip").bounding_box()}

    # ---- the pack: its turn, its walls, its cards ----

    def plant_no_metal(self):
        """Every projection ranked 40th and nobody signed: no hit in the pack; drawn again."""
        self.page.evaluate("""Object.values(LIVE_PROJECTIONS.players).forEach(r => { if (r.rank) r.rank = 40; });
          if (typeof LIVE_SIGNED !== 'undefined' && LIVE_SIGNED) LIVE_SIGNED.players = {};
          render()""")

    def pack_has_a_hit(self):
        return self.page.evaluate("packCards(TEAMS.espn).some(packHit)")

    def pack_size(self):
        return self.page.evaluate("packCards(TEAMS.espn).length")

    def wall_clips(self):
        return self._stage.get_by_test_id("roster-pack-wall").evaluate_all("ws => ws.map(w => getComputedStyle(w).clipPath)")

    def stage_pack_turn(self):
        return self.page.get_by_test_id("roster-pack-center").evaluate("e => parseFloat(e.style.getPropertyValue('--pry'))")

    def stage_pack_turn_style(self):
        """The raw `--pry` value: "" once the pack has sprung back."""
        return self.page.get_by_test_id("roster-pack-center").evaluate("e => e.style.getPropertyValue('--pry')")

    def waiting_pack_box(self):
        return self._gate.get_by_test_id("roster-pack-gpack").bounding_box()

    def waiting_pack_turn(self):
        return self._gate.get_by_test_id("roster-pack-glow").evaluate(r"e => parseFloat((getComputedStyle(e).rotate.match(/(-?[\d.]+)deg/) || [0, 0])[1])")

    def wait_for_the_waiting_pack_to_turn(self, timeout):
        """The pack's own frame loop, on the wall clock: it rests 2 s, then turns."""
        self.page.wait_for_function(r"""parseFloat((getComputedStyle(document.querySelector('[data-testid="roster-pack-gate"] [data-testid="roster-pack-glow"]')).rotate.match(/(-?[\d.]+)deg/) || [0, 0])[1]) > 1""",
                                    timeout=timeout)

    def idle_turns(self):
        """Packs the page keeps turning by itself (`PK_IDLES`): none under reduced motion."""
        return self.page.evaluate("PK_IDLES.size")

    def waiting_pack_shrink(self):
        """The scale the waiting pack shrinks to when Skip is tapped, or None when it does not animate."""
        return self.page.get_by_test_id("roster-pack-gpack").evaluate("""e => { const a = e.getAnimations()[0];
          return a ? +a.effect.getKeyframes()[1].scale : null; }""")

    def wait_for_stage(self):
        self._stage.wait_for()

    def wait_for_stage_seal(self):
        self._seal.wait_for()

    def stage_animation_rates(self):
        """The playback rate of each finite animation on the stage, once each is ready (the clock parks every
        animation with a pending pause, and a rate read before it settles reads 1)."""
        return self._stage.evaluate("""async stage => {
          const anims = stage.getAnimations({subtree: true}).filter(a => a.effect.getTiming().iterations !== Infinity);
          await Promise.all(anims.map(a => a.ready));
          return anims.map(a => a.playbackRate);
        }""")

    def pack_msg(self):
        return self.page.get_by_test_id("roster-pack-msg").text_content()

    def held_card(self):
        """The last card on the stage: its centre, the page's centre, and the label text: [x, mid, text]."""
        return self.page.evaluate("""(() => { const cs = document.querySelectorAll('[data-testid="roster-pack-card"]'), r = cs[cs.length - 1].getBoundingClientRect();
          return [r.left + r.width / 2, document.documentElement.clientWidth / 2, document.querySelector('[data-testid="roster-pack-msg"]').textContent]; })()""")

    def last_stage_card_inking(self):
        """The last stage card's autograph: [still unsigned, running animations on the ink, on the pen tip]."""
        return self.page.evaluate("""(() => { const cs = document.querySelectorAll('[data-testid="roster-pack-card"]'), c = cs[cs.length - 1];
          return [c.classList.contains('pk-unsigned'), c.querySelector('[data-testid="roster-card-auto-cool"]').getAnimations().length,
                  c.querySelector('[data-testid="roster-card-auto-tip"]').getAnimations().length]; })()""")

    def sparks(self):
        return self.page.get_by_test_id("roster-card-spark").count()

    def sign_a_starter(self):
        """Sign a starting TE (else WR) at rank 2, 22.6 pts for week 3; drawn again. Returns his position."""
        return self.page.evaluate("""(() => { const p = TEAMS.espn.roster.find(p => p.start && p.pos === 'TE') || TEAMS.espn.roster.find(p => p.start && p.pos === 'WR');
          LIVE_SIGNED.players[p.slug] = {rank: 2, pts: 22.6}; render(); return p.pos; })()""")

    def browse_espn_following_only_yahoo(self):
        """A reader who follows only the Yahoo team, browsing the ESPN roster in Cards."""
        self.page.evaluate("localStorage.setItem('tw-follow', JSON.stringify(['yahoo'])); navGo('roster'); VIEW='espn'; ROSTER_MODE='cards'; render()")

    def start_rows(self):
        return self.page.get_by_test_id("roster-row").and_(self.page.locator(".start")).count()

    # ---- waits on the page's own clock ----

    def clock_now(self):
        return vc_now(self.page)

    def until(self, cond, limit):
        return vc_until(self.page, cond, limit)

    def until_the_best_card_reveals(self, limit):
        self.until("!!document.querySelector('[data-testid=\"roster-pack-stage\"].pk-dim')", limit)

    def until_the_message_starts(self, text, limit):
        self.until(f"document.querySelector('[data-testid=\"roster-pack-msg\"]')?.textContent.startsWith('{text}')", limit)

    def until_a_hit_is_labelled(self, limit, kind=""):
        """The label's tag is up; `kind` ("signed") asks for that finish."""
        self.until(f"!!document.querySelector('[data-testid=\"roster-pack-msg\"] [data-testid=\"roster-pack-tag\"]{'.t-' + kind if kind else ''}')", limit)

    def until_the_cards_have_turned_up(self, limit):
        """Every starter face up and none still turning (`.up`): the Skip wave is over."""
        self.until(f"document.querySelectorAll('[data-testid=\"roster-cards-starters\"] [data-testid=\"roster-card\"].down').length === 0 && !document.querySelector('[data-testid=\"roster-cards\"] [data-testid=\"roster-card\"].up')", limit)

    def until_the_gate_is_gone(self, limit):
        self.until("!document.querySelector('[data-testid=\"roster-pack-gate\"]')", limit)

    def until_a_card_is_dealt(self):
        self.until("!!document.querySelector('[data-testid=\"roster-pack-card\"]')", 60000)

    def until_the_stage_is_gone(self, limit):
        self.until(STAGE_GONE, limit)

    def until_the_first_pack_is_gone(self, limit):
        self.until("!document.querySelector('[data-testid=\"roster-pack-center\"]')", limit)

    def until_the_pile_counts(self, n, limit):
        self.until(f"document.querySelector('[data-testid=\"roster-pack-count\"]')?.textContent.startsWith('{n} ')", limit)

    def until_the_stage_card_is_labelled(self, limit):
        self.until("""document.querySelector('[data-testid="roster-pack-card"] [data-testid="roster-card"]')
          && document.querySelector('[data-testid="roster-pack-msg"]').textContent.includes('#')""", limit)
