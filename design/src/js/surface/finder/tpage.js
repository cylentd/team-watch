/* ============================== LEAGUE > TRADES: A PLAYER'S TRADE PAGE ==============================
   2026-10-08 (ledger #51, storyboard trades-pin draft B, which David picked; VISION 2026-10-08 "a page per player").
   A page inside the Trades view, at its own hash so a link to it can be shared (David 3a): `#trades/get/<slug>` for
   another team's player, every package that lands him; `#trades/send/<slug>[+<slug>]` for the reader's own, each
   team's best return, one player or two at once. The profile's footer opens it (profile/tradefoot.js).

   The hash is the state: a draw reads it (tpRoute), Back walks it, and the side follows who owns him once the offers
   are in (a Get link for the reader's own player shows Send). The rows are data/tradepage.js's, from the pinned file
   when ff-jarvis has one (tpdata.js) and today's trade_offers.json when not; their markup is tprows.js's. No legend:
   the column heads and the rows say what they are (VISION 2026-10-08, show not tell). */
let TP_OPEN = -1;          // the row whose offer card is open, -1 for none
let TP_AT = "";            // the hash TP_OPEN belongs to: a new page starts closed

const tpRoute = () => tpParse(navHash());

/* Opens a player's page from anywhere: the layers over the view (the profile) close first, then the hash moves, which
   draws the page (nav.js opens Trades; the listener below draws it when Trades is already open). */
function tpGo(side, slugs){
  layersUnwind(() => { location.hash = tpHash(side, slugs); window.scrollTo({top: 0, behavior: "instant"}); });
}

/* Everything the page knows about its player once the offers are in: the league's file, the owner (a values key),
   his values row, and the side, which follows the owner whatever the hash said. null before the file is in. */
function tpFacts(lg, me, route){
  const lgd = TB_DATA && tbLeagueData(lg);
  if (!lgd || !lgd.values) return null;
  const find = slug => { for (const [team, rows] of Object.entries(lgd.values)){ const r = rows.find(x => x.slug === slug); if (r) return {team, row: r}; } return null; };
  const first = find(route.slugs[0]);
  if (!first) return {lgd, owner: null, players: [], side: route.side};
  const side = first.team === me.name ? "send" : "get";
  const picked = side === "get" ? [first] : route.slugs.map(find).filter(f => f && f.team === me.name);
  return {lgd, owner: first.team, players: picked.map(f => f.row), side};
}

/* The head: his face, "Get J. Smith-Njigba" or "Shop B. Purdy", and his line: position, club, who has him, his
   rest-of-season points in that league's scoring (`keep`, the file's own). */
function tpHeadHTML(players, side, owner, fallback){
  const p = players[0] || fallback, names = (players.length ? players : [fallback]).map(x => esc(nameInitial(x.name)));
  const title = side === "send" ? t("tradepage.title.send", {names: names.join(t("lboard.offer.and"))}) : t("tradepage.title.get", {name: names[0]});
  const who = side === "send" ? t("tradepage.line.yours") : esc(owner || "");
  const line = players.length === 1 ? `<p class="tpg-id">${esc(p.pos)} · ${esc(p.team)} · ${who}${typeof p.keep === "number"
    ? ` · ${t("lboard.offer.gain", {n: `<b>${lbNum(p.keep)}</b>`})}` : ""}</p>` : "";
  return `<header class="tpg-head"><div class="tpg-face">${headHTML({n: p.name, pos: p.pos, team: p.team, slug: p.slug})}</div>
    <div class="tpg-who"><h1 class="tpg-title" id="tpg-title" data-testid="tpg-title">${title}</h1>${line}</div></header>`;
}

/* Send's one control row: Add a player (a native picker of the reader's other QB, RB, WR and TE), or with two
   shopped, each with a way to take him out. */
