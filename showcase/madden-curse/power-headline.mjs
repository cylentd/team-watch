import { HEADLINE } from "./constants-power.mjs";
export { HEADLINE };
import { outCubic, seg } from './draft-motion.mjs';
import { TIMES } from "./power-clock.mjs";
import { POWER_COPY } from './power-copy.mjs';

/* Chapter 5's headlines over the riser (docs/madden-film-chapter5.md, beat tables): each slams in with its hit over
   10 frames and leaves in 4, out faster than in (craft, "Chyron slam"). The ranks and the 4-4 are on the cube and
   the plate, so they are textures, not headlines (rule 26). Pure schedule, then the DOM. */
     // seconds one glint takes to cross the TEAM WATCH tag after it lands (97.59)

// 2026-11-05 (David: "Chapter 5 isnt power ranking. It's the actual rankings."): "Standings." over the plates as they
// land in the standings, "Power rankings." with its method from the shuffle's landing.
const WINDOWS = Object.freeze([
  {key: 'standings', from: TIMES.board, to: TIMES.shuffle[1] - HEADLINE.leave},
  {key: 'head', sub: true, from: TIMES.shuffle[1], to: TIMES.verdict - HEADLINE.leave},
  {key: 'feature', from: TIMES.verdict, to: TIMES.four - HEADLINE.leave},
  {key: 'apart', from: TIMES.four, to: TIMES.pull[1] - HEADLINE.closeOut},
  {key: 'close', from: TIMES.trophy[1], to: TIMES.identIn - HEADLINE.closeOut},
]);

/* The headline at film second `time`: {key, sub, enter 0..1}, or null. Reduced motion keeps the windows, no slide. */
export function headlineAt(time, reduced = false) {
  const shown = WINDOWS.find(entry => time >= entry.from && time < entry.to + (reduced ? 0 : HEADLINE.leave));
  if (!shown) return null;
  const enter = reduced ? 1 : outCubic(seg(time, shown.from, shown.from + HEADLINE.enter)) * (1 - seg(time, shown.to, shown.to + HEADLINE.leave));
  return {key: shown.key, sub: Boolean(shown.sub), enter};
}

const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, name) => values[name]);

/* The headline's DOM inside the room, posed every frame from the film's clock. */
export function makeHeadline(root) {
  const section = document.createElement('section'), head = document.createElement('h2'), sub = document.createElement('p');
  section.className = 'power'; section.dataset.power = ''; section.hidden = true;
  head.className = 'power-head'; head.dataset.powerHead = '';
  sub.className = 'power-sub'; sub.dataset.powerSub = '';
  sub.textContent = fill(POWER_COPY.sub, POWER_COPY);
  section.append(head, sub);
  root.append(section);
  return {
    update(time, reduced, mobile) {
      const shown = headlineAt(time, reduced);
      section.hidden = !shown;
      section.dataset.layout = mobile ? 'phone' : 'desk';
      root.style.setProperty('--power-glint', reduced ? 0 : seg(time, TIMES.last, TIMES.last + HEADLINE.glint));
      if (!shown) return;
      if (head.textContent !== POWER_COPY[shown.key]) head.textContent = POWER_COPY[shown.key];
      sub.hidden = !shown.sub;
      section.style.setProperty('--power-enter', shown.enter);
    },
    hide() { section.hidden = true; root.style.setProperty('--power-glint', 0); },
    dispose() { section.remove(); root.style.removeProperty('--power-glint'); },
  };
}
