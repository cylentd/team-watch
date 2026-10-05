/* ============================== LEAGUE > TEAMS: THE TRADE SCORER ==============================
   2026-10-05. A pure port of ff-jarvis's scoring rule for a trade, so the builder's Edit can score a package the
   reader makes. The SOURCE OF TRUTH is the contract: trade_offers.json carries, per league, `lineup`, `values` and
   `other`, per offer `drop`, and in its top-level `rules` the rule itself in words (`rules.scoring`, `rules.drop`).
   This file ports those two texts, and only those; offers.js re-scores every offer it loads against this port and
   shuts Edit when one differs (fail closed), so a rule ff-jarvis changes cannot quietly drift from the page.

   As ported (the texts as of ff-jarvis 29e54f2, 2026-10-05; if `rules` says otherwise, `rules` wins):
     h(x)       integer hundredths, round(100 * x), of a proj or a floor.
     starters   candidates are the roster's players with ir false, ordered by proj descending, then seen descending,
                then name ascending. For each position of lineup.slots, take the first n unused candidates of it; then,
                for each entry of lineup.flex in order, the first n unused candidates whose pos is in the entry's list.
     slot       max(h(proj), bar); bar is h(floor[pos]) for a fixed slot and the largest h(floor[p]) over the entry's
                positions for a flex slot. A slot with nobody left is worth its bar. A floored starter still starts.
     gain       tenths(lineup(R2) - lineup(R1)): R1 is the owner's values, R2 is R1 minus send plus get (the partner's
                players matched by name, keeping their ir flag) minus drop; tenths(d) is d / 10 rounded half away
                from zero, then / 10.
     drop       count = the players of R2 (before drops) with ir false, plus other[owner]; over = count - cap. Release
                the first `over` players of R2 who have ir false, are not in get and are not starters of R2, ordered
                by proj ascending, then seen ascending, then name ascending. K and D/ST (`other`) are never released.
                Drops never start, so they never move the gain.
   Nothing here touches the page: data in, numbers out. A player is {name, pos, seen, proj, ir}. */

const tbKey = p => p.name;
const tbH = x => Math.round(100 * x);

/* {total, used}: the roster's lineup in hundredths, and the names of the players who start. */
function tbLineup(players, lu){
  const cands = players.filter(p => !p.ir).sort((a, b) => b.proj - a.proj || b.seen - a.seen || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
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

/* The roster after the trade, before any drop: without `send`, with `get` (a player already on it is not added twice). */
function tbAfter(roster, send, get){
  const out = new Set(send.map(tbKey)), has = new Set(roster.map(tbKey));
  return roster.filter(p => !out.has(tbKey(p))).concat(get.filter(p => !has.has(tbKey(p))));
}

/* {drop, short}: the players released to stay at the cap (`other` is the K/DST the owner also holds, never released),
   and `short` when the roster cannot reach the cap that way: the producer writes no such offer. */
function tbDrops(after, get, lu, other){
  const over = after.filter(p => !p.ir).length + (other || 0) - lu.cap;
  if (over <= 0) return {drop: [], short: false};
  const keep = tbLineup(after, lu).used, got = new Set(get.map(tbKey));
  const pool = after.filter(p => !p.ir && !got.has(tbKey(p)) && !keep.has(tbKey(p)));
  pool.sort((a, b) => a.proj - b.proj || a.seen - b.seen || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
  return {drop: pool.slice(0, over), short: pool.length < over};
}

/* {gain, drop, ok} for the owner sending `send` and getting `get` (players with `proj` and `ir`, `get` from the
   partner's values). `ok` is false for an empty package (gain 0) and for one the cap cannot take (gain 0, `drop` is
   what could be released). */
function tbGain(roster, send, get, lu, other){
  if (!send.length && !get.length) return {gain: 0, drop: [], ok: false};
  const after = tbAfter(roster, send, get), {drop, short} = tbDrops(after, get, lu, other);
  const gone = new Set(drop.map(tbKey)), kept = after.filter(p => !gone.has(tbKey(p)));
  return {gain: tbTenths(tbLineup(kept, lu).total - tbLineup(roster, lu).total), drop, ok: !short};
}
