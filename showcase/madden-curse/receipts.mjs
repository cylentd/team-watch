import { FILM_COPY } from './film-copy.mjs';
import { receipts } from './draft-data.mjs';
import { clamp } from './timeline.mjs';
import { makeDetails } from './receipt-details.mjs';
import { RECEIPT_ENTER, receiptEntrance } from './receipt-entrance.mjs';

/* The headline over each beat. It stamps in with the beat's motion (film.mjs `headlineAge`); its stat
   waits in place, invisible, and stamps in with the card's own stamp or flip (`statAge`). */


/* Write `text` into `node`, wrapping its stat in a span that holds its place until it lands. */
function write(node, text, stat) {
  node.hidden = !text;   // a beat with no subline draws no empty rule
  const at = stat ? text.indexOf(stat) : -1;
  if (at < 0) { node.textContent = text; return false; }
  const span = document.createElement('span');
  span.dataset.stat = ''; span.textContent = stat;
  node.replaceChildren(text.slice(0, at), span, text.slice(at + stat.length));
  return true;
}

export function makeReceipts(draft) {
  const overlay = document.querySelector('[data-receipt]');
  const room = overlay.closest('[data-room]');
  const words = receipts(draft);
  const details = makeDetails(draft, overlay);
  overlay.querySelector('[data-receipt-chapter]').textContent = FILM_COPY.chapter;
  let shown = null;
  return function update(moment) {
    const beat = moment.chapter === 'draft' ? moment.headline : null;
    overlay.hidden = !beat;
    if (!beat) { shown = null; room.style.setProperty('--third', 0); return; }
    if (beat !== shown) {
      const {headline, sub, stat} = words[beat];
      const inHead = write(overlay.querySelector('[data-receipt-head]'), headline, stat);
      write(overlay.querySelector('[data-receipt-sub]'), sub, inHead ? null : stat);
      overlay.dataset.beat = beat; shown = beat;
      details(beat);
    }
    details.update(moment);
    const entrance = receiptEntrance(beat, moment.headlineAge);
    Object.entries(entrance).forEach(([key, value]) => overlay.style.setProperty(`--${key}`, value));
    room.style.setProperty('--third', entrance.rule);
    overlay.style.setProperty('--stat', clamp(moment.statAge / RECEIPT_ENTER.stat));
  };
}
