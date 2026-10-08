/* ============================== DIGEST: TONIGHT ON ==============================
   A standalone slot's game (Thursday, Saturday, Monday) once it kicks off: the same block as the last game's
   (mnf.js), its clock, score and best performer, one tap to its sheet. Before kickoff the game is the Tonight card
   (cards/game.js) since 2026-10-08 (Home draft B); the card of out players, our calls and projected points that
   stood here from 2026-09-28 (storyboard https://claude.ai/artifact/JSPwg21i9YaTSzhYqAEnQZ) left Home with it.
   data/digest.js decides when it shows and which rows it takes over. */

/* "82°F · 5 mph wind · Clear": the packet's sky for a game (the Tonight card's line). */
function dgTnSky(w){
  const bits = [w.roof === "dome" ? t("digest.tn.dome") : "", w.temp_f != null ? t("digest.lead.wx.temp", {f: w.temp_f}) : "",
    w.roof !== "dome" && w.wind_mph != null ? t("digest.wx.mph", {n: w.wind_mph}) + " " + t("digest.tn.wind") : "",
    w.short ? esc(w.short) : ""];
  return bits.filter(Boolean).join(" · ");
}

function dgTnCard(g){
  const sched = gdWeekGames().find(x => gdSameClub(x.home, g.home) || gdSameClub(x.away, g.home));
  return `<section class="dg-tn dg-mnf on" data-testid="digest-tn" aria-label="${t("digest.tn.label")}">${sched ? dgMnfFor(sched)
    : `<p class="dg-tn-on"><b>${esc(g.away)} @ ${esc(g.home)}</b> ${t("digest.tn.playing")}</p>`}</section>`;
}

/* `mnf` is the last game's card (mnf.js) when one shows: it stands in for the block of the same game, so that game is
   skipped here. A game still to kick off draws nothing here. */
function dgTonightHTML(d, mnf){
  const now = Date.now(), late = mnf ? dgMnfSlot(now) || [] : [];
  const held = g => late.some(x => gdSameClub(x.g.home, g.home) || gdSameClub(x.g.away, g.home));
  const cards = (d.tn || []).filter(g => Date.parse(g.ko) <= now && !held(g)).map(dgTnCard).join("");
  return mnf || cards ? `<div class="dg-tns">${mnf || ""}${cards}</div>` : "";
}
