import { FILM_COPY } from './film-copy.mjs';
import { fill } from './draft-data.mjs';

/* Chapter 2's contract with edition.json's trades block (written by design/midseason_trades.py) and the words it
   fills. Pure, so Node tests it. A block missing a field the card reads fails here, at load, not mid-frame. */
const RECORD = /^\d+-\d+(-\d+)?$/;   // wins-losses, with ties when there are any
const MOST_DEALS = 4;               // the card's rails fan to at most this many partners and stay readable
const SAME = .05;                   // a lead is printed to 0.1, so the block's Week 8 row agrees within half of that

/* A deal's lead, signed from the partner's side as the block's weekly rows are: positive when the partner leads. */
export const signedLead = deal => deal.leader === deal.partner ? deal.lead : -deal.lead;

export function checkTrades(trades, teams) {
  const fail = why => { throw new Error(`Invalid trades block: ${why}`); };
  const ids = new Set((teams ?? []).map(team => team.id));
  if (!trades || !Number.isInteger(trades.through)) fail('through');
  if (!ids.has(trades.team) || !FILM_COPY.team[trades.team]) fail('team');
  if (!RECORD.test(trades.record?.actual ?? '') || !RECORD.test(trades.record?.noTrades ?? '')) fail('record');
  if (!Array.isArray(trades.deals) || !trades.deals.length || trades.deals.length > MOST_DEALS) fail('deals');
  trades.deals.forEach((deal, index) => {
    const name = `deal ${index + 1}`;
    if (!ids.has(deal?.partner) || deal.partner === trades.team || !FILM_COPY.team[deal.partner]) fail(`${name} partner`);
    if (![deal.partner, trades.team].includes(deal.leader)) fail(`${name} leader`);
    if (!Number.isFinite(deal.lead) || deal.lead < 0) fail(`${name} lead`);
    if (!deal.sent?.length || !deal.got?.length) fail(`${name} players`);
    const last = Array.isArray(deal.weekly) ? deal.weekly.at(-1) : null;
    if (last?.week !== trades.through || Math.abs(last.lead - signedLead(deal)) > SAME)
      fail(`${name} Week ${trades.through} row`);
  });
  return trades;
}

/* What the card draws: Aura's name and record both ways, the headline, and for each deal in the block's order its
   partner, its lead's label and who wins it (`partner` or `team`): the winner's half of the rail is the bright one
   and the lead sits at the winner's end. The rail never encodes the lead's size; the number does. */
export function tradesValues(trades) {
  const team = FILM_COPY.team[trades.team], {actual, noTrades} = trades.record;
  return {team: trades.team, name: team, actual, noTrades,
    headline: fill(FILM_COPY.trades.headline, {team, noTrades}),
    label: fill(FILM_COPY.trades.label, {team, through: trades.through}),
    deals: trades.deals.map(deal => ({partner: deal.partner, name: FILM_COPY.team[deal.partner],
      label: fill(FILM_COPY.trades.lead, {lead: deal.lead.toFixed(1)}),
      winner: deal.leader === deal.partner ? 'partner' : 'team'}))};
}
