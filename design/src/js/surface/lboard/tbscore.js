/* ============================== LEAGUE > TEAMS: THE TRADE SCORER ==============================
   2026-10-05. A pure port of ff-jarvis's scoring rule for a trade, so the builder's Edit can score a package the
   reader makes. The SOURCE OF TRUTH is the contract: trade_offers.json carries, per league, `lineup` (with `ir`),
   `values` (with `keep`, `ir_ok`, `protect`) and `other`, per offer `ir_moves` and `drop`, and in its top-level
   `rules` the rule itself in words (`rules.scoring`, `rules.drop`). This file ports those two texts, and only those;
   offers.js re-scores every offer it loads against this port and shuts Edit when one differs (fail closed), so a rule
   ff-jarvis changes cannot quietly drift from the page.

   As ported (the drop rule of 2026-10-05; if `rules` says otherwise, `rules` wins):
     h(x)       integer hundredths, round(100 * x), of a proj or a floor.
     starters   candidates are the roster's players with ir false, ordered by proj descending, then seen descending,
                then name ascending. For each position of lineup.slots, take the first n unused candidates of it; then,
                for each entry of lineup.flex in order, the first n unused candidates whose pos is in the entry's list.
     slot       max(h(proj), bar); bar is h(floor[pos]) for a fixed slot and the largest h(floor[p]) over the entry's
                positions for a flex slot. A slot with nobody left is worth its bar. A floored starter still starts.
     gain       tenths(lineup(R2) - lineup(R1)): R1 is the owner's values, R2 is R1 minus send plus get (the partner's
                players matched by name, keeping their ir flag) minus the IR moves and the drops; tenths(d) is d / 10
                rounded half away from zero, then / 10.
     IR moves   over = (the players of R2 with ir false) + other[owner] - cap; free = lineup.ir - (players of R2 with
                ir true). While over > 0 and a slot is free, the players with ir false and ir_ok true move to IR,
                highest keep first, then higher seen, then name; no more than over. A moved player counts as ir: out of
                the cap, never a starter.
     drop       Then, if still over: release the first `over` players who have ir false, are not in get, are not
                starters of R2, and are not protect, ordered by keep ascending, then seen ascending, then name
                ascending. K and D/ST (`other`) are never released. None left to release: no offer.
                Moves and drops never start, so they never move the gain.
   their      The partner's room (rules.drop applied to the partner, "Only the owner's room is checked" aside): his
                roster loses `get` and takes `send`, and the same moves and drops follow. It scores nothing.
   Nothing here touches the page: data in, numbers out. A player is {name, pos, seen, proj, ir, keep, ir_ok, protect}. */

