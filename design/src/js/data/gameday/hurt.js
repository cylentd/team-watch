/* ============================== GAMEDAY: WHO LEFT THE GAME HURT ==============================
   2026-10-04. David: "the headline should change when something big happens, like an injury". Sleeper
   and the scoreboard say nothing about an injury mid-game; the play-by-play does. nflverse's text for
   a game (games/*.json, checked 2026-10-04) says "LAC-J.Caldwell was injured during the play." and
   later "** Injury Update: LAC-J.Caldwell has returned to the game."
   UNVERIFIED: ESPN's summary (gsFetchSummary, the reader's browser only: ESPN refuses servers) is
   believed to carry the same text in drives[].plays[].text. Check it on Monday's game (ATL @ NO).
   Until then a summary that does not say it flags nobody and nothing on the page changes.

   gdHurtScan is pure: a summary and the players to watch in, who is hurt out. The players to watch are
   league-wide (David, 2026-10-04: "The Digest is supposed to be GENERIC for the public. It shouldn't
   hone on to my roster or their roster."): every QB, RB, WR and TE the projections rate GD_HURT_MIN_PTS
   or more this week, from LIVE_RANKS, which keeps defenders and special teams out. The poller asks for
   a summary of every game that is on, once per 180 s per game, one request at a time, and keeps
   GD_HURT = {slug: {slug, name, team, q, clock, back}}. The Digest's headline and Right now
   (surface/digest/now.js) and Live's Matchup chip (surface/live/mirror.js) read it. */

const GD_HURT_GAP_MS = 180000;
const GD_HURT_MIN_PTS = 8;   /* projected points this week: below it he is not fantasy-relevant news */
let GD_HURT = {};        /* slug -> latest {slug, name, team, q, clock, back} */
let GD_HURT_AT = {};     /* ESPN event id -> epoch ms of the last attempt */
let GD_HURT_BUSY = false;

/* "was injured during the play" (the name is the text before it), or "Injury Update: NAME has returned
   to the game" (group 1). The phrases ignore case; the names do not, so they are matched apart. */
const GD_HURT_PHRASE = /was injured during the play|Injury Update:\s*([^]*?)\s+has returned to the game/gi;
/* "SF-B.Purdy", "T.Stukes", "T. Stukes", "Aj.Terrell", "A.St. Brown": an optional club, the first name's
   initial (up to three letters), the surname (hyphens, apostrophes, one more word). */
const GD_HURT_NAME = "(?:[A-Z]{2,3}-)?[A-Z][a-z]{0,2}\\.\\s?[A-Z][\\w'-]*(?:\\.?\\s[A-Z][\\w'-]*)?";
const GD_HURT_TAIL = new RegExp("(" + GD_HURT_NAME + ")\\s*$");
const GD_HURT_WHOLE = new RegExp("^\\s*(" + GD_HURT_NAME + ")\\s*$");
const GD_HURT_SUFFIX = /^(jr|sr|ii|iii|iv|v)\.?$/i;

/* "b.purdy" from "Brock Purdy" and from "B. Purdy" alike: the first letter, a dot, the surname with its
   spaces and any suffix gone. */
function gdHurtKey(full){
  const w = String(full || "").split(/\s+/).filter(Boolean);
  while (w.length > 2 && GD_HURT_SUFFIX.test(w[w.length - 1])) w.pop();
  return w.length < 2 ? "" : `${w[0][0]}.${w.slice(1).join("")}`.toLowerCase();
}

/* The text's name to {club, key}: "LAC-J.Caldwell" -> {club: "LAC", key: "j.caldwell"}. */
function gdHurtParse(raw){
  const m = /^(?:([A-Z]{2,3})-)?([A-Z])[a-z]{0,2}\.\s?(.+?)\.?$/.exec(raw);
  return m ? {club: m[1] || "", key: `${m[2]}.${m[3].replace(/\s+/g, "")}`.toLowerCase()} : null;
}

/* LIVE_RANKS' rows: every QB, RB, WR and TE with a projection this week ({slug, n, pos, team, pts}). */
const gdHurtRows = () => typeof LIVE_RANKS !== "undefined" && LIVE_RANKS ? LIVE_RANKS.rows : [];

