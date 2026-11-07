from pages.madden_waivers import WaiversFilm, waiver_file


class LoadingFilm(WaiversFilm):
    def __init__(self, browser, width, height, reduced=False):
        super().__init__(browser, width, height, reduced)
        self.reduced = reduced
        self.pending = []
        self.page.route("**/edition.json", lambda route: self.pending.append(route), times=1)

    def hold(self):
        self.page.goto("http://trophy.test/?film", wait_until="domcontentloaded")
        self.page.wait_for_function("document.body.hasAttribute('data-film')")

    def release(self, fail=False):
        route = self.pending.pop()
        if fail:
            route.fulfill(status=503, body="Unavailable")
        else:
            waiver_file(route)

    def loader(self):
        return self.page.locator("[data-loading]")

    def play_button(self):
        return self.page.locator("[data-play]")

    def phase(self):
        return self.page.locator("[data-room]")

    def inactive_controls(self):
        return self.page.locator(".controls")

    def loading_metrics(self):
        return self.loader().evaluate("""node => {
          const box = node.getBoundingClientRect();
          const signal = node.querySelector('[data-loading-signal]');
          const controls = [...document.querySelectorAll('.controls')];
          return {inside:box.left>=0 && box.top>=0 && box.right<=innerWidth && box.bottom<=innerHeight,
            animation:signal ? getComputedStyle(signal.firstElementChild).animationName : null,
            blocked:controls.every(control => control.inert),
            busy:document.querySelector('[data-room]').getAttribute('aria-busy')};
        }""")
