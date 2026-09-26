/* ============================== MATCHUPS ==============================
   Players > Matchups, in the Digest's language (storyboard https://claude.ai/artifact/QyeSKebCWdeCqA9YvxXsdX,
   frames 4 and 5, 2026-09-26): the record strip, the position chips, the best spot as the lead,
   then one line per call, ours and then Pitcher List's. A phone stacks them; a desktop puts the
   lead in a sticky column and the two lists side by side beside it. The page computes nothing:
   every call and the record are ff-jarvis's (lead.js, rows.js). */

function muChipsHTML(){
  return `<div class="filters mu-pos" role="group" aria-label="${t("matchups.filter.label")}">${MU_POSITIONS.map(p =>
    `<button class="chip" data-mupos="${p}" aria-pressed="${MU_POS === p}">${p}</button>`).join("")}</div>`;
}

function muOursHTML(pos){
  const rows = [...muCalls(pos, "start"), ...muCalls(pos, "sit")];
  const body = rows.length ? rows.map(muCallHTML).join("")
    : `<p class="mu-empty">${t("matchups.calls.empty", {pos})}</p>`;
  return `<section class="mu-list"><h3 class="mu-grp">${t("matchups.calls.title")}<span>${t("matchups.calls.cols")}</span></h3>${body}</section>`;
}

function muPlHTML(pos){
  const d = LIVE_STARTSIT, rows = muPl(pos);
  const body = !d.article ? `<p class="mu-empty">${t("matchups.pl.none")}</p>`
    : rows.length ? rows.map(muPlRowHTML).join("")
    : `<p class="mu-empty">${t("matchups.pl.empty", {pos})}</p>`;
  const n = d.article && rows.length ? `<span>${rows.length === 1 ? t("matchups.pl.one") : t("matchups.pl.count", {n: rows.length})}</span>` : "";
  return `<section class="mu-list"><h3 class="mu-grp">${t("matchups.pl.title", {pos})}${n}</h3>${body}</section>`;
}

function matchupsHTML(){
  if (!LIVE_STARTSIT) return `<div class="wrap"><div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b
    ><span>${t("matchups.empty.noCalls")}</span></div></div></div>`;
  const pos = MU_POS;
  return `<div class="mu">
    ${muRecordHTML()}${muChipsHTML()}
    ${muLeadHTML(pos)}
    <div class="mu-cols"><div class="mu-cols-in">${muOursHTML(pos)}${muPlHTML(pos)}</div></div>
    <p class="mu-foot">${t("matchups.foot")} ${t("matchups.record.scale")}</p>
  </div>`;
}

function muSetOpen(row, open){
  row.toggleAttribute("data-open", open);
  row.querySelector(".mu-call-h").setAttribute("aria-expanded", open);
  row.querySelector(".mu-b").inert = !open;
}

/* A row opens in place, never by re-render: its own spring is the motion, and the list must not
   be redrawn under the reader. One open at a time; a second tap closes it. */
function wireMatchups(v){
  v.querySelectorAll("[data-mupos]").forEach(b => b.addEventListener("click", () => {
    if (MU_POS === b.dataset.mupos) return;
    MU_POS = b.dataset.mupos; render();
  }));
  v.querySelectorAll(".mu-call-h").forEach(h => h.addEventListener("click", () => {
    const key = h.parentElement.dataset.mukey;
    MU_OPEN = MU_OPEN === key ? "" : key;
    v.querySelectorAll(".mu-call").forEach(r => muSetOpen(r, r.dataset.mukey === MU_OPEN));
  }));
  v.querySelectorAll("[data-muslug]").forEach(el => el.addEventListener("click", () => {
    const r = LIVE_STARTSIT.calls.find(x => x.slug === el.dataset.muslug);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
}
