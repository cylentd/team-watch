/* ============================== DIGEST: WHAT A ROW OPENS TO ==============================
   Each topic's opened state: the fact, then a foot that says where the numbers come from and links
   to the view that holds all of them. "Not backtested" lives here, on the opened row, never on the
   closed line (plan, 2026-09-26): the closed line is the fact, the caveat is for whoever reads on. */

/* A player line: head, name over one meta line, one number at the right. It opens his profile. */
function dgLnHTML(p, meta, right, extra){
  return `<button type="button" class="dg-ln${extra ? " wide" : ""}" data-dgslug="${esc(p.slug)}">
    <span class="dg-hd">${avatarHTML(p)}</span>
    <span class="dg-ln-t"><b>${esc(p.n)}</b><span>${meta}</span>${extra || ""}</span>
    <span class="dg-ln-r">${right}</span></button>`;
}

function dgFootHTML(text, leaf, label, caveat){
  const go = leaf ? `<button type="button" class="dg-go" data-dggo="${leaf}">${label}${DG_ARROW}</button>` : "";
  return `<div class="dg-foot"><span>${text}${caveat ? ` <span class="dg-nb">${t("digest.nb")}</span>` : ""}</span>${go}</div>`;
}

const dgVs = r => r.home ? t("digest.vs.home", {team: esc(r.team), opp: esc(r.opp)}) : t("digest.vs.away", {team: esc(r.team), opp: esc(r.opp)});
const DG_TAG = {Out: ["out", () => t("digest.tag.out")], IR: ["out", () => t("digest.tag.ir")],
                Doubtful: ["d", () => t("digest.tag.d")], Questionable: ["q", () => t("digest.tag.q")]};

function dgHurtBody(d){
  const q = d.hurt.filter(r => r.status === "Questionable");
  const line = r => {
    const [cls, word] = DG_TAG[r.status] || ["q", () => esc(r.status)];
    const meta = [esc(r.pos), r.game ? dgGame(r.game) : esc(r.team), r.injury ? esc(r.injury) : ""].filter(Boolean).join(" · ");
    return dgLnHTML(r, meta, `<span class="dg-st ${cls}">${word()}</span>`);
  };
  // The questionable get a line each on the wall, where the panel has the room; a phone keeps the one-line list.
  const lines = d.hurt.filter(r => r.status !== "Questionable").map(line).join("")
    + (q.length ? `<div class="dg-qlines">${q.map(line).join("")}</div>` : "");
  const also = q.length ? `<p class="dg-also"><b>${t("digest.tag.q")}</b>${q.map(r => esc(dgShort(r.n))).join(", ")}</p>` : "";
  return lines + also + dgFootHTML(t("digest.foot.hurt"), "news", t("digest.go.news"));
}

function dgMuBody(d){
  const lines = d.best.map(b => dgLnHTML(b, [esc(b.pos), dgVs(b), b.why ? esc(b.why) : ""].filter(Boolean).join(" · "),
    b.pts.toFixed(1))).join("");
  const r = d.record;
  const rec = r ? t("digest.foot.mu", {us: r.ours.score == null ? "—" : r.ours.score.toFixed(2),
                                        pl: r.pl.score == null ? "—" : r.pl.score.toFixed(2), wk: r.through})
    : t("digest.foot.muNone");
  return lines + dgFootHTML(rec, "matchups", t("digest.go.matchups", {n: d.calls}));
}

function dgWxLnHTML(g, near){
  const kind = dgWxKind(g);
  const meta = near ? t("digest.wx.near", {kick: esc(g.kick || "")})
    : [g.kick ? esc(g.kick) : "", g.temp_f != null ? t("digest.lead.wx.temp", {f: g.temp_f}) : "", g.short ? esc(g.short) : ""].filter(Boolean).join(" · ");
  const num = kind === "wind" ? t("digest.wx.mph", {n: g.wind_mph}) : t("digest.wx.pct", {n: g.precip_pct});
  return `<div class="dg-wx${near ? " near" : ""}">${kind === "wind" ? DG_WIND : DG_RAIN}
    <span class="dg-ln-t"><b>${dgGame(g)}</b><span>${meta}</span></span><span class="dg-ln-r">${num}</span></div>`;
}

function dgWxBody(d){
  return d.wx.map(g => dgWxLnHTML(g, false)).join("") + (d.near ? dgWxLnHTML(d.near, true) : "")
    + dgFootHTML(t("digest.foot.wx", d.rules.wx_list),"roster", t("digest.go.roster"), true);
}

/* Each bar grows when the row opens (adds.css): from last week's % rostered to this week's on the
   ESPN fallback, and from nothing to his share of the top count on Sleeper's (2026-09-28). */
function dgAddsBody(d){
  if (d.adds_source === "sleeper"){
    const top = Math.max(1, ...d.adds.map(a => a.count || 0));
    const lines = d.adds.map((a, i) => dgLnHTML(a, a.now != null
      ? t("digest.adds.metaEspn", {pos: esc(a.pos), team: esc(a.team), pct: dgPct(a.now)}) : `${esc(a.pos)} · ${esc(a.team)}`,
      `<span class="dg-plus">${dgBig(a.count)}</span>`,
      `<span class="dg-bar" style="--a:0%;--b:${(100 * a.count / top).toFixed(1)}%;--i:${i}"><i></i><u></u></span>`)).join("");
    return lines + dgFootHTML(t("digest.foot.addsSleeper", {h: d.adds_hours}), "waivers", t("digest.go.waivers"));
  }
  const lines = d.adds.map((a, i) => dgLnHTML(a, t("digest.adds.meta", {pos: esc(a.pos), team: esc(a.team), was: dgPct(a.was), now: dgPct(a.now)}),
    `<span class="dg-plus">${dgSigned(Math.round(a.delta), 0)}</span>`,
    `<span class="dg-bar" style="--a:${a.was}%;--b:${a.now}%;--i:${i}"><i></i><u></u></span>`)).join("");
  const [a, b] = d.adds_weeks;
  return lines + dgFootHTML(a != null ? t("digest.foot.adds", {a, b}) : t("digest.foot.addsNoWeeks"), "waivers", t("digest.go.waivers"));
}

