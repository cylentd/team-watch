import { FILM_COPY } from './film-copy.mjs';

/* Chapter 1's contract with edition.json (written by design/midseason_draft.py) and the words it fills.
   Pure, so Node tests it. A draft block missing a field the film reads fails here, not mid-frame. */
const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'DEF'];
const BEATS = ['steal', 'traded', 'sleeper', 'curse', 'injury'];
const TEAMS = 12, ROUNDS = 14;
const MINUS = '−';   // a true minus sign, so -14 never reads as a hyphen

export function checkDraft(draft) {
  const fail = why => { throw new Error(`Invalid draft block: ${why}`); };
  if (!draft || !Number.isInteger(draft.through)) fail('through');
  if (draft.teams?.length !== TEAMS || new Set(draft.teams.map(team => team.column)).size !== TEAMS) fail('teams');
  if (draft.picks?.length !== TEAMS * ROUNDS) fail('picks');
  draft.picks.forEach(pick => {
    if (!Number.isInteger(pick.overall) || !pick.name || !pick.slug || !POSITIONS.includes(pick.pos) ||
        !Number.isInteger(pick.column) || !Number.isInteger(pick.round) || !Array.isArray(pick.weeks)) fail(`pick ${pick.overall}`);
  });
  const picks = new Map(draft.picks.map(pick => [pick.overall, pick]));
  BEATS.forEach(beat => { if (!picks.has(draft.beats?.[beat]?.overall)) fail(beat); });
  ['traded', 'curse'].forEach(beat => { if (!draft.beats[beat].path?.length) fail(`${beat} path`); });
  if (!draft.beats.traded.path.some(step => step.kind === 'trade')) fail('traded trade step');
  if (!draft.beats.injury.injury?.status) fail('injury status');
  if (!draft.teams.some(team => team.id === draft.beats.finale?.team)) fail('finale team');
  return draft;
}

export const fill = (template, values) => template.replace(/\{(\w+)\}/g, (_, key) => {
  if (!(key in values)) throw new Error(`Draft Receipts copy needs {${key}}`);
  return values[key];
});

const signed = value => (value > 0 ? `+${value}` : value < 0 ? `${MINUS}${-value}` : '0');
const surname = name => name.split(' ').filter(part => !FILM_COPY.suffixes.includes(part)).at(-1);
/* A card's name: first initial and surname ("C. Hubbard"); a first name already in initials stays
   ("A.J. Brown"), a one-word name is a defense ("Rams"), and a suffix is dropped. */
export function cardName(name) {
  const [first, ...rest] = name.split(' ').filter(part => !FILM_COPY.suffixes.includes(part));
  if (!rest.length) return first;
  return `${first.includes('.') ? first : `${first[0]}.`} ${rest.join(' ')}`;
}
const short = id => FILM_COPY.team[id];
const possessive = id => `${short(id)}${short(id).endsWith('s') ? '’' : '’s'}`;

/* Token values for each beat's headline and subline. */
export function receiptValues(draft) {
  const picks = new Map(draft.picks.map(pick => [pick.overall, pick]));
  const pick = beat => picks.get(draft.beats[beat].overall);
  const trade = draft.beats.traded.path.find(step => step.kind === 'trade');
  const curse = draft.beats.curse.path, last = curse.at(-1);
  const ranked = [...draft.teams].sort((a, b) => b.value - a.value);
  const finale = draft.teams.find(team => team.id === draft.beats.finale.team);
  const injured = pick('injury');
  const starts = draft.beats.traded.path.filter(step => step.kind === 'start' && step.team === trade.team);
  const startPoints = starts.flatMap(step => step.points ?? []);
  return {
    board: {through: draft.through},
    steal: {...pick('steal'), smashWord: FILM_COPY.numbers[pick('steal').smash]},
    traded: {...pick('traded'), from: possessive(trade.from), to: possessive(trade.team),
      starts: startPoints.length, startsWord: FILM_COPY.numbers[startPoints.length],
      startPoints: startPoints.map(points => points.toFixed(1)).join(' / ')},
    sleeper: pick('sleeper'),
    curse: {...pick('curse'), surname: surname(pick('curse').name),
      moves: curse.filter(step => step.kind === 'add' || step.kind === 'drop').length,
      points: (last.points?.at(-1) ?? 0).toFixed(1), week: last.weeks?.at(-1) ?? draft.through},
    injury: {...injured, gamesWord: FILM_COPY.numbers[injured.games] ?? injured.games},
    finale: {team: short(finale.id), value: signed(finale.value), next: signed(ranked.find(team => team.id !== finale.id).value)},
  };
}

export function receipts(draft) {
  const values = receiptValues(draft);
  return Object.fromEntries(Object.keys(FILM_COPY.headline).map(beat =>
    [beat, {headline: fill(FILM_COPY.headline[beat], values[beat]), sub: fill(FILM_COPY.sub[beat], values[beat]),
      stat: FILM_COPY.stat[beat] ? fill(FILM_COPY.stat[beat], values[beat]) : null}]));
}

export const stationText = entry => fill(FILM_COPY.station[entry.kind], {team: short(entry.team)});

const RETURN_LIMIT = 5;
export const weekMarkers = weeks => weeks.map((tier, index) => ({week: 'W' + (index + 1),
  label: FILM_COPY.week[tier], flame: tier === 'smash', tier}));
const RETURN_POSITIONS = ['QB', 'RB', 'WR', 'TE'];

export function positiveDraftReturns(draft, team) {
  return draft.picks.filter(pick => pick.team === team && RETURN_POSITIONS.includes(pick.pos) &&
    Number.isFinite(pick.value) && pick.value > 0 && Number.isInteger(pick.price) && Number.isInteger(pick.finish))
    .sort((first, second) => second.value - first.value || first.round - second.round || first.overall - second.overall)
    .slice(0, RETURN_LIMIT).map(pick => ({name: cardName(pick.name), slug: pick.slug, round: pick.round,
      comparison: pick.pos + pick.price + ' → ' + pick.pos + pick.finish, gain: signed(pick.value)}));
}

export function draftDetails(draft) {
  const golden = draft.picks.find(pick => pick.overall === draft.beats.steal.overall);
  const team = draft.teams.find(team => team.id === draft.beats.finale.team);
  return {steal: {price: golden.pos + golden.price, finish: golden.pos + golden.finish,
    pick: golden.overall, gain: signed(golden.value)},
    traded: {points: receiptValues(draft).traded.startPoints},
    finale: {rows: positiveDraftReturns(draft, team.id), total: signed(team.value),
      // How good the total is: the best class of any other team (edition.json draft.teams).
      next: signed(Math.max(...draft.teams.filter(other => other.id !== team.id).map(other => other.value)))}};
}
