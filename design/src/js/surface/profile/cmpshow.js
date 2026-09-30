/* The Compare sheet: the players as chips, their shapes on one radar, then one row per number with
   the best of each lit. Option A of the storyboard: one radar with the shapes laid over each other,
   so the gap between players is the gap between shapes, and three still fit a 360px phone.

   The radar is the profile's own scale (sheet.js): a stat's radius is his season rank among the
   position, first at the rim. Six axes are a position's own six, so the radar draws only when every
   player shares one position; a RB beside a WR keeps the rows, which mean the same for both. */
function cmpShowHTML(){
  const ps = cmpPlayers();
  const add = ps.length < CMP_MAX
    ? `<button type="button" class="cmp-chip add" data-cmp="change" aria-label="${t("profile.compare.add")}">+</button>` : "";
  return `<div class="cmp-h"><h4 id="cmp-t">${t("profile.compare.head")}</h4>
      <button type="button" class="cmp-change" data-cmp="change">${t("profile.compare.change")}</button>
      <button type="button" class="dr-close cmp-x" data-cmp="close" aria-label="${t("profile.compare.close")}">✕</button></div>
    <div class="cmp-chips">${ps.map(cmpChipHTML).join("")}${add}</div>
    ${cmpRadarHTML(ps)}
    <div class="cmp-rows">${cmpRowsHTML(ps)}</div>`;
}

function cmpChipHTML(p, i){
  const inj = injFor(p), rk = cmpRankRow(p);
  const tag = inj ? `<span class="cmp-inj">${esc(inj.code || inj.s)}</span>` : "";
  return `<div class="cmp-chip cmp-s${i}"><span class="cmp-head">${headHTML(p)}</span><b>${shortName(p.n)}</b>
    <span class="lbl">${esc([p.pos, p.team].filter(Boolean).join(" · "))}${rk && rk.opp ? " " + t("profile.compare.vs", {opp: esc(rk.opp)}) : ""}</span>${tag}</div>`;
}

/* The shapes. Every player's radius per axis is the profile's k (sheet.js radarHTML); an axis he
   has no rank on is left out of his shape, as the profile does. */
function cmpRadarHTML(ps){
  const sheets = ps.map(sheetFor);
  const pos = new Set(ps.map((p, i) => sheets[i] ? sheets[i].pos : p.pos));
  if (pos.size > 1) return `<p class="cmp-note">${t("profile.compare.mixed")}</p>`;
  const s = sheets.find(Boolean);
  const drawn = ps.map((p, i) => [p, i]).filter(([, i]) => sheets[i]);
  if (!s || drawn.length < 2) return `<p class="cmp-note">${t("profile.compare.thin")}</p>`;
  const missing = ps.filter((_, i) => !sheets[i]).map(p => shortName(p.n));
  // Room round the dial for a 12px label about 90 units wide on each flank ("Targets/route").
  const n = s.axes.length, cx = 180, cy = 122, R = 80;
  const ang = i => -Math.PI / 2 + i * 2 * Math.PI / n;
  const xy = (i, r) => [cx + Math.cos(ang(i)) * R * r, cy + Math.sin(ang(i)) * R * r];
  const rings = [.25, .5, .75, 1].map(r => `<circle class="cmp-ring" cx="${cx}" cy="${cy}" r="${(R * r).toFixed(1)}"/>`).join("");
  const shapes = drawn.map(([p, i]) => cmpShapeHTML(s, p, i, xy)).join("");
  const labels = s.axes.map((a, i) => {
    const [x, y] = xy(i, 1.18), c = Math.cos(ang(i));
    const anchor = c > .3 ? "start" : c < -.3 ? "end" : "middle";
    return `<text class="cmp-axis" x="${x.toFixed(1)}" y="${(y + 4).toFixed(1)}" text-anchor="${anchor}">${esc(axisName(a))}</text>`;
  }).join("");
  const note = missing.length ? `<p class="cmp-note">${t("profile.compare.unranked", {names: missing.join(", ")})}</p>` : "";
  return `<svg class="cmp-radar" viewBox="0 0 360 244" role="img" aria-label="${t("profile.compare.radar")}">
      ${rings}${labels}${shapes}</svg>
    <p class="cmp-scale lbl">${t("profile.compare.scale")}</p>${note}`;
}

function cmpShapeHTML(s, p, i, xy){
  const k = rk => rk && rk[1] > 1 ? Math.max(.04, 1 - (rk[0] - 1) / (rk[1] - 1)) : null;
  const pts = s.axes.map((a, j) => [j, k(sheetRank(s.pos, a.id, p.slug))]).filter(([, r]) => r !== null)
    .map(([j, r]) => xy(j, r).map(v => v.toFixed(1)));
  if (pts.length < 3) return pts.map(([x, y]) => `<circle class="cmp-dot cmp-s${i}" cx="${x}" cy="${y}" r="3"/>`).join("");
  return `<polygon class="cmp-shape cmp-s${i}" points="${pts.map(q => q.join(",")).join(" ")}"/>`
    + pts.map(([x, y]) => `<circle class="cmp-dot cmp-s${i}" cx="${x}" cy="${y}" r="2.5"/>`).join("");
}
