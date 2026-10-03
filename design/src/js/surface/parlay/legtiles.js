/* The leg sheet's three tiles (2026-09-27): per market, the three numbers the bet rests on, each
   one value over the ten games (or this season, where `u` has not arrived) with a short read when
   the read explains the bet. A tile with no number is not drawn -- never a dash. The numbers come
   from legdata.js; this file only picks and words them. */
const lsF1 = v => v.toFixed(1);
const lsPc = v => `${Math.round(v * 100)}%`;
const lsTile = (label, value, read) => value === null || value === undefined || Number.isNaN(value) ? null : {label, value, read: read || ""};

function legTilesFor(p, log){
  const rows = legWeeks(p), u = log && log.u;
  const grid = k => lsMean(legGrid(rows, k));
  // Longest reception rests on the same three as yards: targets, yards a target, depth.
  if (p.mkt === "RECS" || p.mkt === "REC" || p.mkt === "LONG"){
    const tg = legTargets(p, log), adot = legAdot(p);
    const pg = tg ? tg.pg : null;
    if (p.mkt === "RECS"){
      const cr = tg && tg.tgt ? tg.recs / tg.tgt : null;
      // Deep targets are why a catch rate runs low; say so where the rate is read.
      const read = [cr !== null && pg !== null ? t("legsheet.tile.catchesRead", {n: lsF1(pg * cr)}) : "",
                    adot !== null && adot >= 12 ? t("legsheet.tile.deep", {n: Math.round(adot)}) : ""].filter(Boolean).join(" · ");
      return [lsTile(t("legsheet.tile.tgtPg"), pg === null ? null : lsF1(pg)),
              lsTile(t("legsheet.tile.tgtShare"), tg && tg.share !== null ? lsPc(tg.share) : null),
              lsTile(t("legsheet.tile.catch"), cr === null ? null : lsPc(cr), read)];
    }
    const ypt = tg && tg.tgt ? tg.yds / tg.tgt : null;
    return [lsTile(t("legsheet.tile.tgtPg"), pg === null ? null : lsF1(pg)),
            lsTile(t("legsheet.tile.ypt"), ypt === null ? null : lsF1(ypt), ypt !== null && pg !== null ? t("legsheet.tile.yardsRead", {n: Math.round(pg * ypt)}) : ""),
            lsTile(t("legsheet.tile.adot"), adot === null ? null : lsF1(adot))];
  }
  if (p.mkt === "RUSH"){
    const car = (u ? lsMean(u.car) : null) ?? grid(p.pos === "QB" ? "rush" : "car");
    const snap = grid("snap"), rz = legRzPerGame(p, log);
    return [lsTile(t("legsheet.tile.carPg"), car === null ? null : lsF1(car)),
            lsTile(t("legsheet.tile.snap"), snap === null ? null : `${Math.round(snap)}%`),
            lsTile(t("legsheet.tile.rzPg"), rz === null ? null : lsF1(rz))];
  }
  if (p.mkt === "TD"){
    const rz = legRzPerGame(p, log), share = legRzShare(log);
    const yr = log ? log.g[log.g.length - 1][0] : null;
    const glU = u ? u.gl_car.filter((v, k) => log.g[k][0] === yr && typeof v === "number") : [];
    const gl = glU.length ? lsSum(glU) : rows.some(r => typeof r.v.gl_car === "number") ? lsSum(legGrid(rows, "gl_car")) : null;
    const tds = log && log.v.TD ? log.v.TD.filter(v => v >= 1).length : null;
    return [lsTile(t("legsheet.tile.rzPg"), rz === null ? null : lsF1(rz)),
            lsTile(t("legsheet.tile.gl"), gl),
            share !== null ? lsTile(t("legsheet.tile.rzShare"), lsPc(share))
              : lsTile(t("legsheet.tile.tds"), tds === null ? null : t("legsheet.tile.tdsOf", {hit: tds, n: log.v.TD.length}))];
  }
  if (p.mkt === "PASS"){
    const att = grid("att"), db = grid("dropbacks"), rz = grid("rz_att");
    return [lsTile(t("legsheet.tile.attPg"), att === null ? null : lsF1(att)),
            lsTile(t("legsheet.tile.dbPg"), db === null ? null : lsF1(db)),
            lsTile(t("legsheet.tile.rzAttPg"), rz === null ? null : lsF1(rz))];
  }
  return [];
}

function legTilesHTML(p, log){
  const tiles = legTilesFor(p, log).filter(Boolean);
  return tiles.length ? `<div class="ls-tiles">${tiles.map(x => `<div class="ls-tile"><span>${x.label}</span><b>${x.value}</b>${x.read ? `<em>${x.read}</em>` : ""}</div>`).join("")}</div>` : "";
}

/* One row of small numbers under the bars, per game: the stat that drives the bet. `u` only. */
function legDriver(p, log){
  const u = log && log.u;
  if (!u) return null;
  if (p.mkt === "RECS" || p.mkt === "REC" || p.mkt === "LONG") return {label: t("legsheet.bars.tgt"), vals: u.tgt};
  if (p.mkt === "RUSH") return {label: t("legsheet.bars.car"), vals: u.car};
  if (p.mkt === "TD") return {label: t("legsheet.bars.rz"), vals: u.rz_tgt.map((v, k) => v == null && u.rz_car[k] == null ? null : (v || 0) + (u.rz_car[k] || 0))};
  return null;
}

/* The matchup as one line: what this defense allows at his stat against an average one (the model's
   opp_f as a percent), else its rank at his position, and its starters who will not play, named on a
   tap. A factor within 5% of average is noise and says nothing (0.98x read as a number to weigh,
   David 2026-10-03). No line without either. */
const LS_MATCH_MIN = 5;
function legMatchupHTML(p){
  const opp = legOpp(p), d = legDefense(p);
  const bits = [];
  const pct = typeof p.opp_f === "number" ? Math.round((p.opp_f - 1) * 100) : null;
  const stat = {pos: esc(p.pos), stat: esc(MKT[p.mkt].toLowerCase())};
  if (pct != null) {
    if (Math.abs(pct) >= LS_MATCH_MIN) bits.push(pct > 0 ? t("legsheet.matchup.more", {pct, ...stat}) : t("legsheet.matchup.fewer", {pct: -pct, ...stat}));
  } else if (d && d.form && d.form.rank) bits.push(d.form.rank <= 16 ? t("legsheet.matchup.fewest", {rank: lsOrd(d.form.rank), pos: esc(p.pos)})
    : t("legsheet.matchup.most", {rank: lsOrd(33 - d.form.rank), pos: esc(p.pos)}));
  if (!opp || (!bits.length && !(d && d.out.length))) return "";
  const head = [t("legsheet.matchup.vs", {team: esc(opp)}), ...bits].join(" · ");
  if (!d || !d.out.length) return `<p class="ls-match">${head}</p>`;
  const names = d.out.slice(0, 5).map(o => `<li>${esc(nameInitial(o.name))} <span>${esc(o.pos || "")} · ${esc(o.injury || "")}</span></li>`).join("");
  return `<details class="ls-match"><summary>${head} · <u>${d.out.length === 1 ? t("legsheet.matchup.outOne") : t("legsheet.matchup.outMany", {n: d.out.length})}</u></summary><ul>${names}</ul></details>`;
}
