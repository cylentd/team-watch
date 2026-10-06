/* ============================== LIVE: THE LEAGUE ==============================
   My league's two league-wide parts (2026-10-05, storyboard
   https://claude.ai/artifact/ArF53Lvh12QV8fbL3mr9KP, option 2A): the strip of the league's matchups on
   top, and the ranking below the lineups.

   The league is the reader's team's (live.js gdLeague); the league chips and the sideways swipe between
   leagues went the same day. To switch leagues the reader switches teams: their name on the score head
   is the team switch (board.js). */

const GD_LOCK =`<svg viewBox="0 0 12 12" aria-hidden="true"><rect x="2.5" y="5.5" width="7" height="5" rx="1"/><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5"/></svg>`;

/* One chip per matchup: its state word on top (LIVE in lime, how many are left, FINAL), then each team's
   short name and score, the side behind grey. The reader's team leads its own chip, and the chip wears
   a lime ring; the game on screen is the raised one. A tap shows that game in the score head and the
   lineups under the strip (live.js wireLive); `data-gdgame` keeps the league's [away, home] order. */
function gdChipHTML(g, sides, on, mine){
  let [a, b] = [sides[g[0]], sides[g[1]]];
  if (b.id === mine) [a, b] = [b, a];
  const st = gdChipState(a, b), picked = gdSameGame(g, on);
  const word = st.k === "live" ? t("live.chip.live") : st.k === "left" ? t("live.state.left", {n: st.n}) : t("live.state.final");
  const row = (s, o) => `<span class="gd-cr${s.total < o.total ? " behind" : ""}"><span>${esc(gdShortName(s.name))}</span><b>${gdNum(s.total)}</b></span>`;
  const label = t("live.chip.label", {a: esc(a.name), pa: gdNum(a.total), b: esc(b.name), pb: gdNum(b.total)});
  return `<button type="button" class="gd-chip${picked ? " on" : ""}${a.id === mine ? " mine" : ""}" data-gdgame="${esc(g.join(","))}"
    aria-pressed="${picked}" aria-label="${label}"><small class="gd-cs ${st.k}">${st.k === "final" ? GD_LOCK : ""}${word}</small>${row(a, b)}${row(b, a)}</button>`;
}

/* The strip (data/gameday/strip.js gdStripOrder): the reader's game first, then the league's order. A
   team with no game this week leads with the closest game: by the scores once anyone has played, by
   where each side should finish before that. A playoff week with fewer matchups draws fewer chips. */
function gdStripHTML(lg, sides, on, mine){
  const all = Object.values(sides), started = all.some(s => s.done + s.playing);
  const pts = Object.fromEntries(all.map(s => [s.id, started ? s.total : gdProj(s, projFor)]));
  const chips = gdStripOrder(lg.games, pts, mine).map(g => gdChipHTML(g, sides, on, mine)).join("");
  return chips ? `<div class="gd-strip" role="group" aria-label="${t("live.games", {week: lg.week})}">${chips}</div>` : "";
}

/* Every team's total against the week's median, below the lineups. Kept when the tabs merged: the strip
   says who leads each game, this says who is in the top half, which in a league that pays the top half a
   second win (ESPN's WIN_BONUS_TOP_HALF) is the other game the reader is playing. Only that league draws
   the line in lime; elsewhere the ranking is for bragging and the line is grey. */
function gdLadderHTML(lg, sides){
  const {median, rows} = gdLadder(Object.values(sides));
  const cut = rows.findIndex(r => !r.top), mine = gdMine(lg);
  const row = (r, i) => `<div class="gd-l${mine && r.id === mine ? " mine" : ""}">
      <span>${i + 1}</span><span>${esc(r.name)}</span>
      <small class="${r.total >= median ? "up" : "dn"}">${gdSigned(r.total - median)}</small><b>${gdNum(r.total)}</b></div>`;
  const line = `<div class="gd-median${lg.median ? "" : " quiet"}"><span>${t("live.median", {n: gdNum(median)})}</span></div>`;
  const head = lg.median ? t("live.medianHead") : `${t("live.rankHead")} <em>${t("live.rankNote")}</em>`;
  return `<section class="gd-ladder gd-card"><h3><span>${head}</span></h3>
    ${rows.map((r, i) => (i === cut ? line : "") + row(r, i)).join("")}</section>`;
}
