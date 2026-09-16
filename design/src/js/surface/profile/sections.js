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

function secHTML(label, body, legend){
  return `<section class="dr-sec pf-sec">
    <div class="pf-sechead"><span class="lbl">${label}</span>${legend ? `<span class="pf-legend"><i></i>${legend}</span>` : ""}</div>
    ${body}
  </section>`;
}

function leadHTML(num, text, cls){
  return `<div class="pf-lead${cls ? " " + cls : ""}"><b>${num}</b><span>${text}</span></div>`;
}

function headlineHTML(prof){
  const nx = prof.next;
  if (!nx) return secHTML(t("profile.next.labelBare"), `<p class="pf-cap pf-quiet">${t("profile.next.bye")}</p>`);
  const n = easiestRank(nx.factor);
  return secHTML(t("profile.next.label", {wk: nx.week, where: whereWord(nx), opp: esc(nx.opp)}), n === null
    ? `<p class="pf-cap pf-quiet">${t("profile.matchup.none")}</p>`
    : `<p class="pf-rank ${matchupClass(n, nx.factor.of)}">${matchupRankText(prof)}</p>`);
}

/* His depth shares as one stacked bar, the position average as ticks at its cumulative edges. */
function stackHTML(z, top){
  const keys = DEPTH_ZONES.filter(k => z[k]);
  let edge = 0;
  const ticks = keys.slice(0, -1).map(k => {
    edge += z[k].pos_avg || 0;
    return `<b class="pf-tick" style="left:${(Math.min(1, edge) * 100).toFixed(1)}%"></b>`;
  }).join("");
  const segs = keys.map(k => `<i class="pf-seg${k === top ? " top" : ""}" style="width:${(Math.max(0, z[k].share || 0) * 100).toFixed(1)}%"></i>`).join("");
  const legend = keys.map(k => `<span class="pf-key${k === top ? " top" : ""}"><em>${zoneWord(k)}</em><b>${pfPct(z[k].share)}</b></span>`).join("");
  return `<div class="pf-stack"><span class="pf-stack-track">${segs}${ticks}</span><div class="pf-keys">${legend}</div></div>`;
}

function roleHTML(prof){
  const u = prof.usage || {};
  const z = u.zones;
  const pos = esc(prof.pos);
  if (!z){
    const note = prof.pos === "RB" ? t("profile.role.noZonesBack") : t("profile.role.noZones", {pos});
    return secHTML(t("profile.role.label"),
      leadHTML(u.targets ?? "—", u.targets === 1 ? t("profile.role.seasonOne") : t("profile.role.season"))
      + `<p class="pf-cap pf-quiet">${note}</p>`);
  }
  const byShare = keys => keys.filter(k => z[k]).sort((a, b) => z[b].share - z[a].share)[0];
  const top = byShare(DEPTH_ZONES), side = byShare(SIDE_ZONES);
  const line = [targetsText(u.targets)]
    .concat(side ? [t("profile.role.side", {pct: pfPct(z[side].share), side: zoneWord(side).toLowerCase()})] : [])
    .join(" · ");
  return secHTML(t("profile.role.label"),
    leadHTML(pfPct(z[top].share), t("profile.role.lead", {zone: zoneWord(top).toLowerCase(), pos, avg: pfPct(z[top].pos_avg)}))
    + stackHTML(z, top)
    + `<p class="pf-cap">${line}</p>`,
    t("profile.role.legend", {pos}));
}

/* Counts while the team total is under 10 ("1 of 5"), a share with its counts from 10 up. */
function rzLineHTML(n, team, share, nouns, second){
  const noun = team === 1 ? nouns[0] : nouns[1];
  const cls = second ? "rz sub" : "rz";
  if (team === null || team === undefined) return leadHTML(pfPct(share), noun, cls);
  const num = team < 10 ? t("profile.rz.count", {n, team}) : t("profile.rz.share", {pct: pfPct(share), n, team});
  return leadHTML(num, noun, cls);
}

/* A receiver: his targets. A back: carries first, targets second. */
function redZoneHTML(prof){
  const r = prof.red_zone;
  if (!r) return "";
  const back = r.carries !== null && r.carries !== undefined;
  const targets = rzLineHTML(r.targets ?? 0, r.team_targets, r.target_share,
    [t("profile.rz.teamTarget"), t("profile.rz.teamTargets")], back);
  const carries = back
    ? rzLineHTML(r.carries, r.team_carries, r.carry_share, [t("profile.rz.teamCarry"), t("profile.rz.teamCarries")], false) : "";
  return secHTML(t("profile.rz.label"), carries + targets);
}
