/* SLIPS BY KICKOFF WINDOW (2026-10-08, storyboard "Slips" B's windows with C's one call per game, ledger #33).
   Under the record line, the kickoff tab's windows ("Sunday early · 10:00 AM · 8 games"), each a card of its
   games. A closed game is its matchup, its pick count and its best pick: face, full name, "Our pick" and the
   side and line, the chance and tier word, and a round + that puts the side on the slip. Games whose best
   pick is Confident or better lead the window (data/ourpicks.js opOrder). A tap on the matchup opens the
   game in place: its other picks, then its numbers and every player (board.js).

   One pick per line (David: "our model is claude + model"): a side shows only where Claude and the model
   agree; the lines where they split show no side and sit under the window's Split fold. A game Claude has
   not called yet says when its picks come. Before 2026-10-08 Slips led with five Top calls, then a card per
   game with every player open (226 rows on a Sunday at 360px). */

const slSide = s => t(s === "lower" ? "slips.side.lower" : "slips.side.higher");

/* One pick: the row opens his sheet, the + puts the side on the slip (the same side again takes it off). */
function slPickRowHTML(x){
  const p = PROPS[x.i], mkt = SL_MKT_WORD()[x.mkt] || x.mkt, side = slSide(x.side);
  const on = SLIP.includes(x.i) && slipSide(x.i) === x.side, team = (TEAM_COLOURS[x.team] || [])[0];
  return `<li class="sl-pk" data-testid="parlay-pick">
      <button type="button" class="sl-pkm" data-slplayer="${esc(x.slug)}" aria-haspopup="dialog" aria-label="${t("slips.top.open", {name: esc(x.n)})}">
        <span class="tk-face sl-face"${team ? ` style="--team:${team}"` : ""}>${avatarHTML(p)}</span>
        <span class="sl-pkb">
          <span class="sl-who"><b data-testid="parlay-pick-name">${esc(x.n)}</b><span class="sl-pos">${esc(x.pos)} · ${esc(x.team)}</span></span>
          <span class="sl-pkl"><span class="sl-our">${t("slips.our.label")}</span><span class="sl-pick" data-testid="parlay-pick-side">${t("slips.pick.label", {side, mkt})} <b>${x.line}</b></span></span>
          ${slTierHTML(x.tier, x.pct)}
        </span>
      </button>
      <button type="button" class="sl-add${on ? " on" : ""}" data-testid="parlay-pick-add" data-slpick="${x.i}" data-side="${x.side}" aria-pressed="${on}"
        aria-label="${t("slips.top.add", {side, mkt, name: esc(x.n)})}"><i aria-hidden="true"></i></button>
    </li>`;
}

/* The count beside the matchup: "3 picks", "No pick", or when its picks come. */
function slGameCount(op){
  if (!op.called) return t("slips.game.pending");
  const n = op.picks.length;
  return n ? (n === 1 ? t("slips.game.one") : t("slips.game.many", {n})) : t("slips.game.none");
}

/* A game's kickoff shows only where it differs from its window's heading (a 4:25 game in a 4:05 window). */
function slGameHTML(g, on, wAt){
  const open = !!SL_OPEN[g.game], op = g.op, rest = open ? op.picks.slice(1) : [], at = kickTime(g.at);
  return `<article class="sl-game${open ? " open" : ""}" data-testid="parlay-game" data-slgamecard="${esc(g.game)}">
      <button type="button" class="sl-gr" data-testid="parlay-game-toggle" data-slopen="${esc(g.game)}" aria-expanded="${open}">
        <h3 data-testid="parlay-game-title">${esc(g.game)}</h3>
        <span class="sl-gn" data-testid="parlay-game-count">${slGameCount(op)}</span>
        <span class="sl-gk">${at !== wAt ? esc(at) : ""}</span><i class="sl-chev" aria-hidden="true"></i>
      </button>
      ${op.picks.length ? `<ul class="sl-pks">${[op.picks[0], ...rest].map(slPickRowHTML).join("")}</ul>` : ""}
      ${open ? slGameMoreHTML(g, on) : ""}
    </article>`;
}

