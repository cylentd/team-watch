/* ============================== LEAGUE > TRADES: THE FINDER ==============================
   2026-10-06 (trade finder, unit U4; the Trades leaf was the trade history until then, now Records > Trade
   history). For every league that has Teams data, ESPN's too. One question: "which position do I need a trade
   at?" A chip row, QB RB WR TE, each with the reader's gap to the league's median there (finder/logic.js), opens on
   the most negative gap; under it the offers whose `get` holds that position, best gain first, top 5 (the file's,
   lboard/offers.js; each card lboard/tbcard.js, with Copy offer and Edit); then who is deep at that position (deep.js),
   then Make your own offer. A team's name in that list, or "Trades with them ›" on its Teams card, opens the finder
   filtered to that team: every offer with him, and a way back to the chips. A reader with no team picks one first:
   a trade needs your team. Edit and Make your own open a page of their own (page.js). */
let TF = {lg: null, me: null, pos: null, partner: null, tapped: false};  // the league and reader these belong to; the chip (tapped: the reader chose it); the team filtered to
let TF_SHOWN = [];                                          // the offers on screen, in order: a card addresses its own by place

/* The state for this league and reader, kept for the visit: a new league or a new team of the reader's starts over,
   a chip the league does not have is the most negative gap, a partner no longer there is no filter. Returns the gaps. */
function tfSync(lg, me){
  if (TF.lg !== lg.key || TF.me !== me.key) TF = {lg: lg.key, me: me.key, pos: null, partner: null, tapped: false};
  if (TF.partner && !lg.teams.some(x => x.key === TF.partner && x.key !== me.key)) TF.partner = null;
  const gaps = tfGaps(lg, me);
  // Until the reader taps a chip, the opening chip follows the offers once they land (tfStartPos).
  if (!TF.tapped || !gaps.some(g => g.pos === TF.pos)) TF.pos = tfStartPos(gaps, TB_DATA ? tfOffered(tbOffersOf(lg, me)) : null);
  return gaps;
}

/* With no team picked: one line, then every team to pick from, by league (the picker's own markup, chrome/teamswitch.js). */
function tfNeedHTML(){
  const group = k => `<section class="tp-lg" aria-labelledby="tp-${k}"><h2 id="tp-${k}">${tsLeagueName(k)}</h2>
    <ul>${[k, ...mateKeys(k)].sort(tsByName).map(tpTeamHTML).join("")}</ul></section>`;
  return `<p class="tf-need" data-testid="finder-need">${t("finder.need")}</p><div class="tp-grid">${tsLeagues().map(group).join("")}</div>`;
}

/* The chips: a position and the reader's gap to the league's median there, red below it, green above. One is pressed. */
function tfChipsHTML(gaps){
  const chip = g => `<button type="button" class="tf-chip" data-tfpos="${g.pos}" aria-pressed="${g.pos === TF.pos}" data-testid="finder-chip"
    aria-label="${t("finder.chip.aria", {pos: g.pos, gap: tfSigned(g.gap)})}"><i data-pos="${g.pos}">${g.pos}</i>
    <b class="${g.gap < 0 ? "dn" : g.gap > 0 ? "up" : ""}" data-testid="finder-gap">${tfSigned(g.gap)}</b></button>`;
  return `<div class="tf-chips" role="group" aria-label="${t("finder.chips.aria")}">${gaps.map(chip).join("")}</div>`;
}

/* The filtered state's head: the way back to the chips, then who the offers are with. */
const tfPartnerBarHTML = tm => `<button type="button" class="lbp-back tf-all" data-tfall data-testid="finder-all">${tfChev}<span>${t("finder.partner.all")}</span></button>
  <h2 class="tf-h tf-with" data-testid="finder-with">${t("finder.partner.title", {name: esc(tm.name)})}</h2>`;

/* Under the head: the error, the shapes while the file loads, or the cards (an empty state says so in one line). */
function tfOffersHTML(lg, me, partner){
  const head = partner ? "" : `<h2 class="tf-h" title="${t("lboard.offer.mark")}">${t("finder.offers.pos", {pos: TF.pos})}</h2>`;
  if (TB_ERR) return head + `<div class="state-empty tb-empty" data-testid="finder-error"><div><b>${t("lboard.offer.error")}</b>
    <button type="button" class="chip" data-tbretry>${t("lboard.offer.retry")}</button></div></div>`;
  if (!TB_DATA){ TF_SHOWN = []; return head + tbSkelHTML(); }
  TF_SHOWN = tfOffersFor(tbOffersOf(lg, me), TF.pos, partner && partner.name);
  const edit = tbEditOk(lg, me);
  return head + (TF_SHOWN.length ? TF_SHOWN.map((o, i) => tbCardHTML(o, i, lg, edit)).join("")
    : tbEmptyHTML(partner ? t("finder.partner.none", {name: esc(partner.name)}) : t("finder.empty.pos", {pos: TF.pos})));
}

