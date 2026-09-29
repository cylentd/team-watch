/* ============================== TAKES ==============================
   Players > Takes (leaf `matchups`, hash #matchups or #takes; was Matchups until 2026-09-29, per
   David: "compare hot takes against the experts"). The record strip, then every position in one
   list: where we rank a player higher than the FantasyPros experts, where lower, then Pitcher
   List's calls. A phone stacks them; wider, ours and Pitcher List's sit side by side. The page
   computes nothing: every take and the record are ff-jarvis's (record.js, rows.js). The matchup
   itself moved to Ranks, a tag on the row, since it is worth at most about 2 points. */

/* The column key ("ours / experts · pts") heads the first section only: the second's rows sit in
   the same columns, and two keys beside two long titles wrapped both on a phone. */
function muSectionHTML(title, rows, empty, key){
  const body = rows.length ? rows.map(muCallHTML).join("") : `<p class="mu-empty">${empty}</p>`;
  return `<h3 class="mu-grp">${title}${key ? `<span>${t("matchups.calls.cols")}</span>` : ""}</h3>${body}`;
}

function muOursHTML(){
  return `<section class="mu-list">
    ${muSectionHTML(t("matchups.calls.higher"), muCalls("start"), t("matchups.calls.emptyHigher"), true)}
    ${muSectionHTML(t("matchups.calls.lower"), muCalls("sit"), t("matchups.calls.emptyLower"), false)}
  </section>`;
}

function muPlHTML(){
  const d = LIVE_STARTSIT, rows = muPl();
  const body = !d.article ? `<p class="mu-empty">${t("matchups.pl.none")}</p>`
    : rows.length ? rows.map(muPlRowHTML).join("")
    : `<p class="mu-empty">${t("matchups.pl.empty")}</p>`;
  const n = d.article && rows.length ? `<span>${rows.length === 1 ? t("matchups.pl.one") : t("matchups.pl.count", {n: rows.length})}</span>` : "";
  return `<section class="mu-list"><h3 class="mu-grp">${t("matchups.pl.title")}${n}</h3>${body}</section>`;
}

function matchupsHTML(){
  if (!LIVE_STARTSIT) return `<div class="wrap"><div class="state-empty" style="margin:26px 0;min-height:120px"><div><b>0</b
    ><span>${t("matchups.empty.noCalls")}</span></div></div></div>`;
  return `<div class="mu">
    ${muRecordHTML()}
    <div class="mu-cols"><div class="mu-cols-in">${muOursHTML()}${muPlHTML()}</div></div>
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
