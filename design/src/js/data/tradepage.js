/* ============================== LEAGUE > TRADES: A PLAYER'S TRADE PAGE, THE LOGIC ==============================
   2026-10-08 (ledger #51, storyboard trades-pin draft B, which David picked). Pure, no DOM: data in, data out
   (tests/test_js_tradepage.py, in Node). One page per player, at its own hash so a link can be shared:
   `#trades/get/<slug>` lists every package that lands another team's player, `#trades/send/<slug>[+<slug>]` each
   team's best return for one or two of the reader's own. The page (surface/finder/tpage.js) draws what these return.

   Two sources. ff-jarvis's pinned search (#59, not landed on 2026-10-08), one file per owner at
   trade_pins/<league>/<owner-slug>.json: {updated, league, owner, players: {key: player}, offers: [...],
   get: {key: [offer index, up to 5] | {reason}}, send: {key: {partner: offer index} | {reason}}, pairs: [...]}.
   Where it has no entry for the player, or there is no file, today's trade_offers.json, filtered to him. A player
   with nothing carries one reason: the pinned search's code, or "today" (tonight's search found nothing for him). */
const TP_POS = ["QB", "RB", "WR", "TE"];       // the positions the search prices (ff-jarvis rules: QB, RB, WR, TE)
const TP_SIDES = {get: 1, send: 2};            // how many players a page is for: one to get; one to shop, or two at once (David 2a)
const TP_SLUG = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const TP_TODAY = "today";                      // the reason when today's file is the source and holds nothing for him

/* {side, slugs} for a trade page's hash (without the #), else null. */
function tpParse(hash){
  const m = /^trades\/(get|send)\/(.+)$/.exec(String(hash || ""));
  if (!m) return null;
  const slugs = m[2].split("+");
  if (slugs.length > TP_SIDES[m[1]] || !slugs.every(s => TP_SLUG.test(s)) || new Set(slugs).size !== slugs.length) return null;
  return {side: m[1], slugs};
}

const tpHash = (side, slugs) => `trades/${side}/${slugs.join("+")}`;

/* The profile footer's trade button: "get" for another team's player in the reader's league, "send" for the reader's own,
   null when nobody in that league has him, the reader has no team, or the search does not price his position. */
function tpAction(pos, ownerKey, meKey){
  if (!TP_POS.includes(pos) || !ownerKey || !meKey) return null;
  return ownerKey === meKey ? "send" : "get";
}

/* The two numbers a row shows: the reader's gain and the partner's. An offer with lenses (ledger #44) judges each side on
   its own lens (rest of season when the file names none), as the offer card does; one without shows the rest-of-season
   gains. null for a blank cell. */
function tpGains(o){
  if (o.lenses && o.lens){
    const cell = side => o.lenses[o.lens[side] || "ros"] || {};
    return {me: cell("me").gain ?? null, them: cell("them").their ?? null};
  }
  return {me: o.gain ?? null, them: (o.their || {}).gain ?? null};
}

/* Your gain first (David 1a); a tie goes to the smaller trade, then the partner's name. A blank gain sorts last. */
const tpMine = o => { const g = tpGains(o).me; return g === null ? -Infinity : g; };
const tpSize = o => o.send.length + o.get.length;
const tpOrder = (a, b) => tpMine(b) - tpMine(a) || tpSize(a) - tpSize(b) || a.partner.localeCompare(b.partner);

const tpHolds = (side, slugs) => o => slugs.every(s => (o[side] || []).some(p => p.slug === s));

/* The pinned search's key for a player: the slug itself, or the key whose player carries it. */
function tpKeyOf(pins, slug){
  if (pins.players && slug in pins.players) return slug;
  return Object.keys(pins.players || {}).find(k => (pins.players[k] || {}).slug === slug) || slug;
}

/* The pinned entry for a player on one side, or undefined when the search has none for him. */
const tpEntry = (pins, side, slug) => pins ? pins[side][tpKeyOf(pins, slug)] : undefined;
const tpReason = entry => entry && !Array.isArray(entry) && typeof entry.reason === "string" ? entry.reason : null;

/* Get: every package that lands him. {rows: [offer], reason}. */
function tpGet(pins, offers, slug){
  const entry = tpEntry(pins, "get", slug), why = tpReason(entry);
  if (why) return {rows: [], reason: why};
  const rows = Array.isArray(entry) ? entry.map(i => pins.offers[i]).filter(Boolean)
    : (offers || []).filter(tpHolds("get", [slug]));
  return rows.length ? {rows: [...rows].sort(tpOrder), reason: null} : {rows: [], reason: TP_TODAY};
}

