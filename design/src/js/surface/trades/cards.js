/* ============================== LEAGUE > TRADES: the cards ==============================
   The heists, the trades that decided a season, and the curses. Data: LIVE_TRADES (design/league_trades.py,
   from ff-jarvis model.season.trade_verdicts). Every verdict here is the trade tree's: a player flipped
   later adds his share of what the flip brought back (David, 2026-09-28: "the most honest").

   One card system, the box score (David chose A of two, 2026-09-28, storyboard
   https://claude.ai/artifact/57FSz4b4TrAxrb79EJJXjp): a header strip (what and when), a body, a footnote.
   A trade's body is its two sides as rows, the scores in one right-hand column where they compare. */

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

/* Each decided line leads with what it did to that manager: a trophy for the title, an arrow up for a
   playoff spot or bye gained, down for one lost. Keys are spelled out so assemble.py --check sees each. */
const TR_ICON = {
  title: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2h8v3a4 4 0 0 1-8 0zM4 3H2v1.5A2.5 2.5 0 0 0 4.5 7M12 3h2v1.5A2.5 2.5 0 0 1 11.5 7M8 9v3M5 14h6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  up: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 13V3M3.5 7.5 8 3l4.5 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  dn: `<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 3v10M3.5 8.5 8 13l4.5-4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  flame: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c1 4 5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 2-4 0 2 1 3 2 3-1-3 0-6 1-9z" fill="currentColor"/></svg>`,
};
const TR_DEC_DIR = {title: "title", in: "up", bye: "up", out: "dn", nobye: "dn"};

function trDecidedHTML(tr){
  if (!tr.decided.length) return "";
  const line = d => {
    const v = {m: trName(d.m), y: tr.season, a: d.seed, b: d.without, fa: d.seed && trNth(d.seed), fb: d.without && trNth(d.without)};
    return {title: t("trades.dec.title", v), in: t("trades.dec.in", v), out: t("trades.dec.out", v),
            bye: t("trades.dec.bye", v), nobye: t("trades.dec.nobye", v)}[d.k];
  };
  return `<ul class="tr-dec">${tr.decided.map(d => `<li class="${TR_DEC_DIR[d.k]}">${TR_ICON[TR_DEC_DIR[d.k]]}<span>${line(d)}</span></li>`).join("")}</ul>`;
}

const trFlips = side => side.via.length ? `<span class="tr-flip">${t("trades.row.via", {list: trList(side.via)})}</span>` : "";

/* A traded player is a face and a name, so who moved reads before any number (David, 2026-09-28:
   "hard to see who got traded"). The head where ff-jarvis has one (~60% of traded players; the
   retired ones have none), else his initials in the same circle. */
const trFace = (name, slug) => `<span class="tr-face">${slug && HEADS[slug] ? headImgHTML(HEADS[slug], initials(name), slug, 32)
  : `<span class="fallback">${esc(initials(name))}</span>`}</span>`;
const trPlayersHTML = (names, slugs) => names.length
  ? `<ul class="tr-pls">${names.map((n, i) => `<li>${trFace(n, slugs[i])}<b>${esc(n)}</b></li>`).join("")}</ul>`
  : `<p class="tr-none-got">${t("trades.nothing")}</p>`;

/* The box: a header strip (left what, right when or how many), the body, a footnote when there is one. */
const trBox = (cls, left, right, body, foot = "") => `<article class="tr-bx ${cls}">
  <div class="tr-bx-hd"><span class="tr-bx-t">${left}</span><span>${right}</span></div>${body}${foot ? `<div class="tr-bx-ft">${foot}</div>` : ""}</article>`;
/* A trade's two sides as rows, winner first: the manager, what he got, his score in the right column. */
const trScoreRows = tr => `<table class="tr-sc">${[[tr.win, "tr-w"], [tr.lose, "tr-l"]].map(([s, k]) => `<tr class="${k}">
  <th scope="row">${trName(s.m)}</th><td>${trPlayersHTML(s.got, s.slugs)}${trFlips(s)}</td><td class="tr-n">${trPar(s.tree)}</td></tr>`).join("")}</table>`;

