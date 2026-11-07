import { WAIVERS_DATA_DETAIL as TUNING } from './constants-waivers.mjs';
import { WAIVERS_COPY as COPY } from './waivers-copy.mjs';
import { FILM_COPY } from './film-copy.mjs';
import { cardName, fill } from './draft-data.mjs';

/* Chapter 3's data boundary. edition.json's `pickups` block (design/midseason_pickups.py) is the only source of a
   number on screen: this checks its shape where it enters and fails loudly, so a bad edition breaks the film's load,
   not a frame in the middle of the chapter. waivers-receipts.json only says where that block is. */
export const PICKUPS_CONTRACT = Object.freeze({
  edition: './edition.json', key: 'pickups',
  through: TUNING.through,                 // the Week 8 edition
  count: TUNING.pickupCount,                   // the storyboard's three cards, #3, #2, #1
  digits: 1,                  // points print to a tenth, as the edition rounds them
  via: Object.freeze(['waiver', 'fa']),
  position: /^(QB|RB|WR|TE|K|DEF)$/, slug: /^[a-z0-9-]+$/, // magic-ok: regex character range, not numeric tuning
  portrait: slug => `../../heads/lg/${slug}.webp`,   // the 256px cut (rule 24)
});

const invalid = reason => { throw new TypeError('Invalid pickups: ' + reason); };
const number = value => typeof value === 'number' && Number.isFinite(value);
const whole = value => Number.isInteger(value) && value > 0;

/* The pointer app.mjs fetches (waivers-receipts.json): it must name the edition's pickups block. */
export function checkWaivers(receipt) {
  const rule = PICKUPS_CONTRACT;
  if (receipt?.edition !== rule.edition || receipt?.key !== rule.key || receipt?.throughWeek !== rule.through) invalid('receipt');
  return receipt;
}

function checkWeeks(entry, through) {
  const weeks = entry.weeks;
  if (!Array.isArray(weeks) || weeks.length !== entry.starts) invalid(`${entry.slug} weeks do not match his starts`);
  weeks.forEach((row, index) => {
    if (!whole(row?.week) || row.week > through || (index && row.week <= weeks[index - 1].week)) invalid(`${entry.slug} week order`);
    if (!number(row.pts) || !(row.rank === null || whole(row.rank))) invalid(`${entry.slug} week ${row.week} score or rank`);
  });
}

export function checkPickups(pickups, teams) {
  const rule = PICKUPS_CONTRACT;
  if (pickups?.through !== rule.through || !Array.isArray(pickups.top) || pickups.top.length !== rule.count) invalid('edition or count');
  const top = pickups.top.map((entry, index) => {
    if (entry?.rank !== index + 1) invalid('rank order');
    if (typeof entry.name !== 'string' || !entry.name.trim() || !rule.slug.test(entry.slug ?? '') || !rule.position.test(entry.pos ?? ''))
      invalid(`player ${index + 1}`);
    if (!rule.via.includes(entry.via)) invalid(`${entry.slug} acquisition`);
    const team = teams.find(row => row.id === entry.team);
    if (!team?.avatar || !FILM_COPY.team[entry.team]) invalid(`${entry.slug} team`);
    if (!number(entry.added) || !whole(entry.starts)) invalid(`${entry.slug} points or starts`);
    checkWeeks(entry, rule.through);
    return {...entry, avatar: team.avatar};
  });
  return {through: pickups.through, top};
}

const tenth = value => value.toFixed(PICKUPS_CONTRACT.digits);

/* Everything the cards print, #3 first (the order they land, left to right on a desktop). The top pickup's strip
   carries his starts, so his card prints no starts line (rule 26). Wins swung are not shown (storyboard). */
export function pickupValues(checked) {
  const top = checked.top.length;
  const cards = [...checked.top].reverse().map(entry => ({
    pickup: entry.rank,
    rank: fill(COPY.rank, {rank: entry.rank}),
    name: cardName(entry.name),
    team: FILM_COPY.team[entry.team],
    added: fill(COPY.added, {added: tenth(entry.added)}),
    starts: entry.rank === 1 ? null : fill(COPY.starts, {starts: entry.starts}),
    portrait: PICKUPS_CONTRACT.portrait(entry.slug),
    badge: entry.avatar,
    weeks: entry.weeks.map(row => ({
      label: fill(COPY.week, {week: row.week}),
      points: tenth(row.pts),
      rank: row.rank === null ? COPY.out : fill(COPY.weekRank, {pos: entry.pos, rank: row.rank}),
    })),
  }));
  return {head: COPY.head, sub: COPY.sub, label: fill(COPY.label, {through: checked.through}), count: top, cards};
}
