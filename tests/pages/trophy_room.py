"""Public interactions and observations for the standalone WebGL opening."""


class TrophyRoom:
    def __init__(self, page):
        self.page = page

    def open(self):
        self.page.goto('http://trophy.test/', wait_until='domcontentloaded')
        self.page.wait_for_function("document.querySelector('[data-room]').dataset.phase !== 'loading'")

    def phase(self):
        return self.page.locator('[data-room]').get_attribute('data-phase')

    def time(self):
        return float(self.page.get_by_role('progressbar').get_attribute('aria-valuenow'))

    def action(self, name):
        return self.page.get_by_role('button', name=name, exact=True)

    def advance(self, milliseconds):
        self.page.clock.run_for(milliseconds)

    def visible_title(self):
        return self.page.get_by_role('heading', name='THE MADDEN CURSE').is_visible()

    def hidden_tab(self):
        self.page.evaluate("Object.defineProperty(document, 'hidden', {configurable: true, value: true}); document.dispatchEvent(new Event('visibilitychange'))")

    def title_fits(self):
        return self.page.locator('h1 span').evaluate_all("elements => elements.every(element => { const box = element.getBoundingClientRect(); return box.left >= 0 && box.right <= innerWidth; })")
