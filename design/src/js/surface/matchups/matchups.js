/* ============================== MATCHUPS ==============================
   Players > Matchups: per position, the best spot this week, our start calls on players outside the
   obvious starters, our sit calls on players usually started, and Pitcher List's calls beside them.
   The record leads because it is the one number that says whether to trust the rest; ours trails
   Pitcher List's today, and the page says so. Every row opens the player's profile. */

/* The evidence chips that argue the call, then at most one against it, in words. A call with no
   chip is shown anyway (the record grades it) and says out loud that nothing backs it. */
function muWhyHTML(r){
  const why = r.why.map(w => `<span class="mu-chip${w.k === "mx" ? " mx" : ""}">${esc(w.t)}</span>`).join("");
  const none = r.why.length || r.tag === "best" ? "" : `<span class="mu-chip none">${t("matchups.row.unbacked")}</span>`;
  const but = r.but.map(w => `<span class="mu-chip but">${t("matchups.row.but", {why: esc(w.charAt(0).toLowerCase() + w.slice(1))})}</span>`).join("");
  return why || none || but ? `<div class="mu-why">${why}${none}${but}</div>` : "";
}

/* The best spot's card is headed "Best spot at WR", so its row carries no tag: the room goes to
   the name, which a tag beside a 13.4 truncated at 360px. */
function muTagHTML(tag){
  if (tag === "best") return "";
  const word = {best: t("matchups.call.best"), start: t("matchups.call.start"), sit: t("matchups.call.sit")}[tag];
  return `<span class="mu-tag ${tag}">${word}</span>`;
}

function muRowHTML(r, i){
  const ecr = r.ecr == null ? "—" : r.pos + r.ecr;
  return `<button type="button" class="mu-row" data-muslug="${esc(r.slug)}" style="--i:${i}">
    <span class="xf-head">${avatarHTML(r)}</span>
    <span class="mu-body">
      <span class="mu-top">${muTagHTML(r.tag)}<b>${esc(r.n)}</b><em>${esc(muVs(r))}</em></span>
      <span class="mu-ranks">${t("matchups.row.ranks", {pos: r.pos, rank: r.rank, ecr})}</span>
      ${muWhyHTML(r)}
    </span>
    <span class="mu-pts">${r.pts.toFixed(1)}</span>
  </button>`;
}

function muListHTML(rows, empty, start){
  return rows.length ? rows.map((r, i) => muRowHTML(r, start + i)).join("")
    : `<p class="mu-empty">${empty}</p>`;
}

/* Pitcher List's own call, their words clamped to two lines: the benchmark, not our reasoning. */
function muPlRowHTML(r, i){
  return `<button type="button" class="mu-row pl" data-muslug="${esc(r.slug)}" data-mupl="1" style="--i:${i}">
    <span class="xf-head">${avatarHTML(r)}</span>
    <span class="mu-body">
      <span class="mu-top">${muTagHTML(r.call)}<b>${esc(r.n)}</b><em>${esc(muVs(r))}</em></span>
      <span class="mu-quote">${esc(r.rationale)}</span>
    </span>
  </button>`;
}

function muPlHTML(pos){
  const d = LIVE_STARTSIT;
  const rows = muPl(pos);
  const body = !d.article ? `<p class="mu-empty">${t("matchups.pl.none")}</p>`
    : rows.length ? rows.map((r, i) => muPlRowHTML(r, 20 + i)).join("")
    : `<p class="mu-empty">${t("matchups.pl.empty", {pos})}</p>`;
  const link = d.article ? `<a class="mu-link" href="${esc(d.article)}" target="_blank" rel="noopener noreferrer">${t("matchups.pl.read")}</a>` : "";
  return `<section class="mu-sec"><h3 class="mu-h">${t("matchups.pl.title", {pos})}${link}</h3>${body}</section>`;
}

function muRecordHTML(){
  const r = LIVE_STARTSIT.record;
  if (!r) return `<p class="mu-record">${t("matchups.record.none")}</p>`;
  const lead = r.ours.score != null && r.pl.score != null ? (r.ours.score >= r.pl.score ? "us" : "pl") : "";
  return `<div class="mu-record ${lead}">
    <p>${t("matchups.record.line", {wk: r.through, us: `<b class="us">${muScore(r.ours.score)}</b>`, n: r.ours.n,
      pl: `<b class="pl">${muScore(r.pl.score)}</b>`, pn: r.pl.n})}</p>
    <p class="mu-scale">${t("matchups.record.scale")}</p>
  </div>`;
}

function muChipsHTML(){
  return `<div class="filters"><span class="lbl">${t("matchups.filter.label")}</span>${MU_POSITIONS.map(p =>
    `<button class="chip" data-mupos="${p}" aria-pressed="${MU_POS === p}">${p}</button>`).join("")}</div>`;
}

function muHeroHTML(week){
  return `<section class="hero slim"><div class="wrap hero-in"><div>
    <div class="hero-eyebrow" style="--tint:var(--lime)"><span class="league-mark"></span
      ><span class="lbl">${t("matchups.hero.eyebrow", {week})}</span></div>
  </div></div></section>`;
}

function matchupsHTML(){
  const d = LIVE_STARTSIT;
  if (!d) return muHeroHTML("—") + `<div class="wrap"><div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b
    ><span>${t("matchups.empty.noCalls")}</span></div></div></div>`;
  const pos = MU_POS, best = muCalls(pos, "best")[0], start = muCalls(pos, "start"), sit = muCalls(pos, "sit");
  return muHeroHTML(d.week) + `<div class="wrap muwrap">
    ${muRecordHTML()}${muChipsHTML()}
    <div class="mu-grid">
      <div class="mu-col">
        <section class="mu-sec"><h3 class="mu-h">${t("matchups.start.title", {n: MU_CUT[pos]})}</h3>
          ${muListHTML(start, t("matchups.start.empty", {pos}), 0)}</section>
        <section class="mu-sec"><h3 class="mu-h">${t("matchups.sit.title")}</h3>
          ${muListHTML(sit, t("matchups.sit.empty", {pos}), start.length)}</section>
      </div>
      <div class="mu-col">
        ${best ? `<section class="mu-sec mu-best"><h3 class="mu-h">${t("matchups.best.title", {pos})}</h3>${muRowHTML(best, 10)}</section>` : ""}
        ${muPlHTML(pos)}
      </div>
    </div>
    <p class="note mu-foot">${t("matchups.foot")}</p>
  </div>`;
}

function wireMatchups(v){
  v.querySelectorAll("[data-mupos]").forEach(b => b.addEventListener("click", () => {
    if (MU_POS === b.dataset.mupos) return;
    MU_POS = b.dataset.mupos; render();
  }));
  v.querySelectorAll("[data-muslug]").forEach(el => el.addEventListener("click", () => {
    const list = el.dataset.mupl ? LIVE_STARTSIT.pl : LIVE_STARTSIT.calls;
    const r = list.find(x => x.slug === el.dataset.muslug);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