const tbKey = p => p.name;
const tbH = x => Math.round(100 * x);
const tbName = (a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0;

/* {total, used}: the roster's lineup in hundredths, and the names of the players who start. */
function tbLineup(players, lu){
  const cands = players.filter(p => !p.ir).sort((a, b) => b.proj - a.proj || b.seen - a.seen || tbName(a, b));
  const used = new Set();
  let total = 0;
  const fill = (eligible, n, bar) => {
    const pool = cands.filter(p => eligible.includes(p.pos) && !used.has(tbKey(p))).slice(0, n);
    pool.forEach(p => used.add(tbKey(p)));
    total += pool.reduce((s, p) => s + Math.max(tbH(p.proj), bar), 0) + (n - pool.length) * bar;
  };
  Object.entries(lu.slots).forEach(([pos, n]) => fill([pos], n, tbH(lu.floor[pos])));
  lu.flex.forEach(fx => fill(fx.pos, fx.n, Math.max(...fx.pos.map(q => tbH(lu.floor[q])))));
  return {total, used};
}

/* d hundredths as points: d / 10 rounded half away from zero, then / 10. */
const tbTenths = d => Math.sign(d) * Math.round(Math.abs(d) / 10) / 10;

/* The roster after the trade, before any move or drop: without `send`, with `get` (a player already on it is not added twice). */
function tbAfter(roster, send, get){
  const out = new Set(send.map(tbKey)), has = new Set(roster.map(tbKey));
  return roster.filter(p => !out.has(tbKey(p))).concat(get.filter(p => !has.has(tbKey(p))));
}

/* The players moved to IR: only when the roster is over the cap and the league has a free IR slot (`lu.ir` minus the
   players already on IR). The eligible (`ir_ok`, not yet `ir`) with the highest `keep` go first, one per free slot, and
   no more than it takes to reach the cap. */
function tbIrMoves(after, lu, other){
  const over = after.filter(p => !p.ir).length + (other || 0) - lu.cap, free = lu.ir - after.filter(p => p.ir).length;
  if (over <= 0 || free <= 0) return [];
  const pool = after.filter(p => !p.ir && p.ir_ok).sort((a, b) => b.keep - a.keep || b.seen - a.seen || tbName(a, b));
  return pool.slice(0, Math.min(over, free));
}

/* {drop, short}: the players released to stay at the cap (`after` already has the IR moves flagged `ir`; `other` is
   the K/DST the owner also holds, never released), and `short` when nobody is left to release enough of: the producer
   writes no such offer. The lowest `keep` among players not in `get`, not starters, not on IR and not `protect`. */
function tbDrops(after, get, lu, other){
  const over = after.filter(p => !p.ir).length + (other || 0) - lu.cap;
  if (over <= 0) return {drop: [], short: false};
  const start = tbLineup(after, lu).used, got = new Set(get.map(tbKey));
  const pool = after.filter(p => !p.ir && !p.protect && !got.has(tbKey(p)) && !start.has(tbKey(p)));
  pool.sort((a, b) => a.keep - b.keep || a.seen - b.seen || tbName(a, b));
  return {drop: pool.slice(0, over), short: pool.length < over};
}

/* {irMoves, drop, short, kept}: the room the roster needs, IR first, then drops. `kept` is the roster that plays: the
   moved and the dropped are out of it, so they never start. */
function tbRoom(after, get, lu, other){
  const irMoves = tbIrMoves(after, lu, other), moved = new Set(irMoves.map(tbKey));
  const settled = after.map(p => moved.has(tbKey(p)) ? Object.assign({}, p, {ir: true}) : p);
  const {drop, short} = tbDrops(settled, get, lu, other), gone = new Set(drop.map(tbKey));
  return {irMoves, drop, short, kept: settled.filter(p => !gone.has(tbKey(p)))};
}

/* {irMoves, drop, short}: the partner's room after the same package (option B, 2026-10-05). The same rule, run on the
   partner's roster: it loses what the reader gets (`get`) and takes what the reader sends (`send`, from the reader's
   values), and what it takes in is never dropped. Nothing is scored: it is only the sentence in the copied pitch,
   and the file's per-offer `their` is checked against it (offers.js). */
function tbTheir(theirs, send, get, lu, other){
  if (!send.length && !get.length) return {irMoves: [], drop: [], short: false};
  const r = tbRoom(tbAfter(theirs, get, send), send, lu, other);
  return {irMoves: r.irMoves, drop: r.drop, short: r.short};
}

/* {gain, drop, irMoves, ok} for the owner sending `send` and getting `get` (players with `proj`, `ir` and the drop
   rule's `keep`, `ir_ok`, `protect`; `get` from the partner's values). `ok` is false for an empty package (gain 0)
   and for one the cap cannot take (gain 0, `drop` is what could be released). */
function tbGain(roster, send, get, lu, other){
  if (!send.length && !get.length) return {gain: 0, drop: [], irMoves: [], ok: false};
  const r = tbRoom(tbAfter(roster, send, get), get, lu, other);
  return {gain: tbTenths(tbLineup(r.kept, lu).total - tbLineup(roster, lu).total), drop: r.drop, irMoves: r.irMoves, ok: !r.short};
}