/* The window's Split fold: the lines Claude and the model called opposite ways, no side on any. */
function slSplitHTML(key, lines){
  if (!lines.length) return "";
  const open = !!SL_SPLIT[key];
  const rows = open ? `<ul class="sl-sps">${lines.map(x => `<li><button type="button" class="sl-sp" data-testid="parlay-split-line" data-slplayer="${esc(x.slug)}" aria-haspopup="dialog">
      <b>${esc(x.n)}</b><span class="sl-pos">${esc(x.pos)} · ${esc(x.team)}</span><span class="sl-spm">${esc(MKT[x.mkt] || x.mkt)} <b>${x.line}</b></span></button></li>`).join("")}</ul>` : "";
  return `<div class="sl-split">
      <button type="button" class="sl-spb" data-testid="parlay-split" data-slsplit="${esc(key)}" aria-expanded="${open}">
        <span>${t("slips.split.title", {n: lines.length})}</span><small>${t("slips.split.sub")}</small><i class="sl-chev" aria-hidden="true"></i>
      </button>${rows}
    </div>`;
}

function slWinHTML(x, on){
  const w = x.w, n = x.games.length, split = x.games.flatMap(g => g.op.split), at = kickTime(w.at);
  return `<section class="sl-win" data-testid="parlay-window" aria-label="${esc(galGroupName(w))}">
      <header class="sl-wh"><h2 data-testid="parlay-window-name">${esc(galGroupName(w))}</h2><span>${esc(at)} · ${n === 1 ? t("slips.win.one") : t("slips.win.many", {n})}</span></header>
      <div class="sl-wcard">${x.games.map(g => slGameHTML(g, on, at)).join("")}${slSplitHTML(w.k, split)}</div>
    </section>`;
}

function slBoardHTML(){
  if (SL_FOCUS) SL_OPEN[SL_FOCUS] = true;
  const wins = slWindows(slWin()), on = onSlipSlugs();
  if (!wins.length) return `<div class="state-empty sl-empty"><div><b>0</b><span>${t("slips.empty")}</span></div></div>`;
  return `<div class="sl-board" data-testid="parlay-board">${wins.map(x => slWinHTML(x, on)).join("")}</div>`;
}

/* A toggle redraws in place: the page holds its scroll, so nothing moves under the reader but what opened. */
function slRedraw(){ const y = window.scrollY; render(); window.scrollTo(0, y); }

function wireSlBoard(v){
  v.querySelectorAll("[data-slopen]").forEach(b => b.addEventListener("click", () => {
    const g = b.dataset.slopen;
    SL_OPEN[g] = !SL_OPEN[g];
    slRedraw();
  }));
  v.querySelectorAll("[data-slsplit]").forEach(b => b.addEventListener("click", () => {
    SL_SPLIT[b.dataset.slsplit] = !SL_SPLIT[b.dataset.slsplit];
    slRedraw();
  }));
  v.querySelectorAll("[data-slplayer]").forEach(b => b.addEventListener("click", () => playerSheetOpen(b.dataset.slplayer, b)));
  v.querySelectorAll("[data-slprev]").forEach(b => b.addEventListener("click", () => slOpenPreview(+b.dataset.slprev)));
  v.querySelectorAll(".sl-add[data-slpick]").forEach(b => b.addEventListener("click", () => slPick(b)));
  // Preview's "All N players in Slips": its game, opened and brought into view once.
  if (SL_FOCUS){
    const card = [...v.querySelectorAll("[data-slgamecard]")].find(el => el.dataset.slgamecard === SL_FOCUS);
    SL_FOCUS = null;
    if (card) card.scrollIntoView({block: "start"});
  }
}
