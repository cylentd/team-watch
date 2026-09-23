/* The Waivers sub-tab of My Teams: the packet's candidates as cards, grouped by tier. Must-claims
   all show; Worth and Watch stop at five, because a sixth "worth a look" is a list, not advice;
   Speculative (one week of evidence) and Stash fold shut behind a count. The cards are the same
   whichever team is on screen -- each carries a row per league -- and only the hero is per team. */
const WV_CAP = 5;

function wvSectionHTML(title, list, cap){
  if (!list.length) return "";
  const shown = cap ? list.slice(0, cap) : list;
  const more = list.length - shown.length;
  return `<div class="rule"><h2>${title}</h2><span class="count">${String(list.length).padStart(2, "0")}</span><span class="hair"></span>
      ${more ? `<span class="side">${t("waiver.section.more", {n: more})}</span>` : ""}</div>
    <div class="wvc-list">${shown.map(([r, i], n) => wvCardHTML(r, i, n)).join("")}</div>`;
}

function wvFoldHTML(label, list){
  if (!list.length) return "";
  return `<details class="wvfold"><summary class="wvfold-s">${label}</summary>
    <div class="wvc-list">${list.map(([r, i], n) => wvCardHTML(r, i, n)).join("")}</div></details>`;
}

function waiverHTML(){
  if (!WAIVER) return `<div class="state-empty wv-empty"><div><b>—</b><span>${t("waiver.empty.noPacket")}</span></div></div>`;
  const all = waiverPlayers().map((r, i) => [r, i]);
  const tier = k => all.filter(([r]) => r.tier === k);
  if (!all.length) return `<div class="state-empty wv-empty"><div><b>0</b><span>${t("waiver.empty.noWire")}</span></div></div>`;
  const spec = tier("spec"), stash = tier("stash");
  return wvSectionHTML(t("waiver.section.must"), tier("must"), 0)
    + wvSectionHTML(t("waiver.section.worth"), tier("worth"), WV_CAP)
    + wvSectionHTML(t("waiver.section.watch"), tier("watch"), WV_CAP)
    + wvFoldHTML(t("waiver.fold.spec", {n: spec.length}), spec)
    + wvFoldHTML(t("waiver.fold.stash", {n: stash.length}), stash);
}

/* The hero on Waivers, one line for the team on screen: when its claims clear, how many
   must-claims are open in that league, and what is left to bid there. */
function waiverHeroHTML(team){
  const meta = waiverMeta()[team.key];
  if (!meta) return `<p class="wvhero empty">${t("waiver.hero.none")}</p>`;
  const when = waiverWhen(meta.clears || (WAIVER && WAIVER.clears));
  const n = waiverMustIn(team.key);
  const parts = [
    when ? `<span>${t("waiver.hero.clears", {when})}</span>` : "",
    `<span class="${n ? "up" : ""}">${n === 1 ? t("waiver.hero.mustOne") : t("waiver.hero.must", {n})}</span>`,
    meta.faab_left === null || meta.faab_left === undefined ? "" : `<span>${t("waiver.hero.faab", {n: meta.faab_left})}</span>`,
  ].filter(Boolean);
  // Each part keeps its words together; a narrow hero breaks between parts, never inside one.
  return `<p class="wvhero">${parts.join(` <span class="sep">·</span> `)}</p>`;
}
