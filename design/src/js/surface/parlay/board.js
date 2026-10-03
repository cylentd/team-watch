/* THE SLIPS BOARD, DRAWN (2026-10-03; the reads are builder/board.js). Per kickoff tab, one card per
   game: its matchup and kickoff, each side's implied points as one bar, the spread and total,
   Preview's headline and the first line of its story, then four chips (Work rising, TE, Role guys,
   All N) over the game's players. A player is one row: name, position and club, his work in his
   last three games as bars with the latest number, ff-jarvis's reason, and "N lines". No line and
   no model % on a row: those are one tap away, in the player sheet (playersheet.js).

   Material's rule (DESIGN.md "Cards"): the game is the card, the players are rows in it, divided by
   a hairline; the chips are the card's own buttons and a row is its own tap. */
const SL_CHEV = `<svg viewBox="0 0 8 12" aria-hidden="true"><path d="M2 1.5 6.5 6 2 10.5"/></svg>`;

const slWorkLabel = k => k === "tgt" ? t("slips.work.tgt") : k === "car" ? t("slips.work.car") : t("slips.work.snap");
const slChipLabel = (k, n) => k === "rise" ? t("slips.chip.rise") : k === "te" ? t("slips.chip.te") : k === "role" ? t("slips.chip.role") : t("slips.chip.all", {n});

/* Three bars, the latest the brightest; tallest is his most in the three. */
function slSparkHTML(last){
  const top = Math.max(...last, 1);
  return `<span class="sl-spark" aria-hidden="true">${last.map((v, k) =>
    `<i class="${k === last.length - 1 ? "now" : ""}" style="--h:${Math.max(14, v / top * 100).toFixed(0)}%"></i>`).join("")}</span>`;
}

function slUseHTML(x){
  const w = x.work, snap = slSnapNow(x.p), out = [];
  if (w){
    const pct = w.key === "snap" ? "%" : "";
    out.push(`<span class="sl-use"><span>${slWorkLabel(w.key)}</span>${slSparkHTML(w.last)}<b>${w.last[w.last.length - 1]}${pct}</b></span>`);
  }
  if (snap !== null && (!w || w.key !== "snap")) out.push(`<span class="sl-use"><span>${t("slips.work.snap")}</span><b>${snap}%</b></span>`);
  return out.length ? `<span class="sl-uses">${out.join("")}</span>` : "";
}

function slRowHTML(x, on){
  const p = x.p, n = x.rows.length;
  return `<li><button type="button" class="sl-row" data-slplayer="${esc(x.slug)}" aria-haspopup="dialog">
      <span class="sl-who"><b>${esc(nameInitial(p.n))}</b><span class="sl-pos">${esc(p.pos)} · ${esc(p.team)}</span>${
        on ? `<span class="sl-on">${t("slips.onSlip")}</span>` : ""}<span class="sl-go">${n === 1 ? t("slips.lines.one") : t("slips.lines.many", {n})}${SL_CHEV}</span></span>
      ${slUseHTML(x)}
      ${x.why ? `<span class="sl-why">${esc(x.why)}</span>` : ""}
    </button></li>`;
}

/* "SEA 22.2 [bar] 25.2 SF", then "SF by 3 · total 47.5". */
function slLineBoxHTML(teams, ln){
  if (!ln) return "";
  const bar = ln.imp ? `<div class="sl-imp"><span>${esc(teams[0])} <b>${pvNum(ln.imp[0])}</b></span>
      <i class="sl-impbar" style="--a:${(ln.imp[0] / (ln.imp[0] + ln.imp[1]) * 100).toFixed(1)}%"></i>
      <span><b>${pvNum(ln.imp[1])}</b> ${esc(teams[1])}</span></div>` : "";
  const bits = [ln.by || ln.fav ? pvSpread(ln.fav, ln.by) : "", typeof ln.total === "number" ? t("slips.game.total", {n: pvNum(ln.total)}) : ""].filter(Boolean);
  return bar + (bits.length ? `<p class="sl-odds">${bits.join(" · ")}</p>` : "");
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
        ${k ? `<p class="sl-take">${esc(k.head)}</p>${slScript(k) ? `<p class="sl-script">${esc(slScript(k))}</p>` : ""}` : ""}
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

function wireSlBoard(v){
  v.querySelectorAll("[data-slchip]").forEach(b => b.addEventListener("click", () => {
    SL_CHIP[b.dataset.slgame] = b.dataset.slchip;
    const y = window.scrollY; render(); window.scrollTo(0, y);
  }));
  v.querySelectorAll("[data-slplayer]").forEach(b => b.addEventListener("click", () => playerSheetOpen(b.dataset.slplayer, b)));
  // Preview's "All N players in Slips": its game, brought into view once.
  if (SL_FOCUS){
    const card = [...v.querySelectorAll("[data-slgamecard]")].find(el => el.dataset.slgamecard === SL_FOCUS);
    SL_FOCUS = null;
    if (card) card.scrollIntoView({block: "start"});
  }
}