function tpShopHTML(facts){
  const slugs = facts.players.map(p => p.slug);
  if (slugs.length > 1) return `<div class="tpg-shop">${facts.players.map(p => `<button type="button" class="tpg-pin" data-tpdrop="${esc(p.slug)}"
    data-testid="tpg-drop" aria-label="${esc(t("tradepage.shop.drop", {name: p.name}))}">${esc(nameInitial(p.name))}<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>`).join("")}</div>`;
  const others = (facts.lgd.values[facts.owner] || []).filter(r => !slugs.includes(r.slug) && TP_POS.includes(r.pos));
  if (!others.length) return "";
  const opts = others.map(r => `<option value="${esc(r.slug)}">${esc(r.pos)} · ${esc(r.name)}</option>`).join("");
  return `<div class="tpg-shop"><label class="tpg-add"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>
    <span>${t("tradepage.shop.add")}</span><select data-tpadd data-testid="tpg-add" aria-label="${t("tradepage.shop.add")}">
    <option value="" selected disabled hidden></option>${opts}</select></label></div>`;
}

/* What the list shows: the rows and their source, or why there are none. */
function tpFound(lg, me, facts){
  const pins = tpPinsOf(lg.key, me.name) || null, offers = tbOffersOf(lg, me), slugs = facts.players.map(p => p.slug);
  if (facts.side === "get") return tpGet(pins, offers, slugs[0]);
  const partners = lg.teams.filter(x => x.key !== me.key).map(x => x.name);
  return tpSend(pins, offers, slugs, partners);
}

function tpBodyHTML(lg, me, route){
  if (TB_ERR) return `<div class="state-empty tb-empty" data-testid="tpg-error"><div><b>${t("lboard.offer.error")}</b>
    <button type="button" class="chip" data-tbretry>${t("lboard.offer.retry")}</button></div></div>`;
  const facts = tpFacts(lg, me, route), fallback = tpSearchRow(route.slugs[0]);
  if (!facts || tpPinsOf(lg.key, me.name) === undefined){ TF_SHOWN = []; return tpHeadHTML([], route.side, "", fallback) + tpSkelHTML(); }
  if (!facts.owner){ TF_SHOWN = []; return tpHeadHTML([], route.side, "", fallback)
    + `<div class="state-empty tb-empty tpg-why" data-testid="tpg-why"><b>${t("tradepage.why.free", {name: esc(fallback.name)})}</b></div>`; }
  tpCanon(route, facts);
  const found = tpFound(lg, me, facts), ctx = {side: facts.side, slugs: facts.players.map(p => p.slug), lg, edit: tbEditOk(lg, me), open: TP_OPEN};
  TF_SHOWN = found.rows;
  const own = ctx.edit ? `<button type="button" class="tb-own tpg-own" data-tpown data-testid="tpg-own">${ctx.slugs.length > 1 ? t("tradepage.own.them") : t("tradepage.own.him")}</button>` : "";
  return tpHeadHTML(facts.players, facts.side, facts.owner, fallback) + (facts.side === "send" ? tpShopHTML(facts) : "")
    + (found.rows.length ? tpListHTML(found, ctx) : tpWhy(found.reason, facts.side, facts.owner, ctx.slugs.length > 1))
    + `<div class="tf-tail">${own}<p class="tb-upd">${tbUpdated()}</p></div>`;
}

/* A name to show before the offers are in, or for a player no roster in the league holds: the search's row. */
function tpSearchRow(slug){
  const e = searchIndex().find(x => x.slug === slug);
  return e ? {name: e.n, pos: e.pos, team: e.team, slug} : {name: slug, pos: "", team: "", slug};
}

/* The hash the facts say: the side by the owner, only the players that fit it. Rewritten in place, so Back skips it. */
function tpCanon(route, facts){
  const want = tpHash(facts.side, facts.players.map(p => p.slug));
  if (facts.players.length && want !== navHash()){ history.replaceState(history.state, "", `#${want}`); TP_AT = want; }
}

