/* The Waivers sub-tab of My Teams, for ONE league: the one the team dropdown has on screen (VIEW).
   Its tiers, swaps, drops, hero and Breaking rail are that league's; the other leagues shrink to
   one line on each card's back. Must-claims all show; Worth and Watch stop at five, because a
   sixth "worth a look" is a list, not advice; Speculative and Stash fold shut behind a count.

   Two shapes by weekday (wvMode): on claim day the cards lead and the rail sits under the hero,
   three rows deep; the rest of the week the rail leads and the cards follow. */
const WV_CAP = 5;

/* `deal` numbers the cards across sections, so they land in rank order. */
function wvSectionHTML(title, list, cap, key, deal){
  if (!list.length) return "";
  const shown = cap ? list.slice(0, cap) : list;
  const more = list.length - shown.length;
  return `<div class="rule"><h2 title="${t("waiver.tier.mark")}">${title}</h2>${wvCountHTML(list.length)}<span class="hair"></span>
      ${more ? `<span class="side">${t("waiver.section.more", {n: more})}</span>` : ""}</div>
    <div class="wvc-list">${shown.map(([r, i]) => wvCardHTML(r, i, deal.n++, key)).join("")}</div>`;
}

function wvFoldHTML(label, list, key, deal){
  if (!list.length) return "";
  return `<details class="wvfold"><summary class="wvfold-s" title="${t("waiver.tier.mark")}">${label}</summary>
    <div class="wvc-list">${list.map(([r, i]) => wvCardHTML(r, i, deal.n++, key)).join("")}</div></details>`;
}

function wvCardsHTML(key, blk){
  const all = waiverIn(key, blk);
  if (!all.length) return `<div class="state-empty wv-empty"><div><b>0</b><span>${t("waiver.empty.noWire")}</span></div></div>`;
  const tier = k => all.filter(([r]) => waiverTier(r, key) === k);
  const spec = tier("spec"), stash = tier("stash"), deal = {n: 0};
  return wvSectionHTML(t("waiver.section.must"), tier("must"), 0, key, deal)
    + wvSectionHTML(t("waiver.section.worth"), tier("worth"), WV_CAP, key, deal)
    + wvSectionHTML(t("waiver.section.watch"), tier("watch"), WV_CAP, key, deal)
    + wvFoldHTML(t("waiver.fold.spec", {n: spec.length}), spec, key, deal)
    + wvFoldHTML(t("waiver.fold.stash", {n: stash.length}), stash, key, deal);
}

/* `motion` is wvMotionTake()'s {deal, since}: whether the cards are dealt, and which rail rows
   are new. The markup is otherwise the same on every render. */
function waiverHTML(motion){
  // Anyone but David (data/owner.js) gets the league-wide Most added list, unless the team on screen has
  // cards of its own (a leaguemate's, ledger #22): those are the team's and no secret.
  const team = TEAMS[VIEW], own = wvOwn(team), blk = waiverBlock(team);
  if (!isOwner() && !own) return wvDstLinkHTML() + wvHotHTML();
  if (!WAIVER && !own) return `<div class="state-empty wv-empty"><div><b>—</b><span>${t("waiver.empty.noPacket")}</span></div></div>`;
  const key = waiverKey(team), mate = notMine(team);
  if (!waiverMeta(blk)[key]) return `<div class="state-empty wv-empty"><div><b>—</b><span>${t("waiver.hero.none")}</span></div></div>`;
  const mode = wvMode(), m = motion || {deal: false, since: Infinity};
  // A leaguemate with a packet of its own gets its cards (tiers, swaps and drops judged against its roster);
  // the rail is the league's whoever looks, with David's status rows and verdicts out (`mate`). One without
  // a packet gets the rail alone, which leads every day: the "watch" shape, whatever the weekday.
  const shape = own ? mode : "watch";
  const rail = wvRailHTML(key, shape, m.since, mate);
  const cards = own ? `<div class="wv-cards">${wvCardsHTML(key, blk)}</div>` : `<p class="wv-mate">${t("waiver.mate.soon")}</p>`;
  return `${wvDstLinkHTML()}<div class="wv mode-${shape}${m.deal ? " deal" : ""}">${rail}${cards}</div>`;
}

/* The way into Ranks > D/ST (rkOpenDst, surface/ranks/dst.js): a D/ST is streamed by the week's matchup, not by
   the wire's usage, so the list that shows it lives in Ranks. Taps from the Digest: League, Waivers, this
   link = 3 (Stats, Ranks, D/ST is also 3); on a Tuesday, when Waivers opens first, it is 1. Drawn only when
   the page has the D/ST file. */
const wvDstLinkHTML = () => typeof rkDstBlock === "function" && rkDstBlock()
  ? `<p class="wv-dst"><button type="button" class="btn ghost" data-wvdst>${t("waiver.dst.link")}</button></p>` : "";

/* The hero on Waivers, one line for the league on screen: which day of the week it is for the
   wire, when its claims clear, how many must-claims are open there, and what is left to bid. */
function waiverHeroHTML(team){
  const key = waiverKey(team), mate = notMine(team) || !isOwner();   // David's numbers are his browser's alone
  const own = wvOwn(team), blk = waiverBlock(team);
  const meta = waiverMeta(blk)[key];
  if (!meta) return `<p class="wvhero empty">${t("waiver.hero.none")}</p>`;
  const when = waiverWhen(meta.clears || (WAIVER && WAIVER.clears));
  const n = waiverMustIn(key, blk);
  // The hero keeps the league's facts (the day, when claims clear). The must-claim count is the team's own
  // when it has cards (David's, or a leaguemate's packet); FAAB is David's alone, a site shows a budget
  // to its own manager only.
  const parts = [
    `<span class="wvhero-mode">${wvMode() === "claim" ? t("waiver.hero.claimDay") : t("waiver.hero.wireWatch")}</span>`,
    when ? `<span>${t("waiver.hero.clears", {when})}</span>` : "",
    own ? `<span class="${n ? "up" : ""}" title="${t("waiver.tier.mark")}">${n === 1 ? t("waiver.hero.mustOne") : t("waiver.hero.must", {n})}</span>` : "",
    mate || meta.faab_left === null || meta.faab_left === undefined ? "" : `<span>${t("waiver.hero.faab", {n: meta.faab_left})}</span>`,
  ].filter(Boolean);
  // Each part keeps its words together; a narrow hero breaks between parts, never inside one.
  return `<p class="wvhero">${parts.join(` <span class="sep">·</span> `)}</p>`;
}
