/* ============================== TEAM > TRADES > VALUE ==============================
   2026-11-03 (David: "Jameson for Goedert is terrible. You have to think of PAR."). The Trades leaf has two tabs,
   Offers (the finder, finder.js) and Value, declared with navModes (data/tabrow.js) so a phone opens them in place in
   the Trades pill and a desktop draws the bar (.view-tabs). Value is one chip row (All, Mine, QB, RB, WR, TE), a
   caption with the replacement level per position, then the league's players in PAR order: position rank, name with
   his NFL team and who rosters him, and the answer, his PAR. Under the name, the research: points a game x games, and
   up to two pills, If healthy (a what-if for a player priced for missed games) and League sees (his manager's screen
   against our rate). The numbers are ff-jarvis's (LIVE_TRADE_VALUE, data/tradevalue.js); the page computes none.

   Absent without a file: no tab, and Trades reads as it did. The league is the one chip's (lbLeagueKey). */
let TV_TAB = "offers";
let TV_CHIP = "all";
let TV_ALL = false;           // the All list past its cap
let TV_SPAN = "ros";          // the rest of season, or "po": the fantasy playoff weeks

const tvTabs = () => tvLeague(tvBlock(), lbLeagueKey()) ? ["offers", "value"] : ["offers"];
const tvTab = () => TV_TAB === "value" && tvTabs().includes("value") ? "value" : "offers";
const tvTabName = id => id === "value" ? t("finder.tab.value") : t("finder.tab.offers");
/* The reader's team's name in this league, or null: Mine and the lime rows follow it. One of David's teams has the
   league's own key and is the file's `me` (the roster file's name, emoji and all); a leaguemate's is his Teams name. */
function tvMe(lg){
  const k = myTeamLoad() || (lgMine() || {}).key, key = lbLeagueKey();
  if (!k) return null;
  if (k === key) return lg.me || null;
  const teams = lbOf(key), m = teams && teams.teams.find(x => x.key === k);
  return m ? m.name : null;
}

/* Forgotten when the reader leaves Trades (ledger #91): a visit opens Offers. */
navForget("trades", () => { TV_TAB = "offers"; TV_CHIP = "all"; TV_ALL = false; TV_SPAN = "ros"; });

function tvSelectTab(id){
  if (id === tvTab() || !tvTabs().includes(id)) return;
  TV_TAB = id;
  render();
  window.scrollTo({top: 0});
}
navModes("trades", () => ({ids: tvTabs(), cur: tvTab(), attr: "tvtab", name: t("finder.tabs.label"), label: tvTabName, select: tvSelectTab}));

/* The desktop's bar; "" with one tab, and hidden on a phone, whose tab row holds the tabs. */
const tvTabsHTML = () => tvTabs().length < 2 ? "" : `<div class="setrow tv-tabs view-tabs" role="group" aria-label="${t("finder.tabs.label")}">${
  tvTabs().map(id => `<button type="button" class="chip" data-testid="trades-tab" data-tvtab="${id}" aria-pressed="${id === tvTab()}">${tvTabName(id)}</button>`).join("")}</div>`;

const tvChipName = f => f === "all" ? t("value.chip.all") : f === "mine" ? t("value.chip.mine") : f;

function tvChipsHTML(lg, me, cur){
  return `<div class="setrow tv-chips" role="group" aria-label="${t("value.chips.label")}">${tvFilters(lg, me).map(f =>
    `<button type="button" class="chip" data-testid="value-chip" data-tvchip="${f}" aria-pressed="${f === cur}">${tvChipName(f)}</button>`).join("")}</div>`;
}

/* The span: the rest of season, or the fantasy playoff weeks (Ranks' Rest of season has the same toggle). */
const tvSpanName = (id, block) => id === "po" ? t("value.span.po", {from: block.po_weeks[0], to: block.po_weeks[block.po_weeks.length - 1]}) : t("value.span.ros");
function tvSpanHTML(block, lg, cur){
  const ids = tvSpans(block, lg);
  return ids.length < 2 ? "" : `<div class="setrow tv-spans" role="group" aria-label="${t("value.span.label")}">${ids.map(id =>
    `<button type="button" class="chip" data-testid="value-span" data-tvspan="${id}" aria-pressed="${id === cur}">${tvSpanName(id, block)}</button>`).join("")}</div>`;
}

