/* DIGEST: Claude vs Vegas rows. A game's bets, one row per bet, Vegas beside Claude's side and its confidence word:
   the same rows and words Preview's dossier prints (data/preview.js pvAnswer, pvConfHTML), so the two never disagree.
   Claude's picks carry Preview's marks: the call's own (preview.call.mark) on the winner and on any pick, the chip's
   (preview.conf.mark) on every confidence word, "No pick" included. The night card (night.js) and Tonight (game.js)
   draw them; the Claude vs Vegas card of its own folded into Tonight on 2026-10-08 (Home draft B). */

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

/* The bets table for game `g`, or "" when it has no line and no take. */
function dgVegasTableHTML(g){
  const rows = pvAnswer(g).rows;
  return rows.length ? `<table class="dg-vg" data-testid="digest-vs-bets"><thead><tr><th>${t("digest.card.vegas.bet")}</th><th>${t("digest.card.vegas.vegas")}</th><th>${t("digest.card.vegas.claude")}</th></tr></thead>
    <tbody>${rows.map(r => dgVegasRowHTML(r, !!g.take)).join("")}</tbody></table>` : "";
}
