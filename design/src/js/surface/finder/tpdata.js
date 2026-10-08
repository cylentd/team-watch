/* ============================== LEAGUE > TRADES: A PLAYER'S TRADE PAGE, THE PINNED FILE ==============================
   2026-10-08 (ledger #51). ff-jarvis's pinned search writes one file per owner (data/tradepage.js has the shape); the
   page fetches the reader's own the first time it opens a player's trade page and keeps the answer for the session,
   the file or null. Any failure (no file yet: the build does not copy them until ff-jarvis #59 lands; offline;
   file://; another league's or owner's file) is null, and the page fills from today's trade_offers.json instead.
   Never an error on screen: the pinned file adds rows, it is not needed for any. */
const TP_PINS = {};        // url -> the owner's pinned file, or null once a fetch failed
const TP_PINS_BUSY = {};   // url -> the fetch in flight

/* Resolves to the pinned file for this owner, or null. Never throws. */
function tpPinsLoad(lgKey, owner){
  const url = tpPinsUrl(lgKey, owner);
  if (url in TP_PINS) return Promise.resolve(TP_PINS[url]);
  if (TP_PINS_BUSY[url]) return TP_PINS_BUSY[url];
  TP_PINS_BUSY[url] = (async () => {
    let got = null;
    try {
      const r = await fetch(url);
      if (r.ok) got = tpPinsFor(await r.json(), lgKey, owner);
    } catch (e) { got = null; }
    TP_PINS[url] = got;
    delete TP_PINS_BUSY[url];
    return got;
  })();
  return TP_PINS_BUSY[url];
}

/* The pinned file once its fetch settled (the file or null); undefined while it has not. */
const tpPinsOf = (lgKey, owner) => TP_PINS[tpPinsUrl(lgKey, owner)];
