/* ============================== LEAGUE > TRADES: A PLAYER'S TRADE PAGE, THE PINNED FILE ==============================
   2026-10-08 (ledger #51, #65). ff-jarvis's pinned search writes trade_pins/index.json and one file per owner. The page
   fetches the index once, finds the reader's owner in it (data/tradepage.js tpPinsFile, so our slug never has to match
   theirs), fetches that file the first time it opens a player's trade page and keeps the answer for the session, the file
   or null. Any failure (no index or file yet; offline; file://; another league's or owner's file; a player key with no
   player) is null, and the page fills from today's trade_offers.json instead.
   Never an error on screen: the pinned file adds rows, it is not needed for any. */
const TP_PINS = {};        // tpPinsKey -> the owner's pinned file (players resolved), or null once a fetch failed
const TP_PINS_BUSY = {};   // tpPinsKey -> the fetch in flight
let TP_INDEX = null;       // the index fetch: one promise for the session, resolving to the index or null

/* Resolves to trade_pins/index.json, or null. Never throws. */
function tpIndexLoad(){
  if (!TP_INDEX) TP_INDEX = (async () => {
    try {
      const r = await fetch(`${TP_PINS_DIR}/index.json`);
      return r.ok ? await r.json() : null;
    } catch (e) { return null; }
  })();
  return TP_INDEX;
}

/* Resolves to the pinned file for this owner, or null. Never throws. */
function tpPinsLoad(lgKey, owner){
  const key = tpPinsKey(lgKey, owner);
  if (key in TP_PINS) return Promise.resolve(TP_PINS[key]);
  if (TP_PINS_BUSY[key]) return TP_PINS_BUSY[key];
  TP_PINS_BUSY[key] = (async () => {
    let got = null;
    try {
      const url = tpPinsFile(await tpIndexLoad(), lgKey, owner);
      const r = url ? await fetch(url) : null;
      if (r && r.ok) got = tpPinsResolve(tpPinsFor(await r.json(), lgKey, owner));
    } catch (e) { got = null; }
    TP_PINS[key] = got;
    delete TP_PINS_BUSY[key];
    return got;
  })();
  return TP_PINS_BUSY[key];
}

/* The pinned file once its fetch settled (the file or null); undefined while it has not. */
const tpPinsOf = (lgKey, owner) => TP_PINS[tpPinsKey(lgKey, owner)];
