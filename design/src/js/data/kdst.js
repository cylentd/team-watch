/* A kicker's and a defense's points bars (2026-10-07). Pure and DOM-free, so Node tests it (tests/test_js_kdst.py).
   LIVE_KDST is ff-jarvis's gamelog_kdst.json: per club and played week, the D/ST points on each scoring and the
   K points on each Yahoo scoring, and who kicked. The page picks the league's score and computes nothing; the
   score names are LIVE_DST.leagues' cells (dst_espn, dst_yahoo, k_yahoo, k_ayo). Needs data/dst.js (dstClub). */

/* The score a league reads for a position, null where it has none (ESPN has no K slot) or the league is unknown. */
function kdstKey(dstBlock, lg, pos){
  const L = dstBlock && dstBlock.leagues && dstBlock.leagues[lg];
  return (L && (pos === "K" ? L.k : L.dst)) || null;
}

const kdstTeam = (block, club) => (block && block.teams && block.teams[dstClub(club)]) || null;

/* [{wk, pts}] for a club under one score, a week per played game; a bye has no row, so it stays an empty slot in
   the bars. null with no file, no such club or no score. */
function kdstRows(block, club, key){
  const rows = key && kdstTeam(block, club);
  return rows ? rows.filter(r => typeof r[key] === "number").map(r => ({wk: r.week, pts: r[key]})) : null;
}

/* "Alex Kicker" and "A.Kicker" both read "a.kicker": the first initial and the last word, the file's spelling. */
function kdstName(n){
  const w = String(n || "").trim().split(/\s+/).filter(Boolean), last = w[w.length - 1] || "";
  return (w.length > 1 && !last.includes(".") ? w[0][0] + "." + last : last).toLowerCase();
}

/* The weeks a kicker other than the rostered one kicked (drawn faded). A week where his name is among the
   kickers is his. When his name is in none of the club's weeks the file cannot tell, so nothing fades. */
function kdstFaded(block, club, name){
  const rows = kdstTeam(block, club) || [], me = kdstName(name);
  const mine = r => (r.kickers || []).some(k => kdstName(k) === me);
  return rows.some(mine) ? rows.filter(r => !mine(r)).map(r => r.week) : [];
}
