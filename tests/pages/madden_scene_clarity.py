from pages.madden_clarity import ClarityFilm


class SceneClarityFilm(ClarityFilm):
    def headline(self):
        return self.page.locator('[data-lineup-outcome]')

    def headline_box(self):
        return self.headline().bounding_box()