function trHeistsHTML(){
  const cards = trData().heists.map(trById).map((tr, i) => trBox("", `<b class="tr-rk">${t("trades.heist.rank", {n: i + 1})}</b>`,
    t("trades.when", {y: tr.season, w: tr.week}), trScoreRows(tr),
    `<p class="tr-bx-say">${t("trades.heist.head", {a: trName(tr.win.m), b: trName(tr.lose.m), n: trPar(tr.margin)})}</p>
     <p>${t("trades.heist.after", {a: trName(tr.win.m), ra: tr.win.after, b: trName(tr.lose.m), rb: tr.lose.after})}</p>${trDecidedHTML(tr)}`)).join("");
  return `<section class="tr-sec tr-heists"><h2 class="tr-hd">${t("trades.heist.title")}<span>${t("trades.heist.sub")}</span></h2>${cards}</section>`;
}

/* The title trade stays first; the other slots shuffle through every playoff spot or bye a trade moved,
   a new set every 10 s while the section is on screen and nobody is touching it (wireTrades). David,
   2026-09-28: "make the page feel alive", an exception to STYLE.md's no-timers rule, with its guards.
   Show all lays every card out and stops the shuffle. */
const TR_SHOWN = 4;
let TR_ALL = false;
let TR_ROT = 0;   // where the shuffle's window over the non-title cards starts

function trDecidedShown(){
  const ids = trData().decided, title = ids.filter(id => trById(id).decided.some(d => d.k === "title"));
  const rest = ids.filter(id => !title.includes(id)), n = Math.max(0, TR_SHOWN - title.length);
  if (TR_ALL || rest.length <= n) return {show: TR_ALL ? ids : [...title, ...rest], rotating: false, n};
  return {show: [...title, ...Array.from({length: n}, (_, k) => rest[(TR_ROT + k) % rest.length])], rotating: true, n};
}

function trDecidedBlockHTML(fresh = false){
  const ids = trData().decided;
  if (!ids.length) return "";
  const {show, rotating} = trDecidedShown();
  const cards = show.map(trById).map((tr, i) => {
    const title = tr.decided.some(d => d.k === "title");
    return trBox(`${title ? "title" : ""}${fresh && !title ? " tr-fresh" : ""}`,
      title ? `${TR_ICON.title}${t("trades.dec.tag")}` : t("trades.when", {y: tr.season, w: tr.week}),
      title ? t("trades.when", {y: tr.season, w: tr.week}) : "", trScoreRows(tr),
      `<p>${t("trades.dec.won", {m: trName(tr.win.m), n: trPar(tr.margin)})}</p>${trDecidedHTML(tr)}`)
      .replace("<article", `<article style="--i:${i}"`);
  }).join("");
  const more = !TR_ALL && ids.length > TR_SHOWN ? `<button type="button" class="tr-more" data-trall>${t("trades.dec.more", {n: ids.length})}</button>` : "";
  return `<section class="tr-sec tr-decided"><h2 class="tr-hd">${t("trades.dec.block")}<span>${t("trades.dec.sub", {n: ids.length})}</span></h2>
    ${rotating ? `<div class="tr-shuffle" aria-hidden="true"><i></i></div>` : ""}<div class="tr-grid">${cards}</div>${more}<p class="tr-note">${t("trades.dec.note")}</p></section>`;
}

/* The curse's mark (David chose it from five, 2026-09-28): his face drained of colour in front of black
   fire, and under it one skull per trade of him, red where the sender lost, hollow amber for the one
   still open, so "3 of 3" is counted without reading. The fire is one outline drawn three times,
   smaller and darker toward its core; every sender of a curse lost, so there is no third skull. */
const TR_FIRE = `M14 84 C6 68 12 55 20 46 C20 55 23 59 27 58 C22 44 26 29 36 17 C36 28 39 33 43 34
  C41 22 45 11 51 2 C54 13 58 23 61 30 C63 23 67 17 74 12 C72 25 70 35 72 44 C75 40 79 38 85 33
  C90 49 88 67 82 84 Z`;
