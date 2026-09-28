/* ============================== LEAGUE > TRADES: the cards ==============================
   The heists, the trades that decided a season, and the curses. Data: LIVE_TRADES (design/league_trades.py,
   from ff-jarvis model.season.trade_verdicts). Every verdict here is the trade tree's: a player flipped
   later adds his share of what the flip brought back (David, 2026-09-28: "the most honest"). */

/* A declaration, not a const: the nav asks for it (navTabsOf) and must never meet it uninitialised. */
function trData(){ return typeof LIVE_TRADES !== "undefined" ? LIVE_TRADES : null; }
/* A manager by name; a key that is today's team id falls back to lgMgr (the league's name for him, else
   the team's), and a former manager without a name reads as one. */
const trName = key => {
  const n = (trData().names || {})[key];
  return n ? esc(n) : /^\d+$/.test(key) ? lgMgr(Number(key)) : t("trades.former");
};
const trById = id => trData().trades.find(x => x.id === id);
const trList = arr => arr.length ? arr.map(esc).join(", ") : t("trades.nothing");
const trPar = n => n.toFixed(1);

/* "9th": the only English the JS builds, for a finishing place. */
const trNth = n => n + ((n % 100 >= 11 && n % 100 <= 13) ? "th" : ({1: "st", 2: "nd", 3: "rd"}[n % 10] || "th"));

/* What a trade decided, one line each: the title, then each playoff spot or bye it moved. Keys are spelled
   out so assemble.py --check sees every one. */
function trDecidedHTML(tr){
  if (!tr.decided.length) return "";
  const line = d => {
    const v = {m: trName(d.m), y: tr.season, a: d.seed, b: d.without, fa: d.seed && trNth(d.seed), fb: d.without && trNth(d.without)};
    return {title: t("trades.dec.title", v), in: t("trades.dec.in", v), out: t("trades.dec.out", v),
            bye: t("trades.dec.bye", v), nobye: t("trades.dec.nobye", v)}[d.k];
  };
  return `<ul class="tr-dec">${tr.decided.map(d => `<li>${line(d)}</li>`).join("")}</ul>`;
}

const trFlips = side => side.via.length ? `<span class="tr-flip">${t("trades.row.via", {list: trList(side.via)})}</span>` : "";

function trHeistsHTML(){
  const cards = trData().heists.map(trById).map((tr, i) => `<article class="tr-card">
    <div class="tr-card-top"><span class="tr-rk">${i + 1}</span><h3>${t("trades.heist.head", {a: trName(tr.win.m), b: trName(tr.lose.m), n: trPar(tr.margin)})}
      <small>${t("trades.when", {y: tr.season, w: tr.week})}</small></h3></div>
    <dl class="tr-sides">
      <dt>${t("trades.heist.got", {m: trName(tr.win.m), list: trList(tr.win.got)})} ${trFlips(tr.win)}</dt><dd class="up">${trPar(tr.win.tree)}</dd>
      <dt>${t("trades.heist.got", {m: trName(tr.lose.m), list: trList(tr.lose.got)})}</dt><dd class="dn">${trPar(tr.lose.tree)}</dd>
    </dl>
    <p class="tr-after">${t("trades.heist.after", {a: trName(tr.win.m), ra: tr.win.after, b: trName(tr.lose.m), rb: tr.lose.after})}</p>
    ${trDecidedHTML(tr)}
  </article>`).join("");
  return `<section class="tr-sec"><h2 class="tr-hd">${t("trades.heist.title")}<span>${t("trades.heist.sub")}</span></h2>${cards}</section>`;
}

/* The title trade first, then every playoff spot or bye a trade moved; four show, the rest behind one tap. */
const TR_SHOWN = 4;
let TR_ALL = false;

function trDecidedBlockHTML(){
  const ids = trData().decided;
  if (!ids.length) return "";
  const cards = ids.map(trById).map((tr, i) => {
    const title = tr.decided.some(d => d.k === "title");
    return `<article class="tr-card${title ? " title" : ""}"${!TR_ALL && i >= TR_SHOWN ? " hidden" : ""}>
      ${title ? `<span class="tr-tag">${t("trades.dec.tag")}</span>` : ""}
      <h3>${t("trades.dec.head", {a: trName(tr.win.m), b: trName(tr.lose.m)})}
        <small>${t("trades.dec.when", {y: tr.season, w: tr.week, m: trName(tr.win.m), n: trPar(tr.margin)})}</small></h3>
      <p class="tr-swap">${t("trades.heist.got", {m: trName(tr.win.m), list: trList(tr.win.got)})} · ${t("trades.heist.got", {m: trName(tr.lose.m), list: trList(tr.lose.got)})}</p>
      ${trDecidedHTML(tr)}
    </article>`;
  }).join("");
  const more = !TR_ALL && ids.length > TR_SHOWN ? `<button type="button" class="tr-more" data-trall>${t("trades.dec.more", {n: ids.length})}</button>` : "";
  return `<section class="tr-sec tr-decided"><h2 class="tr-hd">${t("trades.dec.block")}<span>${t("trades.dec.sub", {n: ids.length})}</span></h2>
    ${cards}${more}<p class="tr-note">${t("trades.dec.note")}</p></section>`;
}

function trCurseHTML(c){
  const open = c.moves.find(m => m.open);
  const line = open ? t("trades.curse.lineOpen", {p: esc(c.player), n: c.n, y: open.season}) : t("trades.curse.line", {p: esc(c.player), n: c.n});
  const steps = c.moves.map(m => `<li class="${m.open ? "open" : ""}"><b>${t("trades.curse.step", {y: m.season, a: trName(m.from), b: trName(m.to)})}</b>
    <span class="${m.open ? "live" : m.lost ? "dn" : ""}">${m.open ? t("trades.curse.trails", {m: trName(m.from), n: trPar(m.margin)})
      : m.lost ? t("trades.curse.lost", {m: trName(m.from), n: trPar(m.margin)}) : t("trades.curse.won", {m: trName(m.from), n: trPar(m.margin)})}</span></li>`).join("");
  return `<div class="tr-curse"><h3>${t("trades.curse.name", {s: esc(c.surname)})}</h3><p>${line}</p><ol class="tr-chain">${steps}</ol></div>`;
}

/* The two strongest curses drawn as chains; the rest, and the hot potatoes, as one line each. */
function trCursesHTML(){
  const all = trData().curses, curses = all.filter(c => c.kind === "curse"), potatoes = all.filter(c => c.kind === "potato");
  if (!all.length) return "";
  const rest = curses.slice(2);
  return `<section class="tr-sec"><h2 class="tr-hd">${t("trades.curse.title")}<span>${t("trades.curse.sub")}</span></h2>
    ${curses.slice(0, 2).map(trCurseHTML).join("")}
    ${rest.length ? `<p class="tr-note">${t("trades.curse.also", {list: trList(rest.map(c => c.player))})}</p>` : ""}
    ${potatoes.length ? `<p class="tr-note">${t("trades.potato.line", {list: trList(potatoes.map(c => c.player))})}</p>` : ""}
  </section>`;
}
