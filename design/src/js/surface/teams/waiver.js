/* The Waivers sub-tab of My Teams: suggested moves (only when the packet has any), then the wire
   screen ranked by the packet. A row reads left to right as the decision does: who he is, why he
   is here (the lane's own evidence), what he is worth next week against his price, and whether
   that beats the starter he would replace. */
const wvPts = v => v === null || v === undefined ? "—" : Number(v).toFixed(1);
const wvSigned = v => v === null || v === undefined ? "—" : (v > 0 ? "+" : "") + Number(v).toFixed(1);
const wvPct = v => v === null || v === undefined ? null : `${Math.round(v)}%`;
/* Literal keys, so assemble.py's copy check sees every one. */
const WV_LANE = {
  usage: () => [t("waiver.lane.usage"), t("waiver.lane.usageTip")],
  open:  () => [t("waiver.lane.open"),  t("waiver.lane.openTip")],
  role:  () => [t("waiver.lane.role"),  t("waiver.lane.roleTip")],
};
const WV_MOVE = {add: () => t("waiver.move.add"), stash: () => t("waiver.move.stash"), drop: () => t("waiver.move.drop")};

function waiverWhy(r){
  if (r.lane === "open" && r.vacated)
    return t("waiver.why.open", {name: esc(r.vacated.name), injury: esc(r.vacated.injury || t("waiver.why.out")), share: r.share_pct});
  // A QB's share of targets or carries says nothing about his role; his snaps do.
  const share = r.pos === "QB" ? null
    : r.pos === "RB" ? wvPct(r.car) && t("waiver.why.car", {v: wvPct(r.car)})
    : wvPct(r.tgt) && t("waiver.why.tgt", {v: wvPct(r.tgt)});
  const use = [wvPct(r.snap) && t("waiver.why.snap", {v: wvPct(r.snap)}), share]
    .filter(Boolean).join(" · ");
  const up = r.promoted ? t("waiver.why.depth", {from: r.promoted.from, to: r.promoted.to}) : "";
  return [up, use].filter(Boolean).join(" · ") || "—";
}

function waiverStartsHTML(r){
  if (!r.starts) return `<span class="wv-none">${t("waiver.starts.none")}</span>`;
  const k = r.starts.margin >= 0 ? "up" : "down";
  return `<div class="wv-vs">${t("waiver.starts.vs", {name: esc(r.starts.replaces), slot: esc(r.starts.slot), pts: wvPts(r.starts.their_pts)})}</div>
    <div class="wv-margin ${k}">${r.starts.margin >= 0 ? t("waiver.starts.yes") : t("waiver.starts.no")} ${wvSigned(r.starts.margin)}</div>`;
}

function waiverRowHTML(r, i){
  const opp = r.opp ? `${r.home ? "vs" : "@"} ${esc(r.opp)}` : "";
  const worth = r.lane === "open"
    ? `<b>${wvSigned(r.gain)}</b><small>${t("waiver.worth.gain")}</small>`
    : `<b>${wvPts(r.role_pts)}</b><small>${t("waiver.worth.price", {price: wvPts(r.pts), edge: wvSigned(r.edge)})}</small>`;
  const [lane, laneTip] = (WV_LANE[r.lane] || WV_LANE.usage)();
  return `<div class="wvrow" style="animation-delay:${60 + i * 55}ms" data-wire="${i}" role="button" tabindex="0">
    <div class="wv-rank">${i + 1}</div>
    <div class="head">${headHTML(r)}</div>
    <div class="nm">
      <div class="nm-1"><b>${esc(r.n)}</b><span class="tag lane" title="${laneTip}">${lane}</span></div>
      <div class="nm-2"><span>${esc(r.pos)} · ${esc(r.team)}</span>${opp ? `<span>${opp}</span>` : ""}</div>
    </div>
    <div class="wv-why">${waiverWhy(r)}</div>
    <div class="wv-worth">${worth}</div>
    <div class="wv-starts">${waiverStartsHTML(r)}</div>
  </div>`;
}

