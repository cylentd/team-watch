import { TRADES_VIEW_DETAIL as TUNING } from './constants-trades.mjs';
import { filmPlan } from './film.mjs';
import { GLINT, glintAmount } from './film-glint.mjs';
import { tradesValues } from './trades-data.mjs';
import { edgeToEdge, railEntry, railPoint, tradesLayout } from './trades-layout.mjs';
import { tradesPose, whipIn } from './trades-motion.mjs';

/* Chapter 2's card: DOM and SVG above the board's canvas, posed from the clock like everything else
   (trades-motion.mjs), so seek, pause and a still draw the same frame. It slides in under the whip's light off
   Romo's board (film.mjs sceneChanges: `across`). Each rail is light, not a line (rule 33): a haze trail and a beam
   that fades in from its source and brightens to the winner's end, where the lead sits on a plate just off the
   winner's silver-rimmed avatar. The sequence has one flare, where the biggest lead's light arrives
   (film-glint.mjs). On a phone the beams fan down from the plates to their source, a soft light above the
   headline that rises from Aura on a trunk the build draws and the hold drops. */
const SVG = 'http://www.w3.org/2000/svg';
const svg = (tag, className) => { const node = document.createElementNS(SVG, tag); if (className) node.setAttribute('class', className); return node; };
const html = (tag, className) => { const node = document.createElement(tag); node.className = className; return node; };
const set = (node, values) => Object.entries(values).forEach(([key, value]) => node.setAttribute(key, value));
const px = value => `${value}px`;
const HALF = .5;          // a rail's middle: the beam's gradient midpoint, and where a drifting light starts
const TEAM_BADGE = .85;   // where a lead Aura wins sits on the rail from the partner's end, clear of his avatar
const DEGREES = 180 / Math.PI;
const WARM_AT = Object.freeze([1.25, 2.05]);   // beat seconds drawn once, unseen, before Play (rule 49): the flare,
                                               // then the stamp's plate
const frame = () => new Promise(resolve => requestAnimationFrame(resolve));

/* The headline with its no-trades record in its own span, so the record takes the positive colour. */
function headline(node, text, record) {
  const at = text.lastIndexOf(record), span = document.createElement('span');
  span.dataset.record = ''; span.textContent = record;
  node.replaceChildren(text.slice(0, at), span, text.slice(at + record.length));
}

/* The rail read from the loser's end (0) to the winner's (1). */
const directed = (rail, winner) => winner === 'partner' ? rail : {x1: rail.x2, y1: rail.y2, x2: rail.x1, y2: rail.y1};

/* The badge's box in px for its anchor (trades-layout.mjs): left of the avatar, under it, or centred on the rail. */
function badgeBox({x, y, side}, width, height) {
  if (side === 'left') return [x - width, y - height / 2, x, y + height / 2];
  if (side === 'below') return [x - width / 2, y, x + width / 2, y + height];
  return [x - width / 2, y - height / 2, x + width / 2, y + height / 2];
}

/* A gradient along a line, in the frame's px: `stops` are [offset, class]. */
function gradient(defs, id, stops) {
  const node = svg('linearGradient'); set(node, {id, gradientUnits: 'userSpaceOnUse'});
  stops.forEach(([offset, className]) => { const stop = svg('stop', className); stop.setAttribute('offset', offset); node.append(stop); });
  defs.append(node);
  return node;
}
const along = (node, from, to) => set(node, {x1: from.x, y1: from.y, x2: to.x, y2: to.y});

/* A four-point star at unit size (film-glint.mjs's shape): a core and two thin rays, each fading to nothing. */
function glintNode() {
  const node = svg('g', 'trades-glint');
  const core = svg('circle'); set(core, {r: 1, fill: 'url(#trades-glint-core)'});
  node.append(core, ...[0, TUNING.glintQuarterTurnDegrees].map(turn => { const ray = svg('ellipse'); set(ray, {rx: 1, ry: GLINT.ray, transform: `rotate(${turn})`, fill: 'url(#trades-glint-ray)'}); return ray; }));
  return node;
}
function poseGlint(node, at, size, age) {
  const amount = glintAmount(age);
  node.style.display = amount > GLINT.gone ? '' : 'none';
  if (amount <= GLINT.gone) return;
  set(node, {transform: `translate(${at.x} ${at.y}) scale(${size / 2 * (.5 + amount)}) rotate(${age * GLINT.turn * DEGREES})`, opacity: amount});
}

