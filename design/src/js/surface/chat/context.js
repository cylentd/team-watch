/* ------------------------------------------------------------------
   What the chat sends with a question.

   The page already holds every player row inlined, so it picks the few a question is about and
   posts those. The server keeps no copy of any of this -- which is why there is no second data
   file to deploy and nothing that can fall out of sync with what you are looking at.

   Small on purpose: the whole feed is 3.7 MB and would cost about $5 a question. A handful of
   rows costs a fraction of a cent, and a model reading six players answers better than one
   skimming six hundred.
------------------------------------------------------------------ */

/* At most this many players ride along. A question naming more than six is a question the
   answer should ask to narrow, not one to spend a huge prompt on. */
const CHAT_MAX_PLAYERS = 6;
/* Words that look like a surname but are not one. Without this, "Start Josh or sit him?"
   matches nothing while "Who is the best flex?" matches a player named Best. */
const CHAT_STOPWORDS = new Set(["start","sit","best","who","what","how","why","the","and","or",
  "my","me","is","are","should","this","week","flex","drop","add","trade","over","vs","better"]);

/* One searchable row per player in the pool, built once. POOL is the usage read (snaps, share,
   red-zone work, luck, verdict); LIVE_MARKET_STOCK carries the market-implied points for the
   same player, keyed by slug. Joined here so a question gets both in one row. */
function chatIndex(){
  const stock = (typeof LIVE_MARKET_STOCK !== "undefined" && LIVE_MARKET_STOCK)
    ? LIVE_MARKET_STOCK.players : null;
  return POOL.map(p => {
    const s = stock ? stock[p.slug] : null;
    return {
      row: {
        name: p.n, pos: p.pos, team: p.team, opp: p.opp,
        snap_pct: p.snaps, snap_move: p.dSnap,
        share_pct: p.share, share_move: p.dShare,
        red_zone: p.rz, pts_per_game: p.ppg, td_luck: p.luck,
        usage_verdict: p.v, why: p.why || null,
        market_pts: s ? s.pts : null,
        rostered_by_me: p.mine ? true : false,
        leagues: p.leagues || null,
      },
      hay: (p.n || "").toLowerCase(),
      last: (p.n || "").toLowerCase().split(/\s+/).pop(),
    };
  });
}

/* Players the question names. Full name first, then surname, because "Brown" alone is three
   different players and the full name is the only unambiguous hit. */
function chatNamed(question){
  const q = " " + (question || "").toLowerCase().replace(/[^a-z' ]+/g, " ") + " ";
  const idx = chatIndex(), hits = [];
  let rest = q;
  for (const e of idx){
    if (e.hay && rest.includes(" " + e.hay + " ")){
      hits.push(e);
      /* Blank the name just matched, so the surname pass cannot re-match its halves against
         other players: "Chase Brown" must not also pull in A.J. Brown and Ja'Marr Chase. */
      rest = rest.split(" " + e.hay + " ").join("  ");
    }
  }
  if (hits.length < CHAT_MAX_PLAYERS){
    for (const e of idx){
      if (hits.includes(e)) continue;
      if (e.last && e.last.length > 2 && !CHAT_STOPWORDS.has(e.last)
          && rest.includes(" " + e.last + " ")) hits.push(e);
    }
  }
  return hits.slice(0, CHAT_MAX_PLAYERS).map(e => e.row);
}

/* My players, best first, for a question that names nobody ("who should I start?"). Capped the
   same way: a whole roster is a big prompt and a vague answer. */
function chatMine(){
  return chatIndex()
    .filter(e => e.row.rostered_by_me)
    .sort((a, b) => (b.row.market_pts ?? b.row.pts_per_game ?? 0)
                  - (a.row.market_pts ?? a.row.pts_per_game ?? 0))
    .slice(0, CHAT_MAX_PLAYERS * 2)
    .map(e => e.row);
}

/* The block posted with a question. `scope` tells the model how the rows were chosen, so it
   knows whether it is looking at what was asked about or at a default slice of my roster. */
function chatContext(question){
  const named = chatNamed(question);
  const players = named.length ? named : chatMine();
  if (!players.length) return null;
  return {
    scope: named.length ? "players named in the question" : "my highest-projected players",
    week: (typeof SLATE_WEEK !== "undefined" && SLATE_WEEK) || null,
    scoring: "half-PPR",
    /* Both leagues, so "should I start him" can say which one it is answering for. The ESPN
       league's real scoring is custom and has no kicker; the server's system prompt says so. */
    leagues: (typeof TEAMS !== "undefined" && TEAMS)
      ? Object.keys(TEAMS).map(k => ({key: k, name: TEAMS[k].name || k})) : null,
    players,
  };
}
