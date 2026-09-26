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

/* Each bar grows from last week's % rostered to this week's when the row opens (adds.css). */
function dgAddsBody(d){
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
    ? `<div class="dg-mv"><span>${esc(r.n)}</span><em class="${cls}">${dgSigned(r.d_pts, 1)}</em></div>` : `<div class="dg-mv"></div>`;
  const rows = Array.from({length: n}, (_, i) => cell(d.up[i], "up") + cell(d.down[i], "dn")).join("");
  return `<div class="dg-two"><h4>${t("digest.st.up")}</h4><h4>${t("digest.st.down")}</h4>${rows}</div>`
    + dgFootHTML(t("digest.foot.st"), "movers", t("digest.go.movers"), true);
}

function dgGemsBody(d){
  const lines = d.gems.map(g => dgLnHTML(g, t("digest.gems.meta", {pos: esc(g.pos), team: esc(g.team), pct: dgPct(g.rostered)}),
    `${g.metric === "tgt_pct" ? dgPct(g.usage) + "%" : g.usage.toFixed(1)}<small>${t("digest.gems.ecr", {pos: esc(g.pos), ecr: g.ecr})}</small>`)).join("");
  return lines + dgFootHTML(t("digest.foot.gems", d.rules.gems),"usage", t("digest.go.grid"), true);
}

const DG_KIND = {out: "out", injury: "q"};
function dgNewsBody(d){
  const rows = d.news.map(it => `<div class="dg-news"><time>${esc(it.when || "")}</time><span>${it.n
    ? `<b class="${DG_KIND[it.kind] || ""}">${esc(it.n)}</b> ${esc(it.rest)}` : esc(it.headline)}</span></div>`).join("");
  return rows + dgFootHTML(t("digest.foot.news"), "news", t("digest.go.news"));
}

const DG_BODY = {hurt: dgHurtBody, mu: dgMuBody, wx: dgWxBody, adds: dgAddsBody, t5: dgTop5Body,
                 st: dgStockBody, gems: dgGemsBody, news: dgNewsBody};
