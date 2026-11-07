"""Chapter 4's 3D lineup desk (showcase/madden-curse/lineups-set.mjs). Its words are textures, so every read goes
through the set's own readout (`lineupsReadout`, the screen box of each printed surface), plus the DOM headline."""
from playwright.sync_api import expect

from pages.madden_waivers import WaiversFilm, waiver_file


READOUT = "async () => (await import('./lineups-set.mjs')).lineupsReadout()"
HEADLINE = '[data-lineup-headline]'
OUTCOME = '[data-lineup-outcome]'
PORTRAITS = ['**/heads/xl/harold-fannin.webp', '**/heads/xl/hunter-henry.webp']


class LineupsSetFilm(WaiversFilm):
    def readout(self):
        return self.page.evaluate(READOUT)

    def shown_text(self):
        """The printed words whole inside the frame, in the set's order."""
        return [label['text'] for label in self.readout()['labels'] if label['visible'] and label['inside']]

    def headline(self):
        return self.page.evaluate('''() => {
          const node = document.querySelector('[data-lineup-outcome]');
          if (!node) return {visible: false};
          let alpha = 1;
          for (let parent = node; parent; parent = parent.parentElement) {
            const style = getComputedStyle(parent);
            if (parent.hidden || style.display === 'none' || style.visibility !== 'visible') return {visible: false};
            alpha *= Number(style.opacity);
          }
          const style = getComputedStyle(node), pen = document.createElement('canvas').getContext('2d');
          pen.font = [style.fontWeight, style.fontSize, style.fontFamily].join(' ');
          const range = document.createRange(); range.selectNodeContents(node);
          const box = range.getBoundingClientRect();
          return {visible: alpha > .99, text: node.textContent, cap: pen.measureText(node.textContent.toUpperCase()).actualBoundingBoxAscent,
            transform: style.transform, box: {left: box.left, top: box.top, right: box.right, bottom: box.bottom}};
        }''')

    def canvases(self):
        return self.page.locator('[data-viewport] canvas').count()

    def load_with_held_portrait(self, resource):
        """Hold one portrait until the rest of the page has loaded: Play stays off until it arrives."""
        pending = []
        self.context.route(resource, lambda route: pending.append(route))
        with self.page.expect_request(resource, timeout=30000):
            self.page.goto('http://trophy.test/?film', wait_until='domcontentloaded')
        self.page.evaluate("async () => { await document.fonts.ready; await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))); }")
        held = self.page.locator('[data-play]').is_disabled()
        for route in pending:
            waiver_file(route)
        expect(self.page.locator('[data-play]')).to_be_enabled(timeout=30000)
        return held

    def fail_portrait(self, resource):
        """A portrait that never loads: the room is thrown away and the page falls back."""
        self.context.route(resource, lambda route: route.fulfill(status=404, body='Not found'))
        self.page.goto('http://trophy.test/?film', wait_until='domcontentloaded')
        expect(self.page.locator('[data-room]')).to_have_attribute('data-phase', 'fallback', timeout=30000)
        return self.readout()