/* The best offer per partner, then the order above. */
function tpBestPerPartner(list){
  const best = {};
  list.forEach(o => { if (!best[o.partner] || tpOrder(o, best[o.partner]) < 0) best[o.partner] = o; });
  return Object.values(best).sort(tpOrder);
}

/* Send: each team's best return for the player, or for both at once. `partners` is every other team's name in the
   league's order. {rows: [offer], none: [names of the teams with no offer], reason}. With no offer at all, one reason
   and no folded list. Two players filter the pinned offers (or today's) to those that send both; the search does not
   run pairs (storyboard README). */
function tpSend(pins, offers, slugs, partners){
  const one = slugs.length === 1, entry = one ? tpEntry(pins, "send", slugs[0]) : undefined, why = tpReason(entry);
  if (why) return {rows: [], none: [], reason: why};
  const pool = entry ? Object.values(entry).map(i => pins.offers[i]).filter(Boolean)
    : (one || !pins ? offers || [] : pins.offers).filter(tpHolds("send", slugs));
  const rows = tpBestPerPartner(pool);
  if (!rows.length) return {rows: [], none: [], reason: TP_TODAY};
  const have = new Set(rows.map(o => o.partner));
  return {rows, none: (partners || []).filter(n => !have.has(n)), reason: null};
}

/* The pinned file, only when it is this league's and this owner's and has its parts; else null (today's file then). */
function tpPinsFor(pins, lgKey, owner){
  const obj = x => !!x && typeof x === "object" && !Array.isArray(x);
  if (!obj(pins) || pins.league !== lgKey || pins.owner !== owner) return null;
  return Array.isArray(pins.offers) && obj(pins.get) && obj(pins.send) ? pins : null;
}

/* An owner's file name: his team's name in lower case, letters and digits, words joined by "-". */
const tpOwnerSlug = name => String(name).toLowerCase().replace(/'/g, "").replace(/[^a-z0-9]+/g, " ").trim().split(" ").join("-");
const tpPinsUrl = (lgKey, owner) => `trade_pins/${lgKey}/${tpOwnerSlug(owner)}.json`;

/* ledger #65 (2026-10-08): ff-jarvis's trade_pins/index.json {updated, rules, leagues: {league: {owner: "<league>/<name>.json"}}}
   names each owner's file, so our slug never has to match theirs. `tpPinsUrl` above is the old guess, kept for the
   test that pins it; the page asks the index. */
const TP_PINS_DIR = "trade_pins";
const TP_PINS_FILE = /^([a-z]+)\/([A-Za-z0-9][A-Za-z0-9._-]*)\.json$/;   // league folder, then one plain file name
const tpHas = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const tpPinsKey = (lgKey, owner) => `${lgKey}/${owner}`;

/* The owner's file path from the index, or null: no index, no such owner, or a path that is not <league>/<name>.json. */
function tpPinsFile(index, lgKey, owner){
  const obj = x => !!x && typeof x === "object" && !Array.isArray(x);
  const owners = obj(index) && obj(index.leagues) && tpHas(index.leagues, lgKey) ? index.leagues[lgKey] : null;
  const file = obj(owners) && tpHas(owners, owner) ? owners[owner] : null;
  const m = typeof file === "string" ? TP_PINS_FILE.exec(file) : null;
  return m && m[1] === lgKey && !file.includes("..") ? `${TP_PINS_DIR}/${file}` : null;
}

/* The pinned file with every player key of its offers replaced by the player object (the page draws objects; the file
   stores each player once, in `players`). A player object already in an offer stays. Null when a key has no player, so
   today's file serves instead of an offer with a hole in it. The given file is not changed. */
function tpPinsResolve(pins){
  if (!pins || typeof pins !== "object" || Array.isArray(pins) || !pins.players || typeof pins.players !== "object") return null;
  const who = k => typeof k !== "string" ? k : tpHas(pins.players, k) ? pins.players[k] : null;
  const list = ks => ks.map(who);
  const offers = (pins.offers || []).map(o => ({...o, send: list(o.send), get: list(o.get), drop: list(o.drop), ir_moves: list(o.ir_moves),
    their: {...o.their, ir_moves: list(o.their.ir_moves), drop: list(o.their.drop)}}));
  return offers.some(o => [o.send, o.get, o.drop, o.ir_moves, o.their.ir_moves, o.their.drop].some(l => l.includes(null))) ? null : {...pins, offers};
}
