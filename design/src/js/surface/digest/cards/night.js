/* DIGEST CARD: the night game (Wednesday: Thursday night's; Sunday: Sunday night's, until it kicks off). Claude's
   headline for the game and the lines from Preview's dossier, the same rows and words (data/preview.js pvAnswer,
   cards/vegas.js dgVegasRowHTML), so the two never disagree. The game and its headline are one button that opens
   Preview on the game (dgPreviewOpen); the header link does the same. Which game, and its place in the day, is
   data/dayplan.js (dgPickNight, dgCardOrder). Interface: card.js; returns "" without a night game to preview or
   with neither a headline nor a line to show. */

function dgCardNight(ctx){
  const pick = ctx.preview && schedIsPageWeek(ctx.preview.week) ? dgPickNight(ctx.preview, ctx.day, ctx.now) : null;
  if (!pick) return "";
  const g = pick.game, head = g.take && g.take.head, rows = pvAnswer(g).rows;
  if (!head && !rows.length) return "";
  const title = ctx.day === "wed" ? t("digest.card.night.titleThu") : t("digest.card.night.titleSun");
  const open = `<button type="button" class="dg-nt" data-testid="digest-night-open" data-dgpv="${pick.i}">
      <span class="dg-nt-game" data-testid="digest-night-game">${t("digest.card.vegas.game", {game: dgGame(g), kick: esc(kickFmt(g.kickoff))})}</span>
      ${head ? `<span class="dg-nt-head" data-testid="digest-night-head"${g.take ? ` title="${t("preview.call.mark")}"` : ""}>${esc(head)}</span>` : ""}</button>`;
  const bets = rows.length ? `<table class="dg-vg" data-testid="digest-vs-bets"><thead><tr><th>${t("digest.card.vegas.bet")}</th><th>${t("digest.card.vegas.vegas")}</th><th>${t("digest.card.vegas.claude")}</th></tr></thead>
    <tbody>${rows.map(r => dgVegasRowHTML(r, !!g.take)).join("")}</tbody></table>` : "";
  return dgCardHTML({id: "night", title, more: {leaf: "preview", game: pick.i}, body: open + bets});
}

/* Preview on game `i` (its index in LIVE_PREVIEW.games, the one the dossier opens on): the view, then the dossier. */
function dgPreviewOpen(i){
  morphLogo(); navGo("preview"); pvOpen(i); window.scrollTo({top: 0});
}
