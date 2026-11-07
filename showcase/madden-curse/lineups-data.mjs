import { EDITION } from "./constants-lineups.mjs";
import { LINEUPS_COPY } from './lineups-copy.mjs';

const TE_STARTERS = Object.freeze({5: 'Harold Fannin Jr.', 7: 'Hunter Henry', 8: 'Hunter Henry'});
const TE_BENCH = Object.freeze({5: 'Hunter Henry', 7: 'Harold Fannin Jr.', 8: 'Harold Fannin Jr.'});
const invalid = reason => { throw new Error('Invalid lineup receipts: ' + reason); };
const numeric = value => typeof value === 'number' && Number.isFinite(value);

function player(value, slot) {
  if (!value || typeof value.name !== 'string' || !value.name.trim() || value.position !== slot ||
      typeof value.nfl !== 'string' || !numeric(value.points) || !numeric(value.projection)) invalid('player');
}

function rows(values, weeks, team, slot) {
  if (!Array.isArray(values) || values.length !== weeks.length) invalid('week count');
  values.forEach((row, index) => {
    if (!row || row.week !== weeks[index] || row.team !== team || row.slot !== slot ||
        !numeric(row.points) || !numeric(row.opponent)) invalid('week, team, slot or result');
    player(row.starter, slot);
    if (slot === 'TE') {
      player(row.bench, slot);
      if (row.starter.name !== TE_STARTERS[row.week] || row.bench.name !== TE_BENCH[row.week]) invalid('TE assignment');
    }
  });
}

export function checkLineups(value) {
  if (!value || value.season !== EDITION.season || value.league !== EDITION.league ||
      value.through !== EDITION.through) invalid('edition');
  rows(value.defense, EDITION.defenseWeeks, EDITION.defenseTeam, 'DEF');
  rows(value.tightends, EDITION.tightendWeeks, EDITION.tightendTeam, 'TE');
  return value;
}

const label = week => LINEUPS_COPY.week.replace('{week}', week);
const score = points => String(points).replace('-', '−');
const te = value => ({...LINEUPS_COPY.players[value.name], score: value.points.toFixed(2)});

export function lineupValues(receipts) {
  const negative = receipts.defense.filter(row => row.starter.points < 0);
  const negativeWins = negative.filter(row => row.points > row.opponent).length;
  const outcome = negativeWins === negative.length ? LINEUPS_COPY.outcomeBoth :
    negativeWins === 1 ? LINEUPS_COPY.outcomeOne : LINEUPS_COPY.outcomeNone;
  return {defenseTeam: EDITION.defenseTeam, tightendTeam: EDITION.tightendTeam,
    defenseTotal: receipts.defense.reduce((total, row) => total + row.starter.points, 0), negativeWins, outcome,
    defense: receipts.defense.filter(row => EDITION.shownDefense.includes(row.week)).map(row =>
      ({week: label(row.week), name: row.starter.name, emblem: row.starter.nfl, score: score(row.starter.points), negative: row.starter.points < 0, won: row.points > row.opponent, margin: Math.abs(row.points - row.opponent).toFixed(2)})),   // ~~tokens~~: a negative score ejects its shield (2026-11-05)
    tightends: receipts.tightends.filter(row => EDITION.shownTightends.includes(row.week)).map(row =>
      ({week: label(row.week), starter: te(row.starter), bench: te(row.bench)}))};
}
