"""The pack's rip screen on its stage (design/src/js/surface/teams/pack.js wireRip, pack.css, packshow.css), for
test_pack_rip.py: the mouth under the strip, the flap that follows the finger, the flakes' start, the glow beside the
turning pack, the torn foil after the rip, and the hint under the cards.

`PackRip` wraps a roster page that already shows the stage (`on_cards(mount, pack="stage")`, or `on_motion` and
`open_stage_on_the_clock`). Every locator is a `roster-pack-*` data-testid; the parts the page draws without one
(the mouth, the flap, the torn edge, the foil, the hint) are read through their class under the strip or the seal,
because they are pure decoration with no behaviour a test could reach another way.
"""

SEAL = '[data-testid="roster-pack-stage"] [data-testid="roster-pack-seal"]'
STAGE = '[data-testid="roster-pack-stage"]'

# The first x on the strip, from the left, a finger can grip: the leaned pack's box is wider than its strip.
GRIP = """([l, w, y]) => { for (let f = .02; f < .5; f += .02){
  const e = document.elementFromPoint(l + w * f, y); if (e && e.closest('[data-testid="roster-pack-top"]')) return l + w * (f + .02); }
  return l + w * .15; }"""

# What a packBurst call saw: where the flakes start, and where the torn edge was at that moment.
SPY_FLAKES = """() => { window.__flakes = [];
  packBurst = (x, y) => { const r = document.querySelector('%s .pt-edge').getBoundingClientRect();
    window.__flakes.push({x, y, edge: [r.left, r.top, r.right, r.bottom]}); }; }""" % SEAL


class PackRip:
    def __init__(self, page):
        self.page = page
        self._seal = page.locator(SEAL)

    # ---- the tear ----

    def grip(self):
        """Press on the strip's left end and return [x, y, width] of the grip and the seal's width."""
        box = self._seal.bounding_box()
        y = box["y"] + box["height"] * .07
        x = self.page.evaluate(GRIP, [box["x"], box["width"], y])
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        return x, y, box["width"]

    def tear_to(self, to, pull=0, steps=6):
        """Press on the strip and drag right to `to` (0..1 of the seal's width, from its left edge) and `pull` px up
        (negative is up); the finger stays down. The tear is the finger's place over .75, and past .55 a release
        tears the strip off, so `to` .3 is a tear that closes again."""
        x, y, w = self.grip()
        left = self._seal.bounding_box()["x"]
        for k in range(1, steps + 1):
            self.page.mouse.move(x + (left + w * to - x) * k / steps, y + pull * k / steps)

    def tear_a_little(self):
        """The strip torn part way, written as the tear writes it (a drag costs a round trip a step)."""
        self._seal.evaluate("e => ['--ta', '--tb', '--te', '--tear'].forEach((k, i) => e.style.setProperty(k, [.2, .6, .6, .5][i]))")

    def let_go(self):
        self.page.mouse.up()

    def watch_flakes(self):
        self.page.evaluate(SPY_FLAKES)

    def flakes(self):
        """Each burst's [x, y] and the torn edge's box [left, top, right, bottom] when it fired."""
        return self.page.evaluate("window.__flakes")

    # ---- what the strip draws ----

    def vars(self, *names):
        """The seal's own custom properties as numbers, in the order asked."""
        return self._seal.evaluate("(e, ns) => ns.map(n => parseFloat(getComputedStyle(e).getPropertyValue(n)))", list(names))

    def inline_vars(self, *names):
        """The same, as the strings the page wrote (an empty one when it has not)."""
        return self._seal.evaluate("(e, ns) => ns.map(n => e.style.getPropertyValue(n))", list(names))

    def mouth(self):
        """The mouth under the strip: its opacity, its clip, the left and right insets of that clip as percents,
        and whether it wears the strip's own crimp mask."""
        return self._seal.evaluate("""e => { const m = e.querySelector('.pt-mouth'), b = e.querySelector('.pt-base'), c = getComputedStyle(m);
          const ins = (c.clipPath.match(/inset\\(([^)]*)\\)/) || [0, ''])[1].split(/\\s+/).map(parseFloat);
          const maskOf = s => s.maskImage || s.webkitMaskImage;
          return {opacity: parseFloat(c.opacity), clip: c.clipPath, left: ins[3], right: ins[1],
                  crimped: maskOf(c) !== 'none' && maskOf(c) === maskOf(getComputedStyle(b))}; }""")

    def flap_pose(self):
        """The torn flap's lift (px) and tip (deg) as drawn: [translate y, rotate]."""
        return self._seal.evaluate("""e => { const c = getComputedStyle(e.querySelector('.pt-flap'));
          return [parseFloat(c.translate.split(' ')[1] || 0), parseFloat(c.rotate) || 0]; }""")

    # ---- the stage around it ----

    def glow_scale(self):
        """The tier glow's drawn width scale (`scale` on the centre's ::before) and the value the page set."""
        return self.page.evaluate("""() => { const c = document.querySelector('[data-testid="roster-pack-center"]');
          return [parseFloat(getComputedStyle(c, '::before').scale), parseFloat(c.style.getPropertyValue('--gs'))]; }""")

    def spin_body(self, part):
        """Drag the pack's body `part` of its width to the right, the finger staying down."""
        box = self._seal.bounding_box()
        y = box["y"] + box["height"] * .6
        x = box["x"] + box["width"] / 2
        self.page.mouse.move(x, y)
        self.page.mouse.down()
        self.page.mouse.move(x + box["width"] * part, y, steps=3)

    def tear_the_stage(self):
        """What the rip's own code does the moment it starts (packshow.js pkRip), so the torn look can be read
        without the stage's motion: the stage is marked ripped."""
        self.page.evaluate("document.querySelector('%s').classList.add('pk-ripped')" % STAGE)

    def foil_and_seam(self):
        """The foil's clip and the seam's opacity, once the stage is ripped (or not)."""
        return self._seal.evaluate("""e => ({foil: getComputedStyle(e.querySelector('.pack-foil')).clipPath,
          seam: parseFloat(getComputedStyle(e, '::after').opacity)})""")

    def hint(self):
        """The hint's opacity and animation name, as drawn now."""
        return self.page.evaluate("""() => { const c = getComputedStyle(document.querySelector('%s .pk-hint'));
          return {opacity: parseFloat(c.opacity), animation: c.animationName}; }""" % STAGE)

    def wait_for_hint_to_fade(self):
        """The fade is a CSS transition on the real clock (the virtual one parks animations, not transitions)."""
        self.page.wait_for_function("""() => parseFloat(getComputedStyle(document.querySelector('%s .pk-hint')).opacity) === 0""" % STAGE)

    def flying(self):
        return self.page.evaluate("document.querySelector('%s').classList.contains('pk-flying')" % STAGE)

    def until_a_card_flies(self, roster, limit):
        roster.until("document.querySelector('%s').classList.contains('pk-flying')" % STAGE, limit)
