/* THE SLIPS BOARD, DRAWN (2026-10-03; the reads are builder/board.js). Per kickoff tab, one card per
   game: its matchup and kickoff, each side's implied points as one bar, Preview's headline as a link
   to that game's dossier, then four chips (Work rising, TE, Role guys, All N) over the game's players.
   A player is one row in two columns (2026-10-05, storyboard "Slips Board" A): on the left his name,
   his work in his last three games as bars with every number under them, his snap share, and a chip
   only when something applies (an easy or tough matchup, a teammate out); on the right the model's
   most confident line with its tier word, then "N lines". Pictures and numbers, no sentences.

   Material's rule (DESIGN.md "Cards"): the game is the card, the players are rows in it, divided by
   a hairline; the chips are the card's own buttons and a row is its own tap. */
const SL_CHEV = `<svg viewBox="0 0 8 12" aria-hidden="true"><path d="M2 1.5 6.5 6 2 10.5"/></svg>`;

const slWorkLabel = k => k === "tgt" ? t("slips.work.tgt") : k === "car" ? t("slips.work.car") : t("slips.work.snap");
const slChipLabel = (k, n) => k === "rise" ? t("slips.chip.rise") : k === "te" ? t("slips.chip.te") : k === "role" ? t("slips.chip.role") : t("slips.chip.all", {n});
const SL_MKT_WORD = () => ({REC: t("matchups.stat.rec"), RUSH: t("matchups.stat.rush"), PASS: t("matchups.stat.pass"), RECS: t("slips.mkt.recs")});

/* Three bars, each with its number under it, tallest his most in the three. The last is green when his
   work is rising and bold always. */
const SL_BAR_PX = 18;
function slSparkHTML(last, up){
  const top = Math.max(...last, 1);
  return `<span class="sl-spark">${last.map((v, k) => {
    const now = k === last.length - 1;
    return `<span class="${now && up ? "up" : ""}"><i style="--h:${Math.max(2, v / top * SL_BAR_PX).toFixed(0)}px"></i><em>${v}</em></span>`;
  }).join("")}</span>`;
}

/* "Carries [bars] Snaps 72%": his work, then his snap share unless the bars already are snaps. */
function slUseHTML(x){
  const w = x.work, snap = slSnapNow(x.p), out = [];
  if (w) out.push(`<span class="sl-use"><span class="sl-ul">${slWorkLabel(w.key)}</span>${slSparkHTML(w.last, slRising(x))}</span>`);
  if (snap !== null && (!w || w.key !== "snap")) out.push(`<span class="sl-use"><span class="sl-ul">${t("slips.work.snap")}</span><b>${snap}%</b></span>`);
  return out.length ? `<span class="sl-uses">${out.join("")}</span>` : "";
}

/* The matchup chip and one per teammate out, only when they apply. A dot, then the words. */
function slFlagsHTML(x){
  const tone = slMatchup(x.p), flags = [];
  if (tone) flags.push(`<span class="sl-f ${tone}">${tone === "easy" ? t("slips.flag.easy") : t("slips.flag.tough")}</span>`);
  x.vacated.forEach(v => flags.push(`<span class="sl-f out">${t("slips.flag.out", {last: esc(v.last)})}</span>`));
  return flags.length ? `<span class="sl-fl">${flags.join("")}</span>` : "";
}

/* "Lower rec yds" over its tier word, or nothing when the model has no pick on any of his lines. A lime
   "C" sits on its corner when Claude picked the same side of that exact line (2026-10-05); a call the other
   way shows nothing here, the line sheet carries it. */
function slPickHTML(x){
  const b = slBestLine(x);
  if (!b) return "";
  const side = b.side === "lower" ? t("slips.side.lower") : t("slips.side.higher");
  const c = slClaude(PROPS[b.i]), badge = slClaudeAgrees(c, b) ? slClaudeBadge(true) : "";
  return `<span class="sl-pick">${t("slips.pick.label", {side, mkt: SL_MKT_WORD()[b.mkt] || b.mkt})}${badge}</span>${slTierHTML(b.tier)}`;
}

