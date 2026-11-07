"""Eye geometry for the single closing Blip wink."""
from pages.madden_endcard import EndcardFilm


class LogoWinkFilm(EndcardFilm):
    def seek(self, seconds):
        self.page.locator('[data-seek]').evaluate("element => {element.step = 'any';}")
        super().seek(seconds)

    def faces_at(self, times):
        rows = []
        for time in times:
            self.seek(time)
            rows.append(self.face())
        return rows

    def face(self):
        return self.page.evaluate("""() => {
          const brand = document.querySelector('.brand');
          const box = element => {const rect = element.getBoundingClientRect();
            return [rect.x, rect.y, rect.width, rect.height];};
          return {eyes: [...brand.querySelectorAll('.blip-eye')].map(eye => eye.getBoundingClientRect().height),
            word: box(brand.querySelector('.brand-name')), mark: box(brand.querySelector('.brand-mark'))};
        }""")
