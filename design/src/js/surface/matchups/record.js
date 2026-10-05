/* ============================== START/SIT: RECORD AND LAST WEEK ==============================
   The record is the trust question, so it leads the calls: SMASH, START and SIT each as hit-miss,
   kept apart because they are different bets (METHODOLOGY 12.75), counted from week 5. Before a
   week is graded it says so instead of printing zeros. A call a player was ruled out of after it
   froze is void and shown beside its count, never in it. FantasyPros and Pitcher List are one small
   line for fun; no call here is ever judged against them. */

const MU_KINDS = () => [["smash", t("matchups.call.smash")], ["start", t("matchups.call.start")], ["sit", t("matchups.call.sit")]];

function muTileHTML(kind, label, c){
  const v = c.void > 0 ? `<small>${t("matchups.record.void", {n: c.void})}</small>` : "";
  return `<div class="mu-rt ${kind}"><b>${ss3Wl(c)}</b><span>${label}</span>${v}</div>`;
}

/* The for-fun line, once either has a graded call. */
function muFunHTML(f){
  const fp = f.fantasypros, pl = f.pitcherlist;
  if (fp.hit + fp.miss + pl.hit + pl.miss === 0) return "";
  return `<p class="mu-fun">${t("matchups.record.fun", {fp: `<b>${ss3Wl(fp)}</b>`, pl: `<b>${ss3Wl(pl)}</b>`})}</p>`;
}

function muRecordHTML(){
  const r = LIVE_SS3.record;
  const head = `<div class="mu-rec-h"><h3 class="mu-rec-l">${t("matchups.record.label")}</h3>
    <span class="mu-rec-s">${t("matchups.record.since", {wk: r.since_week})}</span></div>`;
  if (!ss3Graded(r)) return `<section class="mu-rec none" aria-label="${t("matchups.record.label")}">${head}
    <p class="mu-rec-none">${t("matchups.record.none")}</p></section>`;
  return `<section class="mu-rec" aria-label="${t("matchups.record.aria", {wk: r.since_week})}">${head}
    <div class="mu-rts">${MU_KINDS().map(([k, label]) => muTileHTML(k, label, r[k])).join("")}</div>
    ${muFunHTML(r.fun)}</section>`;
}

/* Last week's calls, one line each: the result, the player, what we called and where he finished. A
   void call (ruled out after it froze) has no finish and is not in the record above. */
const MU_RESULT = () => ({hit: t("matchups.last.hit"), miss: t("matchups.last.miss"), void: t("matchups.last.void")});

function muLastHTML(){
  const r = LIVE_SS3.record, rows = r.last_week;
  if (!rows.length) return "";
  const wk = r.weeks.length ? Math.max(...r.weeks.map(w => w.week)) : null;
  const word = MU_RESULT();
  const li = x => {
    const res = word[x.result] ? x.result : "void";
    const callWord = x.call === "SIT" ? t("matchups.call.sit") : x.call === "SMASH" ? t("matchups.call.smash") : t("matchups.call.start");
    const meta = x.finish == null ? `${callWord} · ${esc(x.pos)}` : `${callWord} · ${t("matchups.last.finish", {pos: esc(x.pos), n: x.finish})}`;
    return `<li class="mu-rv ${res}"><span class="mu-rv-r">${word[res]}</span>
      <span class="mu-rv-n"><b>${esc(nameInitial(x.name))}</b><i>${meta}</i></span></li>`;
  };
  return `<section class="mu-card mu-last"><h3 class="mu-ch"><span>${wk ? t("matchups.last.title", {week: wk}) : t("matchups.last.titleNone")}</span></h3>
    <ul>${rows.map(li).join("")}</ul></section>`;
}
