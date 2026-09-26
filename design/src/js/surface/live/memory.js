/* ------------------------------------------------------------------
   LIVE MEMORY — what this browser remembers between polls, and between visits.

   The board itself is stateless: /api/live returns the present and forgets it, which is what
   lets the edge cache it. Everything about CHANGE therefore has to live here, in the one place
   that has seen more than one reply: the reader's own browser.

   Two things are remembered, per week:
     players/totals  the last scores this reader was actually shown, so the next reply can be
                     diffed against them -- a pulse while watching, a catch-up after time away
     wp              ESPN's win probability, one point per reply, so a Sunday has a shape

   Per week, because a snapshot from last week diffed against this week would report every
   player as having scored his whole total in one poll.

   localStorage is per browser and can be absent, full, or throwing (private mode, blocked site
   data). Every read and write here is wrapped and every failure is silent: losing the memory
   costs a delta chip, and must never cost the board.
------------------------------------------------------------------ */

/* Keyed by the team Live follows (gdTeamKey, live.js; 2026-09-26): a leaguemate's board must not
   be diffed against David's, or every player on it would read as a mover. David's keys are the
   same as before, so his memory survives the change. */
const GD_MEM_KEY = week => `tw-live-espn-w${week}${gdTeamKey() ? `-${gdTeamKey()}` : ""}`;
/* The last board itself, so a click paints complete instead of empty. Every other tab's data is
   inlined at build time and paints instantly; Live's arrives over the wire, and the two-step --
   an empty panel, then 130ms later the board -- is what reads as lag. The fetch is not slow, the
   emptiness is. */
const GD_LAST_KEY = () => `tw-live-espn-last${gdTeamKey() ? `-${gdTeamKey()}` : ""}`;
/* How old a remembered board may be and still be worth painting. Two days covers a whole
   gameday and the Monday night after it, and stops short of the Tuesday the NFL week rolls over
   -- painting last week's opponent as though he were this week's would be wrong, not just
   stale. Past it, the skeleton and a fresh fetch. */
const GD_KEEP_MS = 172800000;
/* Long enough that stepping away for a coffee reads as "away" and a glance at another tab does
   not. Below it, a reply is just the next poll. */
const GD_AWAY_MS = 300000;
/* A Sunday at 90 seconds is about 400 points and the sparkline is a few hundred pixels wide, so
   this is well past the resolution anyone can see. It is a cap on storage, not on fidelity. */
const GD_WP_MAX = 600;


function gdMemLoad(week){
  try {
    const raw = localStorage.getItem(GD_MEM_KEY(week));
    const mem = raw ? JSON.parse(raw) : null;
    return (mem && mem.week === week) ? mem : null;
  } catch (e) { return null; }
}

function gdMemSave(mem){
  try { localStorage.setItem(GD_MEM_KEY(mem.week), JSON.stringify(mem)); } catch (e) {}
}

function gdBoardSave(d){
  try { localStorage.setItem(GD_LAST_KEY(), JSON.stringify({asof: d.asof, board: d})); } catch (e) {}
}

/* The last board, if it is recent enough to still describe this week's matchup. Painting it is
   honest because the header states its own timestamp -- "updated 2:14 AM" is a fact about the
   numbers under it, and the fresh reply is already on its way when the reader sees them. */
function gdBoardLoad(){
  try {
    const wrap = JSON.parse(localStorage.getItem(GD_LAST_KEY()) || "null");
    if (!wrap || !wrap.board || !wrap.asof) return null;
    const age = Date.now() - Date.parse(wrap.asof);
    return (age >= 0 && age < GD_KEEP_MS) ? wrap.board : null;
  } catch (e) { return null; }
}

/* Every player on both sides, name -> what he has actually scored. Someone who has not kicked
   off is left out rather than stored as 0: the difference between "no points yet" and "has not
   played" is the whole reason `actual` is nullable, and flattening it here would invent a
   delta the moment his first stat landed. */
function gdScores(d){
  const out = {};
  for (const r of [...d.me.lineup, ...d.opponent.lineup]){
    if (r.name && r.actual !== null && r.actual !== undefined) out[r.name] = r.actual;
  }
  return out;
}

/* One player's movement between two snapshots, biggest first. A correction that takes points
   away is reported as readily as a touchdown: it moved, and the reader can see it moved. */
function gdMovers(before, after){
  const out = [];
  for (const [name, now] of Object.entries(after)){
    const was = before[name];
    if (was === undefined || now === was) continue;
    out.push({name, delta: Math.round((now - was) * 10) / 10});
  }
  return out.filter(m => m.delta !== 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta));
}

/* Called once per reply that the reader is actually shown. Returns what changed since the last
   one, then writes this reply down as the new "last seen".

   `away` is the interesting flag: it means this reader has been gone long enough that the diff
   is worth stating in words rather than shown as a chip that fades.
   A first visit has nothing to diff against and returns no movers at all -- the alternative is
   a board that greets you by claiming every player just scored his entire total.
*/
function gdRemember(d){
  const mem = gdMemLoad(d.week)
    || {week: d.week, seen: 0, totals: null, players: {}, wp: []};
  const before = mem.players || {};
  const first = !mem.seen;
  const now = Date.now();

  const after = gdScores(d);
  const movers = first ? [] : gdMovers(before, after);
  const gap = first ? 0 : now - mem.seen;
  const totals = {me: d.me.live, opp: d.opponent.live};
  const swing = (mem.totals && !first)
    ? {me: Math.round(((totals.me || 0) - (mem.totals.me || 0)) * 10) / 10,
       opp: Math.round(((totals.opp || 0) - (mem.totals.opp || 0)) * 10) / 10}
    : null;

  if (typeof d.me.winPct === "number"){
    const wp = mem.wp || [];
    /* One point per reply, and never two for the same instant: a repaint that re-uses a cached
       reply would otherwise stack points at one x and flatten the line's own history. */
    if (!wp.length || wp[wp.length - 1][0] !== now) wp.push([now, d.me.winPct]);
    mem.wp = wp.slice(-GD_WP_MAX);
  }

  mem.players = after;
  mem.totals = totals;
  mem.seen = now;
  gdMemSave(mem);
  gdBoardSave(d);

  return {movers, swing, away: gap > GD_AWAY_MS, first, wp: mem.wp || []};
}