function dgTop5Body(d){
  const cols = DG_POS.map(pos => {
    const rows = d.top5.filter(r => r.pos === pos);
    return rows.length ? `<div><h4>${pos}</h4><ol>${rows.map(r => `<li><span class="dg-hd sm">${avatarHTML(r)}</span><span>${esc(r.n)}</span><em>${r.pts.toFixed(1)}</em></li>`).join("")}</ol></div>` : "";
  }).join("");
  return `<div class="dg-t5">${cols}</div>` + dgFootHTML(t("digest.foot.t5"), "board", t("digest.go.board"));
}

function dgStockBody(d){
  const n = Math.max(d.up.length, d.down.length), cell = (r, cls) => r
    ? `<div class="dg-mv"><span>${esc(dgShort(r.n))}</span><em class="${cls}">${dgSigned(r.d_pts, 1)}</em></div>` : `<div class="dg-mv"></div>`;
  const rows = Array.from({length: n}, (_, i) => cell(d.up[i], "up") + cell(d.down[i], "dn")).join("");
  return `<div class="dg-two"><h4>${t("digest.st.up")}</h4><h4>${t("digest.st.down")}</h4>${rows}</div>`
    + dgFootHTML(t("digest.foot.st"), "movers", t("digest.go.movers"), true);
}

function dgGemsBody(d){
  const lines = d.gems.map(g => dgLnHTML(g, t("digest.gems.meta", {pos: esc(g.pos), team: esc(g.team), pct: dgPct(g.rostered)}),
    `${g.metric === "tgt_pct" ? dgPct(g.usage) + "%" : g.usage.toFixed(1)}<small>${t("digest.gems.ecr", {pos: esc(g.pos), ecr: g.ecr})}</small>`)).join("");
  return lines + dgFootHTML(t("digest.foot.gems", d.rules.gems),"usage", t("digest.go.grid"), true);
}

/* News by player, not as a log (2026-09-28): one block per player, in the order his newest line
   ranks, his lines newest first; a headline naming no player is a block of its own. The name keeps
   the colour of his newest line's severity. A block opens his profile. The wall lays the blocks out
   as cards three across (wall.css); a phone reads them as one list. */
const DG_KIND = {out: "out", injury: "q"};
function dgNewsGroups(news){
  const groups = [], by = new Map();
  /* Keyed by name: one headline can carry his slug and the next not. */
  for (const it of news){
    let g = it.n && by.get(it.n);
    if (!g){ g = {key: null, n: it.n, kind: it.kind, lines: []}; groups.push(g); if (it.n) by.set(it.n, g); }
    g.key = g.key || (it.slugs && it.slugs[0]) || (it.n ? slugOf(it.n) : null);
    g.lines.push(it);
  }
  return groups;
}

function dgNewsBody(d){
  const who = typeof searchIndex === "function" ? new Map(searchIndex().map(e => [e.slug, e])) : new Map();
  const line = it => `<li><time>${esc(it.when || "")}</time><span>${esc(it.n ? dgCap(it.rest) : it.headline)}</span></li>`;
  const blocks = dgNewsGroups(d.news).map(g => {
    if (!g.key) return `<div class="dg-nw"><ul>${g.lines.map(line).join("")}</ul></div>`;
    const e = who.get(g.key), p = {n: g.n, slug: g.key, pos: e && e.pos, team: e && e.team};
    const meta = [p.pos, p.team].filter(Boolean).map(esc).join(" · ");
    return `<button type="button" class="dg-nw" data-dgslug="${esc(g.key)}">
      <span class="dg-hd">${avatarHTML(p)}</span>
      <span class="dg-nw-t"><span class="dg-nw-who"><b class="${DG_KIND[g.kind] || ""}">${esc(g.n)}</b><small>${meta}</small></span>
      <ul>${g.lines.map(line).join("")}</ul></span></button>`;
  }).join("");
  return `<div class="dg-nws">${blocks}</div>` + dgFootHTML(t("digest.foot.news"), "news", t("digest.go.news"));
}

/* One short list in Top 5's shape: a head, then "K. Mumpfield" and one number per line (Tonight's lists). */
function dgResList(title, rows, num){
  return rows.length ? `<div><h4>${title}</h4><ol>${rows.map(r => `<li><span class="dg-hd sm">${avatarHTML(r)}</span>`
    + `<span>${esc(dgShort(r.n))}</span>${num(r)}</li>`).join("")}</ol></div>` : "";
}

/* Results' body is results.js's (dgResBody). */
const DG_BODY = {res: dgResBody, hurt: dgHurtBody, mu: dgMuBody, wx: dgWxBody, adds: dgAddsBody, t5: dgTop5Body,
                 st: dgStockBody, gems: dgGemsBody, news: dgNewsBody};
