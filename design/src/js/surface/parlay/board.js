/* AN OPENED GAME'S RESEARCH (2026-10-03 as the Slips board; since 2026-10-08 what a game shows once opened in
   its kickoff window, windows.js). Each side's implied points as one bar, Preview's headline as a link to
   that game's dossier, then a row per player: his name, his work in his last three games as bars with every
   number under them, his snap share, a chip only when something applies (an easy or tough matchup), and
   "N lines ›", which opens his sheet. No pick on these rows: a game's picks sit above them, one per line
   (data/ourpicks.js). No TE or Role guys chips since 2026-10-08 (storyboard "Slips" B dropped them). */
const SL_CHEV = `<svg viewBox="0 0 8 12" aria-hidden="true"><path d="M2 1.5 6.5 6 2 10.5"/></svg>`;

const slWorkLabel = k => k === "tgt" ? t("slips.work.tgt") : k === "car" ? t("slips.work.car") : t("slips.work.snap");
const SL_MKT_WORD = () => ({REC: t("matchups.stat.rec"), RUSH: t("matchups.stat.rush"), PASS: t("matchups.stat.pass"), RECS: t("slips.mkt.recs")});

/* Three bars, each with its number under it, tallest his most in the three. The last is bold, never green. */
const SL_BAR_PX = 18;
function slSparkHTML(last){
  const top = Math.max(...last, 1);
  return `<span class="sl-spark">${last.map(v =>
    `<span><i data-testid="parlay-spark-bar" style="--h:${Math.max(2, v / top * SL_BAR_PX).toFixed(0)}px"></i><em>${v}</em></span>`).join("")}</span>`;
}

/* "Carries [bars] Snaps 72%": his work, then his snap share unless the bars already are snaps. */
function slUseHTML(x){
  const w = x.work, snap = slSnapNow(x.p), out = [];
  if (w) out.push(`<span class="sl-use"><span class="sl-ul">${slWorkLabel(w.key)}</span>${slSparkHTML(w.last)}</span>`);
  if (snap !== null && (!w || w.key !== "snap")) out.push(`<span class="sl-use"><span class="sl-ul">${t("slips.work.snap")}</span><b>${snap}%</b></span>`);
  return out.length ? `<span class="sl-uses">${out.join("")}</span>` : "";
}

/* The matchup chip, only when it applies. A dot, then the words. */
function slFlagsHTML(x){
  const tone = slMatchup(x.p), flags = [];
  if (tone) flags.push(`<span class="sl-f ${tone}" title="${t("slips.flag.mark")}">${tone === "easy" ? t("slips.flag.easy") : t("slips.flag.tough")}</span>`);
  return flags.length ? `<span class="sl-fl">${flags.join("")}</span>` : "";
}

function slRowHTML(x, on){
  const p = x.p, n = x.rows.length;
  return `<li><button type="button" class="sl-row" data-testid="parlay-row" data-slplayer="${esc(x.slug)}" aria-haspopup="dialog">
      <span class="sl-l">
        <span class="sl-who"><b data-testid="parlay-row-name">${esc(p.n)}</b><span class="sl-pos">${esc(p.pos)} · ${esc(p.team)}</span>${on ? `<span class="sl-on" data-testid="parlay-row-on">${t("slips.onSlip")}</span>` : ""}</span>
        ${slUseHTML(x)}${slFlagsHTML(x)}
      </span>
      <span class="sl-r"><span class="sl-go" data-testid="parlay-row-go">${n === 1 ? t("slips.lines.one") : t("slips.lines.many", {n})}${SL_CHEV}</span></span>
    </button></li>`;
}

/* "SEA 22.2 [bar] 25.2 SF": each side's implied points. */
function slLineBoxHTML(teams, ln){
  if (!ln || !ln.imp) return "";
  return `<div class="sl-imp"><span>${esc(teams[0])} <b>${pvNum(ln.imp[0])}</b></span>
      <i class="sl-impbar" style="--a:${(ln.imp[0] / (ln.imp[0] + ln.imp[1]) * 100).toFixed(1)}%"></i>
      <span><b>${pvNum(ln.imp[1])}</b> ${esc(teams[1])}</span></div>`;
}

/* The research under an opened game: its numbers and headline, then every player. */
function slGameMoreHTML(g, on){
  const teams = slTeams(g.game), pv = teams.length === 2 ? slPreviewGame(teams) : null, k = pv && pv.take;
  return `<div class="sl-gm">
      ${teams.length === 2 ? slLineBoxHTML(teams, slGameLine(teams, pv)) : ""}
      ${k ? `<button type="button" class="sl-take" data-slprev="${pvGames().indexOf(pv)}">${esc(k.head)}<span aria-hidden="true">›</span></button>` : ""}
    </div>
    <h4 class="sl-every">${t("slips.game.every", {n: g.players.length})}</h4>
    <ul class="sl-rows">${g.players.map(x => slRowHTML(x, on.has(x.slug))).join("")}</ul>`;
}

/* A game's headline opens its Preview dossier, the way a Recap game does (recap.js wrGo). */
function slOpenPreview(i){
  if (typeof morphLogo === "function") morphLogo();
  navGo("preview");
  pvOpen(i);
  window.scrollTo({top: 0});
}
