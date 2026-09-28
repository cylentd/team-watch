/* The same slug rule build.py uses, for a player the headshot set does not know. */
const slugOf = n => n.toLowerCase().replace(/[^a-z0-9 ]/g, "").split(/\s+/).filter(w => !["jr","sr","ii","iii","iv","v"].includes(w)).join("-");
const lastName = n => n.replace(/\s+(Jr|Sr|II|III|IV|V)\.?$/i, "").trim().split(" ").slice(-1)[0];
/* A line's game log drew here as an inline chart under the row until 2026-09-27; it is the leg
   sheet's bars now (legsheet.js), read from the same LIVE_MARKET.logs. */

const INJ = {Q:"Q", O:"O", OUT:"OUT", IR:"IR", SUSP:"SUSP", PUP:"PUP", D:"D"};
