/* The finer reads the panes are built from: the zone read, his coverage split, middle vs
   outside, the opponent's rates and raw factor, and the blend note. Each is a block a pane
   composes (tabs.js), not a section on its own -- they used to sit behind a "Details"
   disclosure inside an already-stacked column, which is a second level of hiding under a first
   level nobody had got through. The one METHODOLOGY citation lives in the method line; the
   coverage note drops its own. */
function subHTML(label, body, extra){
  return `<div class="pf-dsec">
    <div class="pf-sechead"><span class="lbl">${label}</span>${extra || ""}</div>
    ${body}
  </div>`;
}

function zoneReadHTML(prof){
  const nx = prof.next;
  if (!nx) return "";
  if (!nx.zones || !nx.zones.length) return subHTML(t("profile.zoneRead.label"), `<p class="pf-cap pf-quiet">${t("profile.zoneRead.empty")}</p>`);
  const tag = nx.tested ? "" : `<span class="pf-tag">${t("profile.zoneRead.untested")}</span>`;
  return subHTML(t("profile.zoneRead.label"), `<table class="pf-table">
    <thead><tr><th>${t("profile.zoneRead.colZone")}</th><th>${t("profile.zoneRead.colIndex")}</th><th>${t("profile.zoneRead.colRank")}</th><th>${t("profile.zoneRead.colFaced")}</th></tr></thead>
    <tbody>${nx.zones.map(z => `<tr><th scope="row">${zoneWord(z.zone)}</th><td>${Number(z.def_index).toFixed(2)}x</td><td>${z.rank}<small>/${z.of}</small></td><td>${z.targets}</td></tr>`).join("")}</tbody>
  </table>
  <p class="pf-cap pf-fine">${esc(nx.method)}</p>`, tag);
}

function coverageHTML(prof){
  const c = prof.coverage;
  if (!c) return subHTML(t("profile.coverage.labelBare"), `<p class="pf-cap pf-quiet">${t("profile.coverage.none")}</p>`);
  const s = c.seasons || [];
  const span = s.length ? `${s[0]}–${String(s[s.length - 1]).slice(2)}` : "";
  const gap = Math.abs(c.split ?? 0).toFixed(1);
  const words = c.split > 0 ? t("profile.coverage.leadMan", {n: gap}) : c.split < 0 ? t("profile.coverage.leadZone", {n: gap}) : t("profile.coverage.leadEven");
  const ypt = v => v === null || v === undefined ? "—" : Number(v).toFixed(1);
  const row = (label, v, n) => `<tr><th scope="row">${label}</th><td>${ypt(v)}</td><td>${n ?? "—"}</td></tr>`;
  const note = String(c.note || "").replace(/,?\s*METHODOLOGY [\d.\-–]+/g, "");
  return subHTML(t("profile.coverage.label", {span}),
    `<p class="pf-say">${words}</p>`
    + `<table class="pf-table"><thead><tr><th></th><th>${t("profile.coverage.colYpt")}</th><th>${t("profile.coverage.colTargets")}</th></tr></thead>
      <tbody>${row(t("profile.coverage.man"), c.ypt_man, c.targets_man)}${row(t("profile.coverage.zone"), c.ypt_zone, c.targets_zone)}</tbody></table>`
    + (note ? `<p class="pf-cap pf-caution">${esc(note)}</p>` : ""));
}

function sidesHTML(prof){
  const z = prof.usage && prof.usage.zones;
  if (!z) return "";
  const bars = SIDE_ZONES.filter(k => z[k]).map(k => shareBarHTML(zoneWord(k), z[k].share, z[k].pos_avg, false)).join("");
  return subHTML(t("profile.side.label"), `<div class="pf-bars">${bars}</div>`,
    `<span class="pf-legend"><i></i>${t("profile.role.legend", {pos: esc(prof.pos)})}</span>`);
}