/* Under the name: points a game x games, then the pills. */
function tvResearchHTML(p, span){
  const add = tvHealthyAdd(p, span), gap = tvGap(p);
  const healthy = add == null ? "" : `<i class="tv-pill tv-healthy" data-testid="value-healthy" title="${esc(t("value.healthy.tip", {games: p.games_healthy}))}">${t("value.healthy", {par: tvSigned(add)})}</i>`;
  const sees = gap == null ? "" : `<i class="tv-pill ${gap > 0 ? "up" : "dn"}" data-testid="value-sees" title="${esc(t("value.sees.tip", {perc: p.perc.toFixed(1), ours: p.ros_pg.toFixed(1)}))}">${t("value.sees", {gap: tvSigned(gap)})}</i>`;
  return `<span class="tv-why"><span data-testid="value-rate">${t("value.rate", {pg: p.ros_pg.toFixed(1), games: p.show_games.toFixed(1)})}</span>${healthy}${sees}</span>`;
}

function tvRowHTML(p, me, span){
  const mine = !!me && p.holder === me;
  const who = p.holder == null ? t("value.row.free") : mine ? t("value.row.yours") : esc(p.holder);
  return `<button type="button" class="tv-row${mine ? " mine" : ""}" data-testid="value-row" data-tvopen="${esc(p.slug)}">
    <span class="tv-pos" data-pos="${p.pos}" data-testid="value-rank">${p.pos}${p.show_rank}</span>
    <span class="tv-nm"><span class="tv-who"><b data-testid="value-name">${esc(nameInitial(p.n))}</b><small>${esc(p.team || "")} · <span data-testid="value-holder">${who}</span></small></span>${tvResearchHTML(p, span)}</span>
    <span class="tv-par${p.show_par < 0 ? " dn" : ""}" data-testid="value-par">${tvSigned(p.show_par)}</span>
  </button>`;
}

function tvViewHTML(){
  const block = tvBlock(), key = lbLeagueKey(), lg = tvLeague(block, key), me = tvMe(lg);
  const span = tvSpans(block, lg).includes(TV_SPAN) ? TV_SPAN : "ros";
  const chip = tvFilter(lg, me, TV_CHIP), rows = tvRows(lg, chip, me, span), shown = tvShown(rows, chip, TV_ALL), more = tvMore(rows, chip, TV_ALL);
  const repl = tvReplacement(lg).map(([pos, pg]) => `${pos} ${pg.toFixed(1)}`).join(" · ");
  const capArgs = {repl, date: esc(tvDate(block))};
  const cap = `<p class="tv-cap" data-testid="value-cap">${span === "po"
    ? t("value.cap.po", capArgs) : t("value.cap", capArgs)}</p>`;
  const list = rows.length ? `<div class="tv-list" data-testid="value-list">${shown.map(p => tvRowHTML(p, me, span)).join("")}</div>`
    + (more ? `<button type="button" class="chip tv-more" data-tvmore data-testid="value-more">${t("value.more", {n: more})}</button>` : "")
    : `<div class="state-empty" data-testid="value-empty" style="min-height:160px"><div><b>${t("value.empty")}</b></div></div>`;
  return `<div class="wrap tv">${lgChipHTML()}${tvTabsHTML()}${tvChipsHTML(lg, me, chip)}${tvSpanHTML(block, lg, span)}${cap}${list}</div>`;
}

/* "Oct 28": the day the rest-of-season prices were made, which can be older than the file. */
function tvDate(block){
  const s = block.ros_generated || block.generated || "";
  const d = new Date(s.slice(0, 10) + "T12:00:00");
  return isNaN(d) ? "" : d.toLocaleDateString("en-US", {month: "short", day: "numeric"});
}

function wireTv(v){
  wireLgChip(v);
  const root = v.querySelector(".tv");
  if (!root) return;
  root.addEventListener("click", e => {
    const tab = e.target.closest("[data-tvtab]"), chip = e.target.closest("[data-tvchip]"), row = e.target.closest("[data-tvopen]");
    const span = e.target.closest("[data-tvspan]");
    if (tab) return tvSelectTab(tab.dataset.tvtab);
    if (span){ TV_SPAN = span.dataset.tvspan; TV_ALL = false; render(); return v.querySelector(`[data-tvspan="${TV_SPAN}"]`)?.focus({preventScroll: true}); }
    if (chip){ TV_CHIP = chip.dataset.tvchip; TV_ALL = false; render(); return v.querySelector(`[data-tvchip="${TV_CHIP}"]`)?.focus({preventScroll: true}); }
    if (e.target.closest("[data-tvmore]")){ TV_ALL = true; return render(); }
    if (row){
      const p = (tvLeague(tvBlock(), lbLeagueKey()) || {players: []}).players.find(x => x.slug === row.dataset.tvopen);
      if (p) openProfile({n: p.n, pos: p.pos, team: p.team, slug: p.slug}, row);
    }
  });
}