function slRowHTML(x, on){
  const p = x.p, n = x.rows.length;
  return `<li><button type="button" class="sl-row" data-slplayer="${esc(x.slug)}" aria-haspopup="dialog">
      <span class="sl-l">
        <span class="sl-who"><b>${esc(nameInitial(p.n))}</b><span class="sl-pos">${esc(p.pos)} · ${esc(p.team)}</span>${on ? `<span class="sl-on">${t("slips.onSlip")}</span>` : ""}</span>
        ${slUseHTML(x)}${slFlagsHTML(x)}
      </span>
      <span class="sl-r">${slPickHTML(x)}<span class="sl-go">${n === 1 ? t("slips.lines.one") : t("slips.lines.many", {n})}${SL_CHEV}</span></span>
    </button></li>`;
}

/* "SEA 22.2 [bar] 25.2 SF": each side's implied points. */
function slLineBoxHTML(teams, ln){
  if (!ln || !ln.imp) return "";
  return `<div class="sl-imp"><span>${esc(teams[0])} <b>${pvNum(ln.imp[0])}</b></span>
      <i class="sl-impbar" style="--a:${(ln.imp[0] / (ln.imp[0] + ln.imp[1]) * 100).toFixed(1)}%"></i>
      <span><b>${pvNum(ln.imp[1])}</b> ${esc(teams[1])}</span></div>`;
}

function slGameHTML(g, on){
  const teams = slTeams(g.game), pv = teams.length === 2 ? slPreviewGame(teams) : null, k = pv && pv.take;
  const chip = slChip(g), shown = slChipPlayers(g, chip);
  const chips = SL_CHIPS.map(c => `<button type="button" class="chip" data-slchip="${c}" data-slgame="${esc(g.game)}" aria-pressed="${chip === c}">${slChipLabel(c, g.players.length)}</button>`).join("");
  const rows = shown.length ? shown.map(x => slRowHTML(x, on.has(x.slug))).join("")
    : `<li class="sl-none">${chip === "rise" ? t("slips.chip.noneRise") : t("slips.chip.none")}</li>`;
  return `<section class="sl-game" data-slgamecard="${esc(g.game)}">
      <header class="sl-gh">
        <div class="sl-gt"><h3>${esc(g.game)}</h3><span>${esc(g.kick || "")}</span></div>
        ${teams.length === 2 ? slLineBoxHTML(teams, slGameLine(teams, pv)) : ""}
        ${k ? `<button type="button" class="sl-take" data-slprev="${pvGames().indexOf(pv)}">${esc(k.head)}<span aria-hidden="true">›</span></button>` : ""}
        <div class="sl-chips" role="group" aria-label="${t("slips.chip.label")}">${chips}</div>
      </header>
      <ul class="sl-rows">${rows}</ul>
    </section>`;
}

function slBoardHTML(){
  const games = slGames(slWin()), on = onSlipSlugs();
  if (!games.length) return `<div class="state-empty sl-empty"><div><b>0</b><span>${t("slips.empty")}</span></div></div>`;
  return `<div class="sl-board">${games.map(g => slGameHTML(g, on)).join("")}</div>`;
}

/* A game's headline opens its Preview dossier, the way a Recap game does (recap.js wrGo). */
function slOpenPreview(i){
  if (typeof morphLogo === "function") morphLogo();
  navGo("preview");
  pvOpen(i);
  window.scrollTo({top: 0});
}

function wireSlBoard(v){
  v.querySelectorAll("[data-slchip]").forEach(b => b.addEventListener("click", () => {
    SL_CHIP[b.dataset.slgame] = b.dataset.slchip;
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-slplayer]").forEach(b => b.addEventListener("click", () => playerSheetOpen(b.dataset.slplayer, b)));
  v.querySelectorAll("[data-slprev]").forEach(b => b.addEventListener("click", () => slOpenPreview(+b.dataset.slprev)));
  // Preview's "All N players in Slips": its game, brought into view once.
  if (SL_FOCUS){
    const card = [...v.querySelectorAll("[data-slgamecard]")].find(el => el.dataset.slgamecard === SL_FOCUS);
    SL_FOCUS = null;
    if (card) card.scrollIntoView({block: "start"});
  }
}
