"""Chapter 5 of the Madden Curse film, the power riser (showcase/madden-curse/power-set.mjs): its headline, the ident
and the badge loading. The expected copy and times come from the tests, never from production state."""
from playwright.sync_api import expect

from pages.madden_waivers import WaiversFilm, waiver_file

# Honey's badge: only the riser decodes it (Chapters 3 and 4 show other teams), so a failure tests this set alone.
BADGE = '**/avatars/yahoo/7.webp'

HEADLINE = '''() => {
  const stage = document.querySelector('[data-power]');
  const shown = node => {if (!node || !node.textContent.trim()) return false; for (let parent = node; parent; parent = parent.parentElement) {
    const style = getComputedStyle(parent); if (parent.hidden || style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) < .99) return false;} return true;};
  const head = stage?.querySelector('[data-power-head]'), sub = stage?.querySelector('[data-power-sub]');
  const nodes = [head, sub].filter(shown);
  const cap = node => {const style = getComputedStyle(node), pen = document.createElement('canvas').getContext('2d');
    pen.font = [style.fontWeight, style.fontSize, style.fontFamily].join(' ');
    return pen.measureText(node.textContent.toUpperCase()).actualBoundingBoxAscent * node.getBoundingClientRect().height / node.offsetHeight;};
  const ink = node => {const range = document.createRange(); range.selectNodeContents(node); return range.getBoundingClientRect();};
  const within = nodes.every(node => {const box = ink(node); return box.left >= 0 && box.top >= 0 && box.right <= innerWidth && box.bottom <= innerHeight;});
  const upright = nodes.every(node => {for (let parent = node; parent; parent = parent.parentElement) {const matrix = new DOMMatrix(getComputedStyle(parent).transform);
    if (Math.abs(matrix.b) > 1e-6 || Math.abs(matrix.c) > 1e-6) return false;} return true;});
  return {head: shown(head) ? head.textContent : null, sub: shown(sub) ? sub.textContent : null, within, upright,
    capHeight: nodes.length ? Math.min(...nodes.map(cap)) : 0};
}'''


class PowerFilm(WaiversFilm):
    def headline(self):
        return self.page.evaluate(HEADLINE)

    def ident(self):
        return self.page.locator('[data-room]').get_attribute('data-ident')

    def load_with_delayed_badge(self):
        pending, held = [], [True]

        def hold(route):
            if held[0]:
                pending.append(route)
            else:
                waiver_file(route)
        self.context.route(BADGE, hold)
        with self.page.expect_request(BADGE):
            self.page.goto('http://trophy.test/?film', wait_until='domcontentloaded')
        self.page.evaluate("async () => { await document.fonts.ready; await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); }")
        expect(self.page.locator('[data-play]')).to_be_disabled()
        held[0] = False
        for route in pending:
            waiver_file(route)
        expect(self.page.locator('[data-play]')).to_be_enabled(timeout=60000)

    def fail_badge(self):
        self.context.route(BADGE, lambda route: route.fulfill(status=404, body='Not found'))
        self.page.goto('http://trophy.test/?film', wait_until='domcontentloaded')
        expect(self.page.locator('[data-room]')).to_have_attribute('data-phase', 'fallback', timeout=60000)
        return {'canvas': self.page.locator('[data-viewport] canvas').count(), 'headline': self.page.locator('[data-power]').count(),
                'phase': self.page.locator('[data-room]').get_attribute('data-phase')}