const trSkull = (m, i) => `<svg class="tr-skull${m.open ? " live" : ""}" style="--i:${i}" viewBox="0 0 18 18" aria-hidden="true">
  <path class="bone" d="M9 1.6c-4 0-6.5 2.7-6.5 6.1 0 2 1 3.4 2.3 4.2V15h8.4v-3.1c1.3-.8 2.3-2.2 2.3-4.2 0-3.4-2.5-6.1-6.5-6.1z"/>
  <circle class="eye" cx="6.5" cy="8" r="1.7"/><circle class="eye" cx="11.5" cy="8" r="1.7"/><path class="teeth" d="M7.6 15v-2.2M10.4 15v-2.2"/></svg>`;
function trMarkHTML(c, i){
  const layer = (s, cls, fill = "") => `<path class="${cls}"${fill} d="${TR_FIRE}" transform="translate(48 92) scale(${s}) translate(-48 -86)"/>`;
  // A button: a tap flares the fire and counts the skulls in (wireTrades, trades.css).
  return `<button type="button" class="tr-mark" data-trcurse aria-label="${t("trades.curse.name", {s: esc(c.surname)})}"><div class="tr-fire"><svg viewBox="0 0 96 96" aria-hidden="true">
      <defs><linearGradient id="tr-fire-${i}" x1="0" y1="1" x2="0" y2="0"><stop class="s1" offset="0"/><stop class="s2" offset=".6"/><stop class="s3" offset="1"/></linearGradient></defs>
      ${layer(1.3, "rim", ` fill="url(#tr-fire-${i})"`)}${layer(1.05, "mid")}${layer(.82, "core")}</svg>
    ${trFace(c.player, c.slug)}</div><div class="tr-skulls">${c.moves.map(trSkull).join("")}</div></button>`;
}

/* A curse's box score: the mark and its name, then each trade of him a row, the sender's loss in the
   right column (red, or amber for the one still open). */
function trCurseHTML(c, i){
  const open = c.moves.find(m => m.open);
  const line = open ? t("trades.curse.lineOpen", {p: esc(c.player), n: c.n, y: open.season}) : t("trades.curse.line", {p: esc(c.player), n: c.n});
  const rows = c.moves.map(m => `<tr><td class="tr-y">${m.season}</td>
    <th scope="row">${t("trades.curse.step", {a: trName(m.from), b: trName(m.to)})}</th>
    <td class="tr-n ${m.open ? "live" : m.lost ? "dn" : "up"}">${m.open ? t("trades.curse.trails", {n: trPar(m.margin)})
      : m.lost ? t("trades.curse.lost", {n: trPar(m.margin)}) : t("trades.curse.won", {n: trPar(m.margin)})}</td></tr>`).join("");
  return trBox("tr-curse", `${TR_ICON.flame}${t("trades.curse.hd")}`,
    open ? t("trades.curse.countOpen", {n: c.n}) : t("trades.curse.count", {n: c.n}),
    `<div class="tr-curse-top">${trMarkHTML(c, i)}<div><h3>${t("trades.curse.name", {s: esc(c.surname)})}</h3><p>${line}</p></div></div>
     <table class="tr-sc tr-chain">${rows}</table>`);
}

/* The two strongest curses as boxes; the rest, and the hot potatoes, as faces in a box each under them. */
function trCursesHTML(){
  const all = trData().curses, curses = all.filter(c => c.kind === "curse"), potatoes = all.filter(c => c.kind === "potato");
  if (!all.length) return "";
  const rest = curses.slice(2);
  const faces = (left, right, cs) => trBox("tr-rest", left, right, `<div class="tr-bx-in">${trPlayersHTML(cs.map(c => c.player), cs.map(c => c.slug))}</div>`);
  return `<section class="tr-sec tr-curses"><h2 class="tr-hd">${t("trades.curse.title")}<span>${t("trades.curse.sub")}</span></h2>
    <div class="tr-grid">${curses.slice(0, 2).map(trCurseHTML).join("")}
      ${rest.length ? faces(t("trades.curse.also"), rest.length, rest) : ""}${potatoes.length ? faces(t("trades.potato.hd"), t("trades.potato.line"), potatoes) : ""}</div>
  </section>`;
}