/* Every fantasy-relevant player of the week by that key: {"b.purdy": [{slug, name, team}]}. Those the
   projections rate GD_HURT_MIN_PTS or more: no defense, no kicker, nobody who is not projected to play. */
function gdHurtNames(){
  const out = {};
  for (const r of gdHurtRows()){
    const key = !r.slug || !r.team || !(r.pts >= GD_HURT_MIN_PTS) ? "" : gdHurtKey(r.n);
    if (!key) continue;
    const list = out[key] = out[key] || [];
    if (!list.some(x => x.slug === r.slug)) list.push({slug: r.slug, name: r.n, team: r.team});
  }
  return out;
}

/* Who the text means: a club in the text must be his; without one, he must play in this game. */
function gdHurtWho(raw, clubs, names){
  const who = gdHurtParse(raw || "");
  if (!who) return null;
  return (names[who.key] || []).find(c => who.club ? gdSameClub(c.team, who.club) : !clubs.length || clubs.some(x => gdSameClub(c.team, x))) || null;
}

/* Every play in order; the last word on each watched player wins, so "returned" clears him and a second
   injury flags him again. -> [{slug, name, team, q, clock, back}], one per player named. */
function gdHurtScan(summary, names){
  const found = new Map();
  const s = summary || {}, comp = ((s.header || {}).competitions || [])[0] || {};
  const clubs = (comp.competitors || []).map(c => (c.team || {}).abbreviation).filter(Boolean);
  const dr = s.drives || {};
  const chrono = [...(dr.previous || []), ...(dr.current ? [dr.current] : [])];
  const plays = chrono.length ? chrono.flatMap(d => d.plays || []) : Array.isArray(s.plays) ? s.plays : [];
  for (const p of plays){
    const text = String(p.text || "");
    if (!/injur/i.test(text)) continue;
    for (const m of text.matchAll(GD_HURT_PHRASE)){
      const back = m[1] !== undefined;
      const raw = back ? (GD_HURT_WHOLE.exec(m[1]) || [])[1] : (GD_HURT_TAIL.exec(text.slice(Math.max(0, m.index - 60), m.index)) || [])[1];
      const c = gdHurtWho(raw, clubs, names);
      if (!c) continue;
      if (back && !found.has(c.slug)) continue;
      const was = found.get(c.slug) || {};
      found.set(c.slug, {slug: c.slug, name: c.name, team: c.team,
                         q: back ? was.q : (p.period || {}).number || 0, clock: back ? was.clock : (p.clock || {}).displayValue || "", back});
    }
  }
  return [...found.values()];
}

/* One summary per due game (every game that is on), one at a time. Called by every Live poll and never
   awaited: the stats do not wait for ESPN. A failed fetch keeps the last state and says nothing. */
async function gdHurtPoll(){
  if (GD_HURT_BUSY || !PAGE_SERVED() || !gdOnScreen()) return;
  const now = Date.now();
  const due = gdWeekGames().filter(g => g.espn && gdClockOf(g.home).live && now - (GD_HURT_AT[g.espn] || 0) >= GD_HURT_GAP_MS);
  if (!due.length) return;
  GD_HURT_BUSY = true;
  const before = JSON.stringify(GD_HURT);
  try {
    const names = gdHurtNames();
    for (const g of due){
      GD_HURT_AT[g.espn] = Date.now();
      let summary = null;
      try { summary = await gsFetchSummary(g.espn); } catch (e) { /* ESPN down or slow: the last state stands */ }
      for (const h of gdHurtScan(summary, names)) GD_HURT[h.slug] = h;
    }
  } finally { GD_HURT_BUSY = false; }
  if (JSON.stringify(GD_HURT) !== before) paintLive();
}

/* Who is hurt now (flagged, not back), the best projection first, for the Digest's headline and its
   Right now rows: {slug, n, pos, team, pts, h}. A flag for a player the rankings no longer carry is not
   drawn. */
function gdHurtNow(){
  const rows = new Map(gdHurtRows().map(r => [r.slug, r]));
  return Object.values(GD_HURT).filter(h => !h.back && rows.has(h.slug))
    .map(h => { const r = rows.get(h.slug); return {slug: h.slug, n: r.n, pos: r.pos, team: r.team, pts: r.pts, h}; })
    .sort((a, b) => b.pts - a.pts);
}
