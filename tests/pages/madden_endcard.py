"""Screen-space closing identity and blackout inspection."""
from pages.madden_power import PowerFilm


class EndcardFilm(PowerFilm):
    def endcard(self):
        return self.page.evaluate("""() => {
          const root = document.querySelector('[data-room]'), brand = root.querySelector('.brand');
          const rect = brand.getBoundingClientRect(), room = root.getBoundingClientRect();
          const shade = getComputedStyle(root, '::before');
          let opacity = 1;
          for (let node = brand; node; node = node.parentElement) opacity *= Number(getComputedStyle(node).opacity);
          return {active: root.dataset.endcard === 'true', black: Number(shade.opacity), color: shade.backgroundColor,
            opacity, width: rect.width / room.width, height: rect.height / room.height,
            center: [(rect.left + rect.width / 2 - room.left) / room.width,
              (rect.top + rect.height / 2 - room.top) / room.height],
            within: rect.left >= room.left && rect.right <= room.right && rect.top >= room.top && rect.bottom <= room.bottom};
        }""")
