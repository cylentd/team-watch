/* The first three profile sections: usage by zone, against coverage, red zone. Each leads with
   the one number that matters, then bars (a share against its average reads as a bar with a tick),
   then at most one short caption line. Pure functions of the profile; next.js holds the fourth. */
const pfPct = x => x === null || x === undefined ? "—" : Math.round(x * 100) + "%";
const DEPTH_ZONES = ["behind", "short", "intermediate", "deep"];
const SIDE_ZONES = ["middle", "outside"];

function zoneWord(z){
  return {behind: t("profile.zone.behind"), short: t("profile.zone.short"),
    intermediate: t("profile.zone.intermediate"), deep: t("profile.zone.deep"),
    middle: t("profile.zone.middle"), outside: t("profile.zone.outside")}[z] || esc(z);
}

/* One share as a bar. `avg` (optional) draws a tick and the gap to it in points. */
function shareBarHTML(label, share, avg, lead){
  const w = Math.max(0, Math.min(1, share || 0)) * 100;
  const gap = avg === null || avg === undefined || share === null ? null : Math.round((share - avg) * 100);
  return `<div class="pf-bar${lead ? " lead" : ""}${label ? "" : " bare"}">
    ${label ? `<span class="pf-bar-l">${label}</span>` : ""}
    <span class="pf-track"><i style="width:${w.toFixed(0)}%"></i>${gap === null ? "" : `<b class="pf-tick" style="left:${(avg * 100).toFixed(0)}%"></b>`}</span>
    <span class="pf-bar-v">${pfPct(share)}</span>
    <span class="pf-bar-d">${gap === null ? "" : (gap > 0 ? "+" : gap < 0 ? "−" : "±") + Math.abs(gap)}</span>
  </div>`;
}

function secHTML(label, body, legend){
  return `<section class="dr-sec pf-sec">
    <div class="pf-sechead"><span class="lbl">${label}</span>${legend ? `<span class="pf-legend"><i></i>${legend}</span>` : ""}</div>
    ${body}
  </section>`;
}

function leadHTML(num, text){
  return `<div class="pf-lead"><b>${num}</b><span>${text}</span></div>`;
}

function usageHTML(prof){
  const u = prof.usage || {};
  const pos = esc(prof.pos);
  if (!u.zones){
    const note = prof.pos === "RB" ? t("profile.usage.noZonesBack") : t("profile.usage.noZones", {pos});
    return secHTML(t("profile.usage.labelBack"),
      leadHTML(u.targets ?? "—", t("profile.usage.leadBack")) + `<p class="pf-cap">${note}</p>`);
  }
  const z = u.zones;
  const top = DEPTH_ZONES.filter(k => z[k]).sort((a, b) => z[b].share - z[a].share)[0];
  const bars = keys => keys.filter(k => z[k]).map(k => shareBarHTML(zoneWord(k), z[k].share, z[k].pos_avg, k === top)).join("");
  return secHTML(t("profile.usage.label"),
    leadHTML(pfPct(z[top].share), t("profile.usage.lead", {zone: zoneWord(top).toLowerCase(), pos, avg: pfPct(z[top].pos_avg)}))
    + `<div class="pf-bars">${bars(DEPTH_ZONES)}</div>`
    + `<div class="pf-sub lbl">${t("profile.usage.side")}</div>`
    + `<div class="pf-bars">${bars(SIDE_ZONES)}</div>`
    + `<p class="pf-cap">${t("profile.usage.cap", {targets: u.targets, weight: pfPct(u.weight), prior: u.prior_targets})}</p>`,
    t("profile.usage.legend", {pos}));
}

function coverageHTML(prof){
  const c = prof.coverage;
  if (!c){
    const receiver = prof.pos === "WR" || prof.pos === "TE";
    return secHTML(t("profile.coverage.labelBare"),
      `<p class="pf-cap pf-quiet">${receiver ? t("profile.coverage.none") : t("profile.coverage.noneBack")}</p>`);
  }
  const s = c.seasons || [];
  const span = s.length ? `${s[0]}–${String(s[s.length - 1]).slice(2)}` : "";
  const text = c.split > 0 ? t("profile.coverage.leadMan") : c.split < 0 ? t("profile.coverage.leadZone") : t("profile.coverage.leadEven");
  const row = (label, ypt, n) => `<tr><th scope="row">${label}</th><td>${ypt ?? "—"}</td><td>${n ?? "—"}</td></tr>`;
  return secHTML(t("profile.coverage.label", {span}),
    leadHTML(Math.abs(c.split ?? 0).toFixed(1), text)
    + `<table class="pf-table"><thead><tr><th></th><th>${t("profile.coverage.colYpt")}</th><th>${t("profile.coverage.colTargets")}</th></tr></thead>
      <tbody>${row(t("profile.coverage.man"), c.ypt_man, c.targets_man)}${row(t("profile.coverage.zone"), c.ypt_zone, c.targets_zone)}</tbody></table>`
    + `<p class="pf-cap pf-caution">${esc(c.note)}</p>`);
}

function redZoneHTML(prof){
  const r = prof.red_zone;
  if (!r) return "";
  const back = r.carries !== null && r.carries !== undefined;
  if (!back){   // one share: the lead says it all, a bar would only repeat it
    return secHTML(t("profile.rz.label", {wk: r.weeks}),
      leadHTML(pfPct(r.target_share), t("profile.rz.leadTargets", {n: r.targets ?? "—"})));
  }
  return secHTML(t("profile.rz.label", {wk: r.weeks}),
    leadHTML(pfPct(r.carry_share), t("profile.rz.leadCarries", {n: r.carries}))
    + `<div class="pf-bars">${shareBarHTML(t("profile.rz.targets", {n: r.targets ?? "—"}), r.target_share, null, false)}</div>`);
}