/* Under everything, once the file is in: a package of the reader's own, and the date the offers were made. */
const tfTailHTML = (lg, me) => !TB_DATA ? "" : (tbEditOk(lg, me) ? `<button type="button" class="tb-own" data-tbown data-testid="finder-own">${t("lboard.offer.own")}</button>` : "")
  + `<p class="tb-upd">${tbUpdated()}</p>`;

function tfViewHTML(){
  if (TB_EDIT && TB) return tfEditPageHTML();             // page.js
  const lg = lbOf(lbLeagueKey()), head = lgChipHTML(), me = lg && tbMine(lg);
  // No team picked, or a pick that is not in this league (a connected one): the picker. A league with no rosters: the empty block.
  if (!myTeamLoad() || (lg && !me)) return `<div class="wrap tf">${head}${tfNeedHTML()}</div>`;
  if (!lg) return `<div class="wrap tf">${head}${lbEmptyHTML()}</div>`;
  const gaps = tfSync(lg, me), partner = TF.partner ? lg.teams.find(x => x.key === TF.partner) : null;
  return `<div class="wrap tf">${head}${partner ? tfPartnerBarHTML(partner) : tfChipsHTML(gaps)}
    <div class="tf-offers" data-testid="finder-offers">${tfOffersHTML(lg, me, partner)}</div>
    ${partner ? "" : tfDeepHTML(lg, me)}<div class="tf-tail">${tfTailHTML(lg, me)}</div></div>`;
}

/* The partner Make your own opens against: the filtered team, else the deepest at the chip (the page lets the reader change it). */
const tfOwnPartner = (lg, me) => lg.teams.find(x => x.key === (TF.partner || (tfDeep(lg, TF.pos, me.key)[0] || {}).key));

/* The first draw of the finder asks for the file, and draws again when it lands (a reader who left meanwhile is left alone). */
function tfLoad(){
  if (TB_DATA || TB_ERR || TB_BUSY) return;
  tbLoad().then(() => { if (SURFACE === "trades" && !TB_EDIT) render(); });
}

function tfClick(e, lg, me){
  const hit = sel => e.target.closest(sel), v = document.getElementById("view");
  const pos = hit("[data-tfpos]"), who = hit("[data-tfwho]"), edit = hit("[data-tbedit]"), own = hit("[data-tbown]"), pick = hit("[data-pick]");
  if (pick) return pickTeam(pick.dataset.pick);
  if (pos){ TF.pos = pos.dataset.tfpos; TF.tapped = true; render(); return v.querySelector(`[data-tfpos="${TF.pos}"]`)?.focus({preventScroll: true}); }
  if (who){ TF.partner = who.dataset.tfwho; render(); window.scrollTo({top: 0}); return v.querySelector("[data-tfall]")?.focus({preventScroll: true}); }
  if (hit("[data-tfall]")){ TF.partner = null; render(); return v.querySelector(`[data-tfpos="${TF.pos}"]`)?.focus({preventScroll: true}); }
  if (hit("[data-tbretry]")){ TB_ERR = false; render(); tbLoad().then(() => { if (SURFACE === "trades" && !TB_EDIT) render(); }); return; }
  const copy = hit("[data-tbcopy]");
  if (copy && TB_DATA) return tbCopy(copy);
  if (edit && TB_DATA){ const o = TF_SHOWN[+edit.dataset.tbedit], tm = o && lg.teams.find(x => x.name === o.partner); return tm && tbEditOpen(lg, me, tm, o, edit, false); }
  if (own && TB_DATA){ const tm = tfOwnPartner(lg, me); return tm && tbEditOpen(lg, me, tm, null, own, !TF.partner); }
}

/* One listener per draw: the view is new each time, so it never stacks. */
function wireTf(v){
  if (TB_EDIT && TB) return wireTfPage(v);
  wireLgChip(v);
  const root = v.querySelector(".tf"), lg = lbOf(lbLeagueKey()), me = lg && tbMine(lg);
  if (!root) return;
  if (me) tfLoad();
  root.addEventListener("click", e => tfClick(e, lg, me));
}

/* "Trades with them ›" on a Teams card (lboard/lbcard.js): the finder, filtered to that team. */
function tfOpenWith(key){
  const lg = tbLeagueOf(key), me = tbMine(lg);
  if (!lg || !me || me.key === key) return;
  TF = {lg: lg.key, me: me.key, pos: null, partner: key};
  navGo("trades");
  window.scrollTo({top: 0});
}
