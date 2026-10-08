/* DIGEST CARD: the week's tiers (every day, after the day's job; 2026-10-08, Home draft B, ledger #52). One line of
   names per tier, as Boris Chen sets them, so any reader finds his own players in a glance without Home knowing his
   team. Chips QB RB WR TE FLEX over the lines; the tiers, their order and the cut are LIVE_RANKS' own (data/tiers.js
   dgTierLines takes whole tiers until a 12-team league's starters are in). A name opens his profile; a Q or D
   follows a hurt name in amber. The header link opens Players > Ranks on the same position. Interface: card.js;
   returns "" without a ranked list. */

let DG_TIER_PICK = null;   // the reader's chip this visit; the day's position until then (dgTierPos)

const dgTierList = (ranks, pos) => !ranks ? [] : pos === "FLEX" ? ranks.flex || [] : (ranks.rows || []).filter(r => r.pos === pos);

function dgTierNameHTML(r){
  const tag = r.inj === "Q" ? t("digest.card.pill.q") : r.inj === "D" ? t("digest.card.pill.d") : "";
  return `<button type="button" class="dg-tr-n" data-testid="digest-tier-name" data-dgslug="${esc(r.slug)}">${esc(dgShort(r.n))}${
    tag ? `<b class="dg-tr-q">${tag}</b>` : ""}</button>`;
}

function dgTierChipsHTML(pos){
  return `<div class="dg-tr-chips" role="group" aria-label="${t("digest.card.tiers.chips")}">${DG_TIER_POSITIONS.map(p =>
    `<button type="button" class="dg-tr-chip" data-testid="digest-tier-chip" data-dgtier="${p}" aria-pressed="${p === pos}">${
      p === "FLEX" ? t("ranks.filter.flex") : p}</button>`).join("")}</div>`;
}

function dgCardTiers(ctx){
  const pos = dgTierPos(ctx.day, DG_TIER_PICK), cut = dgTierLines(dgTierList(ctx.ranks, pos), DG_TIER_DEPTH[pos]);
  if (!cut.tiers.length) return "";
  const lines = cut.tiers.map(g => `<div class="dg-tr-row" data-testid="digest-tier-row"><dt>${t("digest.card.tiers.tier", {n: g.tier})}</dt>
    <dd>${g.rows.map(dgTierNameHTML).join("")}</dd></div>`).join("");
  const wk = schedWeek(), scoring = ctx.ranks.scoring || "";
  const posName = pos === "FLEX" ? t("ranks.filter.flex") : pos;
  const span = t("digest.card.tiers.span", {pos: posName, n: cut.shown, of: cut.of});
  return dgCardHTML({id: "tiers", title: wk ? t("digest.card.tiers.title", {week: wk}) : t("digest.card.tiers.titleNoWeek"),
    more: {leaf: "ranks"}, body: `${dgTierChipsHTML(pos)}<dl class="dg-tr">${lines}</dl>`,
    foot: scoring ? t("digest.card.tiers.foot", {span, scoring: esc(scoring)}) : span});
}

/* A chip redraws the card in place (nothing above it moves); Ranks › opens Ranks on the position on screen.
   `redrawn`: the card was just swapped, so its names and its link need the listeners wireDigest gave the first one. */
function wireDigestTiers(root, redrawn){
  const card = root && root.querySelector('[data-dgcard="tiers"]');
  if (!card) return;
  card.querySelectorAll("[data-dgtier]").forEach(b => b.addEventListener("click", () => {
    if (b.getAttribute("aria-pressed") === "true") return;
    DG_TIER_PICK = b.dataset.dgtier;
    card.outerHTML = dgCardTiers(dgCardCtx(dgD(), dgDayPlan(Date.now()), Date.now()));
    wireDigestTiers(root, true);
    root.querySelector(`[data-dgcard="tiers"] [data-dgtier="${DG_TIER_PICK}"]`)?.focus();
  }));
  const more = card.querySelector('[data-testid="digest-card-more"]');
  // Capture, so the position is set before the card's own link (wireDigest's data-dggo) opens Ranks.
  more?.addEventListener("click", () => statsPick(dgTierPos(dgDayPlan(Date.now()).key, DG_TIER_PICK)), {capture: true});
  if (!redrawn) return;
  card.querySelectorAll("[data-dgslug]").forEach(el => el.addEventListener("click", () => dgOpenSlug(el)));
  more?.addEventListener("click", () => { morphLogo(); navGo("ranks"); window.scrollTo({top: 0}); });
}
