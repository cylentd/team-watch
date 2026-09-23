/* The three profile blocks above Details: the matchup rank, his role, his red-zone share. Each
   leads with one number and closes on at most one line. Pure functions of the profile; the
   helpers here (bars, section, lead) are shared with details.js, which loads after. */
const pfPct = x => x === null || x === undefined ? "—" : Math.round(x * 100) + "%";
const DEPTH_ZONES = ["behind", "short", "intermediate", "deep"];
const SIDE_ZONES = ["middle", "outside"];

function zoneWord(z){
  return {behind: t("profile.zone.behind"), short: t("profile.zone.short"),
    intermediate: t("profile.zone.intermediate"), deep: t("profile.zone.deep"),
    middle: t("profile.zone.middle"), outside: t("profile.zone.outside")}[z] || esc(z);
}

function targetsText(n){
  return n === 1 ? t("profile.count.targetOne") : t("profile.count.targets", {n: n ?? "—"});
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

function secHTML(label, body, legend, cls){
  return `<section class="dr-sec pf-sec${cls ? " " + cls : ""}">
    <div class="pf-sechead"><span class="lbl">${label}</span>${legend ? `<span class="pf-legend"><i></i>${legend}</span>` : ""}</div>
    ${body}
  </section>`;
}

function leadHTML(num, text, cls){
  return `<div class="pf-lead${cls ? " " + cls : ""}"><b>${num}</b><span>${text}</span></div>`;
}

/* The matchup: the rank as a sentence, then as a cell on the strip of every defence
   (sheet.js), then the forecast at that stadium. */
function headlineHTML(prof){
  const nx = prof.next;
  if (!nx) return secHTML(t("profile.next.labelBare"), `<p class="pf-cap pf-quiet">${t("profile.next.bye")}</p>`);
  const n = easiestRank(nx.factor);
  const cls = n === null ? "" : matchupClass(n, nx.factor.of);
  const rank = n === null
    ? `<p class="pf-cap pf-quiet">${t("profile.matchup.none")}</p>`
    : `<p class="pf-rank ${cls}">${matchupRankText(prof)}</p>` + rankStripHTML(n, nx.factor.of, cls);
  return secHTML(t("profile.next.label", {wk: nx.week, where: whereWord(nx), opp: esc(nx.opp)}), rank + weatherHTML(prof));
}

/* His depth shares against the position's, one column per zone: his bar bright, the average
   dim beside it, both on the same scale (the tallest of either fills the column). */
function zonesHTML(z, top){
  const keys = DEPTH_ZONES.filter(k => z[k]);
  const max = Math.max(.01, ...keys.map(k => Math.max(z[k].share || 0, z[k].pos_avg || 0)));
  const h = v => (Math.max(0, v || 0) / max * 100).toFixed(0);
  return `<div class="pf-zones">${keys.map((k, i) => `<div class="pf-zone${k === top ? " top" : ""}" style="--i:${i}">
      <span class="pf-zone-bars"><i class="me" style="--h:${h(z[k].share)}%"></i><i class="avg" style="--h:${h(z[k].pos_avg)}%"></i></span>
      <em>${zoneWord(k)}</em><b>${pfPct(z[k].share)}</b><small>${pfPct(z[k].pos_avg)}</small>
    </div>`).join("")}</div>`;
}

/* Where his targets come from, for a receiver. A back has no depth zones, and his volume is
   already in the trend tiles, so he gets no block at all. */
function roleHTML(prof){
  const u = prof.usage || {};
  const z = u.zones;
  const pos = esc(prof.pos);
  if (!z) return "";
  const byShare = keys => keys.filter(k => z[k]).sort((a, b) => z[b].share - z[a].share)[0];
  const top = byShare(DEPTH_ZONES), side = byShare(SIDE_ZONES);
  const line = [targetsText(u.targets)]
    .concat(side ? [t("profile.role.side", {pct: pfPct(z[side].share), side: zoneWord(side).toLowerCase()})] : [])
    .join(" · ");
  return secHTML(t("profile.role.label"),
    leadHTML(pfPct(z[top].share), t("profile.role.lead", {zone: zoneWord(top).toLowerCase(), pos, avg: pfPct(z[top].pos_avg)}))
    + zonesHTML(z, top)
    + `<p class="pf-cap">${line}</p>`,
    t("profile.role.legend", {pos}), "pf-sec-zones");
}

/* Counts while the team total is under 10 ("1 of 5"), a share with its counts from 10 up. */
function rzLineHTML(n, team, share, nouns, second){
  const noun = team === 1 ? nouns[0] : nouns[1];
  const cls = second ? "rz sub" : "rz";
  if (team === null || team === undefined) return leadHTML(pfPct(share), noun, cls);
  const num = team < 10 ? t("profile.rz.count", {n, team}) : t("profile.rz.share", {pct: pfPct(share), n, team});
  return leadHTML(num, noun, cls);
}

/* A receiver: his targets. A back: carries first, targets second. Under each line, the team's
   touches as a bar with the teammates who took the rest (sheet.js rzSplitHTML). */
function redZoneHTML(prof){
  const r = prof.red_zone;
  if (!r) return "";
  // A passer has no red-zone role of either kind: no block at all, rather than a dash and a noun.
  if ((r.team_targets ?? null) === null && (r.team_carries ?? null) === null) return "";
  const back = r.carries !== null && r.carries !== undefined, others = r.others || [];
  const targets = rzLineHTML(r.targets ?? 0, r.team_targets, r.target_share,
      [t("profile.rz.teamTarget"), t("profile.rz.teamTargets")], back)
    + rzSplitHTML(r.targets ?? 0, r.team_targets, others, "targets", prof.n);
  const carries = back
    ? rzLineHTML(r.carries, r.team_carries, r.carry_share, [t("profile.rz.teamCarry"), t("profile.rz.teamCarries")], false)
      + rzSplitHTML(r.carries, r.team_carries, others, "carries", prof.n) : "";
  return secHTML(t("profile.rz.label"), carries + targets);
}