function waiverMovesHTML(lg){
  let k = 0;
  const line = (kind, r, detail) => `<div class="wvmove ${kind}" style="animation-delay:${60 + (k++) * 55}ms">
    <span class="tag">${WV_MOVE[kind]()}</span><b>${esc(r.n)}</b>
    <span class="wv-meta">${esc(r.pos)} · ${esc(r.team)}</span><span class="wv-detail">${detail}</span></div>`;
  const rows = [
    ...lg.adds.map(r => line("add", r, r.upgrade ? t("waiver.move.over", {margin: wvSigned(r.upgrade.margin), name: esc(r.upgrade.replaces), slot: esc(r.upgrade.slot)}) : "")),
    ...lg.stash.map(r => line("stash", r, (r.stash_reason === "usage" ? t("waiver.move.reason.usage") : t("waiver.move.reason.handcuff")))),
    ...lg.drops.map(r => line("drop", r, t("waiver.move.perGame", {pts: wvPts(r.pts)}))),
  ];
  if (!rows.length) return "";
  return `<div class="rule"><h2>${t("waiver.moves.heading")}</h2><span class="count">${String(rows.length).padStart(2,"0")}</span><span class="hair"></span></div>
    <div class="wvmoves">${rows.join("")}</div>`;
}

function waiverHTML(team){
  const lg = waiverFor(team.key);
  if (!lg) return `<div class="state-empty" style="margin:24px 0;min-height:140px"><div><b>—</b><span>${t("waiver.empty.noPacket")}</span></div></div>`;
  const n = waiverStarters(lg);
  return `${waiverMovesHTML(lg)}
    <div class="rule"><h2>${t("waiver.wire.heading")}</h2><span class="count">${String(lg.wire.length).padStart(2,"0")}</span><span class="hair"></span>
      <span class="side">${n ? t("waiver.wire.someStart", {n}) : t("waiver.wire.noneStart")}</span></div>
    ${lg.wire.length ? `<div class="wvhead">
        <span class="ch ch-why">${t("waiver.col.why")}</span>
        <span class="ch ch-worth" title="${t("waiver.col.worthTip")}">${t("waiver.col.worth")}</span>
        <span class="ch ch-starts">${t("waiver.col.starts")}</span>
      </div>
      <div class="board">${lg.wire.map(waiverRowHTML).join("")}</div>`
    : `<div class="state-empty" style="margin:14px 0;min-height:110px"><div><b>0</b><span>${t("waiver.empty.noWire")}</span></div></div>`}`;
}

/* The hero tiles on the Waivers sub-tab: when claims clear, what is left to bid, how many would start. */
function waiverTilesHTML(team){
  const lg = waiverFor(team.key);
  const clears = LIVE_WAIVER ? waiverClears(LIVE_WAIVER.clears) : null;
  const budget = lg && lg.budget_left !== null ? `$${lg.budget_left}` : "—";
  return `<div class="signals">
    <div class="sig ${clears ? "" : "empty"}"><div class="lbl">${t("waiver.tile.clears")}</div><div class="sig-val">${clears ? clears[0] : "—"}</div><div class="sig-sub">${clears ? t("waiver.tile.clearsSub", {date: clears[1].toUpperCase()}) : ""}</div></div>
    <div class="sig ${lg && lg.budget_left !== null ? "" : "empty"}"><div class="lbl">${t("waiver.tile.faab")}</div><div class="sig-val">${budget}</div><div class="sig-sub">${t("waiver.tile.faabSub")}</div></div>
    <div class="sig ${lg ? (waiverStarters(lg) ? "up" : "") : "empty"}"><div class="lbl">${t("waiver.tile.starts")}</div><div class="sig-val">${lg ? waiverStarters(lg) : "—"}</div><div class="sig-sub">${t("waiver.tile.startsSub", {n: lg ? lg.wire.length : 0})}</div></div>
  </div>`;
}
