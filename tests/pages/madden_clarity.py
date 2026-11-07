from pages.madden_waivers import WaiversFilm


class ClarityFilm(WaiversFilm):
    def detail(self):
        return self.page.locator('[data-lineup-context]')

    def pickup_frame(self):
        return self.page.evaluate("""() => {
          const stage = document.querySelector('[data-waivers]');
          const nodes = [stage.querySelector('[data-waivers-sub]'), ...stage.querySelectorAll('[data-pickup="1"], [data-pickup="1"] [data-pickup-name], [data-pickup="1"] [data-pickup-face], [data-pickup="1"] [data-pickup-team], [data-pickup="1"] [data-week-rank]')];
          const frame = stage.getBoundingClientRect();
          return nodes.map(node => {
            const box = node.getBoundingClientRect();
            let alpha = 1;
            for (let parent = node; parent; parent = parent.parentElement) {
              const style = getComputedStyle(parent);
              if (parent.hidden || style.display === 'none' || style.visibility !== 'visible') alpha = 0;
              alpha *= Number(style.opacity);
            }
            return {text: node.textContent, visible: alpha > .99, inside: box.width > 0 && box.left >= frame.left && box.right <= frame.right && box.top >= frame.top && box.bottom <= frame.bottom};
          });
        }""")

    def textures(self):
        return self.page.evaluate("""async () => {
          const {PALETTE} = await import('./constants.mjs');
          const {powerValues, checkPower} = await import('./power-data.mjs');
          const {lineupValues, checkLineups} = await import('./lineups-data.mjs');
          const {makeRiser} = await import('./power-riser.mjs');
          const {makeProps: powerProps} = await import('./power-props.mjs');
          const {makeProps: lineupProps} = await import('./lineups-props.mjs');
          const {POSE} = await import('./lineups-pose.mjs');
          const power = powerValues(checkPower(await (await fetch('./power-receipts.json')).json()));
          const lineup = lineupValues(checkLineups(await (await fetch('./lineups-receipts.json')).json()));
          const draws = [], original = CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText = function(text, ...args) {draws.push(String(text)); return original.call(this, text, ...args);};
          let riser, feature, props;
          try {
            riser = makeRiser(power.order, {});
            feature = powerProps(power.feature);
            props = lineupProps(lineup, POSE.scores);
            const ink = [];
            const read = map => {
              const image = map.image, data = image.getContext('2d').getImageData(0, 0, image.width, image.height).data;
              let dark = 0, white = 0;
              for (let index = 0; index < data.length; index += 4) {
                if (data[index + 3] < 250) continue;
                if (data[index] < 40 && data[index + 1] < 45 && data[index + 2] < 50) dark += 1;
                if (data[index] > 245 && data[index + 1] > 245 && data[index + 2] > 245) white += 1;
              }
              return {dark, white};
            };
            ink.push(read(feature.group.children[0].material.map));
            props.cards.forEach(card => card.stamps.filter(mesh => mesh.userData.key.endsWith('bench')).forEach(mesh => ink.push(read(mesh.material.map))));
            return {draws, ink};
          } finally {
            CanvasRenderingContext2D.prototype.fillText = original;
            riser?.dispose(); feature?.dispose();
            props?.group.traverse(object => {object.geometry?.dispose(); [object.material].flat().forEach(material => {material?.map?.dispose(); material?.dispose();});});
          }
        }""")
