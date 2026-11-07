"""Finale camera inspection after the application has drawn a seek."""
from pages.madden_power import PowerFilm


class TrophyFlyinFilm(PowerFilm):
    def ending_camera(self):
        return self.page.evaluate("""async ([width, height]) => {
          const {REDUCED, shot} = await import('/power-camera.mjs');
          const ctx = {mobile: width < 760, size: {width, height}};
          const camera = shot('power-close', 14, ctx);
          return {clock: REDUCED.clock, position: camera.position.toArray()};
        }""", [self.width, self.height])
