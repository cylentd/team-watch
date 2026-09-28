/* Waivers for everyone but David (2026-09-27): the Digest's "Most added" list, league-wide, the same
   for every reader and every team. No tier, no swap, no drop: nothing judged against a roster. Data:
   LIVE_DIGEST.adds (design/digest.py): Sleeper's adds over the last day since 2026-09-28, else ESPN
   % rostered last week and this week. A name opens the profile. */
function wvHotHTML(){
  const d = dgD(), rows = (d && d.adds) || [];
  if (!rows.length) return `<p class="wv-mate">${t("waiver.hot.none")}</p>`;
  const [a, b] = d.adds_weeks || [];
  const sub = d.adds_source === "sleeper" ? t("waiver.hot.subSleeper", {h: d.adds_hours})
    : a != null ? t("waiver.hot.sub", {a, b}) : t("waiver.hot.subNoWeeks");
  const row = (r, i) => `<li><button type="button" class="wv-hot-p" data-hot="${i}">
      <b>${esc(nameInitial(r.n))}</b><span>${esc(r.pos)} · ${esc(r.team)}</span></button>
    <span class="wv-hot-pct">${d.adds_source === "sleeper" ? dgAddCount(r) : `${dgPct(r.was)}% → <b>${dgPct(r.now)}%</b>`}</span></li>`;
  return `<section class="wv-hot" aria-label="${t("waiver.hot.title")}">
    <div class="rule"><h2>${t("waiver.hot.title")}</h2><span class="hair"></span></div>
    <p class="wv-hot-sub">${sub}</p><ol>${rows.map(row).join("")}</ol></section>`;
}

function wireHot(v){
  const rows = (dgD() || {}).adds || [];
  v.querySelectorAll("[data-hot]").forEach(el => el.addEventListener("click", () => {
    const r = rows[+el.dataset.hot];
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
