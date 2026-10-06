/* ============================== RECAP: SCORES ==============================
   The Scores tab: one line of Claude's record, then every game of the week grouped by kickoff window
   (Preview's windows, so a Thursday game and Sunday's three waves read the same on both pages). A final
   game shows the score, the winner bold, with Claude's pick and a Hit or Miss at the right; a game still
   to play shows its kickoff in Eastern time and the pick. A game opens Preview's dossier when Preview
   holds the same week; otherwise the row is plain text. */

const WR_ARROW = `<svg class="wr-arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5L10.5 8 6 12.5"/></svg>`;

/* The strip: "Claude picked 5 of 8 winners · 5–3 vs spread". Hidden before a game is graded. */
function wrStripHTML(d){
  const rec = wrRecord(d);
  if (!rec) return "";
  const [w = 0, l = 0] = String(rec.su || "0-0").split("-").map(Number), b = s => `<b>${s}</b>`;
  const winners = w + l ? `<span>${t("weekrecap.strip.winners", {w: b(w), n: w + l})}</span>` : "";
  const spread = rec.ats ? `<span>${t("weekrecap.strip.spread", {rec: b(pvWL(rec.ats))})}</span>` : "";
  return winners || spread ? `<p class="wr-strip">${[winners, spread].filter(Boolean).join(" · ")}</p>` : "";
}

/* The pick's grade as a word: green Hit, red Miss; none until the game is final and graded. */
const wrMark = p => p && p.su_hit !== null && p.su_hit !== undefined
  ? `<b class="wr-mk ${p.su_hit ? "hit" : "miss"}">${p.su_hit ? t("weekrecap.pick.hit") : t("weekrecap.pick.miss")}</b>` : "";

/* A final game's score: the winner's side bold. A tie bolds neither. */
function wrScoreline(g){
  if (!g.final || g.away_pts == null || g.home_pts == null) return `<span class="wr-sc">${esc(g.away)} @ ${esc(g.home)}</span>`;
  const a = `${esc(g.away)} ${g.away_pts}`, h = `${esc(g.home)} ${g.home_pts}`;
  return `<span class="wr-sc">${g.away_pts > g.home_pts ? `<b>${a}</b>` : a} @ ${g.home_pts > g.away_pts ? `<b>${h}</b>` : h}</span>`;
}

function wrGameRow(d, {g, at}){
  const p = g.preview, pick = p ? t("weekrecap.pick.picked", {team: esc(p.winner)}) : "";
  const kick = !g.final && at ? esc(at.time) : "";
  const right = `<span class="wr-pk">${[kick, pick].filter(Boolean).join(" · ")}${wrMark(g.final ? p : null)}</span>`;
  const i = wrPreviewIndex(d, g), body = wrScoreline(g) + right;
  return i >= 0 ? `<li><button type="button" class="wr-g" data-wrgame="${i}">${body}</button></li>` : `<li><div class="wr-g">${body}</div></li>`;
}

/* One window: its name (Preview's), its kickoff times in the reader's clock, then its games. A window with no
   kickoff (an old recap file) has no heading. */
const wrWindowHTML = (d, w) => `<section class="wr-win${w.rows.length > 2 ? " wide" : ""}">${w.slot ? `<h4 class="wr-wh"><span>${pvWinLabel(w)}</span><em>${
  esc(w.times.join(" · "))}</em></h4>` : ""}<ul>${w.rows.map(r => wrGameRow(d, r)).join("")}</ul></section>`;

function wrScoresHTML(d){
  if (!d.games.length) return "";
  return `${wrStripHTML(d)}<section class="wr-card wr-games"><div class="wr-chr"><h3 class="wr-ch">${t("weekrecap.scores.title")}</h3>
    <button type="button" class="wr-link" data-wrgo="preview">${t("weekrecap.scores.preview")}${WR_ARROW}</button></div>
    <div class="wr-wins">${wrWindows(d).map(w => wrWindowHTML(d, w)).join("")}</div></section>`;
}
