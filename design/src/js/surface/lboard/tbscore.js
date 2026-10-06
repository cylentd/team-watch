/* ============================== LEAGUE > TEAMS: THE TRADE SCORER ==============================
   2026-10-05; rest-of-season points since 2026-10-06 (ff-jarvis METHODOLOGY 12.99). A pure port of ff-jarvis's scoring rule
   for a trade, so the builder's Edit can score a package the reader makes. The SOURCE OF TRUTH is the contract:
   trade_offers.json carries, per league, `weeks_left`, `lineup` (with `ros_floor` and `ir`), `values` (with `ros_pg`,
   `games`, `keep`, `ir_ok`, `protect`) and `other`, per offer `ir_moves`, `drop` and `their`, and in its top-level `rules`
   the rule itself in words (`rules.scoring`, `rules.drop`). This file ports those two texts, and only those; offers.js
   re-scores every offer it loads against this port (the gain, the partner's gain, the moves, the drops) and shuts Edit when
   one differs (fail closed), so a rule ff-jarvis changes cannot quietly drift from the page.

   As ported (the rule of 2026-10-06; if `rules` says otherwise, `rules` wins):
     h(x), t(x) integer hundredths, round(100 * x), of a ros_pg or ros_floor, and tenths, round(10 * x), of a games value.
     ros        W = weeks_left. Candidates are EVERY player of the roster (IR too: his games already leave out what he
                misses), ordered by h(ros_pg) descending, then t(games) descending, then name ascending; each has
                left = t(games). Slot kinds in order: each position of lineup.slots, then each entry of lineup.flex. A kind
                needs n * 10 * W tenths of a game and its bar is the largest h(lineup.ros_floor[p]) over its positions.
                Walk the candidates: one whose pos fits, with games left and h(ros_pg) above the bar, takes
                min(left, need) tenths at h(ros_pg), and both counts fall. What is still needed is the wire's, at the bar.
                So a starter's missed games and byes go to the next candidates, then to the wire. The total is in
                thousandths of a point.
     gain       r(ros(R3) - ros(R1)): R1 is the owner's values; R3 is R1 minus send, plus get (the partner's players matched
                by name, with their own fields), minus the drops. Players moved to IR stay in R3. r(d) is d / 100 rounded
                half away from zero, then / 10: points to one decimal.
     starters   the roster's players with ir false in the candidate order: the first n of each lineup.slots position, then of
                each flex entry (no floors), used once.
     IR moves   over = (the players of R2 with ir false) + other[owner] - cap, R2 being R1 minus send plus get; free =
                max(lineup.ir - (players of R2 with ir true), 0). Players with ir false and ir_ok true, get players
                included, highest keep first, then higher seen, then name: the first min(free, over) move to IR and
                no longer count toward the cap.
     drop       Then, if still over: from the players with ir false that did not move, those not starters (of that
                roster) and not in get and not protect, ordered by keep ascending, then seen ascending, then name
                ascending, release the first `over`. K and D/ST (`other`) are never released. None left to release:
                no offer (`short`).
     their      The partner's room and gain by the same rule: his roster loses `get` and takes `send`, the room follows
                (what he receives is never dropped), and his gain is r(ros(H3) - ros(H1)).
   Nothing here touches the page: data in, numbers out. A player is {name, pos, seen, ros_pg, games, ir, keep, ir_ok, protect}. */

