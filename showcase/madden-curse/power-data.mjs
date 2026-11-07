import { EDITION } from "./constants-power.mjs";
// Chapter 5, Midseason power rankings: the checked receipts (design/midseason_power.py) and the numbers the
// view reads from them. Numbers and names only; every word on screen lives in the copy file.
             // real games played through the edition's last week
const UPPER_PLACES = 6;   // the phone's first group; the rest are the second
const LEADERS = 4;        // the film's top four
const invalid = reason => { throw new Error('Invalid power receipts: ' + reason); };
const numeric = value => typeof value === 'number' && Number.isFinite(value);
const integer = value => Number.isInteger(value);
const places = (teams, key) => new Set(teams.map(team => team[key]));
const share = counts => counts.w + counts.t / 2;

function tally(counts, total, label) {
  if (!counts || !['w', 'l', 't'].every(key => integer(counts[key]) && counts[key] >= 0)) invalid(label + ' counts');
  if (counts.w + counts.l + counts.t !== total) invalid(label + ' total');
}

function team(value) {
  if (!value || !integer(value.id) || typeof value.name !== 'string' || !value.name.trim()) invalid('team');
  if (!numeric(value.points) || !numeric(value.luck)) invalid('points or luck');
  if (!integer(value.power) || !integer(value.standing)) invalid('place');
  tally(value.record, EDITION.games, 'record');
  tally(value.allPlay, EDITION.comparisons, 'all-play');
}

export function checkPower(value) {
  if (!value || value.season !== EDITION.season || value.league !== EDITION.league ||
      value.through !== EDITION.through || value.comparisons !== EDITION.comparisons) invalid('edition');
  const teams = value.teams;
  if (!Array.isArray(teams) || teams.length !== EDITION.teams) invalid('team count');
  teams.forEach(team);
  for (const key of ['id', 'power', 'standing']) {
    const found = places(teams, key);
    for (let place = 1; place <= EDITION.teams; place += 1) if (!found.has(place)) invalid(key + ' places');
  }
  teams.forEach((entry, index) => { if (entry.power !== index + 1) invalid('power order'); });
  teams.slice(1).forEach((entry, index) => {
    const before = teams[index];
    if (share(entry.allPlay) > share(before.allPlay) ||
        (share(entry.allPlay) === share(before.allPlay) && entry.points > before.points)) invalid('power order');
  });
  return value;
}

const text = counts => counts.t > 0 ? `${counts.w}-${counts.l}-${counts.t}` : `${counts.w}-${counts.l}`;
const row = entry => ({id: entry.id, name: entry.name, power: entry.power, standing: entry.standing,
  record: text(entry.record), allPlay: text(entry.allPlay), points: entry.points});

export function powerValues(receipts) {
  const order = receipts.teams.map(row);
  const gap = entry => entry.standing - entry.power;
  const [feature] = [...order].sort((a, b) => gap(b) - gap(a) || a.power - b.power);
  const [first, second] = receipts.teams;
  return {order, upper: order.slice(0, UPPER_PLACES), lower: order.slice(UPPER_PLACES),
    four: order.slice(0, LEADERS), feature: {...feature, gap: gap(feature)},
    apart: first.allPlay.w - second.allPlay.w};
}
