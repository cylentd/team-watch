import { FILM_COPY } from './film-copy.mjs';
import { draftDetails } from './draft-data.mjs';
import { headshots } from './draft-textures.mjs';
import { FINALE } from './draft-curse.mjs';

/* The numbers beside the scene that the picture cannot show (rules 19 and 20): Golden's draft rank
   against his rank now, and Romo's five best returns with the class total. Every other beat leaves the
   headline and its subline alone with the scene. */
const element = (tag, name, text) => {
  const node = document.createElement(tag);
  node.className = name;
  if (text !== undefined) node.textContent = text;
  return node;
};

function headshot(slug) {
  const image = element('img', 'receipt-face');
  const [first, ...rest] = headshots(slug);   // 256px, falling back to 96px where ff-jarvis has none
  image.alt = ''; image.src = first;
  image.onerror = () => { const next = rest.shift(); if (next) image.src = next; else image.onerror = null; };
  return image;
}

export function makeDetails(draft, overlay) {
  const panel = element('div', 'receipt-details');
  overlay.append(panel);
  const data = draftDetails(draft), copy = FILM_COPY.detail;
  const show = beat => {
    panel.replaceChildren();
    panel.hidden = !['steal', 'finale'].includes(beat);
    panel.dataset.kind = beat;
    if (beat === 'steal') {
      const pair = element('p', 'receipt-comparison');
      pair.append(element('strong', 'receipt-was', data.steal.price), element('span', 'receipt-arrow', copy.arrow),
        element('strong', 'receipt-now', data.steal.finish));
      panel.append(pair);
    } else if (beat === 'finale') {
      const list = element('ol', 'receipt-returns');
      data.finale.rows.forEach(row => {
        const item = element('li', 'receipt-return');
        item.append(headshot(row.slug), element('strong', 'receipt-player', row.name), element('strong', 'receipt-gain', row.gain));
        list.append(item);
      });
      const total = element('p', 'receipt-total');
      total.append(element('span', 'receipt-total-label', copy.total), element('strong', 'receipt-total-value', data.finale.total));
      // Under the total, the one number that says how good it is: the next-best class in the league.
      const next = element('p', 'receipt-total receipt-next');
      next.append(element('span', 'receipt-total-label', copy.next), element('strong', 'receipt-total-value', data.finale.next));
      panel.append(list, total, next);
    }
  };
  // Romo's rows pop in one per eighth note after his avatar lands, the class total on the next bar line
  // (draft-curse.mjs FINALE); before its moment an entry is not there (rule 17).
  show.update = moment => {
    if (panel.dataset.kind !== 'finale') return;
    const rows = panel.querySelectorAll('.receipt-return');
    rows.forEach((row, index) => row.style.setProperty('--enter', enterAt(moment.headlineAge, FINALE.rows + index * FINALE.rowStep)));
    panel.querySelector('.receipt-total:not(.receipt-next)')?.style.setProperty('--enter', enterAt(moment.headlineAge, FINALE.total));
    panel.querySelector('.receipt-next')?.style.setProperty('--enter', enterAt(moment.headlineAge, FINALE.next));
  };
  return show;
}

/* An entry is 0 until `at` seconds into its beat, then whole `ENTER` later. */
const ENTER = .12;
export const enterAt = (age, at) => Math.min(1, Math.max(0, (age - at + ENTER) / ENTER));