const tbKey = p => p.name;
const tbH = x => Math.round(100 * x);
const tbT = x => Math.round(10 * x);
const tbName = (a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0;

/* The candidate order of rules.scoring: points a game, then games, then name. A copy, so the roster is not reordered. */
const tbCands = players => players.slice().sort((a, b) => tbH(b.ros_pg) - tbH(a.ros_pg) || tbT(b.games) - tbT(a.games) || tbName(a, b));

/* The slot kinds in fill order: [positions, n] for each fixed slot, then each flex entry. */
const tbKinds = lu => Object.entries(lu.slots).map(([pos, n]) => [[pos], n]).concat(lu.flex.map(fx => [fx.pos, fx.n]));

/* The roster's rest-of-season points, in thousandths of a point, over `weeks` weeks: every slot filled game by game. */
function tbRos(players, lu, weeks){
  const cands = tbCands(players), left = new Map(cands.map(p => [tbKey(p), tbT(p.games)]));
  let total = 0;
  tbKinds(lu).forEach(([pos, n]) => {
    const bar = Math.max(...pos.map(q => tbH(lu.ros_floor[q])));
    let need = n * 10 * weeks;
    for (const p of cands){
      if (need <= 0) break;
      if (!pos.includes(p.pos) || left.get(tbKey(p)) <= 0 || tbH(p.ros_pg) <= bar) continue;
      const take = Math.min(left.get(tbKey(p)), need);
      total += tbH(p.ros_pg) * take;
      left.set(tbKey(p), left.get(tbKey(p)) - take);
      need -= take;
    }
    total += bar * need;
  });
  return total;
}

/* The players who start: names, from the roster's players with ir false, the first n of each position then of each flex entry. */
function tbStarters(players, lu){
  const cands = tbCands(players.filter(p => !p.ir)), used = new Set();
  tbKinds(lu).forEach(([pos, n]) => {
    cands.filter(p => pos.includes(p.pos) && !used.has(tbKey(p))).slice(0, n).forEach(p => used.add(tbKey(p)));
  });
  return used;
}

/* d thousandths as points: d / 100 rounded half away from zero, then / 10 (a loss that rounds to nothing is 0, not -0). */
const tbPts = d => Math.sign(d) * Math.floor((Math.abs(d) + 50) / 100) / 10 + 0;

/* The roster after the trade, before any move or drop: without `send`, with `get` (a player already on it is not added twice). */
function tbAfter(roster, send, get){
  const out = new Set(send.map(tbKey)), has = new Set(roster.map(tbKey));
  return roster.filter(p => !out.has(tbKey(p))).concat(get.filter(p => !has.has(tbKey(p))));
}

/* The players moved to IR: only when the roster is over the cap and the league has a free IR slot (`lu.ir` minus the
   players already on IR). The eligible (`ir_ok`, not yet `ir`) with the highest `keep` go first, one per free slot, and
   no more than it takes to reach the cap. */
function tbIrMoves(after, lu, other){
  const over = after.filter(p => !p.ir).length + (other || 0) - lu.cap, free = Math.max(lu.ir - after.filter(p => p.ir).length, 0);
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
  const start = tbStarters(after, lu), got = new Set(get.map(tbKey));
  const pool = after.filter(p => !p.ir && !p.protect && !got.has(tbKey(p)) && !start.has(tbKey(p)));
  pool.sort((a, b) => a.keep - b.keep || a.seen - b.seen || tbName(a, b));
  return {drop: pool.slice(0, over), short: pool.length < over};
}

/* {irMoves, drop, short, kept}: the room the roster needs, IR first, then drops. `kept` is the roster that plays on: the
   moved stay (they return, and their games already leave out what they miss), the dropped are gone. */
function tbRoom(after, get, lu, other){
  const irMoves = tbIrMoves(after, lu, other), moved = new Set(irMoves.map(tbKey));
  const settled = after.map(p => moved.has(tbKey(p)) ? Object.assign({}, p, {ir: true}) : p);
  const {drop, short} = tbDrops(settled, get, lu, other), gone = new Set(drop.map(tbKey));
  return {irMoves, drop, short, kept: settled.filter(p => !gone.has(tbKey(p)))};
}

/* {irMoves, drop, short, gain}: the partner's room and rest-of-season gain after the same package (option B, 2026-10-05).
   The same rule, run on the partner's roster: it loses what the reader gets (`get`) and takes what the reader sends
   (`send`, from the reader's values), and what it takes in is never dropped. The room is the sentence in the copied
   pitch; the gain is checked against the file's `their.gain` (offers.js). */
function tbTheir(theirs, send, get, lu, other, weeks){
  if (!send.length && !get.length) return {irMoves: [], drop: [], short: false, gain: 0};
  const r = tbRoom(tbAfter(theirs, get, send), send, lu, other);
  return {irMoves: r.irMoves, drop: r.drop, short: r.short, gain: tbPts(tbRos(r.kept, lu, weeks) - tbRos(theirs, lu, weeks))};
}

/* {gain, drop, irMoves, ok} for the owner sending `send` and getting `get` (players with `ros_pg`, `games`, `ir` and the
   drop rule's `keep`, `ir_ok`, `protect`; `get` from the partner's values), over `weeks` weeks. `ok` is false for an
   empty package (gain 0) and for one the cap cannot take (gain 0, `drop` is what could be released). */
function tbGain(roster, send, get, lu, other, weeks){
  if (!send.length && !get.length) return {gain: 0, drop: [], irMoves: [], ok: false};
  const r = tbRoom(tbAfter(roster, send, get), get, lu, other);
  return {gain: tbPts(tbRos(r.kept, lu, weeks) - tbRos(roster, lu, weeks)), drop: r.drop, irMoves: r.irMoves, ok: !r.short};
}
