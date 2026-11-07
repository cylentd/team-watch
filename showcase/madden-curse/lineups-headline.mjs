import { HEADLINE } from "./constants-lineups.mjs";
export { HEADLINE };
import { outCubic, seg } from './draft-motion.mjs';
import { CLOCK } from "./lineups-clock.mjs";
import { LINEUPS_COPY } from './lineups-copy.mjs';

/* Chapter 4's headlines over the desk (docs/madden-film-chapter4.md, beat tables). Each beat opens on its title (David,
   2026-11-05: "you have to have some text to describe what's going on"), which leaves before the beat's punchline:
   "Won both negative weeks." on the wins bar and "Again." on 18.40. Each slams in over 10 frames, from 112% and
   transparent, and leaves in 4, out faster than in (craft, "Chyron slam"). Upright DOM type, never a texture, so it
   stays sharp (rule 21). Pure schedule, then the DOM. */
  // and "Again." at 77.95, before the crane onto Chapter 5's riser
const WINDOWS = Object.freeze([
  {key: 'defense', kind: 'title', from: 0, to: CLOCK.wins[0] - HEADLINE.leave},
  {key: 'defenseWin', kind: 'title', from: CLOCK.wins[0], to: CLOCK.landings[1] - HEADLINE.leave},
  {key: 'defenseNext', kind: 'title', from: CLOCK.landings[1], to: CLOCK.outcome - HEADLINE.titleOut - HEADLINE.leave},
  {key: 'outcome', kind: 'line', from: CLOCK.outcome, to: CLOCK.second - HEADLINE.outcomeOut - HEADLINE.leave},
  {key: 'tightends', kind: 'title', from: CLOCK.second, to: CLOCK.bench8 - HEADLINE.titleOut - HEADLINE.leave},
  {key: 'payoff', kind: 'line', from: CLOCK.bench8, to: CLOCK.end - HEADLINE.payoffOut - HEADLINE.leave},
]);

/* The headline at chapter second `seconds`: {key, kind, enter 0..1}, or null. Reduced motion shows the whole window at once. */
export function headlineAt(seconds, reduced = false) {
  const shown = WINDOWS.find(entry => seconds >= entry.from && seconds < entry.to + HEADLINE.leave);
  if (!shown) return null;
  const enter = reduced ? 1 : outCubic(seg(seconds, shown.from, shown.from + HEADLINE.enter)) * (1 - seg(seconds, shown.to, shown.to + HEADLINE.leave));
  return {key: shown.key, kind: shown.kind, enter};
}

/* The headline's DOM inside the room. `outcome` is the data's own line (lineups-data.mjs lineupValues). */
export function makeHeadline(root, cast, avatar) {
  const section = document.createElement('section'), line = document.createElement('p');
  section.className = 'lineups'; section.dataset.lineups = ''; section.dataset.lineupHeadline = ''; section.hidden = true;
  line.className = 'lineup-outcome'; line.dataset.lineupOutcome = '';
  const manager = document.createElement('div'), badge = document.createElement('img'), name = document.createElement('span');
  manager.className = 'lineup-manager'; manager.dataset.defenseManager = '';
  badge.src = avatar; badge.alt = ''; name.textContent = LINEUPS_COPY.defenseManager;
  manager.append(badge, name); section.append(manager, line);
  const controls = root.querySelector('.controls');   // under the controls, so they stay on top
  if (controls) controls.before(section); else root.append(section);
  const fill = (template, entry) => template.replace(/\{(\w+)\}/g, (_, key) => entry[key]);
  const text = {defense: fill(LINEUPS_COPY.defense, cast.defense[0]),
    defenseWin: fill(LINEUPS_COPY[cast.defense[0].won ? 'defenseWin' : 'defenseLoss'], cast.defense[0]),
    defenseNext: fill(LINEUPS_COPY.defenseNext, cast.defense[1]),
    outcome: cast.outcome, tightends: LINEUPS_COPY.tightends, payoff: LINEUPS_COPY.payoff};
  return {
    update(seconds, reduced, mobile) {
      const shown = headlineAt(seconds, reduced);
      const defense = seconds >= 0 && seconds < CLOCK.second;
      section.hidden = !shown && !defense; manager.hidden = !defense; line.hidden = !shown || !text[shown.key];
      section.dataset.layout = mobile ? 'phone' : 'desk';
      if (!shown) { line.textContent = ''; section.style.setProperty('--lineup-enter', 1); return; }
      Object.assign(section.dataset, {key: shown.key, kind: shown.kind});
      if (line.textContent !== text[shown.key]) line.textContent = text[shown.key];
      line.style.opacity = defense ? shown.enter : '';
      section.style.setProperty('--lineup-enter', defense ? 1 : shown.enter);
      section.style.setProperty('--lineup-slam', defense ? 1 : 1 + HEADLINE.slam * (1 - shown.enter));
    },
    hide() { section.hidden = true; },
    dispose() { section.remove(); },
  };
}
