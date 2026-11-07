from pages.madden_lineups_set import LineupsSetFilm


MANAGER = '[data-defense-manager]'


class DefenseCardsFilm(LineupsSetFilm):
    def identity(self):
        return self.page.locator(MANAGER).evaluate("""node => {
          const image = node.querySelector('img'), box = node.getBoundingClientRect();
          let opacity = 1;
          for (let parent = node; parent; parent = parent.parentElement) {
            const style = getComputedStyle(parent);
            if (parent.hidden || style.display === 'none' || style.visibility !== 'visible') opacity = 0;
            opacity *= Number(style.opacity);
          }
          return {text:node.textContent, loaded:image.complete && image.naturalWidth > 0,
            visible:opacity > .99 && box.width > 0 && box.height > 0,
            inside:box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight};
        }""")

    def power_layers(self):
        return self.page.evaluate("""async () => {
          const {makeRiser} = await import('./power-riser.mjs');
          const image = document.createElement('canvas'); image.width = image.height = 128;
          const team = {id:1,name:'Test',record:'4–4',allPlay:'44–44',standing:6};
          const riser = makeRiser([team], {1:image});
          const result = Object.values(riser.plates[0].faces).map(mesh => ({write:mesh.material.depthWrite,bias:mesh.material.polygonOffset}));
          riser.dispose(); return result;
        }""")
