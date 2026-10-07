/* ============================== DIGEST: A CARD ==============================
   2026-10-06, storyboard "Digest by Day". The day plan (data/digest.js DG_PLAN) names each day's cards;
   this file is the shell they share and the one place that calls them.

   THE CARD INTERFACE. One file per card under cards/, one function per card:

     function dgCard<Name>(ctx) -> HTML, or "" when it has nothing to show (the day then skips it)

   ctx (dgCardCtx), every block null when the page lacks it:
     day       the plan's key, "tue" ... "mon": a card on two days reads it (dgCardGame's title, dgCardStatus's Q-only Thursday)
     plan, now the day plan and the clock (ms) the page drew at
     recordBy  the card that drew Start/Sit's record this render (dgRecordFoot): the record is not repeated on a second card
     d         LIVE_DIGEST as cut for the clock (dgD: adds, hurt, starters, tn, ...)
     ss3, sos, def, preview, schedule, usage, ranks
               LIVE_SS3, LIVE_SOS, LIVE_DEFENSE, LIVE_PREVIEW, LIVE_SCHEDULE, LIVE_USAGE_MOVERS, LIVE_RANKS

   A card draws its rows with dgRowHTML (row.js) and wraps them with dgCardHTML. Copy goes under
   `digest.card.<name>.*`; a pick word or flag with no tested model carries its mark (tests/test_flag_marks.py).
   Card style: one subject, --panel fill, 1px --line border, 16px radius, rows divided by --line (DESIGN.md "Cards"). */

/* `more` is the view that holds the whole list: {leaf, label} (the label defaults to the nav's own). */
function dgCardHTML({id, title, more, body, foot}){
  const go = more ? `<button type="button" class="dg-card-more" data-testid="digest-card-more" data-dggo="${esc(more.leaf)}">${more.label || navLabel(more.leaf)}${DG_ARROW}</button>` : "";
  return `<section class="dg-card" data-testid="digest-card" data-dgcard="${esc(id)}" aria-labelledby="dg-c-${esc(id)}">
    <header class="dg-card-h"><h3 class="dg-card-t" id="dg-c-${esc(id)}" data-testid="digest-card-title">${title}</h3>${go}</header>
    ${body}${foot ? `<p class="dg-card-f" data-testid="digest-card-foot">${foot}</p>` : ""}</section>`;
}

const dgLive = {
  ss3: () => typeof LIVE_SS3 !== "undefined" ? LIVE_SS3 : null,
  sos: () => typeof LIVE_SOS !== "undefined" ? LIVE_SOS : null,
  def: () => typeof LIVE_DEFENSE !== "undefined" ? LIVE_DEFENSE : null,
  preview: () => typeof LIVE_PREVIEW !== "undefined" ? LIVE_PREVIEW : null,
  schedule: () => typeof LIVE_SCHEDULE !== "undefined" ? LIVE_SCHEDULE : null,
  usage: () => typeof LIVE_USAGE_MOVERS !== "undefined" ? LIVE_USAGE_MOVERS : null,
  ranks: () => typeof LIVE_RANKS !== "undefined" ? LIVE_RANKS : null,
};

function dgCardCtx(d, plan, now){
  return {day: plan.key, plan, now, d, recordBy: null, ...Object.fromEntries(Object.entries(dgLive).map(([k, f]) => [k, f() || null]))};
}

/* One card's HTML by its plan id. Need to know and Right now are the Digest's own sections (need.js,
   now.js); Need to know is not drawn once games are on and nothing in it is left to say. */
function dgCardDraw(id, ctx){
  if (id === "need") return ctx.d && !dgNeedEmpty(ctx.d) ? dgNeedHTML(ctx.d) : "";
  if (id === "now") return ctx.d ? dgNowHTML() : "";
  const card = {adds: dgCardAdds, gains: dgCardGains, usage: dgCardUsage, defenses: dgCardDefenses, status: dgCardStatus,
    vegas: dgCardVegas, game: dgCardGame, smash: dgCardSmash, bold: dgCardBold, calls: dgCardCalls, weather: dgCardWeather}[id];
  return card ? card(ctx) || "" : "";
}

/* Start/Sit's record, for the foot of a card of its calls (SMASH, Bold calls, Start in this game; the cards ask
   dgRecordFoot below): the numbers the view prints, then what each call has been through. */
function dgCardRecord(ss3){
  const r = ss3 && ss3.record;
  if (!r) return "";
  const rec = ss3Graded(r) ? t("digest.foot.mu", {wk: r.since_week, smash: ss3Wl(r.smash), start: ss3Wl(r.start), sit: ss3Wl(r.sit)})
    : t("digest.foot.muNone", {wk: r.since_week});
  return `${rec} ${t("digest.foot.muMark")}`;
}

/* The record for the card `id`, or "": it is said once a day, on the first of those cards that draws (the plan
   draws them in order, and a card that returns early never asks), so SMASH and Bold calls do not repeat it. The
   claim is kept on ctx, and the same card asking again (a repaint of one card) gets it again. */
function dgRecordFoot(ctx, id){
  const rec = dgCardRecord(ctx.ss3);
  if (!rec) return "";
  if (!ctx.recordBy) ctx.recordBy = id;
  return ctx.recordBy === id ? rec : "";
}
