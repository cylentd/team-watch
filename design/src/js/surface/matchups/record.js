/* ============================== START/SIT: RECORD AND LAST WEEK ==============================
   The record is the trust question: SMASH, START and SIT each as hit-miss, kept apart because they are
   different bets (METHODOLOGY 12.75), counted from week 5. Since 2026-10-09 (draft A) it is one line in the
   calls card's head (calls.js muRecordLineHTML), beside the calls it grades; it was three tiles above them. A
   call a player was ruled out of after it froze is void and shown beside its count, never in it.
   FantasyPros and Pitcher List are one small line for fun; no call here is ever judged against them. */

/* The for-fun line, once either has a graded call. */
function muFunHTML(f){
  const fp = f.fantasypros, pl = f.pitcherlist;
  if (fp.hit + fp.miss + pl.hit + pl.miss === 0) return "";
  return `<p class="mu-fun">${t("matchups.record.fun", {fp: `<b>${ss3Wl(fp)}</b>`, pl: `<b>${ss3Wl(pl)}</b>`})}</p>`;
}

/* Last week's calls, one line each: the result, the player, what we called and where he finished. A
   void call (ruled out after it froze) has no finish and is not in the record. */
const MU_RESULT = () => ({hit: t("matchups.last.hit"), miss: t("matchups.last.miss"), void: t("matchups.last.void")});

function muLastHTML(){
  const r = LIVE_SS3.record, rows = r.last_week;
  if (!rows.length) return "";
  const wk = r.weeks.length ? Math.max(...r.weeks.map(w => w.week)) : null;
  const word = MU_RESULT();
  const li = x => {
    const res = word[x.result] ? x.result : "void";
    const meta = x.finish == null ? `${muCallWord(x.call)} · ${esc(x.pos)}` : `${muCallWord(x.call)} · ${t("matchups.last.finish", {pos: esc(x.pos), n: x.finish})}`;
    return `<li class="mu-rv ${res}"><span class="mu-rv-r">${word[res]}</span>
      <span class="mu-rv-n"><b>${esc(nameInitial(x.name))}</b><i>${meta}</i></span></li>`;
  };
  return `<section class="mu-card mu-last" data-testid="matchups-last"><h3 class="mu-ch"><span>${wk ? t("matchups.last.title", {week: wk}) : t("matchups.last.titleNone")}</span></h3>
    <ul>${rows.map(li).join("")}</ul></section>`;
}