function opponentHTML(prof){
  const nx = prof.next;
  if (!nx) return "";
  const stale = nx.dc_same === false
    ? `<span class="pf-stale" title="${t("profile.next.staleTip", {season: nx.man_season})}">${t("profile.next.stale")}</span>` : "";
  const man = nx.man_pct === null || nx.man_pct === undefined ? "" : `
    <div class="pf-metric">
      <div class="pf-metric-h"><span>${t("profile.next.man", {season: nx.man_season})}</span>${stale}</div>
      ${shareBarHTML("", nx.man_pct, nx.man_pct_league, false)}
    </div>`;
  const rz = !nx.rz ? "" : `
    <div class="pf-metric">
      <div class="pf-metric-h"><span>${t("profile.next.rz", {n: nx.rz.faced})}</span></div>
      ${shareBarHTML("", nx.rz.rate, nx.rz.league_rate, false)}
    </div>`;
  const f = nx.factor;
  const factor = !f ? "" : `<div class="pf-factor"><span>${t("profile.next.factor")}</span><b>${Number(f.factor).toFixed(2)}x</b></div>`
    + (nx.tested ? `<p class="pf-cap pf-fine">${esc(nx.method)}</p>` : "");
  return subHTML(t("profile.next.opponent", {opp: esc(nx.opp)}),
    `<div class="pf-metrics">${man}${rz}</div>` + factor,
    `<span class="pf-legend"><i></i>${t("profile.next.legend")}</span>`);
}

/* His own team's offensive line this week, from LIVE_TRENCHES. `ol_starters_out` is the lead
   cell: of the five usual starters (ranked by snaps through last week), how many this week's
   injury report lists Out or Doubtful -- the before-kickoff answer to "is his line down
   starters this week". `ol_continuity` (usual starters who actually played) only fills in after
   the game, so it stays as its own cell. The plain injury-report count is the weaker signal --
   every lineman on the report, starter or not -- so it only shows when `ol_starters_out` is
   null (no starting five known yet). Labelled with the team, never with him, because a team
   number beside a player's stats is otherwise read as his. A null field is a count ff-jarvis
   could not take (bye, week not played, report not out) and draws nothing; a real 0 is drawn,
   in the plain colour -- amber is reserved for a real starter actually out. */
const LINE_POS = ["QB", "RB", "WR", "TE"];
function lineHTML(prof){
  if (typeof LIVE_TRENCHES === "undefined" || !LIVE_TRENCHES || !LINE_POS.includes(prof.pos)) return "";
  const r = LIVE_TRENCHES.teams[prof.team];
  if (!r) return "";
  const by = r.ol_out_by_status || {};
  const named = Object.keys(by).filter(k => k !== "none" && by[k] > 0);
  const hurt = named.some(k => /^(out|doubtful)$/i.test(k));
  const cell = (v, words, down, title) => `<span class="pf-wx-c"${title ? ` title="${esc(title)}"` : ""}><b${down ? ` class="down"` : ""}>${v}</b><em>${words}</em></span>`;
  const startersKnown = r.ol_starters_out !== null && r.ol_starters_out !== undefined && r.ol_starters_out_of;
  const starterNames = r.ol_starters_out_names || [];
  const starters = !startersKnown ? "" : cell(`${r.ol_starters_out}/${r.ol_starters_out_of}`,
    t("profile.line.startersOut"), r.ol_starters_out >= 1, starterNames.length ? starterNames.join(", ") : "");
  const list = named.map(k => `${by[k]} ${esc(k.toLowerCase())}`).join(", ");
  // One lineman is "lineman": a literal key per count, because the copy check sees only literal lookups.
  const outWords = r.ol_out === 1
    ? (named.length ? t("profile.line.outListOne", {list}) : t("profile.line.outOne"))
    : (named.length ? t("profile.line.outList", {list}) : t("profile.line.out"));
  const out = startersKnown || r.ol_out === null || r.ol_out === undefined ? "" : cell(r.ol_out, outWords, hurt);
  const kept = r.ol_continuity === null || r.ol_continuity === undefined || !r.ol_continuity_of ? ""
    : cell(`${r.ol_continuity}/${r.ol_continuity_of}`, t("profile.line.kept"), r.ol_continuity < r.ol_continuity_of);
  if (!starters && !out && !kept) return "";
  const wk = LIVE_TRENCHES.week ? `<span class="pf-win">${t("profile.line.week", {wk: LIVE_TRENCHES.week})}</span>` : "";
  return subHTML(t("profile.line.label", {team: esc(prof.team)}), `<div class="pf-wx pf-line">${starters}${kept}${out}</div>`, wk);
}

function blendedHTML(prof){
  const u = prof.usage;
  if (!u || u.targets === null || u.targets === undefined) return "";
  return `<p class="pf-cap pf-blend">${t("profile.details.blended", {targets: targetsText(u.targets), weight: pfPct(u.weight), prior: u.prior_targets ?? "—"})}</p>`;
}

