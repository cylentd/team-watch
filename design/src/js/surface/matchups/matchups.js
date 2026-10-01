/* ============================== TAKES ==============================
   Players > Takes (leaf `matchups`, hash #matchups or #takes; was Matchups until 2026-09-29, per
   David: "compare hot takes against the experts"). The record strip, then every position in one
   list: where we rank a player higher than the FantasyPros experts, where lower, then Pitcher
   List's calls. A phone stacks them; wider, ours and Pitcher List's sit side by side. The page
   computes nothing: every take and the record are ff-jarvis's (record.js, rows.js). The matchup
   itself moved to Ranks, a tag on the row, since it is worth at most about 2 points. No method
   footer, scoring rules or version notes (2026-09-30, David: show, don't tell). */

/* The column key ("ours / experts · pts") heads the first section only: the second's rows sit in
   the same columns, and two keys beside two long titles wrapped both on a phone. */
/* A paused take type (Amendment 2) leaves the list; its line stands where its takes would be, at the
   end of its section, and a section holding only paused takes says that instead of "no takes". */
function muSectionHTML(title, tag, empty, key){
  const rows = muCalls(tag), paused = muPausedHTML(tag);
  const body = rows.length ? rows.map(r => muCallHTML(r)).join("") : paused ? "" : `<p class="mu-empty">${empty}</p>`;
  return `<h3 class="mu-grp">${title}${key ? `<span>${t("matchups.calls.cols")}</span>` : ""}</h3>${body}${paused}`;
}

/* No takes at all: Blip says why, and when that changes (2026-09-29, David: "ask Blip the mascot
   since we have no Takes"). Two reasons, told apart by the data: the experts have not ranked this
   week yet (every Tuesday, until Wednesday's 8 AM fetch and the 2:30 PM refresh), or they have and
   we agree with them on every starter. */
function muBlipHTML(){
  const d = LIVE_STARTSIT, early = d.experts_week != null && d.experts_week < d.week;
  const say = early ? t("matchups.blip.early", {week: d.week}) : t("matchups.blip.agree");
  const when = early ? `<p>${t("matchups.blip.earlyWhen")}</p>` : "";
  return `<section class="mu-list"><div class="mu-blip">${blipSVG(t("matchups.blip.name"), early ? "bored" : "awake")}
    <div><q>${say}</q>${when}</div></div></section>`;
}

function muOursHTML(){
  if (!LIVE_STARTSIT.calls.length && !(LIVE_STARTSIT.shadow || []).length) return muBlipHTML();
  return `<section class="mu-list">
    ${muSectionHTML(t("matchups.calls.higher"), "start", t("matchups.calls.emptyHigher"), true)}
    ${muSectionHTML(t("matchups.calls.lower"), "sit", t("matchups.calls.emptyLower"), false)}
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
    ${muReviewHTML()}
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
    const r = [...LIVE_STARTSIT.calls, ...(LIVE_STARTSIT.shadow || [])].find(x => x.slug === el.dataset.muslug);
    if (r) openProfile({n: r.n, pos: r.pos, team: r.team, slug: r.slug}, el);
  }));
  wireMuSplits(v);
}