export function makeTrades(root, trades, teams) {
  const values = tradesValues(trades), count = values.deals.length;
  const beat = filmPlan().beats.find(entry => entry.id === 'trades');
  const avatar = id => teams.find(team => team.id === id).avatar;
  const card = html('section', 'trades');
  card.dataset.trades = ''; card.hidden = true;
  card.setAttribute('aria-label', values.label);
  const stage = html('div', 'trades-stage');
  const rails = svg('svg', 'trades-rails'); rails.setAttribute('aria-hidden', 'true');
  rails.innerHTML = `<defs><radialGradient id="trades-glow"><stop offset="0" class="trades-glow-core"/>
    <stop offset=".22" class="trades-glow-core"/><stop offset=".45" class="trades-glow-mid"/><stop offset="1" class="trades-glow-edge"/></radialGradient>
    <radialGradient id="trades-pulse"><stop offset="0" class="trades-pulse-core"/><stop offset=".4" class="trades-glow-mid"/>
    <stop offset="1" class="trades-glow-edge"/></radialGradient>
    <mask id="trades-mask" maskUnits="userSpaceOnUse"><rect class="trades-mask-all" x="0" y="0" width="100%" height="100%"/>
    <rect class="trades-mask-head" data-trades-mask/></mask></defs>`;
  const defs = rails.querySelector('defs');
  const group = svg('g', 'trades-rail-group'); group.setAttribute('mask', 'url(#trades-mask)'); rails.append(group);
  const mask = rails.querySelector('[data-trades-mask]');
  // A phone's beam source: a small light with the stem it trails as it rises from Aura.
  const stem = svg('line', 'trades-stem'); stem.setAttribute('stroke', 'url(#trades-stem)');
  const stemPaint = gradient(defs, 'trades-stem', [[0, 'trades-stem-from'], [1, 'trades-stem-to']]);
  const hubGlow = svg('circle', 'trades-light'), hub = svg('circle', 'trades-node');
  group.append(stem);
  // The flare sits over its plate, so it draws in an SVG above the HTML.
  const sparks = svg('svg', 'trades-sparks'); sparks.setAttribute('aria-hidden', 'true');
  sparks.innerHTML = `<defs><radialGradient id="trades-glint-core"><stop offset="0" class="trades-glint-hot"/>
    <stop offset=".45" class="trades-glint-edge"/></radialGradient><radialGradient id="trades-glint-ray">
    <stop offset="0" class="trades-glint-hot"/><stop offset="1" class="trades-glint-edge"/></radialGradient></defs>`;
  const flare = glintNode();
  const biggest = trades.deals.reduce((best, deal, index) => deal.lead > trades.deals[best].lead ? index : best, 0);
  const face = (id) => { const disc = html('div', 'trades-face'), image = html('img', 'trades-face-img');
    image.src = avatar(id); image.alt = ''; disc.append(image); return {disc, image}; };
  const aura = face(values.team);
  aura.disc.classList.add('trades-aura');
  const auraName = html('p', 'trades-name trades-aura-name'); auraName.textContent = values.name;
  const stamp = html('p', 'trades-stamp'); stamp.dataset.tradesStamp = ''; stamp.textContent = values.actual;
  const head = html('h2', 'trades-head'); head.dataset.tradesHead = ''; headline(head, values.headline, values.noTrades);
  const deals = values.deals.map((deal, index) => {
    const parts = {rail: svg('line', 'trades-rail'), glow: svg('line', 'trades-rail-glow'), lit: svg('line', 'trades-rail-lit'),
      drift: svg('circle', 'trades-drift'), light: svg('circle', 'trades-light'),
      name: html('p', 'trades-name'), badge: html('span', 'trades-badge'), ...(() => { const {disc, image} = face(deal.partner); return {face: disc, image}; })()};
    parts.haze = gradient(defs, `trades-haze-${index}`, [[0, 'trades-haze-from'], [HALF, 'trades-haze-mid'], [1, 'trades-haze-to']]);
    parts.beam = gradient(defs, `trades-beam-${index}`, [[0, 'trades-beam-from'], [HALF, 'trades-beam-mid'], [1, 'trades-beam-to']]);
    parts.rail.setAttribute('stroke', `url(#trades-haze-${index})`);
    [parts.glow, parts.lit].forEach(line => line.setAttribute('stroke', `url(#trades-beam-${index})`));
    group.append(parts.rail, parts.glow, parts.lit, parts.drift, parts.light);
    parts.name.textContent = deal.name; parts.badge.textContent = deal.label;
    stage.append(parts.face, parts.name, parts.badge);
    return {...deal, ...parts};
  });
  group.append(hubGlow, hub);
  sparks.append(flare);
  stage.prepend(rails);
  stage.append(aura.disc, auraName, stamp, head, sparks);
  card.append(stage);
  root.querySelector('[data-receipt]').after(card);
  let layout = null, size = '';

  function sizes(view) {
    [['--trades-name-size', view.name], ['--trades-badge-height', view.badge.height], ['--trades-badge-font', view.badge.font],
      ['--trades-stamp-size', view.stamp.size], ['--trades-haze', view.beam.haze], ['--trades-glow', view.beam.glow],
      ['--trades-core', view.beam.core]].forEach(([key, value]) => card.style.setProperty(key, px(value)));
    const box = view.headline;
    Object.assign(head.style, {left: px(box.left), width: px(box.width), textAlign: box.align,
      top: box.top === undefined ? 'auto' : px(box.top), bottom: box.bottom === undefined ? 'auto' : px(view.height - box.bottom)});
  }

  // Every position comes from the layout (trades-layout.mjs), given what only the browser can measure: the
  // headline's height and each partner's widest label. The headline's mask is measured from its own box.
  function place() {
    const width = root.clientWidth, height = root.clientHeight;
    sizes(tradesLayout(width, height, count));
    const items = deals.map(deal => Math.max(deal.name.offsetWidth, deal.badge.offsetWidth));
    layout = tradesLayout(width, height, count, {headHeight: head.offsetHeight, items});
    sizes(layout);
    card.dataset.layout = layout.phone ? 'phone' : 'desk';
    [rails, sparks].forEach(node => set(node, {viewBox: `0 0 ${width} ${height}`}));
    const circle = (node, {x, y, r}) => {
      Object.assign(node.style, {left: px(x), top: px(y), width: px(2 * r), height: px(2 * r)});
      node.style.setProperty('--trades-rim-size', px(r * layout.rim));
    };
    circle(aura.disc, layout.aura);
    Object.assign(auraName.style, {left: px(layout.auraName.x), top: px(layout.auraName.top)});
    Object.assign(stamp.style, {left: px(layout.stamp.x), top: px(layout.stamp.top)});
    [stem, hub, hubGlow].forEach(node => { node.style.display = layout.node ? '' : 'none'; });
    deals.forEach((deal, index) => {
      const partner = layout.partners[index], rail = layout.rails[index];
      circle(deal.face, partner);
      Object.assign(deal.name.style, {left: px(partner.name.x), top: partner.name.top === undefined ? px(partner.name.bottom) : px(partner.name.top)});
      const path = directed(rail, deal.winner);
      const anchor = deal.winner === 'partner' ? partner.badge : {...railPoint(path, TEAM_BADGE), side: 'centre'};
      deal.badge.dataset.side = anchor.side;
      Object.assign(deal.badge.style, {left: px(anchor.x), top: px(anchor.y)});
      deal.entry = railEntry(path, badgeBox(anchor, deal.badge.offsetWidth, deal.badge.offsetHeight));
      const length = Math.hypot(rail.x2 - rail.x1, rail.y2 - rail.y1);
      deal.driftEnd = Math.max(HALF, deal.entry - layout.light / 2 / length);   // a drifting light never reaches the plate
    });
    const pad = layout.maskPad;
    set(mask, {x: head.offsetLeft - pad, y: head.offsetTop - pad, width: head.offsetWidth + 2 * pad, height: head.offsetHeight + 2 * pad});
  }
  document.fonts?.ready.then(() => { size = ''; });   // the headline's and names' boxes change once their face loads

  /* The rails this frame: fixed on a desktop; on a phone they fan from their source as it rises from Aura's top. */
  function railsAt(rise) {
    if (!layout.node) return {rails: layout.rails, source: null};
    const from = layout.aura.y - layout.aura.r, source = {...layout.node, y: from + (layout.node.y - from) * rise};
    return {rails: layout.partners.map(partner => edgeToEdge(source, partner)), source, from};
  }

  function update(moment) {
    const entering = moment.transition?.to === 'trades';
    const leaving = moment.transition?.to === 'waiver-claim';
    card.hidden = moment.chapter !== 'trades' && !entering && !leaving;
    if (card.hidden) return;
    const key = `${root.clientWidth}x${root.clientHeight}`;
    if (key !== size) { size = key; place(); }
    const seconds = moment.chapter === 'trades' ? moment.beatProgress * beat.duration / beat.pace : leaving ? beat.duration / beat.pace : 0;
    const pose = tradesPose(seconds, count), whip = whipIn(entering ? moment.transition : null);
    card.style.setProperty('--trades-reveal', whip.reveal);
    card.style.setProperty('--trades-slide', whip.slide);
    card.style.setProperty('--trades-push', 1 + layout.push * pose.push);
    card.style.setProperty('--trades-stamp', pose.stamp);
    card.style.setProperty('--trades-stamp-scale', pose.stampScale);
    card.style.setProperty('--trades-breathe', pose.breathe);
    card.style.setProperty('--headline', pose.headline);
    mask.style.fillOpacity = pose.headline;
    const now = railsAt(pose.rise);
    if (now.source) {
      const top = {x: now.source.x, y: now.from};
      along(stem, top, now.source); along(stemPaint, top, now.source);
      stem.style.opacity = pose.stem * pose.rise;
      set(hub, {cx: now.source.x, cy: now.source.y, r: now.source.r, opacity: pose.rise});
      set(hubGlow, {cx: now.source.x, cy: now.source.y, r: layout.junction / 2 * pose.breathe, opacity: pose.rise});
    }
    deals.forEach((deal, index) => {
      const rail = now.rails[index], path = directed(rail, deal.winner);
      along(deal.rail, railPoint(rail, 0), railPoint(rail, pose.rails));
      along(deal.haze, railPoint(path, 0), railPoint(path, 1));
      along(deal.beam, railPoint(path, 0), railPoint(path, 1));
      // The light runs from the loser's end to the plate's edge, the beam filling in behind it: its gradient fades it
      // in from the source, so it has no visible start.
      const travelled = deal.entry * pose.travel, at = railPoint(path, travelled);
      [deal.glow, deal.lit].forEach(line => { along(line, railPoint(path, 0), at); line.setAttribute('opacity', travelled > 0 ? 1 : 0); });
      // It hands over to the lead as the plate blooms where it stopped; the biggest lead's arrival is the one flare.
      set(deal.light, {cx: at.x, cy: at.y, r: layout.light / 2 * pose.breathe, opacity: pose.rails * (1 - pose.leads)});
      if (index === biggest) poseGlint(flare, railPoint(path, deal.entry), layout.glint, pose.glint);
      const drift = pose.drift?.[index];
      const shimmer = railPoint(path, HALF + (deal.driftEnd - HALF) * (drift?.along ?? 0));
      set(deal.drift, {cx: shimmer.x, cy: shimmer.y, r: layout.light / 2, opacity: drift?.glow ?? 0});
      deal.badge.style.setProperty('--trades-lead', pose.leads);
    });
  }

  // Rule 49: the avatars decode, then the card draws its flare and plates once, unseen, before Play is enabled.
  async function warm() {
    card.dataset.warm = '';
    for (const at of WARM_AT) { update({chapter: 'trades', beatProgress: at * beat.pace / beat.duration}); await frame(); await frame(); }
    delete card.dataset.warm; card.hidden = true;
  }
  const images = [aura.image, ...deals.map(deal => deal.image)];
  const ready = Promise.all(images.map(image => image.decode().catch(() => {}))).then(warm);
  return {update, ready};
}
