/* DIGEST CARD: Claude vs Vegas (Thursday). The day's game, one row per bet, Vegas beside Claude's side and its
   confidence word: the same rows and words Preview's dossier prints (data/preview.js pvAnswer, pvConfHTML), so
   the two never disagree. Claude's picks carry Preview's marks: the call's own (preview.call.mark) on the
   winner and on any pick, the chip's (preview.conf.mark) on every confidence word, "No pick" included. More to
   Preview. Interface: card.js; returns "" without a game today that has a line or a take. */

/* The game to put side by side: today's (Pacific), not yet over, first by kickoff. */
function dgVegasGame(ctx){
  const games = ctx.preview && schedIsPageWeek(ctx.preview.week) ? ctx.preview.games : [];
  return dgByKick(games).find(g => dgToday(g.kickoff, ctx.now) && !pvOver(g)) || null;
}

/* Claude's cell: his call in bold, its confidence chip and what it needs under it; a bet he made no call on
   says so with the chip (as the dossier does), and a game with no take at all leaves a dash. */
function dgVegasClaude(r, hasTake){
  if (!r.claude) return hasTake ? pvConfHTML(null) : "–";
  return `<b>${r.claude}</b>${r.conf ? " " + pvConfHTML(r.conf) : ""}${r.sub ? ` <small>${r.sub}</small>` : ""}`;
}

function dgVegasRowHTML(r, hasTake){
  const bet = {ml: t("digest.card.vegas.winner"), spread: t("digest.card.vegas.spread"), total: t("digest.card.vegas.total")}[r.id];
  return `<tr data-testid="digest-vs-bet"><th scope="row">${bet}</th><td class="dg-vg-v">${r.vegas || "–"}</td>
    <td class="dg-vg-c"${r.claude ? ` title="${t("preview.call.mark")}"` : ""}>${dgVegasClaude(r, hasTake)}</td></tr>`;
}

function dgCardVegas(ctx){
  const g = dgVegasGame(ctx);
  if (!g) return "";
  const a = pvAnswer(g);
  if (!a.rows.length) return "";
  const body = `<p class="dg-vg-game" data-testid="digest-vs-game">${t("digest.card.vegas.game", {game: dgGame(g), kick: esc(kickFmt(g.kickoff))})}</p>
    <table class="dg-vg" data-testid="digest-vs-bets"><thead><tr><th>${t("digest.card.vegas.bet")}</th><th>${t("digest.card.vegas.vegas")}</th><th>${t("digest.card.vegas.claude")}</th></tr></thead>
    <tbody>${a.rows.map(r => dgVegasRowHTML(r, !!g.take)).join("")}</tbody></table>`;
  return dgCardHTML({id: "vegas", title: t("digest.card.vegas.title"), more: {leaf: "preview"}, body});
}