function tpViewHTML(route){
  if (TP_AT !== navHash()){ TP_AT = navHash(); TP_OPEN = -1; }
  const lg = lbOf(lbLeagueKey()), me = lg && tbMine(lg), back = `<button type="button" class="lbp-back" data-tpback data-testid="tpg-back">${tfChev}<span>${t("tradepage.back")}</span></button>`;
  if (!myTeamLoad() || !lg || !me) return `<div class="wrap tf tpg">${back}${tfNeedHTML()}</div>`;
  return `<div class="wrap tf tpg" data-testid="tpg-page">${back}${tpBodyHTML(lg, me, route)}</div>`;
}

/* The files the page reads: today's offers and the reader's pinned file, side by side; one draw when both are in. */
function tpLoad(lg, me){
  if (TB_DATA && tpPinsOf(lg.key, me.name) !== undefined) return;
  const at = navHash();
  Promise.all([tbLoad(), tpPinsLoad(lg.key, me.name)]).then(() => { if (SURFACE === "trades" && !TB_EDIT && navHash() === at) render(); });
}

/* Make your own offer with him: Edit with him locked in YOU GET against his owner, or in YOU SEND against the best
   return's team (any team, picked on the page). */
function tpOwn(lg, me, btn){
  const facts = tpFacts(lg, me, tpRoute());
  if (!facts || !facts.owner) return;
  const keys = facts.players.map(tbKey);
  if (facts.side === "get"){
    const tm = lg.teams.find(x => x.name === facts.owner);
    return tm && tbEditOpen(lg, me, tm, {send: [], get: facts.players}, btn, false, keys);
  }
  const first = TF_SHOWN[0], tm = lg.teams.find(x => x.key !== me.key && (!first || x.name === first.partner)) || lg.teams.find(x => x.key !== me.key);
  return tm && tbEditOpen(lg, me, tm, {send: facts.players, get: []}, btn, true, keys);
}

function tpClick(e, lg, me){
  const hit = sel => e.target.closest(sel);
  if (hit("[data-tpback]")){ location.hash = "trades"; return; }
  const pick = hit("[data-pick]"), row = hit("[data-tprow]"), drop = hit("[data-tpdrop]"), edit = hit("[data-tbedit]"), copy = hit("[data-tbcopy]");
  if (pick) return pickTeam(pick.dataset.pick);
  if (!me) return;
  if (row){ const i = +row.dataset.tprow; TP_OPEN = TP_OPEN === i ? -1 : i; render(); return document.querySelector(`[data-tprow="${i}"]`)?.focus({preventScroll: true}); }
  if (drop){ const r = tpRoute(); location.hash = tpHash("send", r.slugs.filter(s => s !== drop.dataset.tpdrop)); return; }
  if (copy && TB_DATA) return tbCopy(copy);
  if (edit && TB_DATA){ const o = TF_SHOWN[+edit.dataset.tbedit], tm = o && lg.teams.find(x => x.name === o.partner); return tm && tbEditOpen(lg, me, tm, o, edit, false); }
  if (hit("[data-tpown]") && TB_DATA) return tpOwn(lg, me, hit("[data-tpown]"));
  if (hit("[data-tbretry]")){ TB_ERR = false; render(); tpLoad(lg, me); }
}

function wireTp(v){
  wireLgChip(v);
  const root = v.querySelector(".tpg"), lg = lbOf(lbLeagueKey()), me = lg && tbMine(lg);
  if (!root) return;
  if (me) tpLoad(lg, me);
  root.addEventListener("click", e => tpClick(e, lg, me));
  root.addEventListener("change", e => {
    if (!e.target.matches("[data-tpadd]") || !e.target.value) return;
    location.hash = tpHash("send", [...tpRoute().slugs, e.target.value]);
  });
}

/* A move between two of Trades' own hashes (a page, the finder, another page) leaves the view where it is, so nav.js
   draws nothing: this draws it, at the top. A move from another view is nav.js's (it opens Trades on the first part). */
window.addEventListener("hashchange", () => {
  if (SURFACE !== "trades" || navHash().split("/")[0] !== "trades") return;
  render();
  window.scrollTo({top: 0, behavior: "instant"});
});
