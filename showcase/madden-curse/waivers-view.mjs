import { WAIVERS_VIEW_DETAIL as TUNING } from './constants-waivers.mjs';
import { OPENING } from './constants.mjs';
import { filmPlan } from './film.mjs';
import { waiversPose } from './waivers-motion.mjs';
import { checkPickups, pickupValues } from './waivers-data.mjs';
import { whipIn } from './trades-motion.mjs';

/* Chapter 3, Best pickups (docs/madden-film-chapter3.md): three broadcast cards over the board's canvas, posed from
   the clock (waivers-motion.mjs) so seek, pause and a still draw the same frame. It slides in under the whip's light
   off the trade tracker. A desktop reads #3, #2, #1 left to right, #1 the largest; a phone stacks #1 on top with
   #2 and #3 side by side under him (data-layout, Chapter 2's phone width). Every word and number comes from
   edition.json's pickups block through waivers-data.mjs. */
const WARM_AT = Object.freeze([3, 7.5]);   // chapter seconds drawn once, unseen, before Play (rule 49): the pair, then the hold
const frame = () => new Promise(resolve => requestAnimationFrame(resolve));
const PICKUP_FRAME = Object.freeze({deskAspect: 4 / 3, deskUnits: 160});
const element = (tag, className, data, text) => {
  const node = document.createElement(tag);
  node.className = className;
  if (data) node.setAttribute('data-' + data, '');
  if (text !== undefined) node.textContent = text;
  return node;
};
const image = (className, src, data) => { const node = element('img', className, data); node.alt = ''; node.src = src; return node; };

function buildWeeks(weeks) {
  const strip = element('div', 'pickup-weeks', 'waivers-weeks');
  const cells = weeks.map(week => {
    const cell = element('div', 'pickup-week', 'waivers-week');
    cell.append(element('span', 'pickup-week-label', 'week-label', week.label),
      element('span', 'pickup-week-rank', 'week-rank', week.rank));
    strip.append(cell); return cell;
  });
  return {strip, cells};
}

function buildCard(card) {
  const node = element('article', 'pickup');
  node.dataset.pickup = card.pickup;
  const face = element('div', 'pickup-face');
  const portrait = image('pickup-portrait', card.portrait, 'pickup-face');
  face.append(portrait);
  const rank = element('p', 'pickup-rank', 'pickup-rank', card.rank);
  const name = element('p', 'pickup-name', 'pickup-name', card.name);
  const team = element('p', 'pickup-team');
  const badge = image('pickup-badge', card.badge, 'pickup-badge');
  team.append(badge, element('span', 'pickup-team-name', 'pickup-team', card.team));
  const gain = element('p', 'pickup-gain');
  gain.append(element('span', 'pickup-added', 'pickup-added', card.added));
  if (card.starts) gain.append(element('span', 'pickup-starts', 'pickup-starts', card.starts));
  node.append(face, rank, name, team, gain);
  const weeks = card.pickup === 1 ? buildWeeks(card.weeks) : null;
  if (weeks) node.append(weeks.strip);
  return {node, weeks, images: [portrait, badge]};
}

function build(root, values) {
  const section = element('section', 'waivers', 'waivers');
  section.hidden = true; section.setAttribute('aria-label', values.label);
  const stage = element('div', 'waivers-stage');
  const title = element('div', 'waivers-title');
  title.append(element('h2', 'waivers-head', 'waivers-head', values.head), element('p', 'waivers-sub', 'waivers-sub', values.sub));
  const deck = element('div', 'waivers-cards');
  const cards = values.cards.map(buildCard);
  deck.append(...cards.map(card => card.node));
  stage.append(title, deck);
  section.append(stage);
  root.append(section);
  const top = cards.find(card => card.weeks);
  return {section, cards, cells: top.weeks.cells, images: cards.flatMap(card => card.images)};
}

/* Builds once the edition's pickups have loaded (`receipt` names them, waivers-receipts.json); `update` draws
   nothing until then, and `ready` settles after every portrait, badge and face is decoded and drawn once. */
export function makeWaivers(root, receipt, teams) {
  const beat = filmPlan().beats.find(entry => entry.id === 'waiver-claim');
  let parts = null;

  function update(moment, reduced = false) {
    if (!parts) return;
    const {section, cards, cells} = parts;
    const entering = moment.transition?.to === 'waiver-claim';
    const exiting = moment.transition?.to === 'lineup-defense';
    section.hidden = moment.chapter !== 'waivers' && !entering && !exiting;
    if (section.hidden) return;
    const seconds = moment.chapter === 'waivers' || exiting ? moment.elapsed - beat.start : 0;
    const pose = waiversPose(seconds, reduced, cells.length), whip = whipIn(entering ? moment.transition : null);
    const phone = root.clientWidth < OPENING.mobileWidth || root.clientWidth / root.clientHeight < PICKUP_FRAME.deskAspect;
    section.dataset.layout = phone ? 'phone' : 'desk';
    section.dataset.beat = seconds >= beat.duration ? 'waiver-starts' : 'waiver-claim';
    const set = (node, name, value) => node.style.setProperty('--' + name, value);
    const unit = phone ? root.clientHeight / TUNING.viewportPercent : Math.min(root.clientHeight / TUNING.viewportPercent, root.clientWidth / PICKUP_FRAME.deskUnits);
    set(section, 'waivers-unit', unit + 'px'); set(section, 'pickups-weeks', cells.length);
    set(section, 'waivers-reveal', whip.reveal); set(section, 'waivers-slide', whip.slide);
    set(section, 'waivers-head-in', pose.head); set(section, 'waivers-sub-in', pose.sub);
    set(section, 'waivers-room', pose.room); set(section, 'waivers-push', pose.push); set(section, 'waivers-drift', pose.drift);
    // A card or week not yet landed keeps its place, unseen, so nothing reflows when it arrives.
    const unseen = (node, amount) => { node.style.visibility = amount > 0 ? '' : 'hidden'; };
    cards.forEach((card, index) => {
      unseen(card.node, pose.cards[index]);
      set(card.node, 'pickup-in', pose.cards[index]);
      set(card.node, 'pickup-glow', pose.glow[index]);
      set(card.node, 'pickup-dim', card.weeks ? 0 : pose.dim);
    });
    cells.forEach((cell, index) => { unseen(cell, pose.weeks[index]); set(cell, 'pickup-week-in', pose.weeks[index]); });
    unseen(cells[0].parentElement, Math.max(...pose.weeks));
  }

  async function warm() {
    parts.section.dataset.warm = '';
    for (const seconds of WARM_AT) { update({chapter: 'waivers', elapsed: beat.start + seconds}); await frame(); await frame(); }
    delete parts.section.dataset.warm; parts.section.hidden = true;
  }

  async function load() {
    const response = await fetch(new URL(receipt.edition, import.meta.url));
    if (!response.ok) throw new Error('Edition unavailable for Chapter 3: ' + response.status);
    const values = pickupValues(checkPickups((await response.json())[receipt.key], teams));
    parts = build(root, values);
    const fonts = Promise.all([document.fonts.load('900 24px Shoulders'), document.fonts.load('24px Archivo')]);
    await Promise.all([...parts.images.map(node => node.decode()), fonts]);
    await warm();
  }
  const ready = load();
  return {update, ready, dispose: () => parts?.section.remove()};
}
